#!/usr/bin/env python3
"""Local project recovery: standard library, read-only status, no external resources."""
import argparse,hashlib,json,sys
from pathlib import Path
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def fingerprint(p):
 if p.is_symlink() or not p.is_file():return {"missing_or_nonregular":True}
 b=p.read_bytes();return {"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def status(root):
 state=json.loads((root/"research/state.json").read_text())
 actual={p:fingerprint(root/p) for p in state["tracked_files"]}
 changed=[p for p,old in state["tracked_files"].items() if actual[p]!=old]
 activities={}
 for aid,a in state["activities"].items():
  reasons=[{"file":p,"expected":old,"actual":fingerprint(root/p)} for p,old in a["captured_files"].items() if fingerprint(root/p)!=old]
  for rid,old in a["captured_records"].items():
   now=state["records"].get(rid)
   if not now or now["version"]!=old["version"] or digest(now)!=old["content_sha256"]:reasons.append({"record":rid,"cause":"version or record content changed"})
  activities[aid]={"declared_status":a["declared_status"],"effective_status":"stale" if reasons else a["declared_status"],"reasons":reasons}
 for iteration in range(len(activities)):
  for aid,a in state["activities"].items():
   for dep in a["depends_on"]:
    if activities[dep]["effective_status"]!="done":
     activities[aid]["effective_status"]="stale"
     reason={"depends_on":dep,"cause":"dependency not currently complete"}
     if reason not in activities[aid]["reasons"]:activities[aid]["reasons"].append(reason)
 cp=state.get("checkpoint") or {};cp_reasons=[]
 for key in ["configuration","records","activities"]:
  if cp.get(key+"_sha256")!=digest(state[key]):cp_reasons.append(key+" changed since checkpoint")
 if cp.get("metadata_revision")!=state.get("metadata_revision"):cp_reasons.append("metadata revision changed")
 if cp.get("tracked_files")!=actual:cp_reasons.append("tracked file bytes changed or missing")
 return {"case_id":state["case_id"],"authority":state["authority"],"metadata_revision":state["metadata_revision"],"active_constraints":state["configuration"],"next_action":state["next_action"],"changed_or_missing_paths":changed,"activities":activities,"checkpoint_freshness":{"fresh":not cp_reasons,"reasons":cp_reasons},"scientific_scope":state["scientific_scope"],"source_tracking_limits":state["tracking_exclusions"],"publication_rule":state["publication_rule"],"resume_is_read_only":True,"no_scientific_certification":True}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parent);a=p.parse_args()
 try:
  report=status(a.root.resolve());print(json.dumps(report,ensure_ascii=False,indent=2));return 1 if report["changed_or_missing_paths"] or not report["checkpoint_freshness"]["fresh"] or any(x["effective_status"]!="done" for x in report["activities"].values()) else 0
 except (OSError,ValueError,KeyError,TypeError) as e:
  print(json.dumps({"error":type(e).__name__,"message":str(e)}));return 2
if __name__=="__main__":raise SystemExit(main())
