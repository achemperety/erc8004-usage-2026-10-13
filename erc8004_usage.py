#!/usr/bin/env python3
"""ERC-8004 registry usage counter.

READ-ONLY: uses eth_chainId / eth_blockNumber / eth_getCode / eth_getBlockByNumber /
eth_getLogs / eth_call only. No private key, no transaction is ever built or sent.

Design rules (each exists because the alternative yields a plausible wrong number):
  * topic0 is derived from the vendored ABI JSON, never typed by hand.
  * An RPC error is NEVER treated as "zero logs": a range that cannot be fetched raises.
  * A response whose size equals a common provider cap is split, never accepted
    (silent truncation would otherwise look like a count).
  * Every returned log is re-checked against the requested range/address/topic0.

Usage:  python3 -I erc8004_usage.py <select|asof|deploy|controls|count|report|selftest> [--chains 1,8453]
Needs:  certifi, web3 (web3 only for keccak256).
"""
import argparse, collections, concurrent.futures as cf, datetime as dt, json, os, random, ssl, sys, threading, time
import urllib.error, urllib.request
import certifi
from web3 import Web3

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
CTX = ssl.create_default_context(cafile=certifi.where())
SAFETY_BLOCKS = 256            # to_block = head - SAFETY_BLOCKS  (reorg margin)
FLOOR_TS = int(dt.datetime(2025, 10, 1, tzinfo=dt.timezone.utc).timestamp())  # only used if deploy block unresolved
SLOW_CALL_S = 4.0
LOWER_BOUND_CHAINS = {42220}   # forno.celo.org returned false-empty results in controls (output/endpoint_consistency.txt)
BUDGET_CONTROL_S = 600     # wall-clock cap per control scan; exceeded => reported INCOMPLETE, never as zero
BUDGET_COUNT_S = 2400     # wall-clock cap per counting scan
CONTROL_WINDOW_CALLS = 600     # control (b)/(b') window = at most this many calls' worth of blocks
CAP_SUSPECTS = {1000, 1500, 2000, 5000, 10000, 20000, 50000, 100000}

# chainId -> (name, provenance of the chainId)
CHAINS = {
    1: ("Ethereum", "addresses.ts"), 8453: ("Base", "addresses.ts"), 42161: ("Arbitrum One", "addresses.ts"),
    10: ("Optimism", "addresses.ts"), 137: ("Polygon", "addresses.ts"), 43114: ("Avalanche", "addresses.ts"),
    56: ("BSC", "addresses.ts"), 143: ("Monad", "addresses.ts"), 534352: ("Scroll", "addresses.ts"),
    100: ("Gnosis", "addresses.ts"), 42220: ("Celo", "addresses.ts"), 167000: ("Taiko", "addresses.ts"),
    59144: ("Linea", "addresses.ts"), 4326: ("MegaETH", "addresses.ts"), 196: ("XLayer", "addresses.ts"),
    2741: ("Abstract", "addresses.ts"), 5000: ("Mantle", "addresses.ts"), 1868: ("Soneium", "addresses.ts"),
    2345: ("GOAT Network", "addresses.ts"), 1088: ("Metis", "addresses.ts"), 295: ("Hedera", "addresses.ts"),
    1187947933: ("SKALE Base", "addresses.ts"), 360: ("Shape", "addresses.ts"),
    # in the reference README mainnet list but NOT in addresses.ts MAINNET_CHAIN_IDS;
    # chainId resolved by name from chainid.network (non-authoritative)
    4663: ("Robinhood Chain", "chainid.network name match"), 45056: ("Billions", "chainid.network name match"),
    1776: ("Injective", "chainid.network name match"), 16661: ("0G", "chainid.network name match"),
}
# Extra public endpoints tried (ahead of chainlist ones) where chainlist's endpoints failed the eth_getLogs smoke test.
# Not authoritative; recorded in output/rpc_selection.json like every other endpoint.
EXTRA_RPCS = {
    8453: ["https://base.llamarpc.com", "https://base.drpc.org", "https://1rpc.io/base", "https://base-mainnet.public.blastapi.io",
           "https://base.meowrpc.com", "https://base.api.onfinality.io/public", "https://mainnet.base.org", "https://base.publicnode.com"],
    56: ["https://bsc-rpc.publicnode.com", "https://bsc.drpc.org", "https://1rpc.io/bnb", "https://binance.llamarpc.com",
          "https://bsc-mainnet.public.blastapi.io", "https://bsc.meowrpc.com", "https://rpc-bsc.48.club", "https://bnb.rpc.subquery.network/public",
          "https://endpoints.omniatech.io/v1/bsc/mainnet/public", "https://bsc.publicnode.com"],
    143: ["https://rpc1.monad.xyz", "https://rpc2.monad.xyz", "https://rpc3.monad.xyz", "https://monad-mainnet.drpc.org"],
    10: ["https://mainnet.optimism.io", "https://optimism.drpc.org", "https://1rpc.io/op", "https://optimism.llamarpc.com"],
    1776: ["https://injective-evm-rpc.publicnode.com", "https://injective.drpc.org", "https://evm-rpc.injective.network"],
    196: ["https://xlayer.drpc.org", "https://xlayer-rpc.publicnode.com", "https://endpoints.omniatech.io/v1/xlayer/mainnet/public"],
}
ADDR = {  # reference repo scripts/addresses.ts MAINNET_ADDRESSES (CREATE2, same on every mainnet)
    "identity": "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432",
    "reputation": "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63",
    "validation": "0x8004Cc8439f36fd5F9F049D9fF86523Df6dAAB58",
}
ABI_FILE = {"identity": "IdentityRegistry", "reputation": "ReputationRegistry", "validation": "ValidationRegistry"}
EVENTS = [("identity", "Registered"), ("reputation", "NewFeedback"),
          ("validation", "ValidationRequest"), ("validation", "ValidationResponse")]


def keccak_hex(text):
    return "0x" + Web3.keccak(text=text).hex().removeprefix("0x")


def event_sig(reg, name):
    abi = json.load(open(os.path.join(HERE, "abis", ABI_FILE[reg] + ".json")))
    abi = abi["abi"] if isinstance(abi, dict) else abi
    evs = [e for e in abi if e.get("type") == "event" and e["name"] == name]
    assert len(evs) == 1, (reg, name, len(evs))
    assert all("tuple" not in i["type"] for i in evs[0]["inputs"])
    sig = f"{name}({','.join(i['type'] for i in evs[0]['inputs'])})"
    return sig, keccak_hex(sig)


def corrupt(topic0):  # flip the last hex digit
    last = topic0[-1]
    return topic0[:-1] + ("0" if last != "0" else "1")


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_log_lock = threading.Lock()
def log(*a):
    line = f"[{now()}] " + " ".join(str(x) for x in a)
    with _log_lock:
        print(line, flush=True)
        with open(os.path.join(OUT, "run.log"), "a") as f:
            f.write(line + "\n")


# ---------------------------------------------------------------- RPC
class RpcFail(Exception):
    pass

_host_sems = collections.defaultdict(lambda: threading.Semaphore(3))
_host_pace = collections.defaultdict(lambda: {"interval": 0.12, "next": 0.0, "ok_streak": 0})
_pace_lock = threading.Lock()


def _pace_wait(host):
    with _pace_lock:
        p = _host_pace[host]
        t = time.time()
        wait = max(0.0, p["next"] - t)
        p["next"] = max(t, p["next"]) + p["interval"]
    if wait:
        time.sleep(wait)


def _pace_feedback(host, rate_limited):
    with _pace_lock:
        p = _host_pace[host]
        if rate_limited:
            p["interval"] = min(3.0, p["interval"] * 1.5 + 0.05)
            p["ok_streak"] = 0
        else:
            p["ok_streak"] += 1
            if p["ok_streak"] >= 10:
                p["interval"] = max(0.12, p["interval"] * 0.85)
                p["ok_streak"] = 0


class Rpc:
    """JSON-RPC over HTTPS with endpoint failover. Errors propagate; they are never turned into empty results."""
    def __init__(self, urls, timeout=30):
        self.urls, self.timeout = list(urls), timeout
        self.used = collections.Counter()
        self.calls = 0
        self.streak = collections.Counter()   # consecutive failures per url; healthier endpoints are tried first
        self._tl = threading.local()          # http_s: server round-trip of this thread's last call (excludes queueing)

    def _post(self, url, method, params):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        req = urllib.request.Request(url, body, {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        host = url.split("/")[2]
        with _host_sems[host]:
            _pace_wait(host)
            t_http = time.time()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout, context=CTX) as r:
                    out = json.load(r)
                self._tl.http_s = time.time() - t_http
            except urllib.error.HTTPError as e:
                self._tl.http_s = time.time() - t_http
                _pace_feedback(host, e.code == 429)
                raise
            limited = isinstance(out, dict) and "error" in out and any(
                k in str(out["error"].get("message", "")).lower() for k in ("rate limit", "too many requests", "429", "request limit"))
            _pace_feedback(host, limited)
            return out

    def call(self, method, params, tries=3):
        last = None
        for url in sorted(self.urls, key=lambda u: self.streak[u]):
            for attempt in range(tries):
                r = None
                try:
                    self.calls += 1
                    r = self._post(url, method, params)
                except urllib.error.HTTPError as e:
                    last = f"{url}: HTTP {e.code}"
                    if e.code == 429:
                        for k in range(8):           # rate limited: wait and retry the SAME call, do not subdivide
                            time.sleep(min(10, 1.5 ** k) + random.random())
                            try:
                                r = self._post(url, method, params)
                                break
                            except urllib.error.HTTPError as e2:
                                if e2.code != 429:
                                    break
                            except Exception:
                                break
                        if r is None:
                            self.streak[url] += 1
                            break
                    elif e.code in (502, 503, 504):
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    else:
                        self.streak[url] += 1
                        break
                except Exception as e:  # timeouts, resets, TLS, bad JSON
                    last = f"{url}: {type(e).__name__}: {str(e)[:80]}"
                    self.streak[url] += 1
                    if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                        break   # a hanging range query will not get faster by repeating it; caller subdivides
                    time.sleep(1.0 * (attempt + 1))
                    continue
                if r is None:
                    break
                if "error" in r:
                    msg = str(r["error"].get("message", r["error"]))[:120]
                    last = f"{url}: rpc error: {msg}"
                    if "rate" in msg.lower() or "limit exceeded" in msg.lower() and "range" not in msg.lower():
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    self.streak[url] += 1
                    break  # deterministic node-side refusal -> next endpoint / caller subdivides
                if r.get("result") is None and method == "eth_getBlockByNumber":
                    last = f"{url}: null block (likely pruned/no history)"
                    break
                self.used[url] += 1
                self.streak[url] = 0
                return r["result"]
        raise RpcFail(last or "no endpoints")


def hx(n):
    return hex(n)


def get_head(rpc):
    return int(rpc.call("eth_blockNumber", []), 16)


def block_ts(rpc, n):
    b = rpc.call("eth_getBlockByNumber", [hx(n), False])
    if b is None:
        raise RpcFail(f"block {n} not found")
    return int(b["timestamp"], 16)


def has_code(rpc, addr, block):
    c = rpc.call("eth_getCode", [addr, hx(block)])
    return c not in ("0x", "0x0", None)


def block_at_or_after_ts(rpc, ts, hi):
    """First block with timestamp >= ts, searched inside a window estimated from recent block time (verified, not assumed)."""
    t_hi = block_ts(rpc, hi)
    if t_hi < ts:
        raise RpcFail("as-of block is older than the requested timestamp")
    probe = min(100_000, hi)
    bt = max(1e-3, (t_hi - block_ts(rpc, hi - probe)) / probe) if probe else 1.0
    est = max(0, hi - int((t_hi - ts) / bt))
    lo = max(0, est - max(5_000, int(0.5 * (hi - est))))
    hi2 = max(lo, min(hi, est + max(5_000, int(0.5 * (hi - est)))))
    if block_ts(rpc, lo) >= ts and lo > 0:        # estimate was too optimistic; widen to genesis (may hit pruned history)
        lo = 0
    if block_ts(rpc, hi2) < ts:
        hi2 = hi
    while lo < hi2:
        mid = (lo + hi2) // 2
        if block_ts(rpc, mid) >= ts:
            hi2 = mid
        else:
            lo = mid + 1
    return lo


# ---------------------------------------------------------------- scanner
class ScanError(Exception):
    pass


def scan(rpc, addr, topic0, lo, hi, init_chunk=200_000, max_chunk=5_000_000, keep_logs=False, tag="", budget_s=None):
    """Count logs of (addr, topic0) in [lo, hi] inclusive. topic0 may be a str or a list of str (OR at position 0).
    Raises ScanError if any sub-range cannot be fetched."""
    addr_l = addr.lower()
    t_list = [topic0] if isinstance(topic0, str) else list(topic0)
    t_set = {t.lower() for t in t_list}
    by_topic = collections.Counter()
    seen = set()
    first = last = None
    d_t1, d_t2 = set(), set()
    kept = []
    size, p = init_chunk, lo
    ceiling = max_chunk
    fast_streak = 0
    chunks = splits = dup = 0
    biggest_ok = 0
    t0 = time.time()
    deadline = None if budget_s is None else t0 + budget_s
    incomplete = False
    while p <= hi:
        if deadline is not None and time.time() > deadline:
            incomplete = True            # out of time: report what was covered, flagged INCOMPLETE by the caller
            break
        end = min(hi, p + size - 1)
        t_call = time.time()
        try:
            res = rpc.call("eth_getLogs", [{"fromBlock": hx(p), "toBlock": hx(end), "address": addr, "topics": [t_list if len(t_list) > 1 else t_list[0]]}], tries=2)
        except RpcFail as e:
            if end == p:
                raise ScanError(f"{tag} single block {p} unfetchable: {e}")
            size = max(1, (end - p + 1) // 2); splits += 1
            ceiling = min(ceiling, size)
            continue
        if not isinstance(res, list):
            raise ScanError(f"{tag} non-list result for [{p},{end}]: {str(res)[:80]}")
        if len(res) in CAP_SUSPECTS and end > p:       # possible silent truncation -> subdivide
            size = max(1, (end - p + 1) // 2); splits += 1
            continue
        for l in res:
            bn = int(l["blockNumber"], 16)
            if not (p <= bn <= end) or l["address"].lower() != addr_l or l["topics"][0].lower() not in t_set:
                raise ScanError(f"{tag} log outside request: block {bn} addr {l['address']} topic0 {l['topics'][0]}")
            key = (bn, int(l["logIndex"], 16))
            if key in seen:
                dup += 1; continue
            seen.add(key)
            by_topic[l["topics"][0].lower()] += 1
            first = bn if first is None else min(first, bn)
            last = bn if last is None else max(last, bn)
            if len(l["topics"]) > 1: d_t1.add(l["topics"][1].lower())
            if len(l["topics"]) > 2: d_t2.add(l["topics"][2].lower())
            if keep_logs:
                kept.append({"block": bn, "tx": l["transactionHash"], "logIndex": key[1], "topics": l["topics"], "data": l["data"]})
        span = end - p + 1                  # measured BEFORE p advances
        chunks += 1
        if tag and chunks % 250 == 0:
            log(f"  progress {tag}: {100*(end-lo+1)/(hi-lo+1):.0f}% ({chunks} calls, {len(seen)} logs so far)")
        biggest_ok = max(biggest_ok, span)
        p = end + 1
        tl = getattr(rpc, "_tl", None)
        lat = getattr(tl, "http_s", None) if tl is not None else None
        lat = (time.time() - t_call) if lat is None else lat          # mocks: wall clock
        if lat > SLOW_CALL_S:                 # slow SERVER-side: stop growing this scan's range
            ceiling = max(1, min(ceiling, span)); fast_streak = 0
        else:
            fast_streak += 1
            if fast_streak >= 20 and ceiling < max_chunk:     # recover from a transient slow patch
                ceiling = min(max_chunk, ceiling * 2); fast_streak = 0
        if len(res) < 500:
            size = max(1, min(ceiling, size * 2))
    out = {"count": len(seen), "first_block": first, "last_block": last, "chunks": chunks, "splits": splits,
           "duplicates_dropped": dup, "largest_ok_range": biggest_ok, "distinct_topic1": len(d_t1),
           "distinct_topic2": len(d_t2), "elapsed_s": round(time.time() - t0, 1), "by_topic": dict(by_topic),
           "incomplete": incomplete, "scanned_from": lo, "scanned_to": p - 1}
    if keep_logs:
        out["logs"] = kept
    return out


def scan_parallel(rpc, addr, topic0, lo, hi, parts=6, keep_logs=False, tag="", **kw):
    if hi - lo + 1 < 50_000 or parts <= 1:
        return scan(rpc, addr, topic0, lo, hi, keep_logs=keep_logs, tag=tag, **kw)
    step = (hi - lo + 1 + parts - 1) // parts
    segs = [(lo + i * step, min(hi, lo + (i + 1) * step - 1)) for i in range(parts) if lo + i * step <= hi]
    with cf.ThreadPoolExecutor(len(segs)) as ex:
        outs = list(ex.map(lambda se: scan(rpc, addr, topic0, se[0], se[1], keep_logs=keep_logs, tag=f"{tag}[{se[0]}-{se[1]}]", **kw), segs))
    merged = {"count": sum(o["count"] for o in outs),
              "first_block": min([o["first_block"] for o in outs if o["first_block"] is not None], default=None),
              "last_block": max([o["last_block"] for o in outs if o["last_block"] is not None], default=None),
              "chunks": sum(o["chunks"] for o in outs), "splits": sum(o["splits"] for o in outs),
              "duplicates_dropped": sum(o["duplicates_dropped"] for o in outs),
              "largest_ok_range": max(o["largest_ok_range"] for o in outs),
              # distinct sets cannot be merged from counts; recomputed exactly only when logs are kept
              "distinct_topic1": None if not keep_logs else len({l["topics"][1].lower() for o in outs for l in o.get("logs", []) if len(l["topics"]) > 1}),
              "distinct_topic2": None, "elapsed_s": round(max(o["elapsed_s"] for o in outs), 1), "segments": len(segs),
              "by_topic": dict(sum((collections.Counter(o["by_topic"]) for o in outs), collections.Counter())),
              "incomplete": any(o["incomplete"] for o in outs),
              "covered_ranges": [[o["scanned_from"], o["scanned_to"]] for o in outs],
              "scanned_from": lo, "scanned_to": max(o["scanned_to"] for o in outs)}
    if keep_logs:
        merged["logs"] = sorted((l for o in outs for l in o["logs"]), key=lambda l: (l["block"], l["logIndex"]))
    return merged


# ---------------------------------------------------------------- io helpers
def jload(name, default=None):
    p = os.path.join(OUT, name)
    return json.load(open(p)) if os.path.exists(p) else default


def jsave(name, obj):
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)


def chain_list(arg):
    ids = [int(x) for x in arg.split(",")] if arg else list(CHAINS)
    return ids


def rpc_for(sel, cid):
    urls = sel.get(str(cid), {}).get("rpcs", [])
    if not urls:
        raise SystemExit(f"no selected RPC for chain {cid}; run `select` first")
    return Rpc(urls)


def init_chunk_for(sel, cid):
    m = sel.get(str(cid), {}).get("max_range_measured", {})
    return max([1_000] + list(m.values()))


def scan_kw(sel, cid):
    best = init_chunk_for(sel, cid)
    return {"init_chunk": min(best, 10_000), "max_chunk": best}


# ---------------------------------------------------------------- commands
def cmd_select(args):
    import urllib.request as ur
    cl_path = os.path.join(OUT, "chainlist.json")
    if not os.path.exists(cl_path):
        req = ur.Request("https://chainid.network/chains.json", headers={"User-Agent": "Mozilla/5.0"})
        open(cl_path, "wb").write(ur.urlopen(req, timeout=60, context=CTX).read())
    chainlist = {c["chainId"]: c for c in json.load(open(cl_path))}
    sel = jload("rpc_selection.json", {})

    def one(cid):
        cands = [u for u in chainlist.get(cid, {}).get("rpc", []) if u.startswith("https://") and "${" not in u and "API_KEY" not in u.upper()]
        good, notes = [], []
        for url in (EXTRA_RPCS.get(cid, []) + cands)[:14]:
            try:
                r = Rpc([url], timeout=20)
                if int(r.call("eth_chainId", [], tries=2), 16) != cid:
                    notes.append((url, "chainId mismatch")); continue
                head = get_head(r)
                for a in ADDR.values():
                    r.call("eth_getCode", [a, "latest"], tries=2)
                r.call("eth_getLogs", [{"fromBlock": hx(max(0, head - 500)), "toBlock": hx(head - 1), "address": ADDR["validation"],
                                         "topics": [event_sig("validation", "ValidationRequest")[1]]}], tries=2)
                best = 0
                for span in (1_000, 5_000, 10_000, 50_000, 100_000, 500_000, 2_000_000):
                    try:
                        r.call("eth_getLogs", [{"fromBlock": hx(max(0, head - span)), "toBlock": hx(head - 1), "address": ADDR["validation"],
                                                 "topics": [event_sig("validation", "ValidationRequest")[1]]}], tries=1)
                        best = span
                    except Exception:
                        break
                good.append((best, url))
                if len(good) >= 5:
                    break
            except Exception as e:
                notes.append((url, f"{type(e).__name__}: {str(e)[:60]}"))
        good.sort(key=lambda t: -t[0])
        return cid, {"name": CHAINS[cid][0], "rpcs": [u for _, u in good[:3]], "max_range_measured": {u: b for b, u in good}, "rejected": notes}
    with cf.ThreadPoolExecutor(10) as ex:
        for cid, v in ex.map(one, chain_list(args.chains)):
            sel[str(cid)] = v
            log(f"select {cid} {v['name']}: {len(v['rpcs'])} endpoints {v['rpcs'][:1]}")
    jsave("rpc_selection.json", sel)


def cmd_asof(args):
    sel, asof = jload("rpc_selection.json", {}), jload("as_of.json", {})
    for cid in chain_list(args.chains):
        if cid in (295,) and not sel.get(str(cid), {}).get("rpcs"): continue
        rpc = rpc_for(sel, cid)
        head = get_head(rpc)
        tb = head - SAFETY_BLOCKS
        asof[str(cid)] = {"name": CHAINS[cid][0], "head_when_fixed": head, "to_block": tb, "to_block_ts": block_ts(rpc, tb),
                          "to_block_utc": iso(block_ts(rpc, tb)), "fixed_at_utc": now(), "safety_blocks": SAFETY_BLOCKS}
        log(f"asof {cid} {CHAINS[cid][0]} to_block={tb} {asof[str(cid)]['to_block_utc']}")
    jsave("as_of.json", asof)


def cmd_deploy(args):
    sel, asof, dep = jload("rpc_selection.json", {}), jload("as_of.json", {}), jload("deploy_blocks.json", {})
    def one(cid, reg):
        rpc = rpc_for(sel, cid)
        hi = asof[str(cid)]["to_block"]
        addr = ADDR[reg]
        res = {"address": addr}
        try:
            if not has_code(rpc, addr, hi):
                res.update(status="no_code_at_to_block"); return cid, reg, res
            floor = block_at_or_after_ts(rpc, FLOOR_TS, hi)
            res["search_window_start"] = floor
            if has_code(rpc, addr, floor):
                res.update(status="code_present_at_search_floor", floor_block=floor); return cid, reg, res
            lo, h, probes = floor, hi, 0
            while lo < h:
                mid = (lo + h) // 2; probes += 1
                if has_code(rpc, addr, mid): h = mid
                else: lo = mid + 1
            b = lo
            ok_prev = (b == 0) or (not has_code(rpc, addr, b - 1))
            ok_here = has_code(rpc, addr, b)
            logs_at_b = rpc.call("eth_getLogs", [{"fromBlock": hx(b), "toBlock": hx(b), "address": addr}])
            res.update(status="resolved", block=b, block_utc=iso(block_ts(rpc, b)), method="binary search on eth_getCode within [first block >= 2025-10-01 UTC, as-of]",
                       probes=probes, code_at_block=ok_here, no_code_at_prev_block=ok_prev, logs_at_deploy_block=len(logs_at_b))
            if not (ok_here and ok_prev):
                res["status"] = "inconsistent"
        except RpcFail as e:
            res.update(status="unresolved_no_archive", error=str(e)[:200])
            try:
                fb = block_at_or_after_ts(rpc, FLOOR_TS, hi)
                res.update(floor_block=fb, floor_utc=iso(block_ts(rpc, fb)),
                           method="fallback: first block at/after 2025-10-01 UTC")
            except RpcFail as e2:
                res.update(status="unresolved_no_floor", floor_error=str(e2)[:200])
        except Exception as e:  # never let one task kill the batch; the failure is recorded as data
            res.update(status="error", error=f"{type(e).__name__}: {str(e)[:200]}")
        return cid, reg, res
    jobs = [(cid, reg) for cid in chain_list(args.chains) if str(cid) in asof for reg in ADDR]
    with cf.ThreadPoolExecutor(12) as ex:
        for cid, reg, res in ex.map(lambda j: one(*j), jobs):
            dep.setdefault(str(cid), {"name": CHAINS[cid][0]})[reg] = res
            log(f"deploy {cid} {CHAINS[cid][0]} {reg}: {res.get('status')} block={res.get('block', res.get('floor_block'))}")
    jsave("deploy_blocks.json", dep)


COUNTABLE = ("resolved", "unresolved_no_archive", "code_present_at_search_floor")


def from_block(dep, cid, reg):
    r = dep[str(cid)][reg]
    return r.get("block", r.get("floor_block"))


def cmd_controls(args):
    """(a) range entirely before the deployment block -> must be 0.
       (b) last hex digit of topic0 flipped -> must be 0, over a window; paired with (b') the TRUE topic over the identical
           window, which shows the window is not simply empty. Window = full range unless it would need > 3,000 calls
           (then the first 3,000 calls' worth of blocks); --full forces full range (validation events only).
       Both validation events are scanned together (OR at topic position 0) and so are corrupted together."""
    sel, asof, dep = jload("rpc_selection.json", {}), jload("as_of.json", {}), jload("deploy_blocks.json", {})
    out_name = "controls_full.json" if args.full else "controls.json"
    results, bad, jobs = [], [], []
    for cid in chain_list(args.chains):
        if str(cid) not in dep: continue
        if dep[str(cid)]["validation"].get("status") in COUNTABLE:
            jobs.append((cid, "validation", "ValidationRequest+ValidationResponse"))
        if args.full: continue
        for reg, ev in (("identity", "Registered"), ("reputation", "NewFeedback")):
            if dep[str(cid)][reg].get("status") in COUNTABLE:
                jobs.append((cid, reg, ev))
    def one(job):
        cid, reg, ev = job
        rpc = rpc_for(sel, cid)
        if reg == "validation":
            t0 = [event_sig("validation", "ValidationRequest")[1], event_sig("validation", "ValidationResponse")[1]]
            t_cor = [corrupt(t) for t in t0]
        else:
            t0 = event_sig(reg, ev)[1]
            t_cor = corrupt(t0)
        db, tb = from_block(dep, cid, reg), asof[str(cid)]["to_block"]
        kw = dict(scan_kw(sel, cid), budget_s=BUDGET_CONTROL_S)
        resolved = dep[str(cid)][reg].get("status") == "resolved"
        a = scan(rpc, ADDR[reg], t0, max(0, db - 200_000), db - 1, **kw, tag=f"ctlA {cid} {ev}") if (resolved and db > 0 and not args.full) else None
        w_hi = tb if args.full else min(tb, db + CONTROL_WINDOW_CALLS * min(kw["max_chunk"], 20_000))
        b = scan_parallel(rpc, ADDR[reg], t_cor, db, w_hi, **kw, tag=f"ctlB {cid} {ev}")
        bp = scan_parallel(rpc, ADDR[reg], t0, db, w_hi, **kw, tag=f"ctlB' {cid} {ev}")
        return {"chainId": cid, "chain": CHAINS[cid][0], "registry": reg, "address": ADDR[reg], "event": ev, "topic0": t0,
                "topic0_corrupted": t_cor,
                "pre_deploy_range": [max(0, db - 200_000), db - 1] if a else None, "pre_deploy_count": a["count"] if a else None,
                "window": [db, w_hi], "window_is_full_range": w_hi == tb,
                "corrupted_topic_count": b["count"], "true_topic_count_same_window": bp["count"],
                "incomplete": bool((a and a["incomplete"]) or b["incomplete"] or bp["incomplete"]),
                "rpc_endpoints_used": dict(rpc.used)}
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for fut in cf.as_completed([ex.submit(one, j) for j in jobs]):
            try:
                r = fut.result()
            except Exception as e:
                log(f"CONTROL-ERROR {type(e).__name__}: {str(e)[:200]}")
                results.append({"error": f"{type(e).__name__}: {str(e)[:300]}"}); continue
            results.append(r)
            if r["incomplete"]:
                log(f"CONTROL-INCOMPLETE chain={r['chainId']} {r['chain']} {r['event']}: time budget hit; "
                    f"(a)={r['pre_deploy_count']} (b)={r['corrupted_topic_count']} (b')={r['true_topic_count_same_window']} are LOWER BOUNDS over partial coverage, not a pass")
                continue
            tc = r["topic0_corrupted"][0] if isinstance(r["topic0_corrupted"], list) else r["topic0_corrupted"]
            log(f"CONTROL chain={r['chainId']:<11} {r['chain']:<13} {r['event']:<38} "
                f"(a) pre-deploy {r['pre_deploy_range'] or 'n/a'} -> {r['pre_deploy_count']}   "
                f"(b) corrupted topic0 {tc[:14]}.. over {r['window']}{'' if r['window_is_full_range'] else ' [window]'} -> {r['corrupted_topic_count']}   "
                f"(b') true topic0, same window -> {r['true_topic_count_same_window']}")
            if r["pre_deploy_count"] or r["corrupted_topic_count"]:
                bad.append(r)
    errors = [r for r in results if "error" in r]
    incompletes = [r for r in results if r.get("incomplete")]
    jsave(out_name, {"run_at_utc": now(), "results": results, "nonzero": bad, "errors": errors, "incomplete": incompletes})
    if bad:
        log("!!! CONTROL RETURNED NON-ZERO — STOP. See", out_name); sys.exit(2)
    log(f"{len(results)-len(errors)-len(incompletes)} control sets returned zero for (a)/(b); "
        f"{len(incompletes)} incomplete (budget); {len(errors)} errored (see {out_name})")


def cmd_count(args):
    sel, asof, dep = jload("rpc_selection.json", {}), jload("as_of.json", {}), jload("deploy_blocks.json", {})
    c = jload("controls.json")
    if not c or c.get("nonzero"):
        raise SystemExit("controls.json missing or non-zero; refusing to count")
    os.makedirs(os.path.join(OUT, "counts"), exist_ok=True)
    jobs = []
    for cid in chain_list(args.chains):
        if str(cid) not in dep: continue
        if dep[str(cid)]["validation"].get("status") in COUNTABLE:
            jobs.append((0, cid, "validation", "VALIDATION"))
        for reg, ev in (("identity", "Registered"), ("reputation", "NewFeedback")):
            if dep[str(cid)][reg].get("status") in COUNTABLE:
                jobs.append((1, cid, reg, ev))
        for reg in ADDR:   # positive control: each proxy must show >=1 Initialized(uint64) from its from-block
            if dep[str(cid)][reg].get("status") in COUNTABLE:
                jobs.append((2, cid, reg, "Initialized"))
    jobs.sort(key=lambda j: j[0])   # decisive (validation) first
    def base_rec(cid, reg, ev, sig, t0, rpc, fb, tb):
        return {"chainId": cid, "chain": CHAINS[cid][0], "registry": reg, "address": ADDR[reg], "event": ev, "signature": sig,
                "topic0": t0, "from_block": fb, "from_block_source": dep[str(cid)][reg]["status"], "to_block": tb,
                "to_block_utc": asof[str(cid)]["to_block_utc"], "rpc_endpoints_configured": rpc.urls}
    def one(job):
        _, cid, reg, ev = job
        rpc = rpc_for(sel, cid)
        fb, tb = from_block(dep, cid, reg), asof[str(cid)]["to_block"]
        if ev == "VALIDATION":
            pr, pp = event_sig("validation", "ValidationRequest"), event_sig("validation", "ValidationResponse")
            names = {"ValidationRequest": pr, "ValidationResponse": pp}
            paths = {n: os.path.join(OUT, "counts", f"{cid}_validation_{n}.json") for n in names}
            if all(os.path.exists(p) for p in paths.values()) and not args.force:
                return
            recs = {n: base_rec(cid, reg, n, sg, t, rpc, fb, tb) for n, (sg, t) in names.items()}
            try:
                r = scan_parallel(rpc, ADDR[reg], [pr[1], pp[1]], fb, tb, **scan_kw(sel, cid), budget_s=BUDGET_COUNT_S, keep_logs=True, tag=f"{cid} validation")
                for n, (sg, t) in names.items():
                    logs = [l for l in r["logs"] if l["topics"][0].lower() == t.lower()]
                    recs[n].update(status="INCOMPLETE_BUDGET" if r["incomplete"] else "complete", scanned_to_block=r["scanned_to"],
                                   covered_ranges=r.get("covered_ranges"), count=r["by_topic"].get(t.lower(), 0),
                                   first_block=min([l["block"] for l in logs], default=None),
                                   last_block=max([l["block"] for l in logs], default=None), logs=logs,
                                   distinct_validators=len({l["topics"][1].lower() for l in logs}),
                                   distinct_agentIds=len({l["topics"][2].lower() for l in logs}),
                                   scan_chunks=r["chunks"], scan_splits=r["splits"], scan_duplicates_dropped=r["duplicates_dropped"],
                                   scan_note="ValidationRequest and ValidationResponse fetched in one eth_getLogs OR-topic scan")
            except (ScanError, RpcFail) as e:
                for rec in recs.values():
                    rec.update(status="INCOMPLETE", error=str(e)[:300])
            for n, rec in recs.items():
                rec["rpc_endpoints_used"] = dict(rpc.used)
                json.dump(rec, open(paths[n], "w"), indent=1)
                log(f"count {cid} {CHAINS[cid][0]:<13} {n:<18} {rec['status']} count={rec.get('count')} validators={rec.get('distinct_validators')} blocks={fb}-{tb}")
            return
        path = os.path.join(OUT, "counts", f"{cid}_{reg}_{ev}.json")
        if os.path.exists(path) and not args.force:
            return
        sig, t0 = event_sig(reg, ev)
        rec = base_rec(cid, reg, ev, sig, t0, rpc, fb, tb)
        hi_scan = tb
        if ev == "Initialized" and dep[str(cid)][reg]["status"] == "resolved":
            hi_scan = min(tb, fb + CONTROL_WINDOW_CALLS * min(scan_kw(sel, cid)["max_chunk"], 20_000))
            rec["to_block_note"] = "Initialized presence check scanned only the window after the deploy block"
        try:
            r = scan_parallel(rpc, ADDR[reg], t0, fb, hi_scan, **scan_kw(sel, cid), budget_s=BUDGET_COUNT_S, tag=f"{cid} {ev}")
            rec.update(status="INCOMPLETE_BUDGET" if r["incomplete"] else "complete", scanned_to_block=r["scanned_to"],
                       **{k: v for k, v in r.items() if k != "scanned_to"})
        except (ScanError, RpcFail) as e:
            rec.update(status="INCOMPLETE", error=str(e)[:300])
        rec["rpc_endpoints_used"] = dict(rpc.used)
        json.dump(rec, open(path, "w"), indent=1)
        log(f"count {cid} {CHAINS[cid][0]:<13} {ev:<18} {rec['status']} count={rec.get('count')} blocks={fb}-{hi_scan}")
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for fut in cf.as_completed([ex.submit(one, j) for j in jobs]):
            try:
                fut.result()
            except Exception as e:
                log(f"COUNT-ERROR {type(e).__name__}: {str(e)[:200]}")


def cmd_ranges(args):
    """Re-rank endpoints by the largest eth_getLogs range they actually serve on an interior HISTORICAL window
    (select's recent-window measurement over-states what old ranges allow)."""
    sel, asof, dep = jload("rpc_selection.json", {}), jload("as_of.json", {}), jload("deploy_blocks.json", {})
    chainlist = {c["chainId"]: c for c in json.load(open(os.path.join(OUT, "chainlist.json")))}
    t0 = event_sig("validation", "ValidationRequest")[1]
    def one(cid):
        d = dep[str(cid)]["validation"]
        fb = d.get("block", d.get("floor_block", 0)) or 0
        tb = asof[str(cid)]["to_block"]
        w = fb + (tb - fb) // 3
        cands = EXTRA_RPCS.get(cid, []) + [u for u in chainlist.get(cid, {}).get("rpc", [])
                                         if u.startswith("https://") and "${" not in u and "API_KEY" not in u.upper()]
        cands += sel.get(str(cid), {}).get("rpcs", [])
        seen, res = set(), {}
        for url in cands:
            if url in seen: continue
            seen.add(url)
            r = Rpc([url], timeout=20)
            best, slow = 0, 0.0
            try:
                if int(r.call("eth_chainId", [], tries=1), 16) != cid: continue
                for span in (1_000, 2_000, 5_000, 10_000, 50_000, 100_000, 500_000):
                    t = time.time()
                    r.call("eth_getLogs", [{"fromBlock": hx(w), "toBlock": hx(w + span - 1), "address": ADDR["validation"], "topics": [t0]}], tries=1)
                    if time.time() - t > 8: break
                    best = span
            except Exception:
                pass
            if best:
                res[url] = best
        return cid, res
    ids = [c for c in chain_list(args.chains) if str(c) in dep and dep[str(c)]["validation"].get("status") in COUNTABLE]
    with cf.ThreadPoolExecutor(8) as ex:
        for cid, res in ex.map(one, ids):
            if res:
                order = sorted(res, key=lambda u: -res[u])
                sel[str(cid)]["rpcs"] = order[:3]
                sel[str(cid)]["max_range_historical"] = res
                sel[str(cid)]["max_range_measured"] = {u: res[u] for u in order[:3]}
            log(f"ranges {cid} {CHAINS[cid][0]}: " + ", ".join(f"{u.split('/')[2]}={b}" for u, b in sorted(res.items(), key=lambda t: -t[1])[:4]))
    jsave("rpc_selection.json", sel)


# Block ranges the quoted figures were indexed over, copied from the author's repo (RESEARCH.md "run history", last row per
# chain). Third-party data: used ONLY for the separate same-scope replication diagnostic, never for the primary measurement.
AUTHOR_RANGES = {1: (24_339_800, 25_601_554), 8453: (42_003_733, 49_019_181)}
AUTHOR_FIGURES = {1: {"Registered": 36_778, "NewFeedback": 3_203, "ValidationRequest": 0, "ValidationResponse": 0},
                  8453: {"Registered": 59_697, "NewFeedback": 415_952, "ValidationRequest": 12, "ValidationResponse": 7}}


def cmd_replicate(args):
    """Same counter, the author's block ranges. Diagnostic for comparing scope/time; does not alter primary counts."""
    sel = jload("rpc_selection.json", {})
    out = jload("replication.json", {})
    for cid in [int(c) for c in args.chains.split(",")] if args.chains else list(AUTHOR_RANGES):
        lo, hi = AUTHOR_RANGES[cid]
        rpc = rpc_for(sel, cid)
        res = {}
        pr, pp = event_sig("validation", "ValidationRequest"), event_sig("validation", "ValidationResponse")
        r = scan_parallel(rpc, ADDR["validation"], [pr[1], pp[1]], lo, hi, **scan_kw(sel, cid), keep_logs=False, tag=f"repl {cid} validation")
        res["ValidationRequest"] = r["by_topic"].get(pr[1].lower(), 0)
        res["ValidationResponse"] = r["by_topic"].get(pp[1].lower(), 0)
        log(f"replicate {cid} validation over {lo}-{hi}: req={res['ValidationRequest']} resp={res['ValidationResponse']}")
        for reg, ev in (("identity", "Registered"), ("reputation", "NewFeedback")):
            r = scan_parallel(rpc, ADDR[reg], event_sig(reg, ev)[1], lo, hi, **scan_kw(sel, cid), tag=f"repl {cid} {ev}")
            res[ev] = r["count"]
            log(f"replicate {cid} {ev} over {lo}-{hi}: {res[ev]}")
        out[str(cid)] = {"chain": CHAINS[cid][0], "range": [lo, hi], "my_counts": res, "author_figures": AUTHOR_FIGURES[cid],
                         "rpc_endpoints_used": dict(rpc.used), "run_at_utc": now()}
        jsave("replication.json", out)


def cmd_mergecontrols(args):
    """Fold controls_part1.stdout (a completed first run whose JSON was never written because the process was stopped
    while a few slow chains were outstanding) and controls_part2.json (the follow-up run) into controls.json."""
    import re
    merged, bad = [], []
    p1 = os.path.join(OUT, "controls_part1.stdout")
    pat = re.compile(r"CONTROL chain=(\d+)\s+(.+?)\s{2,}(\S+)\s+\(a\) pre-deploy (.+?) -> (\S+)\s+\(b\) corrupted topic0 (0x[0-9a-f]+)\.\. over "
                     r"(\[\d+, \d+\])( \[window\])? -> (\d+)\s+\(b'\) true topic0, same window -> (\d+)")
    errs = []
    for line in open(p1):
        m = pat.search(line)
        if m:
            cid, name, ev, a_rng, a_cnt, t_cor, win, is_win, b_cnt, bp_cnt = m.groups()
            r = {"chainId": int(cid), "chain": name.strip(), "event": ev, "pre_deploy_range": a_rng,
                 "pre_deploy_count": None if a_cnt == "None" else int(a_cnt), "topic0_corrupted_first": t_cor + "..",
                 "window": json.loads(win), "window_is_full_range": not is_win, "corrupted_topic_count": int(b_cnt),
                 "true_topic_count_same_window": int(bp_cnt), "incomplete": False, "source": "controls_part1.stdout (verbatim log line)"}
            merged.append(r)
            if (r["pre_deploy_count"] or 0) != 0 or r["corrupted_topic_count"] != 0:
                bad.append(r)
        elif "CONTROL-ERROR" in line:
            errs.append({"error": line.split("CONTROL-ERROR", 1)[1].strip()[:300], "source": "controls_part1.stdout"})
    p2 = jload("controls_part2.json", {"results": [], "nonzero": [], "errors": [], "incomplete": []})
    merged += [r for r in p2["results"] if "error" not in r and not r.get("incomplete")]
    bad += p2["nonzero"]
    errs += p2["errors"]
    inc = p2["incomplete"]
    jsave("controls.json", {"merged_at_utc": now(), "results": merged, "nonzero": bad, "errors": errs, "incomplete": inc,
                            "note": "part1 = first run (parsed from its verbatim stdout, kept as output/controls_part1.stdout); part2 = follow-up run for chains outstanding when part1 was stopped"})
    log(f"controls merged: {len(merged)} sets passed to the record, {len(bad)} non-zero, {len(errs)} errors, {len(inc)} incomplete")
    if bad:
        sys.exit(2)


def cmd_finish(args):
    """Resume INCOMPLETE_BUDGET records: rescan only the sub-ranges not yet covered and merge (no block is scanned twice)."""
    import glob
    sel = jload("rpc_selection.json", {})
    for path in sorted(glob.glob(os.path.join(OUT, "counts", "*.json"))):
        rec = json.load(open(path))
        if rec.get("status") != "INCOMPLETE_BUDGET" or rec["event"] in ("ValidationResponse", "Initialized"):
            continue
        cid, reg, ev = rec["chainId"], rec["registry"], rec["event"]
        if args.chains and str(cid) not in args.chains.split(","):
            continue
        if args.registry and reg not in args.registry.split(","):
            continue
        hi_target = rec["to_block"]
        cov = sorted(rec.get("covered_ranges") or [[rec["from_block"], rec["scanned_to_block"]]])
        remaining = []
        for i, (lo_i, done_to) in enumerate(cov):
            seg_hi = cov[i + 1][0] - 1 if i + 1 < len(cov) else hi_target
            if done_to < seg_hi:
                remaining.append([done_to + 1, seg_hi])
        if not remaining:
            continue
        rpc = rpc_for(sel, cid)
        is_val = reg == "validation"
        log(f"finish {cid} {CHAINS[cid][0]} {ev}: {len(remaining)} uncovered range(s), {sum(b-a+1 for a,b in remaining):,} blocks")
        topics = [event_sig("validation", "ValidationRequest")[1], event_sig("validation", "ValidationResponse")[1]] if is_val else event_sig(reg, ev)[1]
        by_topic, chunks, splits, dups, new_logs, new_cov, inc = collections.Counter(), 0, 0, 0, [], [], False
        for a, b in remaining:
            r = scan_parallel(rpc, ADDR[reg], topics, a, b, **scan_kw(sel, cid), budget_s=args.budget, keep_logs=is_val, tag=f"finish {cid} {ev}")
            by_topic.update(r["by_topic"]); chunks += r["chunks"]; splits += r["splits"]; dups += r["duplicates_dropped"]
            new_logs += r.get("logs", []); inc |= r["incomplete"]
            new_cov += r.get("covered_ranges") or [[r["scanned_from"], r["scanned_to"]]]
        targets = [path] + ([path.replace("ValidationRequest", "ValidationResponse")] if is_val else [])
        for tp in targets:
            t = json.load(open(tp))
            tt = t["topic0"].lower()
            if is_val:
                logs = t.get("logs", []) + [l for l in new_logs if l["topics"][0].lower() == tt]
                logs.sort(key=lambda l: (l["block"], l["logIndex"]))
                t["logs"] = logs
                t["count"] = len(logs)
                t["distinct_validators"] = len({l["topics"][1].lower() for l in logs})
                t["distinct_agentIds"] = len({l["topics"][2].lower() for l in logs})
                t["first_block"] = min([l["block"] for l in logs], default=None)
                t["last_block"] = max([l["block"] for l in logs], default=None)
            else:
                t["count"] = t["count"] + by_topic.get(tt, 0)
                t["distinct_topic1"] = None; t["distinct_topic2"] = None
            t["scan_chunks"] = t.get("scan_chunks", t.get("chunks", 0)) + chunks
            t["covered_ranges"] = sorted((t.get("covered_ranges") or []) + new_cov)
            t["status"] = "INCOMPLETE_BUDGET" if inc else "complete"
            t["scanned_to_block"] = hi_target if not inc else t["scanned_to_block"]
            t["resumed_at_utc"] = now()
            t["resume_note"] = "uncovered sub-ranges rescanned by `finish` and merged; covered ranges never rescanned"
            json.dump(t, open(tp, "w"), indent=1)
        log(f"finish {cid} {CHAINS[cid][0]} {ev}: now status={'INCOMPLETE_BUDGET' if inc else 'complete'}")


def cmd_union(args):
    """For endpoints measured to return false-empty results: repeat the validation scan `--passes` times and take the union of
    distinct logs (a union can only move toward the true set; it never over-counts). Result remains labelled a lower bound."""
    sel = jload("rpc_selection.json", {}); dep = jload("deploy_blocks.json", {}); asof = jload("as_of.json", {})
    for cid in [int(c) for c in args.chains.split(",")]:
        rpc = rpc_for(sel, cid)
        fb, tb = from_block(dep, cid, "validation"), asof[str(cid)]["to_block"]
        topics = [event_sig("validation", "ValidationRequest")[1], event_sig("validation", "ValidationResponse")[1]]
        paths = {n: os.path.join(OUT, "counts", f"{cid}_validation_{n}.json") for n in ("ValidationRequest", "ValidationResponse")}
        recs = {n: json.load(open(p)) for n, p in paths.items()}
        union = {}
        for n, r in recs.items():
            for l in r["logs"]: union[(l["block"], l["logIndex"])] = l
        history = [len(union)]
        for k in range(args.passes):
            r = scan_parallel(rpc, ADDR["validation"], topics, fb, tb, **scan_kw(sel, cid), keep_logs=True, budget_s=args.budget, tag=f"union{k} {cid}")
            for l in r["logs"]: union[(l["block"], l["logIndex"])] = l
            history.append(len(union))
            log(f"union {cid} pass {k+1}: this pass saw {r['count']} logs, union={len(union)}, incomplete={r['incomplete']}")
        for n, t in zip(recs, topics):
            logs = sorted((l for l in union.values() if l["topics"][0].lower() == t.lower()), key=lambda l: (l["block"], l["logIndex"]))
            rec = recs[n]
            rec.update(logs=logs, count=len(logs), distinct_validators=len({l["topics"][1].lower() for l in logs}),
                       distinct_agentIds=len({l["topics"][2].lower() for l in logs}),
                       first_block=min([l["block"] for l in logs], default=None), last_block=max([l["block"] for l in logs], default=None),
                       reliability="LOWER BOUND: endpoint returned false-empty results in controls; value is the union of passes",
                       union_passes=args.passes + 1, union_size_after_each_pass=history)
            json.dump(rec, open(paths[n], "w"), indent=1)


def cmd_report(args):
    """Markdown tables generated from output/*.json (no hand transcription)."""
    import glob
    dep, asof, sel = jload("deploy_blocks.json", {}), jload("as_of.json", {}), jload("rpc_selection.json", {})
    counts = {}
    for f in glob.glob(os.path.join(OUT, "counts", "*.json")):
        r = json.load(open(f))
        counts[(r["chainId"], r["registry"], r["event"])] = r
    def cell(cid, reg, ev):
        r = counts.get((cid, reg, ev))
        if r is None: return "not run"
        if r["status"] == "complete":
            return f"≥{r['count']:,} (lower bound: endpoint returns false-empties)" if cid in LOWER_BOUND_CHAINS else f"{r['count']:,}"
        if r["status"] == "INCOMPLETE_BUDGET":
            cov = r.get("covered_ranges") or []
            done = sum(b - a + 1 for a, b in cov); tot = r["to_block"] - r["from_block"] + 1
            return f">={r['count']:,} (partial, {100*done/tot:.0f}% of blocks)"
        return "NOT MEASURED"
    print("### Counts per chain (to-block fixed per chain; see as-of table)\n")
    print("| chain | chainId | Identity `Registered` | Reputation `NewFeedback` | Validation `ValidationRequest` | Validation `ValidationResponse` | distinct validators (req / resp) |")
    print("|---|---|---:|---:|---:|---:|---|")
    tot = collections.Counter()
    for cid in sorted(CHAINS, key=lambda c: (c != 1, c != 8453, c)):
        name = CHAINS[cid][0]
        vr, vp = counts.get((cid, "validation", "ValidationRequest")), counts.get((cid, "validation", "ValidationResponse"))
        dv = f"{vr.get('distinct_validators')} / {vp.get('distinct_validators')}" if vr and vp and vr["status"] != "INCOMPLETE" else "—"
        if str(cid) not in dep or dep[str(cid)]["validation"].get("status") not in COUNTABLE:
            st = dep.get(str(cid), {}).get("validation", {}).get("status", "no endpoint")
            print(f"| {name} | {cid} | — | — | — | — | not measured ({st}) |")
            continue
        print(f"| {name} | {cid} | {cell(cid,'identity','Registered')} | {cell(cid,'reputation','NewFeedback')} | "
              f"{cell(cid,'validation','ValidationRequest')} | {cell(cid,'validation','ValidationResponse')} | {dv} |")
        for k, reg, ev in (("reg", "identity", "Registered"), ("fb", "reputation", "NewFeedback"),
                           ("vr", "validation", "ValidationRequest"), ("vp", "validation", "ValidationResponse")):
            r = counts.get((cid, reg, ev))
            if r and r["status"] == "complete": tot[k] += r["count"]
    print(f"\nSum over chains with a *complete* scan only: Registered={tot['reg']:,}, NewFeedback={tot['fb']:,}, "
          f"ValidationRequest={tot['vr']:,}, ValidationResponse={tot['vp']:,}\n")
    print("### As-of blocks, deployment blocks, endpoints\n")
    print("| chain | chainId | from-block (validation) | from-block source | to-block | to-block UTC | endpoints that served logs |")
    print("|---|---|---:|---|---:|---|---|")
    for cid in sorted(CHAINS):
        d = dep.get(str(cid), {}).get("validation")
        if not d: continue
        fb = d.get("block", d.get("floor_block"))
        used = collections.Counter()
        for (c, reg, ev), r in counts.items():
            if c == cid:
                for u, n in r.get("rpc_endpoints_used", {}).items(): used[u.split("/")[2]] += n
        print(f"| {CHAINS[cid][0]} | {cid} | {fb} | {d.get('status')} | {asof.get(str(cid), {}).get('to_block')} | "
              f"{asof.get(str(cid), {}).get('to_block_utc')} | {', '.join(sorted(used)) or '—'} |")
    print("\n### Positive control: `Initialized(uint64)` seen from from-block (proves log history present)\n")
    print("| chain | identity | reputation | validation |")
    print("|---|---:|---:|---:|")
    for cid in sorted(CHAINS):
        row = []
        for reg in ("identity", "reputation", "validation"):
            r = counts.get((cid, reg, "Initialized"))
            row.append("—" if r is None else (str(r["count"]) if r["status"] != "INCOMPLETE" else "ERR"))
        if any(x != "—" for x in row): print(f"| {CHAINS[cid][0]} | " + " | ".join(row) + " |")
    print("\n### Validation events (all chains, raw)\n")
    for (cid, reg, ev), r in sorted(counts.items(), key=lambda t: (t[0][0], t[0][2])):
        if reg == "validation" and ev in ("ValidationRequest", "ValidationResponse") and r.get("count"):
            vs = collections.Counter(l["topics"][1].lower() for l in r["logs"])
            print(f"- **{CHAINS[cid][0]}** `{ev}`: {r['count']} logs, blocks {r['first_block']}–{r['last_block']}, "
                  f"{len(vs)} validator(s); status {r['status']}")

def cmd_selftest(args):
    """Chunker correctness against a mock provider: error-on-big-range, silent truncation at a cap, and a clean provider."""
    class Mock:
        def __init__(self, blocks, mode, cap=1000, maxrange=None):
            self.b, self.mode, self.cap, self.maxrange, self.used = sorted(blocks), mode, cap, maxrange, collections.Counter()
            self.urls = ["mock"]
        def call(self, method, params, tries=3):
            f = params[0]; lo, hi = int(f["fromBlock"], 16), int(f["toBlock"], 16)
            if self.maxrange and hi - lo + 1 > self.maxrange: raise RpcFail("range too large")
            hits = [x for x in self.b if lo <= x <= hi]
            if self.mode == "error" and len(hits) > self.cap: raise RpcFail("too many results")
            if self.mode == "truncate": hits = hits[:self.cap]
            tp = f["topics"][0]
            return [{"blockNumber": hx(x), "logIndex": "0x0", "address": ADDR["validation"],
                     "topics": [(tp[x % len(tp)] if isinstance(tp, list) else tp), "0x" + "00" * 31 + "01"],
                     "transactionHash": "0x" + "00" * 32, "data": "0x"} for x in hits]
    ok = True
    try:
        Rpc(["https://example.invalid"]).streak
    except NameError as e:
        ok = False; print("Rpc missing:", e)
    # topic0 derivation pinned to values computed independently with `cast keccak` (Phase 3)
    pinned = {("identity", "Registered"): "0xca52e62c367d81bb2e328eb795f7c7ba24afb478408a26c0e201d155c449bc4a",
              ("reputation", "NewFeedback"): "0x6a4a61743519c9d648a14e6493f47dbe3ff1aa29e7785c96c8326a205e58febc",
              ("validation", "ValidationRequest"): "0x530436c3634a98e1e626b0898be2f1e9980cc1bd2a78c07a0aba52d0a48a5059",
              ("validation", "ValidationResponse"): "0xafddf629e874ccc3963b6a888c477bd464a6c8525024fc88759ea3b2326349ae"}
    for (reg, ev), want in pinned.items():
        got = event_sig(reg, ev)[1]
        if got != want:
            ok = False; print("TOPIC0 MISMATCH", reg, ev, got, want)
    rnd = random.Random(7)
    for n in (0, 1, 999, 1000, 1001, 4321):
        for mode, cap, mr in (("error", 1000, None), ("truncate", 1000, None), ("clean", 0, 50_000), ("truncate", 10000, 10_000)):
            blocks = rnd.sample(range(10_000, 400_000), n)
            m = Mock(blocks, mode, cap, mr)
            r = scan(m, ADDR["validation"], "0x" + "ab" * 32, 10_000, 399_999, init_chunk=300_000)
            good = r["count"] == n
            ok &= good
            T = ["0x" + "cd" * 32, "0x" + "ef" * 32]
            r2 = scan(Mock(blocks, mode, cap, mr), ADDR["validation"], T, 10_000, 399_999, init_chunk=300_000)
            want = dict(collections.Counter(T[x % 2] for x in blocks))
            good2 = r2["count"] == n and r2["by_topic"] == want
            ok &= good2
            if not good2: print("FAIL-OR", n, mode, cap, mr, r2["count"], r2["by_topic"], want)
            if not good: print("FAIL", n, mode, cap, mr, r["count"])
    rb = scan(Mock(rnd.sample(range(10_000, 400_000), 50), "clean", 0, None), ADDR["validation"], "0x" + "ab" * 32, 10_000, 399_999,
              init_chunk=50_000, budget_s=-1)
    gb = rb["incomplete"] is True and rb["scanned_to"] == 9_999 and rb["count"] == 0
    ok &= gb
    if not gb: print("FAIL-BUDGET", rb)
    global SLOW_CALL_S
    saved, SLOW_CALL_S = SLOW_CALL_S, -1.0          # every call counts as "slow"
    try:
        m = Mock(rnd.sample(range(10_000, 400_000), 500), "clean", 0, None)
        r = scan(m, ADDR["validation"], "0x" + "ab" * 32, 10_000, 399_999, init_chunk=50_000, max_chunk=300_000)
        good = r["count"] == 500 and r["chunks"] < 400 and r["splits"] == 0
        ok &= good
        if not good: print("FAIL-SLOWPATH", r["count"], r["chunks"], r["splits"])
    finally:
        SLOW_CALL_S = saved
    print("selftest:", "PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)


def main():
    os.makedirs(OUT, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["select", "asof", "deploy", "ranges", "controls", "count", "replicate", "mergecontrols", "finish", "union", "report", "selftest"])
    ap.add_argument("--chains", default="")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--budget", type=int, default=10_800, help="finish: wall-clock seconds allowed per resumed scan")
    ap.add_argument("--registry", default="", help="finish: only these registries (comma list: identity,reputation,validation)")
    ap.add_argument("--passes", type=int, default=2, help="union: extra passes")
    ap.add_argument("--full", action="store_true", help="controls: full-range corrupted-topic scans, validation events only")
    a = ap.parse_args()
    globals()["cmd_" + a.cmd](a)


if __name__ == "__main__":
    main()
