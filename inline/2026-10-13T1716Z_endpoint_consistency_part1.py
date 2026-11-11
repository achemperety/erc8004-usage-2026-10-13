import sys,json,time,collections,concurrent.futures as cf; sys.path.insert(0,".")
import erc8004_usage as u
sel=json.load(open("output/rpc_selection.json")); dep=json.load(open("output/deploy_blocks.json"))
used=collections.defaultdict(set)
import glob
for f in glob.glob("output/counts/*.json"):
    r=json.load(open(f))
    for url in r.get("rpc_endpoints_used",{}): used[r["chainId"]].add(url)
N=15
def test(job):
    cid,url,reg=job
    b=dep[str(cid)][reg]["block"]; ok=empty=err=0
    for i in range(N):
        try:
            n=len(u.Rpc([url],timeout=20).call("eth_getLogs",[{"fromBlock":hex(b),"toBlock":hex(b),"address":u.ADDR[reg]}],tries=1))
            if n==3: ok+=1
            elif n==0: empty+=1
            else: err+=1
        except Exception: err+=1
        time.sleep(0.25)
    return cid,url,reg,ok,empty,err
jobs=[(int(c),url,reg) for c,urls in used.items() if dep[str(c)]["validation"].get("status")=="resolved" for url in urls for reg in ("identity","reputation","validation")]
agg=collections.defaultdict(lambda:[0,0,0])
with cf.ThreadPoolExecutor(8) as ex:
    for cid,url,reg,ok,empty,err in ex.map(test,jobs):
        a=agg[(cid,url)]; a[0]+=ok; a[1]+=empty; a[2]+=err
print(f"{'chain':<16}{'endpoint':<36}{'correct(3 logs)':>16}{'false-empty':>13}{'other/err':>11}   (of {N*3} queries)")
for (cid,url),(ok,empty,err) in sorted(agg.items()):
    flag="  <-- UNRELIABLE" if empty else ""
    print(f"{u.CHAINS[cid][0]:<16}{url.split('/')[2]:<36}{ok:>16}{empty:>13}{err:>11}{flag}")
