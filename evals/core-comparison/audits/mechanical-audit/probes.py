#!/usr/bin/env python3
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
globals().update({k:getattr(m,k) for k in ['S','A','PY','PLAN','load','sha','dump','snap','clone','run','prun','cli','payload','identity']})
import copy,json,shutil
RESULT={}
def summary(d):return {k:v for k,v in d.items() if k not in ['stdout','stderr']}
def status(c,root,label):
 if c in ['P1','P4']:return cli(label,root,['resume','--root',root],True)
 script={'P2':'management/status.py','P3':'resume.py','P5':'scripts/manage.py','P6':'scripts/project_status.py'}[c]
 return prun(label,root,script,['--root',root,'status'] if c=='P5' else ['--root',root],True)
def state_path(c,root):return root/{'P1':'records/registry.json','P2':'management/state.json','P3':'research/state.json','P4':'records/registry.json','P5':'.research/state.json','P6':'records/state.json'}[c]
def change_guard(result,st,before):
 result=summary(result);result['authoritative_bytes_preserved']=sha(st)==before;return result

# Whole-project read-only status on B and migration execution on a renamed C copy.
for chain in PLAN:
 c=chain['chain_id'];row={};root=clone(c,'B','readonly-B');r=status(c,root,c+'-B-readonly');row['readonly_B']=summary(r);row['B_status']=payload(r)
 origin=clone(c,'C','migration-origin');moved=origin.parent.parent/'迁移后 科研项目';origin.rename(moved)
 r=status(c,moved,c+'-migration-readonly');row['migration']={**summary(r),'old_copy_path':str(origin),'old_copy_unreachable':not origin.exists(),'new_copy_path':str(moved),'empty_HOME_and_XDG_CACHE_HOME':True,'os_access_enforcement':False,'scope':'Own project entry executed from renamed copy with common interpreter. Actual old paths verified absent separately; public cache exclusion remains an instruction boundary, not syscall evidence.'};row['migrated_status']=payload(r)
 if c=='P2':
  r=prun(c+'-numeric-verifier',moved,'management/verify_current.py',['--root',moved],True);row['delivered_independent_numeric_verifier']={**summary(r),'result':payload(r)}
 RESULT[c]=row

# Native record transactions: exact delivered CLI, no replacements or repairs.
for c in ['P1','P4']:
 row=RESULT[c];root=clone(c,'C','record-CAS');st=state_path(c,root);s=load(st);rdata=copy.deepcopy(s['records']['evidence'][('T' if c=='P1' else 'D')+'-PARAM']);rid=rdata['data']['id'];v=rdata['version'];rdata['data']['provenance']=rdata['data'].get('provenance','')+' [audit legal revision]'
 patch=root.parent/'legal.json';dump(patch,rdata['data']);r=cli(c+'-legal-update',root,['register','--root',root,'--kind','evidence','--file',patch,'--replace','--expected-version',v],True)
 before=sha(st);r2=cli(c+'-stale-record-write',root,['register','--root',root,'--kind','evidence','--file',patch,'--replace','--expected-version',v],True)
 row['stale_write']={'level':'logical record expected_version; observed vN then legal vN+1','old_version':v,'current_version':load(st)['records']['evidence'][rid]['version'],'legal_update':summary(r),'stale_request':change_guard(r2,st,before)}
 root=clone(c,'C','dangling');st=state_path(c,root);s=load(st);base=copy.deepcopy(next(iter(s['records']['relations'].values()))['data']);base['id']='AUDIT-DANGLING';base['evidence_id']='AUDIT-MISSING';patch=root.parent/'dangling.json';dump(patch,base);before=sha(st)
 r=cli(c+'-dangling-reference',root,['register','--root',root,'--kind','relation','--file',patch],True);row['dangling_reference']={**change_guard(r,st,before),'reference_field':'evidence_id=AUDIT-MISSING'}
 root=clone(c,'C','atomic-batch');st=state_path(c,root);s=load(st);valid=copy.deepcopy(next(iter(s['records']['sources'].values()))['data']);valid['id']='AUDIT-VALID-SOURCE';bad=copy.deepcopy(base);bad['id']='AUDIT-BAD-LINK';patch=root.parent/'batch.json';dump(patch,[{'kind':'source','record':valid},{'kind':'relation','record':bad}]);before=sha(st)
 r=cli(c+'-batch-invalid-later-reference',root,['register-batch','--root',root,'--file',patch],True);row['batch_invalid_later_reference']={**change_guard(r,st,before),'valid_first_absent':'AUDIT-VALID-SOURCE' not in load(st)['records']['sources']}
 root=clone(c,'B','dirty-checkpoint');r1=cli(c+'-dirty-save-checkpoint',root,['checkpoint','--root',root,'--next-action','audit: recompute before review'],True);r2=status(c,root,c+'-dirty-status-after-checkpoint');row['dirty_checkpoint']={'automatic_checkpoint_interface':True,'checkpoint_call':summary(r1),'subsequent_status':summary(r2),'result':payload(r2)}

# Guidance T custom update transactions, with separate global-revision and record-version probes.
c='P3';row=RESULT[c];root=clone(c,'C','record-CAS');st=state_path(c,root);s=load(st);rev=s['metadata_revision'];record=copy.deepcopy(s['records']['T-CLAIM']);record['data']['meaning']+=' [audit legal revision]';patch=root.parent/'legal.json';dump(patch,{'rationale':'audit legal revision','records':{'T-CLAIM':{'expected_version':record['version'],'data':record['data']}}})
r=prun(c+'-legal-update',root,'update-state.py',['--root',root,'--expected-revision',rev,'--patch',patch],True);before=sha(st)
r2=prun(c+'-stale-global-write',root,'update-state.py',['--root',root,'--expected-revision',rev,'--patch',patch],True)
r3=prun(c+'-stale-record-write',root,'update-state.py',['--root',root,'--expected-revision',rev+1,'--patch',patch],True)
row['stale_write']={'level':'global metadata_revision and per-record expected_version','legal_update':summary(r),'stale_global_request':change_guard(r2,st,before),'stale_record_request':change_guard(r3,st,before)}
root=clone(c,'C','dangling');st=state_path(c,root);s=load(st);rec=s['records']['T-REL'];bad=copy.deepcopy(rec['data']);bad['to']='AUDIT-MISSING';patch=root.parent/'dangling.json';dump(patch,{'rationale':'audit dangling reference','records':{'T-REL':{'expected_version':rec['version'],'data':bad}}});before=sha(st)
r=prun(c+'-dangling-reference',root,'update-state.py',['--root',root,'--expected-revision',s['metadata_revision'],'--patch',patch],True);row['dangling_reference']={**change_guard(r,st,before),'dangling_target_committed':load(st)['records']['T-REL']['data']['to']=='AUDIT-MISSING'}
for mode in ['invalid-version','dangling']:
 root=clone(c,'C','batch-'+mode);st=state_path(c,root);s=load(st);valid=copy.deepcopy(s['records']['T-CLAIM']['data']);valid['meaning']+=' [audit first operation]';bad=copy.deepcopy(s['records']['T-REL']['data']);bad['to']='AUDIT-MISSING'
 changes={'T-CLAIM':{'expected_version':s['records']['T-CLAIM']['version'],'data':valid},'T-REL':{'expected_version':-99 if mode=='invalid-version' else s['records']['T-REL']['version'],'data':bad}};patch=root.parent/'batch.json';dump(patch,{'rationale':'audit transaction later invalid item','records':changes});before=sha(st)
 r=prun(c+'-batch-'+mode,root,'update-state.py',['--root',root,'--expected-revision',s['metadata_revision'],'--patch',patch],True);row['batch_'+mode]={**change_guard(r,st,before),'valid_first_committed':load(st)['records']['T-CLAIM']['data']==valid}

# Guidance D custom ledger replacement: version/hash CAS and version checks are real,
# while referential integrity is tested separately rather than presumed.
c='P6';row=RESULT[c]
def p6update(label,root,candidate,old,expected_version=None,expected_sha=None):
 patch=root.parent/(label+'.json');dump(patch,candidate)
 return prun(label,root,'scripts/guarded_state_update.py',['--root',root,'--candidate',patch,'--expected-version',old['state_version'] if expected_version is None else expected_version,'--expected-sha256',sha(state_path(c,root)) if expected_sha is None else expected_sha,'--reason','independent audit probe'],True)
root=clone(c,'C','record-CAS');st=state_path(c,root);s=load(st);oldhash=sha(st);new=copy.deepcopy(s);new['state_version']+=1;rec=next(r for r in new['records'] if r['id']=='D-CLAIM');rec['text']+=' [audit legal revision]';rec['version']+=1
r=p6update(c+'-legal-update',root,new,s);before=sha(st);r2=p6update(c+'-stale-global-write',root,new,s,expected_sha=oldhash);current=load(st);new=copy.deepcopy(current);new['state_version']+=1;rec=next(r for r in new['records'] if r['id']=='D-CLAIM');rec['text']+=' [audit missing required record increment]';r3=p6update(c+'-stale-record-write',root,new,current)
row['stale_write']={'level':'global state_version + full-state SHA; record content/version increment validation','legal_update':summary(r),'stale_global_request':change_guard(r2,st,before),'stale_record_request':change_guard(r3,st,before)}
root=clone(c,'C','dangling');st=state_path(c,root);s=load(st);new=copy.deepcopy(s);new['state_version']+=1;rec=next(r for r in new['records'] if r['id']=='D-REL');rec['to_id']='AUDIT-MISSING';rec['version']+=1;before=sha(st)
r=p6update(c+'-dangling-reference',root,new,s);row['dangling_reference']={**change_guard(r,st,before),'dangling_target_committed':next(r for r in load(st)['records'] if r['id']=='D-REL')['to_id']=='AUDIT-MISSING'}
for mode in ['invalid-version','dangling']:
 root=clone(c,'C','batch-'+mode);st=state_path(c,root);s=load(st);new=copy.deepcopy(s);new['state_version']+=1;first=next(r for r in new['records'] if r['id']=='D-CLAIM');first['text']+=' [audit first operation]';first['version']+=1;last=next(r for r in new['records'] if r['id']=='D-REL');last['to_id']='AUDIT-MISSING';last['version']+=2 if mode=='invalid-version' else 1;before=sha(st)
 r=p6update(c+'-batch-'+mode,root,new,s);row['batch_'+mode]={**change_guard(r,st,before),'valid_first_committed':next(r for r in load(st)['records'] if r['id']=='D-CLAIM')['text']==first['text']}

# Baseline T offers a narrower but genuine expected-current-file-SHA restore guard.
c='P5';row=RESULT[c];root=clone(c,'C','file-CAS');target=root/'notes/parameters.json';old=sha(target);r=prun(c+'-legal-restore',root,'scripts/manage.py',['--root',root,'restore-initial','notes/parameters.json','--expected-current',old,'--write'],True);newhash=sha(target)
r2=prun(c+'-stale-file-write',root,'scripts/manage.py',['--root',root,'restore-initial','notes/parameters.json','--expected-current',old,'--write'],True)
row['stale_write']={'level':'current file SHA expected-current; restore-initial only, not logical record CAS','original_sha':old,'after_legal_restore_sha':newhash,'legal_update':summary(r),'stale_request':summary(r2),'newer_file_preserved':sha(target)==newhash,'logical_record_update_interface':'not-provided'}
r=prun(c+'-invalid-unpreserved-path',root,'scripts/manage.py',['--root',root,'restore-initial','AUDIT-MISSING','--expected-current','MISSING','--write'],True);row['invalid_restore_path']=summary(r)
row['dangling_reference']={'status':'not-provided/not-comparable','reason':'No logical record update interface. Exact-byte initial file restoration does not accept record links.'};row['batch_invalid_later_reference']={'status':'not-provided/not-comparable','reason':'No multi-file/record batch update API delivered.'}
RESULT['P2']['stale_write']={'status':'not-provided/not-comparable','reason':'Delivered status/verify_current are read-only; revisions done by explicit file workflow. No automated update API.'};RESULT['P2']['dangling_reference']={'status':'not-provided/not-comparable','reason':'No record-write API.'};RESULT['P2']['batch_invalid_later_reference']={'status':'not-provided/not-comparable','reason':'No batch-write API.'}

# Replay the controls' preserved pre-recompute bytes and the exact checkpoint saved
# in C. This is an audit data adapter, not a newly supplied checkpoint program.
for c,arch,cpfile in [
 ('P2','management/checkpoints/C-pre-recompute/tree',None),
 ('P3','.history/C-drift/files','.history/C-drift/checkpoint.json'),
 ('P5','.research/checkpoints/C-drift-before-recompute/files',None),
 ('P6','snapshots/stage-C-before-recompute','records/drift-checkpoint-C.json')]:
 source=S/'runs'/c/'C/sealed-project';root=A/c/'dirty-replay'/'project';shutil.copytree(source/arch,root)
 if c=='P6':
  # The saved drift archive predates creation of project_status.py; use the exact
  # sealed delivered script, without editing it, to read the preserved ledger.
  for name in ['project_status.py','guarded_state_update.py']:shutil.copy2(source/'scripts'/name,root/'scripts'/name)
 st=state_path(c,root);s=load(st)
 if cpfile:s['checkpoint']=load(source/cpfile)
 if c=='P3':s['metadata_revision']=s['checkpoint']['metadata_revision']
 if c=='P5':
  # C archived actual dirty files first, then saved checkpoint. Recover only that
  # exact checkpoint from the sealed intermediate stdout, without rebinding work.
  receipt=load(source/'.research/evidence/C/intermediate-status-execution.json');s['checkpoint']['material_sha256']={p:sha(root/p) for p in s['checkpoint']['material_sha256']}
 if c=='P6':s['state_version']=s['checkpoint']['state_version']
 dump(st,s);r=status(c,root,c+'-dirty-checkpoint-replay');RESULT[c]['dirty_checkpoint']={'automatic_checkpoint_interface':False,'adapter':'Replay preserved dirty archive plus exact saved checkpoint; P5 checkpoint fingerprints refreshed by audit adapter to reproduce saved intermediate stdout. Activity completion bindings not changed. P2 has separate checkpoint tree but no auto checkpoint API.','subsequent_status':summary(r),'result':payload(r)}

dump(A/'engineering.json',RESULT);dump(A/'engineering-receipts.json',m.RECEIPTS)
print(json.dumps({c:{k:v['exit_code'] for k,v in row.items() if isinstance(v,dict) and 'exit_code' in v} for c,row in RESULT.items()}))
