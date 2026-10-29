"""Shared isolated project reconstruction for recorded evaluation artifacts."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def reviewed_resource(relative, expected_sha256, historical=None):
    """Bind an old task to its actual source; never relabel current guidance."""
    saved = (historical or {}).get(relative)
    if saved is None:
        history = json.loads((ROOT/'evals/current/guidance-history.json').read_text(encoding='utf-8'))
        candidate = history['resources'].get(relative)
        if candidate and candidate['sha256'] == expected_sha256:
            saved = candidate
    data = saved['source_text'].encode('utf-8') if saved else (ROOT/relative).read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    # Early legal snapshots store text only; their independent review supplies
    # the mandatory expected hash. Later snapshots also declare their own hash.
    if actual != expected_sha256 or (saved and actual != saved.get('sha256', expected_sha256)):
        raise AssertionError('Recorded resource identity differs: ' + relative)
    return data


class ReplayHarness:
    def __init__(self,base,phase):
        self.base=Path(base)
        self.phase=phase

    def invoke(self,script,*arguments,expected=0):
        result=subprocess.run([sys.executable,'-B',str(script),*map(str,arguments)],
                              cwd=ROOT,text=True, encoding='utf-8',capture_output=True,
                              timeout=60 if os.name == 'nt' else 30,
                              env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        if result.returncode!=expected:
            raise AssertionError(result.stdout+result.stderr)
        return json.loads(result.stdout)

    def assemble(self,case,suffix=''):
        recording=ROOT/'evals'/self.phase/'recordings'/case
        manifest=json.loads((recording/'recording.json').read_text(encoding='utf-8'))
        config=manifest['project_init'];project=self.base/(case+suffix)
        arguments=['init','--output',project,'--title',config['title'],'--interest',config['interest'],
                   '--mode',config['workflow_mode'],'--language',config['language'],'--entry',config['entry_activity']]
        for kind,flag in [('disciplines','--discipline'),('methods','--method')]:
            for value in config[kind]:arguments.extend([flag,value])
        self.invoke(ROOT/'tools/research.py',*arguments)
        self.invoke(ROOT/'tools/connect_skills.py','install','--root',project)
        for destination,source in manifest['case_files'].items():
            target=project/destination;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/'evals'/self.phase/'cases'/case/source,target)
        for relative in manifest['output_files']:
            if relative.split('/')[0] in {'.agents', '.research'}:
                raise AssertionError('Recorded research output must not overwrite generated project state')
            target=project/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(recording/'outputs'/relative,target)
        return project,manifest

    def register_records(self,project,runtime,records):
        """Use the real ordered batch CLI, preserving per-record history/bindings.

        These are final-state reconstruction fixtures, not concurrency tests.
        Individual registration, writer locking and concurrent processes remain
        exercised in test_core.py and test_skill_connection.py.
        """
        operations=[]
        for entry in records:
            operation={'kind':entry['kind'],'record':entry['record']}
            if 'expected_version' in entry:
                operation.update(replace=True,expected_version=entry['expected_version'])
            operations.append(operation)
        record_input=self.base/('record-input-'+project.name+'.json')
        record_input.write_text(json.dumps(operations,ensure_ascii=False),encoding='utf-8')
        return self.invoke(runtime,'register-batch','--root',project,'--file',record_input)

    def replay(self,case,suffix=''):
        project,manifest=self.assemble(case,suffix)
        runtime=project/'.agents/skills/_rw-runtime/tools/research.py'
        self.register_records(project,runtime,manifest['records'])
        args=['checkpoint','--root',project,'--next-action',manifest['cursor']['next_action']]
        if manifest['cursor']['activity_id']:args.extend(['--activity',manifest['cursor']['activity_id']])
        self.invoke(runtime,*args)
        return project,manifest,runtime
