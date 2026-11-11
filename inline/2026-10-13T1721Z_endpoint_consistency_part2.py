import sys,json,time,collections; sys.path.insert(0,".")
import erc8004_usage as u
print("\n-- chains without a resolved deploy block: known-positive = first Initialized log found by the count scan --")
N=15
for cid in (42161,2345,4663,1187947933):
    r=json.load(open(f"output/counts/{cid}_identity_Initialized.json"))
    b=r.get("first_block")
    sel=json.load(open("output/rpc_selection.json"))[str(cid)]["rpcs"]
    for url in sel[:1]:
        res=collections.Counter()
        for i in range(N):
            try:
                n=len(u.Rpc([url],timeout=20).call("eth_getLogs",[{"fromBlock":hex(b),"toBlock":hex(b),"address":u.ADDR["identity"],"topics":[u.event_sig("identity","Initialized")[1]]}],tries=1))
                res[n]+=1
            except Exception: res["err"]+=1
            time.sleep(0.25)
        print(f"{u.CHAINS[cid][0]:<16}{url.split('/')[2]:<36} block {b}: results {dict(res)}")
