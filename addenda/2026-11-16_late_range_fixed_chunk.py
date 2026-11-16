"""Addendum D, update 2026-11-16, late-range control, follow-up: fixed-chunk re-read of the last 10 % of the range.

Why. The control (addenda/2026-11-16_late_range_control.py) used the adaptive reader; its widest successful
eth_getLogs range was 160,000 blocks on Tenderly and 20,000 on MEV Blocker. At the quiet address 0x8004Cb1B...4272 the
same reader may have used wider ranges, and wide ranges are where some nodes return an empty result instead of an
error. Recorded widest ranges at Cb1B: all-topics read 160,000 (Tenderly) and 80,000 (MEV Blocker); addendum D
section 3 (addenda/2026-11-16_cb1b_ethereum.json) did not record it. So, per the owner's instruction, on each node the
Registered and NewFeedback logs over the last 10 % of the range are re-read with a FIXED chunk of 500,000 blocks (the
reader's maximum; used where the Cb1B figure is not recorded), and on MEV Blocker also with 80,000 (its recorded
all-topics figure). No splitting, no adaptive growth: each call either returns logs or its error is recorded.

Each returned log is re-checked as erc8004_usage.scan does (block inside the call's range, address, topic0) and
de-duplicated by (block, logIndex). A result whose length is one of E.CAP_SUSPECTS is flagged.

Expected (control, both nodes): Registered 2,406, NewFeedback 7,404 over 26,205,415 - 26,427,741.

Read-only: eth_chainId, eth_blockNumber, eth_getLogs.
Usage, from the repo root:
  python3 -I addenda/2026-11-16_late_range_fixed_chunk.py addenda/2026-11-16_late_range_fixed_chunk.json
"""
import hashlib, json, os, sys, time, concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import erc8004_usage as E                     # noqa: E402

E.log = lambda *a: print("[log]", *a, file=sys.stderr, flush=True)

OUTP = sys.argv[1]
LO, HI = 26205415, 26427741                  # last 10 % of 24,204,475 - 26,427,741
TARGETS = [("identity", "Registered"), ("reputation", "NewFeedback")]
EXPECTED = {"Registered": 2406, "NewFeedback": 7404}   # late-range control, both nodes
RUNS = {"tenderly": ("https://mainnet.gateway.tenderly.co", [500_000]),
        "mevblocker": ("https://rpc.mevblocker.io/fast", [500_000, 80_000])}
CB1B_WIDEST = {"tenderly": {"all_topics": 160_000, "section_3": None},
               "mevblocker": {"all_topics": 80_000, "section_3": None}}
CONTROL_WIDEST = {"tenderly": 160_000, "mevblocker": 20_000}


def fixed_read(url, reg, ev, chunk):
    rpc = E.Rpc([url])                       # unchanged client, one URL, same tries as the reader (2)
    addr, (sig, t0) = E.ADDR[reg], E.event_sig(reg, ev)
    seen, pos, calls, dup = set(), set(), [], 0
    p = LO
    while p <= HI:
        end = min(HI, p + chunk - 1)
        c = {"from": p, "to": end, "span": end - p + 1}
        t = time.time()
        try:
            res = rpc.call("eth_getLogs", [{"fromBlock": E.hx(p), "toBlock": E.hx(end), "address": addr, "topics": [t0]}], tries=2)
        except E.RpcFail as x:
            c.update(ok=False, error=str(x)[:200], s=round(time.time() - t, 1))
            calls.append(c); p = end + 1; continue
        c.update(ok=True, s=round(time.time() - t, 1), n=len(res) if isinstance(res, list) else None)
        if not isinstance(res, list):
            c.update(ok=False, error=f"non-list result: {str(res)[:80]}")
        else:
            c["cap_suspect"] = len(res) in E.CAP_SUSPECTS
            for l in res:
                bn = int(l["blockNumber"], 16)
                if not (p <= bn <= end) or l["address"].lower() != addr.lower() or l["topics"][0].lower() != t0.lower():
                    raise E.ScanError(f"log outside request: {bn} {l['address']} {l['topics'][0]}")
                k = (bn, int(l["logIndex"], 16), l["transactionHash"].lower())
                if (k[0], k[1]) in pos:
                    dup += 1; continue
                pos.add((k[0], k[1])); seen.add(k); c.setdefault("_k", set()).add(k)
        calls.append(c); p = end + 1
    keys = sorted(seen)
    complete = all(c["ok"] for c in calls)
    return {"event": ev, "address": addr, "topic0": t0, "chunk": chunk, "calls": calls, "complete": complete,
            "count": len(keys), "duplicates_dropped": dup, "expected": EXPECTED[ev],
            "matches_control": complete and len(keys) == EXPECTED[ev],
            "last_log": list(keys[-1]) if keys else None,
            "keys_sha256": hashlib.sha256("\n".join(f"{b},{t},{i}" for b, i, t in keys).encode()).hexdigest(),
            "_keys": keys, "_per_call_keys": [c.pop("_k", None) for c in calls]}


def per_node(node):
    url, chunks = RUNS[node]
    rpc = E.Rpc([url])
    out = {"url": url, "chainId": int(rpc.call("eth_chainId", []), 16), "head_at_run": E.get_head(rpc),
           "cb1b_widest_recorded": CB1B_WIDEST[node], "control_widest": CONTROL_WIDEST[node], "reads": []}
    assert out["chainId"] == 1 and HI <= out["head_at_run"] - E.SAFETY_BLOCKS
    for ch in chunks:
        for reg, ev in TARGETS:
            out["reads"].append(fixed_read(url, reg, ev, ch))
    return out


def main():
    rec = {"run_started_utc": E.now(), "range": [LO, HI], "expected": EXPECTED,
           "erc8004_usage.py_sha256": hashlib.sha256(open(os.path.join(ROOT, "erc8004_usage.py"), "rb").read()).hexdigest()}
    with cf.ThreadPoolExecutor(2) as ex:
        rec["nodes"] = dict(zip(RUNS, ex.map(per_node, RUNS)))
    # cross-check: every successful call, on either node, against Tenderly's 500,000-chunk read of the same sub-range
    ref = {r["event"]: set(r["_keys"]) for r in rec["nodes"]["tenderly"]["reads"] if r["chunk"] == 500_000 and r["complete"]}
    for n in rec["nodes"].values():
        for r in n["reads"]:
            for c, ks in zip(r["calls"], r.pop("_per_call_keys")):
                if c["ok"] and r["event"] in ref:
                    want = {k for k in ref[r["event"]] if c["from"] <= k[0] <= c["to"]}
                    c["tenderly_500k_same_subrange"] = len(want)
                    c["identical_to_tenderly_500k"] = (ks or set()) == want
            r.pop("_keys")
    rec["all_match"] = all(r["matches_control"] for n in rec["nodes"].values() for r in n["reads"])
    rec["successful_calls_all_identical_to_tenderly_500k"] = all(
        c.get("identical_to_tenderly_500k", True) for n in rec["nodes"].values() for r in n["reads"] for c in r["calls"] if c["ok"])
    rec["failed_calls_returned_error_not_empty"] = all(
        "error" in c for n in rec["nodes"].values() for r in n["reads"] for c in r["calls"] if not c["ok"])
    rec["run_finished_utc"] = E.now()
    json.dump(rec, open(OUTP, "w"), indent=1, sort_keys=True)
    print(json.dumps(rec, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
