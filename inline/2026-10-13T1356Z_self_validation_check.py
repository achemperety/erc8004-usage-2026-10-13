import sys,json,glob,collections; sys.path.insert(0,".")
import erc8004_usage as u
sel=json.load(open("output/rpc_selection.json")); asof=json.load(open("output/as_of.json"))
# 1) subset of my Base events inside the author's window (pure filter of already-scanned logs)
lo,hi=u.AUTHOR_RANGES[8453]
sub={}
for ev in ("ValidationRequest","ValidationResponse"):
    r=json.load(open(f"output/counts/8453_validation_{ev}.json"))
    ins=[l for l in r["logs"] if lo<=l["block"]<=hi]
    sub[ev]={"in_author_window":len(ins),"after_author_window":len([l for l in r["logs"] if l["block"]>hi]),"before_author_window":len([l for l in r["logs"] if l["block"]<lo]),
             "validators_in_window":len({l["topics"][1] for l in ins}),"agents_in_window":len({l["topics"][2] for l in ins})}
print("Base events vs author window",lo,hi); print(json.dumps(sub,indent=1))
# 2) validator == owner of agent?  (eth_call ownerOf(agentId) on IdentityRegistry at latest)
sel_ownerof=u.keccak_hex("ownerOf(uint256)")[:10]
out=[]
for f in sorted(glob.glob("output/counts/*_validation_ValidationRequest.json")):
    r=json.load(open(f))
    if not r.get("count"): continue
    rpc=u.Rpc(sel[str(r["chainId"])]["rpcs"])
    for l in r["logs"]:
        agent=int(l["topics"][2],16); validator="0x"+l["topics"][1][-40:]
        try:
            res=rpc.call("eth_call",[{"to":u.ADDR["identity"],"data":sel_ownerof+hex(agent)[2:].rjust(64,"0")},"latest"])
            owner="0x"+res[-40:]
        except Exception as e: owner=f"ERR {str(e)[:40]}"
        out.append({"chain":r["chain"],"chainId":r["chainId"],"block":l["block"],"agentId":agent,"validator":validator,"owner_now":owner,
                    "validator_is_owner": validator.lower()==owner.lower() if owner.startswith("0x") else None})
json.dump(out,open("output/self_validation_check.json","w"),indent=1)
by=collections.defaultdict(lambda:[0,0,0])
for o in out:
    k=o["chain"]; by[k][0]+=1
    if o["validator_is_owner"] is True: by[k][1]+=1
    if o["validator_is_owner"] is None: by[k][2]+=1
for k,v in by.items(): print(f"{k:<8} requests={v[0]:<3} validator==current owner of agent: {v[1]:<3} lookup errors: {v[2]}")
