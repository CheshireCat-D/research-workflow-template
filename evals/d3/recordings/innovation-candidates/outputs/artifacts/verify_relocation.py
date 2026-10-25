"""Clone just code/config/inputs to a temporary directory and compare numeric rows."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
original=json.loads(Path('artifacts/results.json').read_text())
with tempfile.TemporaryDirectory(prefix='rw-relocated-') as directory:
    root=Path(directory)
    shutil.copytree('inputs',root/'inputs')
    (root/'artifacts').mkdir()
    for name in ['run.py','config.json']:
        shutil.copy2(Path('artifacts')/name,root/'artifacts'/name)
    process=subprocess.run([sys.executable,'artifacts/run.py'],cwd=root,capture_output=True,text=True,timeout=10)
    if process.returncode:
        raise RuntimeError(process.stderr)
    rerun=json.loads((root/'artifacts/results.json').read_text())
    assert original['rows']==rerun['rows']
    report={'exit_status':process.returncode,'numeric_rows_identical':True,'rows':len(rerun['rows']),'relocated_elapsed_seconds':rerun['elapsed_seconds'],'subprocess_stdout':process.stdout,'subprocess_stderr':process.stderr,'clone_scope':['inputs/','artifacts/run.py','artifacts/config.json'],'temporary_clone_removed':True,'comparison_excludes':['elapsed_seconds','platform metadata']}
Path('checks/relocation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
