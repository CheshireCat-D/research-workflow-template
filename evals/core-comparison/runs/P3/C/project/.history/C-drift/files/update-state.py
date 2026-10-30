#!/usr/bin/env python3
"""Explicit guarded metadata revisions. Never marks scientific activities fresh."""
import argparse, copy, fcntl, json, os, sys, tempfile
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
 p.add_argument('--expected-revision',type=int,required=True)
 p.add_argument('--patch',type=Path,required=True,help='JSON: rationale, configuration optional, records {id: {expected_version,data}} optional, next_action optional')
 a=p.parse_args();root=a.root.resolve();patch=json.loads(a.patch.read_text())
 if not patch.get('rationale'):raise ValueError('Revision rationale is required')
 with (root/'research/write.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  target=root/'research/state.json';old_bytes=target.read_bytes();state=json.loads(old_bytes)
  if state['metadata_revision']!=a.expected_revision:raise ValueError('Conflict: current metadata revision differs; reread current state')
  new=copy.deepcopy(state)
  if 'configuration' in patch:new['configuration']=patch['configuration']
  for rid,change in patch.get('records',{}).items():
   old=state['records'].get(rid)
   if old is None or old['version']!=change.get('expected_version'):raise ValueError('Conflict: record '+rid+' version differs')
   if change['data'].get('id')!=rid:raise ValueError('Record ID must be retained')
   new['records'][rid]={'version':old['version']+1,'data':change['data']}
  if 'next_action' in patch:new['next_action']=patch['next_action']
  if new==state:raise ValueError('No change requested')
  new['metadata_revision']+=1
  new['history'].append({'revision':new['metadata_revision'],'rationale':patch['rationale'],'previous_state':'.history/metadata/revision-'+str(state['metadata_revision'])+'.json'})
  archive=root/'.history/metadata'/('revision-'+str(state['metadata_revision'])+'.json');archive.parent.mkdir(parents=True,exist_ok=True)
  if archive.exists() and archive.read_bytes()!=old_bytes:raise ValueError('History conflict; existing archive has different bytes')
  if not archive.exists():
   with archive.open('xb') as f:f.write(old_bytes)
  fd,tmp=tempfile.mkstemp(prefix='.state-',dir=root/'research')
  try:
   with os.fdopen(fd,'w') as f:json.dump(new,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
   if target.read_bytes()!=old_bytes:raise ValueError('Conflict: metadata changed during revision')
   os.replace(tmp,target)
  finally:
   if os.path.exists(tmp):os.unlink(tmp)
  print(json.dumps({'metadata_revision':new['metadata_revision'],'scientific_activities_rebound':False,'checkpoint_updated':False}))
 return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except (OSError,ValueError,KeyError,TypeError) as e:
  print(json.dumps({'error':type(e).__name__,'message':str(e)}),file=sys.stderr);raise SystemExit(2)
