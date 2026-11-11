"""Addendum 2026-11-11 (owner at request block): for every ValidationRequest on Base, Mantle, 0G, Celo and Monad, read
ownerOf(agentId) on the Identity registry AT THE BLOCK OF THE REQUEST (historical state), on every listed public endpoint.
Read-only: eth_chainId, eth_getCode, eth_call only.

Usage, from the repo root:  python3 -I addenda/2026-11-11_owner_at_request_block.py addenda/2026-11-11_owner_at_request_block.json

Per endpoint and request, the outcome is one of:
  owner          eth_call returned a 32-byte word and the Identity registry has code at that block
  reverted       eth_call reverted while the registry has code at that block (token did not exist / no owner then)
  no_state       the endpoint said it has no state for that block (missing trie node, pruned, header not found, ...)
  empty          eth_call returned "0x" or eth_getCode returned "0x" at that block (cannot distinguish pruning from absence)
  error          any transport or HTTP error on either call, or any other RPC error
Per request: "determined" only if at least TWO endpoints returned `owner` (or `reverted`) and all endpoints that answered
agree; otherwise "not determined" (with the reason: only one endpoint answered / none answered / endpoints disagree). A block-N eth_call sees the state after all transactions of block N.
An endpoint that gives no usable answer (anything but owner/reverted) for 3 consecutive requests on a chain is skipped
for the rest of that chain; skipped requests are recorded as outcome "skipped" for that endpoint.
Retry: a request that is not determined after the first pass is retried once, after 5 s, on every endpoint whose outcome
was "error" (transient failures only; no_state/empty/skipped are not retried). Both attempts are kept in the output.
"""
import json, os, sys, time, ssl, urllib.request, urllib.error, datetime as dt, concurrent.futures as cf
import certifi

OUTP = sys.argv[1]
CTX = ssl.create_default_context(cafile=certifi.where())
IDENTITY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
OWNER_OF = "0x6352211e"   # ownerOf(uint256)
ENDPOINTS = {   # public, keyless; the first ones are those that served the 13 October scan (output/rpc_selection.json)
    8453: ["https://base.gateway.tenderly.co", "https://mainnet.base.org", "https://base-rpc.publicnode.com",
           "https://base.drpc.org", "https://1rpc.io/base", "https://base.llamarpc.com"],
    5000: ["https://mantle-rpc.publicnode.com", "https://rpc.mantle.xyz", "https://mantle.drpc.org", "https://1rpc.io/mantle"],
    16661: ["https://evmrpc.0g.ai", "https://0g.drpc.org"],
    143: ["https://rpc2.monad.xyz", "https://rpc1.monad.xyz", "https://rpc.monad.xyz", "https://rpc3.monad.xyz",
          "https://monad-mainnet.drpc.org"],
    42220: ["https://forno.celo.org", "https://celo-rpc.publicnode.com", "https://celo.drpc.org", "https://1rpc.io/celo",
            "https://celo-rpc.blockreq.com/v1/rpc/public"],
}
NAMES = {8453: "Base", 5000: "Mantle", 16661: "0G", 42220: "Celo", 143: "Monad"}
NO_STATE = ("missing trie node", "header not found", "state", "pruned", "historical", "archive", "not available",
            "unknown block", "block not found", "too old", "beyond")


def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    last = None
    for k in range(2):
        try:
            with urllib.request.urlopen(req, timeout=15, context=CTX) as r:
                out = json.load(r)
            if isinstance(out, dict) and "error" in out:
                msg = str(out["error"].get("message", out["error"]))[:200]
                if "rate" in msg.lower() or "too many" in msg.lower():
                    time.sleep(2 + 2 * k); last = ("rpc_error", msg); continue
                return ("rpc_error", msg)
            return ("ok", out.get("result"))
        except urllib.error.HTTPError as e:
            last = ("http_error", f"HTTP {e.code}")
            if e.code in (429, 502, 503, 504):
                time.sleep(2 + 2 * k); continue
            return last
        except Exception as e:
            last = ("transport", f"{type(e).__name__}: {str(e)[:120]}")
            time.sleep(1 + k)
    return last


def classify(url, block, agent):
    b = hex(block)
    st, code = rpc(url, "eth_getCode", [IDENTITY, b])
    data = OWNER_OF + hex(agent)[2:].rjust(64, "0")
    st2, res = rpc(url, "eth_call", [{"to": IDENTITY, "data": data}, b])
    rec = {"getCode": (st, None if st != "ok" else (len(code or "0x") - 2) // 2) if st == "ok" else (st, code),
           "eth_call": (st2, res)}
    if st in ("transport", "http_error") or st2 in ("transport", "http_error"):
        return "error", None, rec
    if st2 == "ok" and isinstance(res, str) and len(res) == 66:
        if st == "ok" and code not in (None, "0x"):
            return "owner", "0x" + res[-40:], rec
        return "empty", None, rec
    if st2 == "ok" and res in (None, "0x"):
        return "empty", None, rec
    msg = str(res).lower()
    if st2 == "rpc_error" and "revert" in msg:
        return ("reverted" if (st == "ok" and code not in (None, "0x")) else "empty"), None, rec
    if st2 == "rpc_error" and any(k in msg for k in NO_STATE):
        return "no_state", None, rec
    return "error", None, rec


latest = json.load(open("output/self_validation_check.json"))
latest_by = {(o["chainId"], o["block"], o["agentId"], o["validator"].lower()): o for o in latest}
out = {"run_started_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "identity_registry": IDENTITY,
       "method": "eth_call ownerOf(agentId) at the request block (state after that block), every endpoint; eth_getCode of the "
                 "Identity registry at the same block as a state-availability check", "endpoints": {}, "requests": []}


def do_chain(cid):
    urls = ENDPOINTS[cid]
    ep = {}
    for u in urls:
        st, r = rpc(u, "eth_chainId", [])
        ep[u] = int(r, 16) if st == "ok" and r else f"{st}: {r}"
    good = [u for u in urls if ep[u] == cid]
    misses = {u: 0 for u in good}
    rows = []
    req = json.load(open(f"output/counts/{cid}_validation_ValidationRequest.json"))
    for l in req["logs"]:
        agent = int(l["topics"][2], 16); validator = ("0x" + l["topics"][1][-40:]).lower()
        per = {}
        for u in good:
            if misses[u] >= 3:
                per[u] = {"outcome": "skipped", "owner": None, "raw": "skipped after 3 consecutive non-answers on this chain"}
                continue
            outcome, owner, raw = classify(u, l["block"], agent)
            per[u] = {"outcome": outcome, "owner": owner, "raw": raw}
            misses[u] = 0 if outcome in ("owner", "reverted") else misses[u] + 1
            time.sleep(0.15)
        answering = [v for v in per.values() if v["outcome"] in ("owner", "reverted")]
        if len(answering) < 2 or len({(v["outcome"], v["owner"]) for v in answering}) > 1:
            retry = [u for u, v in per.items() if v["outcome"] == "error"]
            if retry:
                time.sleep(5)
            for u in retry:
                outcome, owner, raw = classify(u, l["block"], agent)
                per[u] = {"outcome": outcome, "owner": owner, "raw": raw, "first_attempt": per[u]}
            answering = [v for v in per.values() if v["outcome"] in ("owner", "reverted")]
        answers = {(v["outcome"], v["owner"]) for v in answering}
        if len(answers) > 1:
            outcome, owner, status = "conflict", None, "not determined (endpoints disagree)"
        elif len(answers) == 1 and len(answering) >= 2:
            (outcome, owner), status = answers.pop(), "determined"
        elif len(answers) == 1:
            outcome, owner, status = None, None, "not determined (only one endpoint answered)"
        else:
            outcome, owner, status = None, None, "not determined (no endpoint served state for this block)"
        lt = latest_by.get((cid, l["block"], agent, validator))
        row = {"chain": NAMES[cid], "chainId": cid, "block": l["block"], "logIndex": l["logIndex"], "tx": l["tx"], "agentId": agent,
               "validator": validator, "status": status, "outcome_at_request_block": outcome, "owner_at_request_block": owner,
               "validator_is_owner_at_request_block": (owner == validator) if outcome == "owner" else None,
               "owner_latest_2026_10_13": lt["owner_now"].lower() if lt else None,
               "validator_is_owner_latest_2026_10_13": lt["validator_is_owner"] if lt else None,
               "endpoints_answered": sorted(u for u, v in per.items() if v["outcome"] in ("owner", "reverted")),
               "per_endpoint": per}
        rows.append(row)
        print(f"{NAMES[cid]:<7} block {l['block']:>10} agent {agent:>7}  {status[:14]:<14} self@block={row['validator_is_owner_at_request_block']}  "
              f"self@latest={row['validator_is_owner_latest_2026_10_13']}  same_owner={owner == row['owner_latest_2026_10_13'] if owner else None}  "
              f"answered={len(row['endpoints_answered'])}/{len(good)}", flush=True)
    return cid, ep, rows


with cf.ThreadPoolExecutor(len(ENDPOINTS)) as ex:
    results = list(ex.map(do_chain, ENDPOINTS))
for cid, ep, rows in results:
    out["endpoints"][str(cid)] = ep
    out["requests"] += rows
out["run_finished_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
json.dump(out, open(OUTP, "w"), indent=1)
print("written", OUTP)
