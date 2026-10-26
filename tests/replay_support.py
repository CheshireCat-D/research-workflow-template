"""Shared isolated project reconstruction for recorded evaluation artifacts."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


class ReplayHarness:
    def __init__(self,base,phase):
        self.base=Path(base)
        self.phase=phase

    def invoke(self,script,*arguments,expected=0):
        result=subprocess.run([sys.executable,'-B',str(script),*map(str,arguments)],
                              cwd=ROOT,text=True, encoding='utf-8',capture_output=True,timeout=30,
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

    def replay(self,case,suffix=''):
        project,manifest=self.assemble(case,suffix)
        runtime=project/'.agents/skills/_rw-runtime/tools/research.py'
        record_input=self.base/('record-input-'+case+suffix+'.json')
        for entry in manifest['records']:
            record_input.write_text(json.dumps(entry['record'],ensure_ascii=False),encoding='utf-8')
            args=['register','--root',project,'--kind',entry['kind'],'--file',record_input]
            if 'expected_version' in entry:
                args.extend(['--replace','--expected-version',entry['expected_version']])
            self.invoke(runtime,*args)
        args=['checkpoint','--root',project,'--next-action',manifest['cursor']['next_action']]
        if manifest['cursor']['activity_id']:args.extend(['--activity',manifest['cursor']['activity_id']])
        self.invoke(runtime,*args)
        return project,manifest,runtime
