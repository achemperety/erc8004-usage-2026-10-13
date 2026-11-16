"""Addendum D, update 2026-11-16: late-range positive control for the log reader (closes, or not, caveat 2 of
addendum D). Suggested by RealSpap, Ethereum Magicians topic 25098, post #453.

Same reader, same chunking, same range, same two nodes as the all-topics read of addendum D, on contracts known to
emit logs late in the range: the ERC-8004 IdentityRegistry (Registered) and ReputationRegistry (NewFeedback) on
Ethereum mainnet, at the addresses and topic0s of the 13 October scan (E.ADDR, E.event_sig from the vendored ABIs).

  range   24,204,475 - 26,427,741 (RealSpap's all-topics range, post #451)
  nodes   https://mainnet.gateway.tenderly.co, https://rpc.mevblocker.io/fast (one URL per client, no failover)
  reader  erc8004_usage.scan_parallel, UNCHANGED (filtered on topic0), initial chunk 10,000, max chunk 500,000

Pass criteria, each event, each node:
  1. at least one log in the last 10 % of the range (block > 26,205,415); the last log's block is reported;
  2. the two nodes return identical (block, tx, logIndex) sets; duplicates dropped by the reader are reported;
  3. the count over [24,204,475, 26,182,323] equals the published 13 October Ethereum count (output/counts/1_*.json).
     The published counts are totals only, scanned from the registries' deploy blocks (24,339,871 / 24,339,873). The
     restriction is made exact here by counting [24,204,475, deploy-1] directly (must be 0) and by checking
     eth_getCode is empty at deploy-1 on each node.

Read-only: eth_chainId, eth_blockNumber, eth_getBlockByNumber, eth_getCode, eth_getLogs. No key, no signing.
The JSON keeps counts, deciles, the last logs and a SHA-256 of each node's sorted (block, tx, logIndex) list, not all
logs (about 80,000).

Usage, from the repo root:
  python3 -I addenda/2026-11-16_late_range_control.py addenda/2026-11-16_late_range_control.json
"""
import hashlib, json, os, sys, time, traceback, concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import erc8004_usage as E                     # noqa: E402

# the scanner's log() appends to output/run.log; this addendum must not touch the original output
E.log = lambda *a: print("[log]", *a, file=sys.stderr, flush=True)

OUTP = sys.argv[1]
NODES = {"tenderly": "https://mainnet.gateway.tenderly.co", "mevblocker": "https://rpc.mevblocker.io/fast"}
LO, HI = 24204475, 26427741                  # all-topics range of addendum D (RealSpap, post #451)
N = HI - LO + 1                              # 2,223,267 blocks
LAST10_ABOVE = 26205415                      # "last 10 %": blocks above this
SNAPSHOT = 26182323                          # 13 October as-of block, Ethereum (output/as_of.json)
KW = {"init_chunk": 10_000, "max_chunk": 500_000}   # addendum D chunk sizes
TARGETS = [("identity", "Registered"), ("reputation", "NewFeedback")]
# decile d (0..9) = [LO + floor(d*N/10), LO + floor((d+1)*N/10) - 1]
DECILES = [(LO + d * N // 10, LO + (d + 1) * N // 10 - 1) for d in range(10)]


def sha256_file(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


class PointRetryRpc(E.Rpc):
    """As in addenda/2026-11-16_cb1b_ethereum.py: eth_getLogs unchanged (the reader splits a range that fails);
    point reads retried up to 5 times on RpcFail."""
    def call(self, method, params, tries=3):
        if method == "eth_getLogs":
            return super().call(method, params, tries)
        for i in range(5):
            try:
                return super().call(method, params, tries)
            except E.RpcFail:
                if i == 4:
                    raise
                time.sleep(3 * (i + 1))


def canon(keys):
    return hashlib.sha256("\n".join(f"{b},{t},{i}" for b, t, i in keys).encode()).hexdigest()


def one(node, url, reg, ev, deploy, published):
    rpc = PointRetryRpc([url])
    addr = E.ADDR[reg]
    sig, t0 = E.event_sig(reg, ev)
    o = {"address": addr, "event": ev, "signature": sig, "topic0": t0}
    o["code_at_deploy_minus_1"] = E.has_code(rpc, addr, deploy - 1)
    o["code_at_deploy"] = E.has_code(rpc, addr, deploy)
    started = time.time()
    r = E.scan_parallel(rpc, addr, t0, LO, HI, keep_logs=True, tag=f"{node} {ev}", **KW)
    if r["incomplete"]:
        raise E.ScanError(f"{node} {ev}: incomplete scan")
    keys = sorted((l["block"], l["tx"].lower(), l["logIndex"]) for l in r["logs"])
    o["reader"] = {k: v for k, v in r.items() if k != "logs"}
    o["wall_s"] = round(time.time() - started, 1)
    o["count"] = len(keys)
    o["by_decile"] = [sum(1 for b, _, _ in keys if a <= b <= z) for a, z in DECILES]
    o["count_above_last10_threshold"] = sum(1 for b, _, _ in keys if b > LAST10_ABOVE)
    o["count_lo_to_deploy_minus_1"] = sum(1 for b, _, _ in keys if b < deploy)
    o["count_lo_to_snapshot"] = sum(1 for b, _, _ in keys if b <= SNAPSHOT)
    o["count_deploy_to_snapshot"] = sum(1 for b, _, _ in keys if deploy <= b <= SNAPSHOT)
    o["count_after_snapshot"] = sum(1 for b, _, _ in keys if b > SNAPSHOT)
    o["published"] = published
    o["equals_published"] = o["count_lo_to_snapshot"] == published["count"]
    o["first_log"] = list(keys[0]) if keys else None
    o["last_logs"] = [list(k) for k in keys[-5:]]
    if keys:
        o["last_log_block"] = keys[-1][0]
        o["last_log_utc"] = E.iso(E.block_ts(rpc, keys[-1][0]))
        o["last_log_fraction_of_range"] = round((keys[-1][0] - LO) / (HI - LO), 6)
    o["keys_sha256"] = canon(keys)
    o["rpc_requests"] = rpc.calls
    o["pass_last10"] = o["count_above_last10_threshold"] >= 1
    return o, keys


def per_node(node, url, deploy, published):
    rpc = PointRetryRpc([url])
    out = {"url": url, "chainId": int(rpc.call("eth_chainId", []), 16)}
    assert out["chainId"] == 1, out["chainId"]
    out["head_at_run"] = E.get_head(rpc)
    out["range_end_within_head_minus_safety"] = HI <= out["head_at_run"] - E.SAFETY_BLOCKS
    if not out["range_end_within_head_minus_safety"]:
        raise E.ScanError(f"range end {HI} > head {out['head_at_run']} - {E.SAFETY_BLOCKS}")
    out["events"], keys = {}, {}
    for reg, ev in TARGETS:                  # sequential per node, the two nodes run in parallel
        out["events"][ev], keys[ev] = one(node, url, reg, ev, deploy[reg], published[ev])
    return out, keys


def main():
    dep = json.load(open(os.path.join(ROOT, "output", "deploy_blocks.json")))["1"]
    deploy = {reg: dep[reg]["block"] for reg, _ in TARGETS}
    published = {}
    for reg, ev in TARGETS:
        p = json.load(open(os.path.join(ROOT, "output", "counts", f"1_{reg}_{ev}.json")))
        assert p["address"].lower() == E.ADDR[reg].lower() and p["topic0"].lower() == E.event_sig(reg, ev)[1].lower()
        assert p["to_block"] == SNAPSHOT and p["status"] == "complete" and not p["incomplete"]
        published[ev] = {k: p[k] for k in ("count", "from_block", "to_block", "first_block", "last_block", "chunks",
                                           "splits", "duplicates_dropped", "rpc_endpoints_used")}
        published[ev]["file"] = f"output/counts/1_{reg}_{ev}.json"
        published[ev]["file_sha256"] = sha256_file(os.path.join(ROOT, published[ev]["file"]))
    rec = {"run_started_utc": E.now(), "range": [LO, HI], "range_blocks": N, "last10_threshold_above": LAST10_ABOVE,
           "snapshot_block": SNAPSHOT, "deciles": DECILES, "chunking": KW, "deploy_blocks": deploy,
           "suggested_by": "RealSpap, ethereum-magicians topic 25098 post #453",
           "reader": {"function": "erc8004_usage.scan_parallel (unchanged)",
                      "erc8004_usage.py_sha256": sha256_file(os.path.join(ROOT, "erc8004_usage.py"))}}
    rec["nodes"], allkeys = {}, {}
    with cf.ThreadPoolExecutor(2) as ex:
        futs = {n: ex.submit(per_node, n, u, deploy, published) for n, u in NODES.items()}
        for n, f in futs.items():
            try:
                rec["nodes"][n], allkeys[n] = f.result()
            except Exception as x:
                rec["nodes"][n] = {"url": NODES[n], "error": f"{type(x).__name__}: {str(x)[:300]}",
                                   "traceback_tail": traceback.format_exc()[-800:]}
    if len(allkeys) == 2:
        a, b = allkeys["tenderly"], allkeys["mevblocker"]
        rec["comparison"] = {}
        for _, ev in TARGETS:
            sa, sb = set(a[ev]), set(b[ev])
            rec["comparison"][ev] = {"identical": a[ev] == b[ev], "only_tenderly": len(sa - sb), "only_mevblocker": len(sb - sa),
                                     "only_tenderly_examples": sorted(sa - sb)[:10], "only_mevblocker_examples": sorted(sb - sa)[:10]}
        rec["all_pass"] = all(
            rec["comparison"][ev]["identical"]
            and all(rec["nodes"][n]["events"][ev]["pass_last10"] and rec["nodes"][n]["events"][ev]["equals_published"]
                    and rec["nodes"][n]["events"][ev]["count_lo_to_deploy_minus_1"] == 0
                    and not rec["nodes"][n]["events"][ev]["code_at_deploy_minus_1"]
                    for n in NODES)
            for _, ev in TARGETS)
    rec["run_finished_utc"] = E.now()
    json.dump(rec, open(OUTP, "w"), indent=1, sort_keys=True)
    print(json.dumps(rec, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
