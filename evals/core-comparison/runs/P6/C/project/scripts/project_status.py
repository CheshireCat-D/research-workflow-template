from pathlib import Path
import argparse, hashlib, json, sys
p=argparse.ArgumentParser(description='Read-only local ledger identity/dependency check')
p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();root=a.root.resolve()
def fp(path):
 if path.is_symlink() or not path.is_file():return None
 b=path.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def sig(r):return hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!='completion_bindings'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
try:
 state_path=root/'records/state.json';state=json.loads(state_path.read_text(encoding='utf-8'));records={r['id']:r for r in state['records']}
 files={};changes=[]
 for id,r in records.items():
  if 'path' not in r:continue
  rel=Path(r['path'])
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe relative path '+str(rel))
  full=root/rel
  if any(v.is_symlink() for v in [full,*list(full.parents)[:len(rel.parts)-1]]):raise ValueError('Symlink in tracked path '+str(rel))
  actual=fp(full);files[str(rel)]={'record':id,'expected':r.get('binding'),'actual':actual,'state':'missing' if actual is None else ('current' if actual==r.get('binding') else 'changed')}
  if files[str(rel)]['state']!='current':changes.append(str(rel))
 activities={}
 for id,r in records.items():
  if r['kind']!='activity':continue
  reasons=[]
  for dep,b in r.get('completion_bindings',{}).items():
   current=records.get(dep)
   if current is None:reasons.append('missing record '+dep);continue
   if current['version']!=b['version'] or sig(current)!=b['record_sha256']:reasons.append('changed record '+dep)
   if 'path' in b and fp(root/b['path'])!=b['file']:reasons.append('changed or missing file '+b['path'])
  activities[id]={'declared_status':r['status'],'effective_status':'stale' if r['status']=='done' and reasons else r['status'],'reasons':reasons}
 for _ in activities:
  for id,v in activities.items():
   for dep in records[id].get('depends_on',[]):
    if activities.get(dep,{}).get('effective_status')!='done':
     reason='dependency activity not current: '+dep
     if reason not in v['reasons']:v['reasons'].append(reason)
     if v['declared_status']=='done':v['effective_status']='stale'
 cp=state.get('checkpoint',{});cp_reasons=[]
 if state['state_version']!=cp.get('state_version'):cp_reasons.append('ledger version changed')
 config_sha=hashlib.sha256(json.dumps(state['configuration'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
 if config_sha!=cp.get('configuration_sha256'):cp_reasons.append('configuration changed')
 if cp.get('record_signatures')!={id:sig(r) for id,r in records.items()}:cp_reasons.append('logical records changed')
 for rel,expected in cp.get('files',{}).items():
  if fp(root/rel)!=expected:cp_reasons.append('changed or missing checkpoint file '+rel)
 mismatch=[]
 param=next((r for r in records.values() if r['id']=='D-PARAM'),None)
 if param and (root/param['path']).is_file():
  spec=json.loads((root/param['path']).read_text(encoding='utf-8'))
  for key,val in state['configuration'].get('current_scope',{}).items():
   if key in spec and spec[key]!=val:mismatch.append(key)
 out={'root':str(root),'authority':str(state_path),'state_version':state['state_version'],'state_sha256':fp(state_path)['sha256'],'files':files,'changed_or_missing_paths':changes,'activities':activities,'checkpoint_freshness':'stale' if cp_reasons else 'current','checkpoint_reasons':cp_reasons,'configuration_parameter_conflicts':mismatch,'configuration':state['configuration'],'next_action':cp.get('next_action'),'coverage_limits':state['coverage_limits'],'scientific_validity':'not-certified by identity check'}
 print(json.dumps(out,ensure_ascii=False,indent=2));sys.exit(1 if changes or cp_reasons or mismatch or any(x['effective_status']=='stale' for x in activities.values()) else 0)
except (OSError,ValueError,KeyError,TypeError) as e:
 print(json.dumps({'error':type(e).__name__,'message':str(e)},ensure_ascii=False));sys.exit(2)
