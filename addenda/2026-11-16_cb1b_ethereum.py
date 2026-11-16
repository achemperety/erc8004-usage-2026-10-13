"""Addendum D 2026-11-16: ValidationRequest / ValidationResponse at the second Validation proxy
0x8004Cb1BF31DAf7788923b405b754f57acEB4272 on Ethereum mainnet, which the 13 October scan did not read.

Read-only: eth_chainId, eth_blockNumber, eth_getBlockByNumber, eth_getCode, eth_getStorageAt, eth_getLogs,
eth_getTransactionByHash, eth_call. No key, no signing, no transaction.

Reuses the scanner of the 13 October run (erc8004_usage.py): event_sig (topics from the vendored ABI), corrupt,
Rpc, scan_parallel (the log reader, with its split-on-error / split-on-cap / re-check rules), and the chunk sizes that
run used on Ethereum (scan_kw for chainId 1: init 10,000, max 500,000 blocks). Each node is a separate Rpc with a
single URL, so there is no failover between nodes: every number is per node.

Usage, from the repo root:
  python3 -I addenda/2026-11-16_cb1b_ethereum.py addenda/2026-11-16_cb1b_ethereum.json
"""
import json, os, sys, time, traceback, datetime as dt, concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import erc8004_usage as E                     # noqa: E402
from web3 import Web3                         # noqa: E402

# the scanner's log() appends to output/run.log; this addendum must not touch the original output
E.log = lambda *a: print("[log]", *a, file=sys.stderr, flush=True)

OUTP = sys.argv[1]
NODES = {"tenderly": "https://mainnet.gateway.tenderly.co", "mevblocker": "https://rpc.mevblocker.io/fast"}
CB1B = "0x8004Cb1BF31DAf7788923b405b754f57acEB4272"
SNAPSHOT = 26182323                          # output/as_of.json["1"]["to_block"]
SEARCH_FLOOR = 23479244                      # output/deploy_blocks.json["1"][*]["search_window_start"] (first block >= 2025-10-01)
EIP1967_IMPL = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
PRE_DEPLOY_SPAN = 200_000                    # control (a) of the original design
KW = {"init_chunk": 10_000, "max_chunk": 500_000}   # == E.scan_kw(rpc_selection, 1) of the 13 October run
CLAIMED = {"creation_block": 24204475, "switch_block": 24204487, "switch_utc": "2026-01-10T13:06:11Z", "upgraded_events": 3}

T_REQ = E.event_sig("validation", "ValidationRequest")[1]
T_RESP = E.event_sig("validation", "ValidationResponse")[1]
T_UPG = E.event_sig("validation", "Upgraded")[1]
VAL_TOPICS = [T_REQ, T_RESP]

abi = json.load(open(os.path.join(ROOT, "abis", "ValidationRegistry.json")))
abi = abi["abi"] if isinstance(abi, dict) else abi
def _ty(i): return i["type"] if not i["type"].startswith("tuple") else "(" + ",".join(_ty(c) for c in i["components"]) + ")" + i["type"][5:]
SELECTORS = {f"{f['name']}({','.join(_ty(i) for i in f['inputs'])})": None for f in abi
             if f.get("type") == "function" and f["name"] in ("validationRequest", "validationResponse", "getValidationStatus")}
for s in SELECTORS:
    SELECTORS[s] = "0x" + Web3.keccak(text=s).hex().removeprefix("0x")[:8]
SEL_GET_IDENTITY = "0x" + Web3.keccak(text="getIdentityRegistry()").hex().removeprefix("0x")[:8]
SEL_OWNER_OF = "0x6352211e"


def iso(ts): return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def addr_of_word(w): return "0x" + w[-40:].lower()


def code(rpc, a, b): return rpc.call("eth_getCode", [a, hex(b)]).lower()
def slot(rpc, b): return addr_of_word(rpc.call("eth_getStorageAt", [CB1B, EIP1967_IMPL, hex(b)]))


def creation_block(rpc, hi):
    probes = []
    lo_has, hi_has = E.has_code(rpc, CB1B, SEARCH_FLOOR), E.has_code(rpc, CB1B, hi)
    probes += [(SEARCH_FLOOR, lo_has), (hi, hi_has)]
    if lo_has or not hi_has:
        return {"status": "not_resolved", "probes": probes}
    lo = SEARCH_FLOOR                          # invariant: no code at lo, code at hi
    while hi - lo > 1:
        mid = (lo + hi) // 2
        h = E.has_code(rpc, CB1B, mid); probes.append((mid, h))
        if h: hi = mid
        else: lo = mid
    return {"status": "resolved", "block": hi, "code_at_block": E.has_code(rpc, CB1B, hi),
            "no_code_at_prev_block": not E.has_code(rpc, CB1B, hi - 1), "n_probes": len(probes),
            "search_window": [SEARCH_FLOOR, probes[1][0]]}


def selector_check(c):
    return {s: ("present" if ("63" + sel[2:]) in c else "absent") for s, sel in sorted(SELECTORS.items())}


def sc(rpc, topics, lo, hi, keep=False):
    r = E.scan_parallel(rpc, CB1B, topics, lo, hi, keep_logs=keep, tag="", **KW)
    if r["incomplete"]:
        raise E.ScanError(f"incomplete scan [{lo},{hi}]")
    return r


class PointRetryRpc(E.Rpc):
    """E.Rpc, unchanged for eth_getLogs (the scanner splits a range that times out). Point reads (eth_getCode,
    eth_getStorageAt, eth_getBlockByNumber, ...) are retried up to 5 times on RpcFail, because E.Rpc does not retry a
    timeout and a single timed-out point read would otherwise abort the node's whole run (run 1, mevblocker)."""
    def call(self, method, params, tries=3):
        if method == "eth_getLogs":
            return super().call(method, params, tries)
        for k in range(5):
            try:
                return super().call(method, params, tries)
            except E.RpcFail:
                if k == 4:
                    raise
                time.sleep(3 * (k + 1))


def per_node(name, url, head_fixed):
    rpc = PointRetryRpc([url])
    out = {"url": url}
    out["chainId"] = int(rpc.call("eth_chainId", []), 16)
    assert out["chainId"] == 1, out["chainId"]
    out["head_at_run"] = E.get_head(rpc)

    # step 3: creation block
    cr = creation_block(rpc, SNAPSHOT)
    out["creation"] = cr
    C = cr["block"]
    out["creation"]["block_utc"] = iso(E.block_ts(rpc, C))
    out["creation"]["runtime_code"] = {"bytes": (len(code(rpc, CB1B, C)) - 2) // 2,
                                       "keccak": Web3.keccak(hexstr=code(rpc, CB1B, C)).hex()}

    # step 4: implementation slot, Upgraded logs (the positive control uses the same reader and chunking)
    upg_snap = sc(rpc, T_UPG, C, SNAPSHOT, keep=True)
    upg_head = sc(rpc, T_UPG, C, head_fixed, keep=True)
    ups = []
    for l in upg_head["logs"]:
        b = l["block"]
        ups.append({"block": b, "utc": iso(E.block_ts(rpc, b)), "tx": l["tx"], "logIndex": l["logIndex"],
                    "implementation": addr_of_word(l["topics"][1]),
                    "slot_at_block_minus_1": slot(rpc, b - 1) if b > C else "(before creation)",
                    "slot_at_block": slot(rpc, b)})
    out["upgraded"] = {"count_to_snapshot": upg_snap["count"], "count_to_head": upg_head["count"], "events": ups,
                       "chunks_to_head": upg_head["chunks"], "splits_to_head": upg_head["splits"]}
    out["slot"] = {"at_creation": slot(rpc, C), "at_snapshot": slot(rpc, SNAPSHOT), "at_head_fixed": slot(rpc, head_fixed)}
    if CLAIMED["switch_block"] > C:
        out["slot"]["at_24204486"] = slot(rpc, CLAIMED["switch_block"] - 1)
        out["slot"]["at_24204487"] = slot(rpc, CLAIMED["switch_block"])

    # step 5: selectors in each implementation's runtime code
    impls = sorted({u["implementation"] for u in ups} | {v for v in out["slot"].values()})
    out["implementations"] = {}
    for im in impls:
        first = min([u["block"] for u in ups if u["implementation"] == im], default=C)
        rec = {}
        for tag, b in (("at_first_upgrade_block", first), ("at_head_fixed", head_fixed)):
            c = code(rpc, im, b)
            rec[tag] = {"block": b, "bytes": (len(c) - 2) // 2, "keccak": Web3.keccak(hexstr=c).hex(), "selectors": selector_check(c)}
        out["implementations"][im] = rec

    # step 6: counts (OR-topic scan, as in the original count), from the creation block
    ranges = {"creation_to_snapshot": (C, SNAPSHOT), "creation_to_head": (C, head_fixed),
              "creation_to_24204486": (C, CLAIMED["switch_block"] - 1)}
    out["counts"] = {}
    logs_head = []
    for k, (lo, hi) in ranges.items():
        if hi < lo:
            out["counts"][k] = {"range": [lo, hi], "note": "empty range"}; continue
        r = sc(rpc, VAL_TOPICS, lo, hi, keep=True)
        out["counts"][k] = {"range": [lo, hi], "ValidationRequest": r["by_topic"].get(T_REQ.lower(), 0),
                            "ValidationResponse": r["by_topic"].get(T_RESP.lower(), 0), "chunks": r["chunks"],
                            "splits": r["splits"], "duplicates_dropped": r["duplicates_dropped"]}
        if k == "creation_to_head":
            logs_head = r["logs"]

    # step 7: negative controls
    a = sc(rpc, VAL_TOPICS, C - PRE_DEPLOY_SPAN, C - 1)
    bad = [E.corrupt(t) for t in VAL_TOPICS]
    b = sc(rpc, bad, C, head_fixed)
    out["controls"] = {
        "a_pre_deployment": {"range": [C - PRE_DEPLOY_SPAN, C - 1], "count": a["count"], "pass": a["count"] == 0},
        "b_corrupted_topic0": {"range": [C, head_fixed], "topics": bad, "count": b["count"], "pass": b["count"] == 0},
        "b_prime_true_topic0_same_range": out["counts"]["creation_to_head"]["ValidationRequest"] + out["counts"]["creation_to_head"]["ValidationResponse"],
        "c_positive_upgraded": {"range": [C, head_fixed], "count": upg_head["count"],
                                "every_log_matches_slot_transition": bool(ups) and all(
                                    u["slot_at_block"] == u["implementation"] and u["slot_at_block_minus_1"] != u["implementation"]
                                    for u in ups if u["block"] > C) and all(u["slot_at_block"] == u["implementation"] for u in ups if u["block"] == C),
                                "slot_at_head_equals_last_upgraded": bool(ups) and out["slot"]["at_head_fixed"] == ups[-1]["implementation"]},
    }
    pc = out["controls"]["c_positive_upgraded"]
    pc["pass"] = pc["count"] >= 1 and pc["every_log_matches_slot_transition"] and pc["slot_at_head_equals_last_upgraded"]

    # step 8 (raw material): every validation log with tx sender
    evs = []
    for l in logs_head:
        tx = rpc.call("eth_getTransactionByHash", [l["tx"]])
        evs.append({"event": "ValidationRequest" if l["topics"][0].lower() == T_REQ.lower() else "ValidationResponse",
                    "block": l["block"], "utc": iso(E.block_ts(rpc, l["block"])), "tx": l["tx"], "logIndex": l["logIndex"],
                    "validator": addr_of_word(l["topics"][1]), "agentId": int(l["topics"][2], 16),
                    "requestHash": l["topics"][3] if len(l["topics"]) > 3 else None, "tx_from": tx["from"].lower(),
                    "tx_to": (tx.get("to") or "").lower()})
    out["validation_events"] = evs
    out["rpc_calls"] = rpc.calls
    return out


def owner_checks(nodes_out, head_fixed):
    """Addendum C method: ownerOf(agentId) at the request block on the Identity registry the proxy itself names
    (getIdentityRegistry() at that block); determined only if >= 2 endpoints answered and all answers agree."""
    reqs = {(e["block"], e["tx"], e["logIndex"]): e for n in nodes_out.values() for e in n["validation_events"] if e["event"] == "ValidationRequest"}
    res = []
    for key, e in sorted(reqs.items()):
        ans = {}
        for name, url in NODES.items():
            rpc = PointRetryRpc([url])
            try:
                ir = addr_of_word(rpc.call("eth_call", [{"to": CB1B, "data": SEL_GET_IDENTITY}, hex(e["block"])]))
                has = E.has_code(rpc, ir, e["block"])
                w = rpc.call("eth_call", [{"to": ir, "data": SEL_OWNER_OF + hex(e["agentId"])[2:].rjust(64, "0")}, hex(e["block"])])
                ans[name] = {"identity_registry": ir, "registry_has_code": has, "owner": addr_of_word(w) if has and len(w) >= 66 else None}
            except Exception as x:
                ans[name] = {"error": str(x)[:160]}
        owners = {a.get("owner") for a in ans.values() if a.get("owner")}
        answered = [a for a in ans.values() if a.get("owner")]
        det = len(answered) >= 2 and len(owners) == 1
        own = owners.pop() if det else None
        res.append({"block": e["block"], "tx": e["tx"], "agentId": e["agentId"], "validator": e["validator"],
                    "per_endpoint": ans, "determined": det, "owner_at_request_block": own,
                    "validator_is_owner": (own == e["validator"]) if det else None})
    return res


def main():
    heads = {n: E.get_head(PointRetryRpc([u])) for n, u in NODES.items()}
    head_fixed = min(heads.values()) - E.SAFETY_BLOCKS
    head_ts = E.block_ts(PointRetryRpc([NODES["tenderly"]]), head_fixed)
    rec = {"run_started_utc": E.now(), "address": CB1B, "snapshot_block": SNAPSHOT, "heads_seen": heads,
           "head_fixed": head_fixed, "head_fixed_utc": iso(head_ts), "safety_blocks": E.SAFETY_BLOCKS,
           "topics": {"ValidationRequest": T_REQ, "ValidationResponse": T_RESP, "Upgraded": T_UPG},
           "selectors": SELECTORS, "chunking": KW, "claimed_by_RealSpap": CLAIMED}
    with cf.ThreadPoolExecutor(2) as ex:
        futs = {n: ex.submit(per_node, n, u, head_fixed) for n, u in NODES.items()}
        rec["nodes"] = {}
        for n, f in futs.items():
            try:
                rec["nodes"][n] = f.result()
            except Exception as x:
                rec["nodes"][n] = {"url": NODES[n], "error": f"{type(x).__name__}: {str(x)[:300]}", "traceback_tail": traceback.format_exc()[-800:]}
    if all("error" not in v for v in rec["nodes"].values()) and any(v["validation_events"] for v in rec["nodes"].values()):
        rec["owner_checks"] = owner_checks(rec["nodes"], head_fixed)
    rec["run_finished_utc"] = E.now()
    json.dump(rec, open(OUTP, "w"), indent=1, sort_keys=True)
    print(json.dumps(rec, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
