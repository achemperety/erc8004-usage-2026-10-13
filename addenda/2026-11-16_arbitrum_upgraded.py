"""Addendum D 2026-11-16, one replay of a figure from RealSpap's errata: Upgraded(address) logs at the Validation proxy
0x8004Cc8439f36fd5F9F049D9fF86523Df6dAAB58 on Arbitrum One, blocks 428895484-428895794, on https://arb1.arbitrum.io/rpc.
Read-only (eth_chainId, eth_getLogs, eth_getBlockByNumber). The endpoint has no historical state
(eth_getStorageAt at these blocks: "missing trie node"), so only the logs are read. Uses the scanner's own reader (scan).

Usage, from the repo root:  python3 -I addenda/2026-11-16_arbitrum_upgraded.py addenda/2026-11-16_arbitrum_upgraded.json
"""
import json, os, sys, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import erc8004_usage as E                     # noqa: E402

E.log = lambda *a: print("[log]", *a, file=sys.stderr, flush=True)
URL, LO, HI, EXPECTED = "https://arb1.arbitrum.io/rpc", 428895484, 428895794, 2
ADDR = E.ADDR["validation"]
T_UPG = E.event_sig("validation", "Upgraded")[1]

rpc = E.Rpc([URL])
assert int(rpc.call("eth_chainId", []), 16) == 42161
r = E.scan(rpc, ADDR, T_UPG, LO, HI, keep_logs=True, init_chunk=10_000, max_chunk=10_000)
assert not r["incomplete"]
iso = lambda ts: dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
logs = [{"block": l["block"], "utc": iso(E.block_ts(rpc, l["block"])), "tx": l["tx"], "logIndex": l["logIndex"],
         "implementation": "0x" + l["topics"][1][-40:].lower()} for l in r["logs"]]
out = {"run_utc": E.now(), "url": URL, "address": ADDR, "topic0": T_UPG, "range": [LO, HI], "expected": EXPECTED,
       "count": r["count"], "matches": r["count"] == EXPECTED, "chunks": r["chunks"], "logs": logs}
json.dump(out, open(sys.argv[1], "w"), indent=1, sort_keys=True)
print(json.dumps(out, indent=1, sort_keys=True))
