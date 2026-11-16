"""Addendum D, update 2026-11-16: replay of RealSpap's all-topics read (Ethereum Magicians topic 25098, post #451,
2026-11-16T13:27Z). Every log at 0x8004Cb1BF31DAf7788923b405b754f57acEB4272 on Ethereum mainnet, NO topic filter,
blocks 24,204,475 to 26,427,741 (his range), on the two nodes of addendum D, with addendum D's chunk sizes.

Read-only: eth_chainId, eth_blockNumber, eth_getBlockByNumber, eth_getLogs. No key, no signing, no transaction.

The reader. erc8004_usage.scan always sends a topic0 filter and re-checks every returned log's topic0 against it, so it
cannot read all topics unchanged. erc8004_usage.py is not edited. Instead this script takes the source of E.scan and
E.scan_parallel, applies the exact substitutions listed in SUBST below (each must match exactly once, else the script
stops), and executes the result in the scanner's own module namespace under new names (scan_all, scan_parallel_all).
Everything else (split on error, split at a suspected cap, adaptive chunk size, block-range and address re-check,
de-duplication by (block, logIndex), parallel segmentation) is the scanner's code as it is. The substitutions, and the
SHA-256 of erc8004_usage.py and of the derived source, are written to the output.

Cross-check. On each node, the topic0 values found are then read again with the UNCHANGED filtered reader
(E.scan_parallel, OR-filter on those topic0s, same range, same chunk sizes). The two reads must return the same
(block, logIndex, tx) set.

Usage, from the repo root:
  python3 -I addenda/2026-11-16_cb1b_all_topics.py addenda/2026-11-16_cb1b_all_topics.json
"""
import hashlib, inspect, json, os, sys, time, traceback, concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import erc8004_usage as E                     # noqa: E402
from web3 import Web3                         # noqa: E402

# the scanner's log() appends to output/run.log; this addendum must not touch the original output
E.log = lambda *a: print("[log]", *a, file=sys.stderr, flush=True)

OUTP = sys.argv[1]
NODES = {"tenderly": "https://mainnet.gateway.tenderly.co", "mevblocker": "https://rpc.mevblocker.io/fast"}
CB1B = "0x8004Cb1BF31DAf7788923b405b754f57acEB4272"
LO, HI = 24204475, 26427741                  # RealSpap's range, post #451
KW = {"init_chunk": 10_000, "max_chunk": 500_000}   # addendum D chunk sizes (== E.scan_kw for chainId 1, 13 October run)
EXPECTED = {"total": 7, "Upgraded": 3, "OwnershipTransferred": 2, "Initialized": 2, "validation_events": 0}
ADDENDUM_D_UPGRADED = {(24204475, 428), (24204487, 727), (24339656, 889)}   # (block, logIndex), addendum D section 1

# ---- topic0 candidates
def k(sig): return "0x" + Web3.keccak(text=sig).hex().removeprefix("0x")
CAND = {}
for name in ("Upgraded", "ValidationRequest", "ValidationResponse"):      # from the vendored ABI
    sig, t = E.event_sig("validation", name)
    CAND[t.lower()] = {"name": name, "signature": sig, "source": "abis/ValidationRegistry.json via E.event_sig"}
for sig in ("OwnershipTransferred(address,address)", "Initialized(uint8)", "Initialized(uint64)"):  # computed here
    CAND[k(sig).lower()] = {"name": sig.split("(")[0], "signature": sig, "source": "keccak256 computed in this script"}
VALIDATION = {t for t, v in CAND.items() if v["name"] in ("ValidationRequest", "ValidationResponse")}

# ---- derive the all-topics reader from the scanner's own source
SUBST = [
    ("def scan(rpc, addr, topic0, lo, hi,", "def scan_all(rpc, addr, topic0, lo, hi,"),
    (', "topics": [t_list if len(t_list) > 1 else t_list[0]]}], tries=2)', "}], tries=2)"),
    (' or l["topics"][0].lower() not in t_set:', ":"),
    ('by_topic[l["topics"][0].lower()] += 1', 'by_topic[l["topics"][0].lower() if l["topics"] else "(no topics)"] += 1'),
]
SUBST_PAR = [
    ("def scan_parallel(rpc, addr, topic0, lo, hi,", "def scan_parallel_all(rpc, addr, topic0, lo, hi,"),
    ("return scan(rpc, addr, topic0, lo, hi, keep_logs", "return scan_all(rpc, addr, topic0, lo, hi, keep_logs"),
    ("lambda se: scan(rpc, addr, topic0, se[0]", "lambda se: scan_all(rpc, addr, topic0, se[0]"),
]


def derive(fn, subs):
    src = inspect.getsource(fn)
    for old, new in subs:
        n = src.count(old)
        if n != 1:
            raise SystemExit(f"substitution matched {n} times, expected 1: {old!r}")
        src = src.replace(old, new)
    return src


SRC_SCAN = derive(E.scan, SUBST)
SRC_PAR = derive(E.scan_parallel, SUBST_PAR)
assert '"topics"' not in SRC_SCAN.split("rpc.call(")[1].split("tries=2)")[0], "topic filter still present"
exec(compile(SRC_SCAN, "<scan_all derived from erc8004_usage.scan>", "exec"), E.__dict__)
exec(compile(SRC_PAR, "<scan_parallel_all derived from erc8004_usage.scan_parallel>", "exec"), E.__dict__)


def sha256_file(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def sha256_text(s): return hashlib.sha256(s.encode()).hexdigest()


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


def per_node(name, url):
    rpc = PointRetryRpc([url])
    out = {"url": url}
    out["chainId"] = int(rpc.call("eth_chainId", []), 16)
    assert out["chainId"] == 1, out["chainId"]
    out["head_at_run"] = E.get_head(rpc)
    out["range_end_within_head_minus_safety"] = HI <= out["head_at_run"] - E.SAFETY_BLOCKS
    if not out["range_end_within_head_minus_safety"]:
        raise E.ScanError(f"range end {HI} > head {out['head_at_run']} - {E.SAFETY_BLOCKS}")

    r = E.scan_parallel_all(rpc, CB1B, [], LO, HI, keep_logs=True, tag="", **KW)
    if r["incomplete"]:
        raise E.ScanError("incomplete all-topics scan")
    logs = []
    for l in r["logs"]:
        t0 = l["topics"][0].lower() if l["topics"] else None
        c = CAND.get(t0)
        logs.append({"block": l["block"], "utc": E.iso(E.block_ts(rpc, l["block"])), "tx": l["tx"],
                     "logIndex": l["logIndex"], "topic0": t0, "event": c["signature"] if c else None,
                     "n_topics": len(l["topics"]), "topics": l["topics"], "data": l["data"]})
    out["all_topics"] = {k2: v for k2, v in r.items() if k2 != "logs"}
    out["logs"] = logs

    # cross-check with the unchanged filtered reader, OR on every topic0 found
    found = sorted({x["topic0"] for x in logs if x["topic0"]})
    if found:
        f = E.scan_parallel(rpc, CB1B, found, LO, HI, keep_logs=True, tag="", **KW)
        if f["incomplete"]:
            raise E.ScanError("incomplete filtered cross-check")
        a = sorted((x["block"], x["logIndex"], x["tx"].lower()) for x in logs if x["topic0"])
        b = sorted((x["block"], x["logIndex"], x["tx"].lower()) for x in f["logs"])
        out["filtered_crosscheck"] = {"topic0s": found, "count": f["count"], "chunks": f["chunks"], "splits": f["splits"],
                                      "duplicates_dropped": f["duplicates_dropped"], "same_logs_as_all_topics": a == b}
    out["rpc_calls"] = rpc.calls
    return out


def summarise(n):
    logs = n["logs"]
    by = {}
    for x in logs:
        by[x["event"] or f"UNKNOWN {x['topic0']}"] = by.get(x["event"] or f"UNKNOWN {x['topic0']}", 0) + 1
    names = {}
    for x in logs:
        nm = CAND[x["topic0"]]["name"] if x["topic0"] in CAND else None
        names[nm] = names.get(nm, 0) + 1
    last = max((x["block"] for x in logs), default=None)
    up = {(x["block"], x["logIndex"]) for x in logs if x["event"] == "Upgraded(address)"}
    return {"total": len(logs), "by_signature": by,
            "matches_expected": len(logs) == EXPECTED["total"] and all(names.get(k2, 0) == v for k2, v in EXPECTED.items()
                                                                     if k2 not in ("total", "validation_events")),
            "validation_events": sum(1 for x in logs if x["topic0"] in VALIDATION),
            "unknown_topic0": sorted({x["topic0"] for x in logs if x["topic0"] not in CAND}, key=str),
            "upgraded_equal_addendum_D": up == ADDENDUM_D_UPGRADED,
            "last_log_block": last,
            "last_log_fraction_of_range": None if last is None else round((last - LO) / (HI - LO), 6)}


def main():
    rec = {"run_started_utc": E.now(), "address": CB1B, "range": [LO, HI], "range_source": "RealSpap, ethereum-magicians topic 25098 post #451",
           "chunking": KW, "expected_per_RealSpap": EXPECTED,
           "topic0_candidates": CAND,
           "reader": {"erc8004_usage.py_sha256": sha256_file(os.path.join(ROOT, "erc8004_usage.py")),
                      "substitutions_scan": SUBST, "substitutions_scan_parallel": SUBST_PAR,
                      "derived_scan_all_sha256": sha256_text(SRC_SCAN), "derived_scan_parallel_all_sha256": sha256_text(SRC_PAR)}}
    with cf.ThreadPoolExecutor(2) as ex:
        futs = {n: ex.submit(per_node, n, u) for n, u in NODES.items()}
        rec["nodes"] = {}
        for n, f in futs.items():
            try:
                rec["nodes"][n] = f.result()
                rec["nodes"][n]["summary"] = summarise(rec["nodes"][n])
            except Exception as x:
                rec["nodes"][n] = {"url": NODES[n], "error": f"{type(x).__name__}: {str(x)[:300]}", "traceback_tail": traceback.format_exc()[-800:]}
    ok = [v for v in rec["nodes"].values() if "error" not in v]
    if len(ok) == 2:
        key = lambda v: sorted((x["block"], x["logIndex"], x["tx"].lower(), x["topic0"]) for x in v["logs"])
        rec["nodes_agree"] = key(ok[0]) == key(ok[1])
    rec["run_finished_utc"] = E.now()
    json.dump(rec, open(OUTP, "w"), indent=1, sort_keys=True)
    print(json.dumps(rec, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
