from pathlib import Path
import argparse, hashlib, json, os, sys
p=argparse.ArgumentParser(description='Guarded local ledger replacement; never executes research steps')
p.add_argument('--root',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--expected-version',type=int,required=True);p.add_argument('--expected-sha256',required=True);p.add_argument('--reason',required=True);a=p.parse_args()
root=a.root.resolve();state=root/'records/state.json';lock=root/'records/.edit.lock'
try:
 # POSIX flock is standard library on this project's actual macOS environment.
 import fcntl
 with lock.open('a+b') as f:
  fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  old_bytes=state.read_bytes();old=json.loads(old_bytes);old_sha=hashlib.sha256(old_bytes).hexdigest()
  if old['state_version']!=a.expected_version or old_sha!=a.expected_sha256:raise ValueError('Conflict: authoritative state has changed; reread it before editing')
  new=json.loads(a.candidate.read_text(encoding='utf-8'))
  if new['state_version']!=old['state_version']+1:raise ValueError('state_version must increase exactly by one')
  prior={r['id']:r for r in old['records']}
  for r in new['records']:
   prev=prior.get(r['id'])
   if prev is None and r['version']!=1:raise ValueError('New record version must be 1')
   if prev is not None:
    changed={k:v for k,v in prev.items() if k!='version'}!={k:v for k,v in r.items() if k!='version'}
    if r['version']!=prev['version']+int(changed):raise ValueError('Record version conflict: '+r['id'])
  new.setdefault('history',[]).append({'prior_state_version':old['state_version'],'prior_state_sha256':old_sha,'snapshot':'snapshots/authority/v'+str(old['state_version'])+'-'+old_sha+'.json','reason':a.reason,'executor':'current explicit local update; no implied human scientific approval'})
  snap=root/new['history'][-1]['snapshot'];snap.parent.mkdir(parents=True,exist_ok=True)
  if snap.exists() and snap.read_bytes()!=old_bytes:raise ValueError('Snapshot collision')
  if not snap.exists():snap.write_bytes(old_bytes)
  temp=state.with_name('.state.pending-'+str(os.getpid())+'.json')
  try:
   with temp.open('x',encoding='utf-8') as out:json.dump(new,out,ensure_ascii=False,indent=2,allow_nan=False);out.write('\n');out.flush();os.fsync(out.fileno())
   os.replace(temp,state)
  finally:
   if temp.exists():temp.unlink()
  print(json.dumps({'updated':True,'state_version':new['state_version'],'old_state_snapshot':str(snap)}))
except (OSError,ValueError,KeyError,TypeError) as e:
 print(json.dumps({'updated':False,'error':type(e).__name__,'message':str(e)}));sys.exit(2)
