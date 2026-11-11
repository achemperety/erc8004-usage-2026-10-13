"""Addendum B 2026-11-11: does each Base implementation's runtime bytecode contain PUSH4 <selector> for the three
validation functions of the vendored ValidationRegistry ABI? Read-only (eth_getCode).
Usage, from the repo root: python3 -I addenda/2026-11-11_selector_check.py abis/ValidationRegistry.json addenda/2026-11-11_base_calls.json"""
import json, sys, urllib.request, ssl
import certifi
from web3 import Web3

abi = json.load(open(sys.argv[1])); abi = abi["abi"] if isinstance(abi, dict) else abi
d = json.load(open(sys.argv[2]))
fns = [f for f in abi if f.get("type") == "function" and f["name"] in ("validationRequest", "validationResponse", "getValidationStatus")]
def ty(i): return i["type"] if not i["type"].startswith("tuple") else "(" + ",".join(ty(c) for c in i["components"]) + ")" + i["type"][5:]
sigs = sorted(f"{f['name']}({','.join(ty(i) for i in f['inputs'])})" for f in fns)
CTX = ssl.create_default_context(cafile=certifi.where())
def code(a, b):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getCode", "params": [a, b]}).encode()
    req = urllib.request.Request("https://mainnet.base.org", body, {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, context=CTX, timeout=30))["result"]
print("endpoint https://mainnet.base.org; blocks: as_of", d["as_of_block"], "head", d["head_block_at_run"])
for impl in sorted(d["implementations"]):
    for tag, b in (("as_of", hex(d["as_of_block"])), ("head", hex(d["head_block_at_run"]))):
        c = code(impl, b).lower()
        print(impl, tag, "code bytes", (len(c) - 2) // 2, "keccak", Web3.keccak(hexstr=c).hex())
        for sig in sigs:
            s = Web3.keccak(text=sig).hex().removeprefix("0x")[:8]
            print("   ", sig, "0x" + s, "PUSH4 present" if ("63" + s) in c else "absent")
