"""Addenda 2026-11-11 (A and B): read-only Base calls. Usage, from the repo root: python3 -I addenda/2026-11-11_base_calls.py . addenda/2026-11-11_base_calls.json
Only eth_getBlockByNumber / eth_getTransactionReceipt / eth_getCode / eth_getStorageAt / eth_blockNumber / eth_chainId."""
import json, sys, os, time, datetime as dt, urllib.request, ssl
import certifi

MDIR, OUTP = sys.argv[1], sys.argv[2]
CTX = ssl.create_default_context(cafile=certifi.where())
EPS = ["https://base.gateway.tenderly.co", "https://mainnet.base.org", "https://base.publicnode.com", "https://base.drpc.org"]
SCANNED = "0x8004Cc8439f36fd5F9F049D9fF86523Df6dAAB58"
POST437 = "0x8004Cb1BF31DAf7788923b405b754f57acEB4272"
IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
ASOF = json.load(open(os.path.join(MDIR, "output", "as_of.json")))["8453"]["to_block"]


def call(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    for k in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
                out = json.load(r)
            if "error" in out:
                return {"error": str(out["error"])[:160]}
            return {"result": out["result"]}
        except Exception as e:
            err = f"{type(e).__name__}: {str(e)[:120]}"
            time.sleep(1 + k)
    return {"error": err}


def first_ok(method, params, eps=EPS):
    errs = {}
    for u in eps:
        r = call(u, method, params)
        if "result" in r and r["result"] is not None:
            return u, r["result"], errs
        errs[u] = r.get("error", "null result")
    return None, None, errs


out = {"run_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "as_of_block": ASOF, "endpoints": {}}
for u in EPS:
    r = call(u, "eth_chainId", [])
    out["endpoints"][u] = {"chainId": int(r["result"], 16) if "result" in r else r}
head_ep, head, _ = first_ok("eth_blockNumber", [])
out["head_block_at_run"] = int(head, 16)

# --- A: timestamps of the 15 requests (two endpoints each, must agree)
req = json.load(open(os.path.join(MDIR, "output", "counts", "8453_validation_ValidationRequest.json")))
assert req["count"] == len(req["logs"]) == 15, (req["count"], len(req["logs"]))
rows = []
for l in req["logs"]:
    ts = {}
    for u in EPS[:2] + EPS[2:]:
        r = call(u, "eth_getBlockByNumber", [hex(l["block"]), False])
        if "result" in r and r["result"]:
            ts[u] = int(r["result"]["timestamp"], 16)
        if len(ts) == 2:
            break
    vals = set(ts.values())
    t = vals.pop() if len(vals) == 1 else None
    # emitter of the logged event, from the tx receipt
    ep, rc, errs = first_ok("eth_getTransactionReceipt", [l["tx"]])
    emitter = topic0 = None
    if rc:
        for lg in rc["logs"]:
            if int(lg["logIndex"], 16) == l["logIndex"]:
                emitter, topic0 = lg["address"], lg["topics"][0]
    rows.append({"block": l["block"], "logIndex": l["logIndex"], "tx": l["tx"],
                 "validator": "0x" + l["topics"][1][-40:], "agentId": int(l["topics"][2], 16),
                 "timestamp": t, "utc": dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if t else None,
                 "timestamp_sources": ts, "receipt_endpoint": ep, "emitter": emitter, "receipt_topic0": topic0,
                 "receipt_errors": errs or None})
out["requests"] = rows

# --- B: code + EIP-1967 implementation slot for both addresses, at as-of and at head
blocks = {"as_of": hex(ASOF), "latest_at_run": hex(out["head_block_at_run"])}
out["proxies"] = {}
for name, a in (("scanned", SCANNED), ("post437", POST437)):
    rec = {"address": a}
    for tag, b in blocks.items():
        per_ep = {}
        for u in EPS:
            c = call(u, "eth_getCode", [a, b]); s = call(u, "eth_getStorageAt", [a, IMPL_SLOT, b])
            per_ep[u] = {"code_len_bytes": (len(c["result"]) - 2) // 2 if "result" in c else None,
                         "code_keccak": None, "impl_slot": s.get("result"), "errors": {k: v for k, v in (("code", c.get("error")), ("slot", s.get("error"))) if v}}
            if "result" in c and c["result"] not in ("0x", None):
                from web3 import Web3
                per_ep[u]["code_keccak"] = Web3.keccak(hexstr=c["result"]).hex()
        rec[tag] = per_ep
    out["proxies"][name] = rec

# implementations' code size now (does the implementation exist?)
impls = set()
for name in out["proxies"]:
    for tag in blocks:
        for u, v in out["proxies"][name][tag].items():
            if v["impl_slot"] and int(v["impl_slot"], 16):
                impls.add("0x" + v["impl_slot"][-40:])
out["implementations"] = {}
for i in sorted(impls):
    ep, code, errs = first_ok("eth_getCode", [i, hex(out["head_block_at_run"])])
    out["implementations"][i] = {"code_len_bytes_at_head": (len(code) - 2) // 2 if code else None, "endpoint": ep}
json.dump(out, open(OUTP, "w"), indent=1)
print("written", OUTP)
