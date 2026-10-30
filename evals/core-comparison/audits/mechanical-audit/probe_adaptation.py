#!/usr/bin/env python3
import importlib.util
from pathlib import Path
sp=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
globals().update({k:getattr(m,k) for k in ['S','A','PY','PLAN','load','sha','dump','snap','clone','run','prun','cli','payload','identity']})
import copy
eng=load(A/'engineering.json');adapt={}
def clean(r):return {k:v for k,v in r.items() if k not in ['stdout','stderr']}
for c in ['P1','P4']:
 source=S/'runs'/c/'C/sealed-project';s=load(source/'records/registry.json');original=copy.deepcopy(next(iter(s['records']['relations'].values()))['data']);candidate=copy.deepcopy(original);candidate['id']='AUDIT-DANGLING-STATEMENT';candidate['statement_id']='AUDIT-MISSING'
 root=clone(c,'C','statement-dangling');st=root/'records/registry.json';patch=root.parent/'dangling-statement.json';dump(patch,candidate);before=sha(st)
 r=cli(c+'-statement-dangling',root,['register','--root',root,'--kind','relation','--file',patch],True)
 after=load(st);eng[c]['statement_target_dangling']={**clean(r),'authority_sha_before':before,'authority_sha_after':sha(st),'authority_preserved':before==sha(st)}
 valid=copy.deepcopy(next(iter(s['records']['sources'].values()))['data']);valid['id']='AUDIT-VALID-SOURCE'
 root=clone(c,'C','valid-prefix-positive');patch=root.parent/'valid-source.json';dump(patch,valid);r=cli(c+'-valid-prefix-positive',root,['register','--root',root,'--kind','source','--file',patch],True);eng[c]['batch_prefix_positive_control']={**clean(r),'actual_saved':load(root/'records/registry.json')['records']['sources'].get(valid['id'],{}).get('data')==valid}
 root=clone(c,'C','batch-statement-dangling');st=root/'records/registry.json';patch=root.parent/'batch.json';dump(patch,[{'kind':'source','record':valid},{'kind':'relation','record':candidate}]);before=sha(st)
 r=cli(c+'-batch-statement-dangling',root,['register-batch','--root',root,'--file',patch],True);after=load(st);eng[c]['batch_statement_target_dangling']={**clean(r),'authority_sha_before':before,'authority_sha_after':sha(st),'authority_preserved':before==sha(st),'valid_prefix_absent':valid['id'] not in after['records']['sources']}
 adapt[c]={'original_relation':original,'candidate_relation':candidate,'existing_target_field':'statement_id','unknown_id':'AUDIT-MISSING','unknown_id_absent_before':not any('AUDIT-MISSING' in col for col in s['records'].values()),'standalone_write_saved_relation':load(A/c/'statement-dangling/project/records/registry.json')['records']['relations'].get(candidate['id']),'batch_write_saved_relation':after['records']['relations'].get(candidate['id']),'batch_first_operation':{'kind':'source','record':valid},'original_evidence_endpoint_probe_retained':str(A/'receipts'/f'{c}-dangling-reference.json')}

c='P3';s=load(S/'runs'/c/'C/sealed-project/research/state.json');original=s['records']['T-REL']['data'];candidate=load(A/c/'dangling/dangling.json')['records']['T-REL']['data'];post=load(A/c/'dangling/project/research/state.json')['records']['T-REL']['data'];batch=load(A/c/'batch-dangling/project/research/state.json')['records']['T-REL']['data'];valid=load(A/c/'batch-dangling/batch.json')['records']['T-CLAIM']
adapt[c]={'original_relation':original,'candidate_relation':candidate,'existing_target_field':'to','unknown_id':'AUDIT-MISSING','unknown_id_absent_before':'AUDIT-MISSING' not in s['records'],'standalone_write_saved_relation':post,'batch_write_saved_relation':batch,'batch_first_operation':valid}
root=clone(c,'C','valid-prefix-positive');patch=root.parent/'valid.json';dump(patch,{'rationale':'audit prefix positive control','records':{'T-CLAIM':valid}});r=prun(c+'-valid-prefix-positive',root,'update-state.py',['--root',root,'--expected-revision',s['metadata_revision'],'--patch',patch],True);eng[c]['batch_prefix_positive_control']={**clean(r),'actual_saved':load(root/'research/state.json')['records']['T-CLAIM']['data']==valid['data']}

c='P6';s=load(S/'runs'/c/'C/sealed-project/records/state.json');original=next(r for r in s['records'] if r['id']=='D-REL');candidate=next(r for r in load(A/c/'dangling/P6-dangling-reference.json')['records'] if r['id']=='D-REL');post=next(r for r in load(A/c/'dangling/project/records/state.json')['records'] if r['id']=='D-REL');batch=next(r for r in load(A/c/'batch-dangling/project/records/state.json')['records'] if r['id']=='D-REL');valid=next(r for r in load(A/c/'batch-dangling/P6-batch-dangling.json')['records'] if r['id']=='D-CLAIM')
adapt[c]={'original_relation':original,'candidate_relation':candidate,'existing_target_field':'to_id','unknown_id':'AUDIT-MISSING','unknown_id_absent_before':'AUDIT-MISSING' not in {r['id'] for r in s['records']},'standalone_write_saved_relation':post,'batch_write_saved_relation':batch,'batch_first_operation':valid}
root=clone(c,'C','valid-prefix-positive');new=copy.deepcopy(s);new['state_version']+=1;new['records']=[valid if r['id']=='D-CLAIM' else r for r in new['records']];patch=root.parent/'valid.json';dump(patch,new);r=prun(c+'-valid-prefix-positive',root,'scripts/guarded_state_update.py',['--root',root,'--candidate',patch,'--expected-version',s['state_version'],'--expected-sha256',sha(root/'records/state.json'),'--reason','audit prefix positive control'],True);eng[c]['batch_prefix_positive_control']={**clean(r),'actual_saved':next(r for r in load(root/'records/state.json')['records'] if r['id']=='D-CLAIM')==valid}

# Attach actual authority SHA before/after to existing standalone/batch receipts.
for c,rel in [('P3','research/state.json'),('P6','records/state.json')]:
 for field,receipt in [('dangling_reference',c+'-dangling-reference'),('batch_dangling',c+'-batch-dangling')]:
  b=load(A/'receipts'/f'{receipt}.before.json');a=load(A/'receipts'/f'{receipt}.after.json');eng[c][field]['authority_sha_before']=b['files'][rel]['sha256'];eng[c][field]['authority_sha_after']=a['files'][rel]['sha256']
dump(A/'engineering.json',eng);dump(A/'relation-adaptations.json',adapt);dump(A/'adaptation-receipts.json',m.RECEIPTS)
print({c:{'field':v['existing_target_field'],'unknown_absent':v['unknown_id_absent_before'],'positive_prefix_exit':eng[c]['batch_prefix_positive_control']['exit_code']} for c,v in adapt.items()})
