#!/usr/bin/env python3
import csv,hashlib,json,pathlib,sys,platform
w=pathlib.Path(__file__).resolve().parent;root=pathlib.Path('STUDY_ROOT');i=root/'runs/D04/input';g=root/'guidance/rwt-package/research-workflow-template';arc=w/'stage1_archive'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
reads={}
def add(p,logical,access='full',version=None):
    item={'logical_name':logical,'sha256':sha(p),'access':access}
    if version:item['version']=version
    key=(logical,item['sha256'])
    if key not in reads or access=='full':reads[key]=item
for f in ('EXECUTOR.md','execution.template.json'):
    add(root/'runs/D04'/f,'input/data-b/'+f)
for f in ('TASK.md','INPUT_MANIFEST.json','ORIGINAL_README.txt','SOURCES.md','UCI_PAGE_EXCERPT.txt'):
    add(i/f,'input/data-b/'+f)
for f in ('skills/rw-workflow/SKILL.md','skills/rw-validation/SKILL.md','core/skill-bridge.md','core/protocol.md','profiles/methods/computational.md','profiles/methods/empirical-quantitative.md'):
    add(g/f,'guidance/rwt/'+f)
add(root/'runs/D02/input/TASK.md','prior-input/data-a/TASK.md')
prior=json.loads((arc/'artifact_manifest.json').read_text())
for f in prior:
    if f in ('report.md','handoff.md','RUN.md','execution.json'):
        pp=arc/f
    else:pp=w/f
    add(pp,'workspace/'+f,'digest-only','stage1')
for f in ('report.md','handoff.md','RUN.md'):
    add(arc/f,'workspace/'+f,'full','stage1')
for f in ('analyze.py','results/model.json','results/results.json','verification.json','reproduction_check.json','artifact_manifest.json'):
    pp=arc/f if f=='artifact_manifest.json' else w/f
    add(pp,'workspace/'+f,'full','stage1')
prov=json.loads((w/'results_2012/provenance.json').read_text())
for ent in prov['reads']:
    ent=dict(ent);logical=ent['logical_name']
    if logical=='input/INPUT_MANIFEST.json':logical='input/data-b/INPUT_MANIFEST.json'
    ent['logical_name']=logical;key=(logical,ent['sha256'])
    if key not in reads or ent['access']=='full':reads[key]=ent
for f in ('update2012.py','verify2012.py','write_stage2.py','finalize_stage2.py','report.md','handoff.md','RUN.md','results_2012/results.json','results_2012/audit.json','results_2012/annual_summary.json','results_2012/model_recovery.json','results_2012/provenance.json','results_2012/independent_verification.json','results_2012/reproduction_check.json'):
    add(w/f,'workspace/'+f)
for f in ('results_2012/predictions.csv','results_2012/daily_errors.csv','results_2012/bootstrap_7.csv','results_2012/bootstrap_28.csv'):
    add(w/f,'workspace/'+f,'full' if f.endswith('predictions.csv') or 'bootstrap_' in f else 'digest-only')
add(sys.executable,'common/python','digest-only')
base=pathlib.Path(sys.base_prefix)
for name,mod in sorted(sys.modules.items()):
    path=getattr(mod,'__file__',None)
    if not path:continue
    pp=pathlib.Path(path)
    try:rel=pp.relative_to(base)
    except ValueError:continue
    if pp.is_file():add(pp,'common/'+rel.as_posix(),'runtime-import')
with (i/'data/hour_2012.csv').open(newline='') as f:source=list(csv.DictReader(f))
with (w/'results_2012/predictions.csv').open(newline='') as f:pred=list(csv.DictReader(f))
assert len(source)==len(pred) and all((x['dteday'],int(x['hr']),int(x['workingday']),int(x['cnt']))==(y['dteday'],int(y['hr']),int(y['workingday']),int(y['cnt'])) for x,y in zip(source,pred))
assert sha(w/'results/model.json')=='f8a758c6c73cf7e0cfcfa0936b594afb8f23b1260610ecae15929f601dc8e5d4'
for f in ('predictions.csv','daily_errors.csv','bootstrap_7.csv','bootstrap_28.csv','results.json'):
    assert sha(w/'results'/f)==sha(w/'results_2012/recovery_2011'/f)
report=(w/'report.md').read_text();assert len(report)<=12000
qa={'report_unicode_characters':len(report),'all_2012_source_keys_and_targets_match':True,'frozen_model_unchanged':True,'2011_holdout_five_files_byte_identical':True,'all_first_2012_results_preserved':True,'independent_verification':json.loads((w/'results_2012/independent_verification.json').read_text()),'exact_reproduction':json.loads((w/'results_2012/reproduction_check.json').read_text())}
(w/'results_2012/delivery_qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
record=json.loads((root/'runs/D04/execution.template.json').read_text())
record['status']='executed';record['tool_calls']=9;record['network_calls']=0;record['violations']=[];record['reads']=list(reads.values());record['duration_seconds']=None
record['duration_note']='Wall clock for whole agent turn unavailable; individual analysis elapsed_seconds recorded in results_2012/provenance.json.'
record['scope']='instruction-only; no OS audit';record['failure']=None
pyp=str(root/'env/bin/python')+' -I -B '
run=pyp+str(w/'update2012.py')+' --input-dir '+str(i)+' --prior-input '+str(root/'runs/D02/input')+' --model '+str(w/'results/model.json')+' --prior-results '+str(w/'results/results.json')+' --original-code '+str(w/'analyze.py')+' --output-dir '
record['commands']=[
 {'tool_call':1,'command':'cat runs/D04/EXECUTOR.md, execution.template.json, input/TASK.md and six specified guidance files (absolute allowed paths)','exit_code':0},
 {'tool_call':2,'command':'rg --files '+str(w)+' '+str(i)+' '+str(root/'runs/D02/input'),'exit_code':0},
 {'tool_call':3,'command':'cat allowed prior code, handoff, report, RUN, model, results, verification; new input manifest and three source documents; prior TASK.md','exit_code':0,'note':'Tool presentation truncated aggregate text; code/task/source contents available; full prior report read again in call 4.'},
 {'tool_call':4,'command':'cat '+str(w/'RUN.md')+' '+str(w/'report.md')+' '+str(w/'reproduction_check.json')+' '+str(w/'artifact_manifest.json'),'exit_code':0},
 {'tool_call':5,'command':'write update2012.py; '+pyp+'- (archive seven prior delivery files and verify 24 original manifest hashes)','exit_code':0},
 {'tool_call':5,'command':run+str(w/'results_2012'),'exit_code':0,'first_scientific_run':True},
 {'tool_call':6,'command':'write verify2012.py; '+pyp+str(w/'verify2012.py')+' --output-dir '+str(w/'results_2012')+' --model '+str(w/'results/model.json'),'exit_code':0},
 {'tool_call':6,'command':run+str(w/'reproduction_2012')+' > '+str(w/'reproduction_2012.log'),'exit_code':0},
 {'tool_call':6,'command':pyp+'- (compare nine scientific output hashes; print incomplete-date audit)','exit_code':0},
 {'tool_call':7,'command':'write write_stage2.py; '+pyp+str(w/'write_stage2.py'),'exit_code':0},
 {'tool_call':8,'command':'write finalize_stage2.py; '+pyp+str(w/'finalize_stage2.py'),'exit_code':0},
 {'tool_call':9,'command':pyp+'- (final readback: requested fields, output files, source/model/code hashes, report limit and execution log; save final artifact manifest)','exit_code':None,'status':'planned final readback; updated to executed within that call'}]
record['effective']={'model':None,'reasoning_effort':None,'temperature':None,'seed':None,'output_token_limit':None}
record['analysis_configuration']={'bootstrap_seed':20261029,'bootstrap_B':2000,'block_lengths_days':[7,28],'python':sys.version,'platform':platform.platform(),'model_or_effort_override_used':False,'fit_called':False}
(w/'execution.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':record['status'],'recorded_reads':len(reads),'report_characters':len(report),'source_target_match':True,'original_model_unchanged':True},ensure_ascii=False))
