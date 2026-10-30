import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

BASE = Path('STUDY_ROOT')
ROOT = BASE / 'numeric-replays'
PYTHON = BASE / 'env/bin/python'
PLAN = json.loads((BASE / 'numeric-audit-plan.json').read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def run(item):
    trial = item['trial_id']
    root = ROOT / trial
    root.mkdir(exist_ok=False)
    source = Path(item['sealed_workspace'])
    initial = manifest(source)
    workspace = root / 'workspace-copy'
    shutil.copytree(source, workspace)
    input_dir = root / 'input-copy'
    shutil.copytree(item['input_dir'], input_dir)
    assert initial == manifest(workspace)
    output = root / 'output'
    model = workspace / ('model.json' if trial in ('D01','D06') else 'results/model.json')
    entry = {'D01':'analysis.py', 'D02':'analyze.py', 'D03':'analyze.py',
             'D04':'update2012.py', 'D05':'update_2012.py', 'D06':'stage_b.py'}[trial]
    args = []
    if trial == 'D01':
        args = ['--input-dir', str(input_dir), '--output-dir', str(output)]
    elif trial == 'D02':
        args = ['train','--input-dir',str(input_dir),'--output-dir',str(output)]
    elif trial == 'D03':
        args = ['fit','--input-dir',str(input_dir),'--output-dir',str(output)]
    elif trial == 'D04':
        prior_input = root / 'prior-input-copy'
        shutil.copytree(BASE/'runs'/item['predecessor']/'input', prior_input)
        args = ['--input-dir', str(input_dir), '--prior-input', str(prior_input),
                '--model', str(model), '--prior-results', str(workspace/'results/results.json'),
                '--original-code', str(workspace/'analyze.py'), '--output-dir', str(output)]
    elif trial == 'D05':
        args = ['--input-dir',str(input_dir),'--output-dir',str(output),'--model',str(model),
                '--prior-results',str(workspace/'results')]
    elif trial == 'D06':
        args = ['--input-dir',str(input_dir),'--prior-dir',str(workspace/'stage_a_snapshot'),
                '--model',str(model),'--output-dir',str(output)]
    argv = [str(PYTHON), '-I', '-B', str(workspace/entry), *args]
    before = {'sealed':initial, 'input':manifest(Path(item['input_dir'])),
              'copied_input':manifest(input_dir), 'copied_workspace':manifest(workspace)}
    record = {'trial_id':trial,'task_id':item['task_id'],'predecessor':item['predecessor'],
              'source':str(source),'cwd':str(workspace),'entry_script':entry,'argv':argv,
              'entry_sha256':sha(workspace/entry), 'python_executable':str(PYTHON),
              'python_version':subprocess.check_output([str(PYTHON),'-I','-B','--version'],text=True).strip(),
              'inputs_sha256':before['copied_input'], 'source_manifest_before':initial,
              'code_sha256':{str(p.relative_to(workspace)):sha(p) for p in workspace.rglob('*.py')},
              'output_dir':str(output),'no_code_or_model_changes':True}
    save(root/'execution-record.json',record)
    start=time.monotonic()
    with (root/'stdout.log').open('w') as stdout, (root/'stderr.log').open('w') as stderr:
        try:
            process = subprocess.run(argv,cwd=workspace,stdout=stdout,stderr=stderr,
                                     timeout=300,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
            record['exit_code']=process.returncode
        except subprocess.TimeoutExpired:
            record['exit_code']=None
            record['failure']='timeout after 300 seconds; no code repair attempted'
    record['elapsed_seconds']=time.monotonic()-start
    record['source_unchanged']=initial==manifest(source)
    record['source_input_unchanged']=before['input']==manifest(Path(item['input_dir']))
    record['copied_workspace_unchanged']=before['copied_workspace']==manifest(workspace)
    record['copied_input_unchanged']=before['copied_input']==manifest(input_dir)
    record['output_sha256']=manifest(output) if output.exists() else {}
    record['stdout_sha256']=sha(root/'stdout.log')
    record['stderr_sha256']=sha(root/'stderr.log')
    save(root/'execution-record.json',record)
    return {k:record[k] for k in ('trial_id','exit_code','elapsed_seconds','source_unchanged',
            'source_input_unchanged','copied_workspace_unchanged','copied_input_unchanged')}

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        results=list(executor.map(run,PLAN))
    save(ROOT/'replay-execution-summary.json',results)
    print(json.dumps(results,ensure_ascii=False,indent=2))
