from pathlib import Path
import json, hashlib, shutil, zipfile, sys, datetime, os
from decimal import Decimal
B=Path('STUDY_ROOT');R=Path('REPOSITORY_ROOT');E=R/'evals/core-comparison';D=B/'design';PYTHON='EVAL_PYTHON'
PLAN=[{'chain_id':p,'case_id':c,'arm':a} for p,c,a in [('P1','T','core'),('P2','D','baseline'),('P3','T','guidance'),('P4','D','core'),('P5','T','baseline'),('P6','D','guidance')]]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def norm(s):
 for a,b in [('KEY_AUDIT_WORK','KEY_AUDIT_WORK'),(str(B),'STUDY_ROOT'),(str(R),'REPOSITORY_ROOT'),(PYTHON,'EVAL_PYTHON'),('PRIOR_STUDY_CACHE','PRIOR_STUDY_CACHE'),('MATERIAL_CHECK_CACHE','MATERIAL_CHECK_CACHE')]:s=s.replace(a,b)
 return s

def strict_parameters(text):
 def pairs(items):
  out={}
  for key,value in items:
   if key in out:raise ValueError('Duplicate JSON key')
   out[key]=value
  return out
 def bad(value):raise ValueError('Nonfinite JSON number')
 return json.loads(text,object_pairs_hook=pairs,parse_int=Decimal,parse_float=Decimal,parse_constant=bad)

def same_parameters(a,b):
 if type(a) is not type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys() and all(same_parameters(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(same_parameters(x,y) for x,y in zip(a,b))
 return a==b

def freeze():
 if (B/'freeze.json').exists():raise RuntimeError('Already frozen')
 assert (B/'core-key-audit.json').exists(),'independent pre-execution audit required'
 E.mkdir(parents=True,exist_ok=True)
 (E/'orchestration').mkdir(exist_ok=True)
 (E/'orchestration/prepare.py').write_text(norm(Path(__file__).read_text()))
 identities={}
 for f in sorted(D.rglob('*')):
  if not f.is_file():continue
  rel=f.relative_to(D).as_posix();identities[rel]={'sha256':sha(f),'bytes':f.stat().st_size}
  if f.suffix in {'.pdf','.csv'} and '/project_payload/' in rel and ('/data/' in rel or '/sources/' in rel):continue
  if f.name=='build_materials.py':continue
  target=E/'materials'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(norm(f.read_text()))
 dump(E/'input-identities.json',{'scope':'Original private material byte identities; raw source PDF/CSV not redistributed. Supplied creator payloads are frozen before first lifecycle execution.','files':identities})
 shutil.copyfile(D/'shared/rubric.json',E/'rubric.json')
 for ext in ['json','md']:
  p=E/'audits'/f'key-audit.{ext}';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(norm((B/f'core-key-audit.{ext}').read_text()))
 protocol='''# 项目核心能力对照：执行前协议\n\n两项真实材料项目（Howard固定版本论文、UCI 2011切片及既有冻结模型），三臂各一条四阶段链，共6条链、24个全新上下文。生命周期事件和工作笔记由本次构造，不是来源作者的错误或真实远端更新。A建档，B统一上游参数变化后的只读恢复，C先保存漂移断点再实际复核修订，D新目录且旧工具/缓存路径不可达的只读恢复。全部首次交付保留，不为不利结果改题、补台账或只留最佳一次。\n\n三臂：强文件基线（共同研究协议，不读额外技能正文）；RWT指导但不用核心；RWT指导并实际启用init+connect/register/checkpoint以及后续查询。前两臂可自写指纹、版本、依赖、恢复与冲突保护脚本。所有臂拥有相同材料、约束和通用义务，不按某产品JSON、术语、命令或文件数加科研分。指导组/核心组读同一组rw-workflow、bridge、protocol，其他资源按当前允许范围按需读取。核心组必须实际启用工具，因此本轮不评估宿主自动触发。\n\nA/C请求最多24次外层工具调用，B/D16次；各主报告10000Unicode字符。均为软限制，不是已验证宿主硬上限。所有执行fork_turns=none、无模型/推理配置override，实际模型/温度/随机种子/token不可得时保留null。共同Python标准库环境，禁止联网、安装、个人技能正文/memory、旧聊天、其他组、未来材料/答案或其他agent。各组都可能看见宿主技能metadata。隔离是指令和自报，没有OS访问审计。\n\nB参数事件先确认当前JSON语义等同初始，允许记录格式不同；保留实际before摘要后按统一after参数投放。语义已变、缺文件或不安全路径不由组织者偷偷修复。B/D答卷位于项目外，组织者比较项目文件字节/mtime与目录mtime；即使只读失败仍保留记录和分母。C的漂移断点不能代替实际复核；旧登记与SHA不等于旧研究文件原字节归档，A共同要求各组实际保存小型初始参数/结果/表/摘要历史，组织者不补档。source-only/明确未绑定文件/未登记依赖不宣称自动覆盖。D不再额外注入科学变更，迁移本身不等于证据失效。\n\n共同100分按A20/B35/C30/D15逐项审查；同链阶段不作独立重复，两个案例不支持总体准确率/因果优越性推断。版本冲突、无效批次回滚、漂移checkpoint和只读等工程探针在隔离副本另列，不加科学分。没有自动接口记未提供自动保障，不能冒充科学内容失败。\n\n每阶段原始项目和外部答卷封存；原始路径和品牌线索可做明确行政公开投影，原SHA另存，不能润色科学内容或隐藏失败。链级匿名AI初评不给组映射/执行历史，但文件布局可能透露方法；另作机械审计与主要发现复核。AI流程可能共享盲点，无人类专家认证。\n'''
 (E/'protocol.md').write_text(protocol)
 dump(E/'environment.json',{'python_executable_logical':'EVAL_PYTHON','python':'3.12.14','libraries_allowed':'Python standard library only','host_effective_model':None,'reasoning_effort':None,'temperature':None,'seed':None,'token_limit':None})
 dump(E/'target.json',{'user_archive_sha256':sha(B/'target-user-runtime.zip'),'files':80,'previous_user_archive_sha256':sha(B/'old-user-runtime.zip'),'runtime_core_logic_changed_for_this_test':False,'new_theory_entry':['skills/rw-review/SKILL.md','skills/rw-review/references/theory-review.md']})
 frozen={p.relative_to(E).as_posix():sha(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='validate.py'}
 dump(E/'freeze.json',{'scope':'Frozen scientific/material/project obligations, reference, event, common protocol and target identity before first lifecycle executor. Record validator and future results excluded.','files':frozen})
 shutil.copyfile(E/'freeze.json',B/'freeze.json')
 dump(E/'study.json',{'format_version':1,'study_id':'RWT-core-lifecycle-v1','freeze_sha256':sha(E/'freeze.json'),'expected_chains':PLAN,'scope':'Two purposive real-material projects; six dependent four-stage chains. Separate content and engineering results.'})
 dump(B/'plan.json',PLAN)
 print(json.dumps({'frozen_files':len(frozen),'freeze_sha256':sha(E/'freeze.json'),'chains':6,'stages':24}))

def snapshot(project):
 files={};dirs={}
 for p in [project,*sorted(project.rglob('*'))]:
  s=p.lstat();name=p.relative_to(project).as_posix()
  if p.is_symlink():
   raw=os.readlink(p).encode();files[name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'mtime_ns':s.st_mtime_ns,'type':'symlink','target':raw.decode()};continue
  if p.is_dir():dirs[name]=s.st_mtime_ns
  elif p.is_file():files[name]={'sha256':sha(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
 return {'files':files,'directories':dirs}

def stage(chain,phase):
 planned=next(x for x in PLAN if x['chain_id']==chain);case=planned['case_id'];arm=planned['arm'];root=B/'runs'/chain;work=root/'project';folder=root/phase;folder.mkdir(parents=True,exist_ok=False);inp=folder/'input';inp.mkdir();out=folder/'output';out.mkdir()
 for f in ['PROTOCOL.md','RECORDING.md',f'STAGE-{phase}.md']:shutil.copyfile(D/'shared'/f,inp/f)
 if phase=='A':
  shutil.copytree(D/case/'initial',inp/'initial')
  if arm in ['core','guidance']:
   guide=B/'toolkits'/chain
   with zipfile.ZipFile(B/'target-user-runtime.zip') as z:z.extractall(guide)
 elif phase=='B':
  before=snapshot(work) if work.exists() else None
  receipt={'case_id':case,'event_applied':False,'scope':'Organizer working-parameter event only; no silent setup repair or source-file replacement.'}
  try:
   assert (root/'A/sealed-project').exists(),'Earlier stage did not leave a sealed project'
   patch=json.loads((D/case/'events/B.patch.json').read_text());target=work/patch['target']
   assert target.is_relative_to(work) and target.is_file() and not any(p.is_symlink() for p in [target,*target.parents]),'Unsafe/missing parameter path'
   initial=strict_parameters((D/case/'initial/project_payload'/patch['target']).read_text());assert same_parameters(strict_parameters(target.read_text()),initial),'Unexpected semantic parameters; do not silently repair'
   raw_before=target.read_bytes();actual_before_sha=sha(target);raw_after=(json.dumps(patch['after_json'],ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();assert hashlib.sha256(raw_after).hexdigest()==patch['after_sha256']
   (folder/'parameter-before.json').write_bytes(raw_before);target.write_bytes(raw_after)
   receipt.update(event_applied=True,changed_paths=[patch['target']],before_sha256=actual_before_sha,canonical_before_sha256=patch['before_sha256'],format_only_initial_difference=actual_before_sha!=patch['before_sha256'],after_sha256=sha(target))
  except Exception as exc:
   receipt['error']={'type':type(exc).__name__,'message':str(exc)}
  after=snapshot(work) if work.exists() else None
  if before is not None and after is not None:
   changed=[k for k in sorted(set(before['files'])|set(after['files'])) if before['files'].get(k)!=after['files'].get(k)]
  else:changed=[] if before==after else ['project-existence']
  receipt['actual_changed_paths']=changed;receipt['no_project_mutation_when_event_rejected']=before==after if not receipt['event_applied'] else None
  if receipt['event_applied'] and changed!=receipt['changed_paths']:receipt['unexpected_additional_differences']=True
  dump(folder/'injection.json',receipt)
 elif phase=='C':shutil.copytree(D/case/'stage-C',inp/'author-revision')
 elif phase=='D':
  moved=B/'moved projects'/f'{chain} 科研项目';moved.parent.mkdir(parents=True,exist_ok=True);work.rename(moved);work=moved
  guide=B/'toolkits'/chain
  if guide.exists():vault=B/'unavailable-toolkit-vault'/chain;vault.parent.mkdir(exist_ok=True);guide.rename(vault)
  assert not (root/'project').exists() and not guide.exists()
  dump(folder/'migration.json',{'previous_project_location_exists':False,'previous_toolkit_location_exists':False,'new_project':str(work),'bytes_preserved_by_rename':True,'scope':'Instruction boundary prevents vault/old repo/cache access; no OS-level access proof.'})
 else:raise ValueError(phase)
 dump(folder/'project-before.json',snapshot(work) if work.exists() else None)
 scope=''
 if phase!='D' and arm=='core':scope=f'''本臂实际启用RWT核心。工具根为 {B/'toolkits'/chain/'research-workflow-template'}。先读其 skills/rw-workflow/SKILL.md、core/skill-bridge.md、core/protocol.md；相关schema/其他指导按需。A必须实际init --connect-skills，register/register-batch并checkpoint；后续已有项目先resume，用正式接口写登记，不手工改权威JSON。'''
 elif phase!='D' and arm=='guidance':scope=f'''本臂读取RWT指导但不使用核心引擎。指导根为 {B/'toolkits'/chain/'research-workflow-template'}，先读 skills/rw-workflow/SKILL.md、core/skill-bridge.md、core/protocol.md；其余markdown/schema按需。不要执行、导入、复制或阅读该包的Python引擎源码，也不要建立伪装成核心输出的记录；用自己的持久文件/脚本落实相同研究义务，可自写hash/version/dependency/recovery/conflict保护。'''
 elif phase!='D':scope='本臂为强文件基线：不额外读取任何skill正文或RWT包，以共同协议和Python标准库/普通文件工具落实研究义务；允许自写hash、manifest、版本/依赖/恢复和冲突保护脚本，允许保存自写必要运行资源。'
 else:scope='本阶段不再提供或允许访问原工具包/指导缓存/源码；只能使用迁移后的项目实际留下的文件、说明与运行资源。原位不存在。'
 request=f'''你是项目生命周期任务的全新上下文执行者。当前仅阶段{phase}，case {case}。先读 {inp/'PROTOCOL.md'}、{inp/'RECORDING.md'}、{inp/f'STAGE-{phase}.md'} 及本阶段input资料，然后完成实际请求。
PROJECT_ROOT={work}
INPUT_DIR={inp}
OUTPUT_DIR={out}
EVAL_PYTHON={PYTHON}，命令请使用 -I -B；仅Python标准库和普通本地文件工具。A中project尚未创建；initial/project_payload是实际需复制的材料，initial其他约束/义务/来源资料也需按实际需求在项目保留以供未来恢复。核心init须在新project目录生成后再复制，不能先创建同名目录阻断init。其他臂可自建新目录。
{scope}
A/C允许写本项目，B/D禁止修改项目字节/mtime/目录mtime。主答卷和执行记录均写OUTPUT_DIR；未来恢复所需持久状态须真实留在项目。输出应报告具体状态与证据，主报告不写组别/技能品牌。soft预算：外层工具调用最多{24 if phase in ['A','C'] else 16}次、主报告10000Unicode字符，真实超出保留。不要联络父agent、调用其他agent或读取前文；禁止memory/个人skills/其他项目或未来材料/参考答案/网络/安装，不能读design/或evals/。本阶段允许input、自己的PROJECT_ROOT和上面明确的指导/工具根，以及共同Python运行文件。生效模型/温度/seed/token未知填null，不推定同配置。所有实际读入文件记录完整SHA/bytes；执行记录须留实际argv/cwd/exit_code、tool_calls、violations、失败/补救与输出。工作完成仅向父任务返回产物路径，不要发进度消息。
'''
 (folder/'REQUEST.md').write_text(request);dump(folder/'assignment.json',{**planned,'stage':phase,'project':str(work),'request_sha256':sha(folder/'REQUEST.md')});print(str(folder/'REQUEST.md'))

if __name__=='__main__':
 if sys.argv[1]=='freeze':freeze()
 elif sys.argv[1]=='stage':stage(sys.argv[2],sys.argv[3])
