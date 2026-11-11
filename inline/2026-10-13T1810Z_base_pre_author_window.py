import sys,json; sys.path.insert(0,".")
import erc8004_usage as u
sel=json.load(open("output/rpc_selection.json")); dep=json.load(open("output/deploy_blocks.json"))
rpc=u.Rpc(sel["8453"]["rpcs"]); kw=u.scan_kw(sel,8453)
fb=dep["8453"]["identity"]["block"]; lo_auth=u.AUTHOR_RANGES[8453][0]
out={}
for reg,ev in (("identity","Registered"),("reputation","NewFeedback")):
    r=u.scan_parallel(rpc,u.ADDR[reg],u.event_sig(reg,ev)[1],dep["8453"][reg]["block"],lo_auth-1,**kw,tag="pre-window")
    out[ev]={"range":[dep["8453"][reg]["block"],lo_auth-1],"count":r["count"]}
    print(ev,"in [deploy,",lo_auth-1,"] =",r["count"])
print("author Registered 59,697 - my in-window 42,949 =",59697-42949)
json.dump(out,open("output/base_pre_author_window.json","w"),indent=1)
