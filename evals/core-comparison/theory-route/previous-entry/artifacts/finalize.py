"""Reproducibility record for this isolated review; no external access."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

BASE = Path('STUDY_ROOT/route-runs/a')
WORK = BASE / 'workspace'
GUIDE = Path('GUIDANCE_ROOT')
PYTHON = 'EVAL_PYTHON'

commands = [
    "cat STUDY_ROOT/route-runs/a/REQUEST.md",
    "cat INPUT_DIR/TASK.md GUIDANCE_ROOT/skills/rw-review/SKILL.md",
    "ls -la INPUT_DIR WORKSPACE\ncat GUIDANCE_ROOT/core/skill-bridge.md GUIDANCE_ROOT/core/protocol.md GUIDANCE_ROOT/skills/rw-validation/SKILL.md GUIDANCE_ROOT/skills/rw-literature/SKILL.md",
    "cat INPUT_DIR/draft.tex INPUT_DIR/source-manifest.json GUIDANCE_ROOT/profiles/methods/formal-theory.md\nls -la INPUT_DIR/sources",
    "rg -n 'Definition 1|Theorem 1|normal mixture|Normal mixture|empirical Bernstein|Empirical Bernstein|rho|ρ|optimal|optimiz|ψE|psi_E' INPUT_DIR/sources/howard2020-arxiv-v7.txt INPUT_DIR/sources/howard2021-arxiv-v9.txt",
    r'''EVAL_PYTHON -I -B - <<'PY'
from pathlib import Path
root=Path('INPUT_DIR/sources')
queries={'howard2020-arxiv-v7.txt':['Definition 1.','Theorem 1. Fix'], 'howard2021-arxiv-v9.txt':['Definition 1.','Theorem 4','Proposition 5','Proposition 3','Proposition 4','Empirical-Bernstein','empirical-Bernstein','optimize the squared boundary','λYt−']}
for name,terms in queries.items():
 pages=(root/name).read_text().split('\f')
 print(name,'segments',len(pages))
 for i,p in enumerate(pages,1):
  hits=[s for s in terms if s in p]
  if hits: print('PDF page',i, 'hits',hits)
PY''',
    r'''EVAL_PYTHON -I -B - <<'PY'
import importlib.util
print({m:bool(importlib.util.find_spec(m)) for m in ['pypdf','fitz','pdfplumber']})
from pathlib import Path
p=Path('INPUT_DIR/sources/howard2021-arxiv-v9.txt')
print(p.read_text()[:1800])
PY''',
    r'''EVAL_PYTHON -I -B - <<'PY'
from pathlib import Path
import re
root=Path('INPUT_DIR/sources')
queries={'howard2020-arxiv-v7.txt':['Deﬁnition 1.','Theorem 1. Fix'], 'howard2021-arxiv-v9.txt':['Deﬁnition 1.','Theorem 4','Proposition 5','Proposition 3','Proposition 4','optimize the squared boundary','λYt−']}
for name,terms in queries.items():
 text=(root/name).read_text(); parts=re.split(r'===== PDF PAGE (\d+) =====',text)
 print('\nSOURCE',name)
 for j in range(1,len(parts),2):
  n,p=int(parts[j]),parts[j+1]
  if any(s in p for s in terms): print('PAGE',n,':\n',p)
PY''',
    r'''EVAL_PYTHON -I -B - <<'PY'
from pathlib import Path
import re
root=Path('INPUT_DIR/sources')
for name in ['howard2020-arxiv-v7.txt','howard2021-arxiv-v9.txt']:
 parts=re.split(r'===== PDF PAGE (\d+) =====',(root/name).read_text())
 print(name)
 for j in range(1,len(parts),2):
  n,p=int(parts[j]),parts[j+1];norm=p.replace('ﬁ','fi').replace('ﬀ','ff')
  terms=['Definition 1','Theorem 4.','Proposition 5 (','Proposition 3.','Lemma 2 (','ψE,c(λ)','ψE,c (λ)']
  hits=[s for s in terms if s in norm]
  if hits: print(n,hits)
 for j in range(1,len(parts),2):
  n,p=int(parts[j]),parts[j+1]
  selected=([10] if '2020' in name else [12,15,27,28])
  if n in selected:print('\nPAGE',n,'\n',p)
PY''',
    r'''EVAL_PYTHON -I -B - <<'PY'
from pathlib import Path
import re
root=Path('INPUT_DIR/sources')
for name,selected in [('howard2020-arxiv-v7.txt',[9,14]),('howard2021-arxiv-v9.txt',[6,9,14,30])]:
 parts=re.split(r'===== PDF PAGE (\d+) =====',(root/name).read_text())
 for j in range(1,len(parts),2):
  if int(parts[j]) in selected:print('\nSOURCE',name,'PDF PAGE',parts[j],'\n',parts[j+1])
PY''',
    r'''EVAL_PYTHON -I -B - <<'PY'
from pathlib import Path
from pypdf import PdfReader
import re,hashlib,math,json
base=Path('INPUT_DIR')
manifest=json.loads((base/'source-manifest.json').read_text())
for sid,name,pages in [('S1','howard2020-arxiv-v7',[9,10,12]),('S2','howard2021-arxiv-v9',[4,5,6,9,12,14,28,30,35,37])]:
 pdf=base/'sources'/f'{name}.pdf'; txt=base/'sources'/f'{name}.txt'; r=PdfReader(pdf)
 source=next(s for s in manifest['sources'] if s['source_id']==sid)
 parts=re.split(r'===== PDF PAGE (\d+) =====',txt.read_text()); mapped={int(parts[j]):parts[j+1] for j in range(1,len(parts),2)}
 norm=lambda s:''.join(s.split())
 print(json.dumps({'source':sid,'pages':len(r.pages),'sha256_matches_manifest':hashlib.sha256(pdf.read_bytes()).hexdigest()==source['pdf_sha256'],'verified_pdf_vs_text':[{'pdf_page':n,'normalized_text_equal':norm(r.pages[n-1].extract_text())==norm(mapped[n])} for n in pages]},ensure_ascii=False))
print('B threshold squared = log(800)/2:',math.log(800)/2,'threshold:',math.sqrt(math.log(800)/2),'event probability:',.9**20,'integer strict comparison:',20*9**20>10**20)
PY''',
]


def identity(name, path, category):
    data = path.read_bytes()
    return {'logical_name': name, 'path': str(path), 'category': category,
            'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


files = [('request', BASE / 'REQUEST.md', 'request')]
for item in ['TASK.md', 'draft.tex', 'source-manifest.json']:
    files.append((item, BASE / 'input' / item, 'input'))
for item in ['howard2020-arxiv-v7.pdf', 'howard2020-arxiv-v7.txt',
             'howard2021-arxiv-v9.pdf', 'howard2021-arxiv-v9.txt']:
    files.append((item, BASE / 'input' / 'sources' / item, 'input'))
for item in ['skills/rw-review/SKILL.md', 'core/skill-bridge.md', 'core/protocol.md',
             'skills/rw-validation/SKILL.md', 'skills/rw-literature/SKILL.md',
             'profiles/methods/formal-theory.md']:
    files.append((item, GUIDE / item, 'guidance'))
inputs = [identity(*item) for item in files]

report = (WORK / 'report.md').read_text()
(WORK / 'audit.md').write_text(report)
check_command = [PYTHON, '-I', '-B', str(WORK / 'checks.py')]
completed = subprocess.run(check_command, capture_output=True, text=True, check=False)
if completed.returncode != 0:
    results = {'execution_error': completed.stderr, 'exit_code': completed.returncode}
else:
    results = json.loads(completed.stdout)
(WORK / 'checks-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')

calls = [{'outer_call_index': i, 'tool': 'functions.exec', 'nested_tool': 'exec_command',
          'command': command, 'exit_code': 0} for i, command in enumerate(commands, 1)]
calls.extend([
    {'outer_call_index': 12, 'tool': 'functions.exec', 'nested_tool': 'apply_patch',
     'command': None, 'action': 'Add report.md and checks.py inside workspace',
     'observed_result': '{}; files subsequently read successfully'},
    {'outer_call_index': 13, 'tool': 'functions.exec', 'nested_tool': 'apply_patch',
     'command': None, 'action': 'Add finalize.py inside workspace',
     'observed_result': '{}; script subsequently invoked'},
    {'outer_call_index': 14, 'tool': 'functions.exec', 'nested_tool': 'exec_command',
     'command': PYTHON + ' -I -B ' + str(WORK / 'finalize.py'),
     'exit_code': None, 'result_status': 'finalize script reached execution-record write; outer shell exit is reported by host tool'},
])

manifest = json.loads((BASE / 'input' / 'source-manifest.json').read_text())
source_access = []
for sid, stem, pages in [('S1', 'howard2020-arxiv-v7', [9, 10, 12]),
                        ('S2', 'howard2021-arxiv-v9', [4, 5, 6, 9, 12, 14, 28, 30, 35, 37])]:
    meta = next(s for s in manifest['sources'] if s['source_id'] == sid)
    pdf_id = next(i for i in inputs if i['logical_name'] == stem + '.pdf')
    source_access.append({
        'source_id': sid, 'fixed_arxiv_id': meta['fixed_arxiv_id'],
        'title': meta['title'], 'authors': meta['authors'],
        'doi': meta['doi'], 'pdf_url': meta['pdf_url'],
        'pdf_pages': meta['pdf_pages'], 'content_access': 'partial: relevant original passages',
        'pdf_vs_cache_verified_page_numbers': pages,
        'all_selected_normalized_pdf_text_comparisons_equal': True,
        'sha256_matches_manifest': pdf_id['sha256'] == meta['pdf_sha256'],
        'full_text_file_loaded_in_memory': True,
        'full_article_claims_not_all_audited': True,
        'page_convention': 'one-based fixed-author-version PDF page index',
    })

artifacts = [identity(item, WORK / item, 'output') for item in
             ['report.md', 'audit.md', 'checks.py', 'checks-results.json', 'finalize.py']]
record = {
    'task_id': 'T-CS-01', 'actor': 'AI assistant',
    'model': None, 'parameters': None, 'tokens': None,
    'duration_seconds': None, 'start_time': None, 'end_time': None,
    'runtime': {'executable': PYTHON, 'python_version': sys.version,
                'isolated_flag': '-I', 'bytecode_disabled_flag': '-B',
                'installation_performed': False},
    'inputs_and_guidance_read': inputs,
    'source_access': source_access,
    'tool_calls': calls,
    'outer_tool_call_count': len(calls), 'outer_tool_call_limit': 18,
    'nested_subprocess_commands': [
        {'command_argv': check_command, 'exit_code': completed.returncode,
         'stdout_saved_as': 'checks-results.json', 'stderr': completed.stderr}],
    'failures': [],
    'recoverable_execution_issues': [
        {'calls': [5, 8], 'issue': 'Tool output was truncated',
         'resolution': 'Targeted original-page reads in calls 9 and 10 recovered passages needed for the report'},
        {'calls': [6], 'issue': 'Initial form-feed delimiter assumption found one text segment rather than PDF pages',
         'resolution': 'Call 7 identified explicit PDF PAGE markers; subsequent parsing and direct PDF comparison used those markers'},
    ],
    'violations': [],
    'boundaries': {'network_used': False, 'other_agents_called': False,
                   'personal_skills_or_memory_read': False,
                   'other_groups_or_scoring_keys_read': False,
                   'input_modified': False, 'writes_only_in_designated_workspace': True,
                   'source_full_text_redistributed_in_output': False},
    'report_unicode_characters': len(report),
    'report_soft_character_limit': 12000,
    'report_soft_character_limit_exceeded': len(report) > 12000,
    'requested_prose_length_note': 'TASK suggests 1500-3000 Chinese characters excluding formulas and table; detailed proof obligations were prioritized. Main report remains within 12000 Unicode-character soft limit if reported count permits.',
    'scientific_assessment': {
        'A': 'valid under stated SG and standard finite-valued measurability conditions',
        'B': 'false; finite-time analytic Bernoulli counterexample',
        'C': 'false; optimized envelope has simultaneous coverage zero in an iid Bernoulli(1/2) example by the supplied LIL',
        'D': 'false; contradicted by original source conditions and existing constructions',
        'E': 'valid by event inclusion; no finite expectation assumption',
        'basis': 'Manual mathematical arguments and original-source comparison',
        'formal_verification': 'not performed',
        'numeric_checks_are_not_proofs': True,
        'global_novelty_assessed': False,
    },
    'artifacts': artifacts,
    'unfinished_items': [],
}
if completed.returncode != 0:
    record['failures'].append({'command_argv': check_command, 'exit_code': completed.returncode,
                               'stderr': completed.stderr})
    record['unfinished_items'].append('Numerical checks failed; see stderr')
(WORK / 'execution.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
loaded = json.loads((WORK / 'execution.json').read_text())
print(json.dumps({'report_characters': len(report), 'outer_tool_calls': len(calls),
                  'input_and_guidance_files': len(inputs),
                  'checks_exit_code': completed.returncode,
                  'record_reloaded': loaded['task_id'] == 'T-CS-01',
                  'report_and_audit_identical': (WORK / 'report.md').read_bytes() == (WORK / 'audit.md').read_bytes(),
                  'outputs': [str(WORK / item) for item in ['report.md', 'audit.md', 'execution.json', 'checks.py', 'checks-results.json']]}, ensure_ascii=False, indent=2))
