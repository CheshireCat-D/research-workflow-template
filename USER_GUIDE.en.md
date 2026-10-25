# Research Workflow Template: Introduction and User Guide

[中文使用说明](中文介绍与使用说明.md) · [English overview](README.en.md)

This toolkit helps researchers work with an AI assistant from an initial research interest through question formation, literature comparison, candidate validation, proofs or experiments, manuscript writing, and delivery checks.

It supports natural sciences, engineering, medicine and health, agriculture and life sciences, humanities, social sciences, and law. These fields share question management and source traceability, while proofs, statistical analysis, experiments, historical interpretation, and legal analysis require their own validation methods.

## How the toolkit works

You do the research with an assistant in Codex or another compatible skill host. The toolkit stores questions, statements, materials, relationships, and next actions. The command-line tools register and inspect this information; the skills guide the assistant's research work. The local commands need no API key or additional Python packages. Access to literature databases still depends on the accounts and permissions you actually have.

Only one current edition is maintained. Its distribution is named `research-workflow-template.zip`; older editions do not accumulate under numbered filenames. Updates are identified by the source inventory and SHA-256 content fingerprints. Data formats, individual records, Python, and external tools retain the version information needed for compatibility and traceability.

## First use: create a separate research project

You need macOS or Linux and Python 3.11 or later. Windows writer locks are not supported.

Open the toolkit folder in Codex. In a terminal, change to the same folder and run:

```sh
python3 tools/research.py init --output '../my-research' --title 'My research question' --interest 'The area I want to investigate'
python3 tools/connect_skills.py install --root '../my-research'
python3 tools/connect_skills.py check --root '../my-research'
```

Replace `../my-research` with a new directory that does not yet exist. Initialization refuses to overwrite an existing directory. Keep your manuscript, data, and results in the new project; the toolkit folder holds the tools and skills.

Then open the new research project in Codex and send a prompt such as:

> My research interests are: … . My current knowledge, materials, and constraints are: … . My intended deliverable is: … . First read or resume this project, clarify the most important open questions, and help me choose one feasible next step. Keep missing sources, unverified conclusions, and unresolved decisions explicit. Complete the work needed at the current stage; we do not need to run through the whole workflow at once.

You do not need to fill every field before starting or list the skill names in every request. Once the project skills are connected, the host assistant selects skills for the current task. Successful installation and file-integrity checks do not establish that the host interface has actually invoked a skill.

## If you already have a manuscript or research materials

For a project already created with this toolkit, resume it first:

```sh
python3 tools/research.py resume --root '/path/to/your/project' --format markdown
```

Tell the assistant whether you need topic selection, literature positioning, proof review, experimental analysis, editing, or a response to reviewers. If your question is already settled, enter at the relevant stage; there is no requirement to restart topic selection.

For a manuscript that has not been registered, you can begin with a local task. When you need persistent project management, create a separate project and have the assistant register the actual materials without overwriting the original manuscript directory.

## What the eight skills do

| Skill | Suitable tasks |
|---|---|
| `rw-workflow` | Coordinate the workflow, read project state, and plan the next action |
| `rw-question` | Clarify interests, research questions, scope, and feasibility |
| `rw-literature` | Examine and compare sources, position existing work, and identify evidence gaps |
| `rw-innovation` | Develop concrete mechanisms, constructions, or testable ideas |
| `rw-candidates` | Compare existing candidate directions and assess them adversarially |
| `rw-validation` | Select minimum validation, proof checks, or experimental checks for the method |
| `rw-writing` | Organize manuscript prose from available statements and materials |
| `rw-review` | Review claim support, limitations, structure, and delivery completeness |

Combine specialist methods as needed. Finite numerical checks cannot replace a mathematical proof. Clinical, field, interview, and historical materials each have their own evidence, permission, and ethics requirements. See [disciplinary and method adaptation](docs/02-disciplinary-adaptation.md) for details.

For legal research, initialize with `--discipline law --method legal-analysis` and use the [legal project template](profiles/templates/legal-research.md). Record jurisdiction, relevant dates, the basis for authority and precedential status, and precise citations. Keep doctrinal interpretation, comparative description, normative proposals, and empirical effects distinct. Legal metadata can use `source.extensions.legal`; successful registration does not certify legal meaning or validity. The added [legal tasks](evals/legal/README.md) use fictional jurisdictions and have a limited testing scope.

## Common daily operations

Usually, you can describe the task in chat and let the assistant register the work. To operate the tools yourself:

| Purpose | Command |
|---|---|
| List supported disciplines, methods, and entry points | `python3 tools/research.py options` |
| Inspect current status and changes | `python3 tools/research.py status --root PROJECT` |
| Read a recovery summary | `python3 tools/research.py resume --root PROJECT --format markdown` |
| List IDs and versions for one record kind | `python3 tools/research.py show --root PROJECT --kind statement` |
| Read one complete record | `python3 tools/research.py show --root PROJECT --kind statement --id S1` |
| Add a method or target venue | `python3 tools/research.py configure --root PROJECT --add-method formal-theory --venue 'Target journal'` |
| Save a concrete next action | `python3 tools/research.py checkpoint --root PROJECT --next-action 'The specific next action'` |

Replace `PROJECT` with your actual project path and quote paths containing spaces. Replace `S1` with an existing statement ID. JSON examples for single and batch registration, standard input, and explicit version replacement are in the [detailed CLI guide](docs/07-core-usage.md).

`options` also separates declared method guidance from explicit variant bindings in task records. Records without a variant remain method-level evidence; neither category certifies an entire specialty or method. [Subfield navigation](profiles/selection.md) gives entry examples for education, economics/management, psychology, philosophy and arts. Project copies do not include the full evaluation materials and report that evidence as unavailable locally.

The project's `project.json` and `records/registry.json` are the authoritative machine-readable records. `PROJECT.md` holds author notes. Recording a target journal or governance requirement records a choice; it does not certify compliance or approval.

## Understanding check results

- Exit code `0`: the requested registration or file/reference check passed.
- Exit code `1`: changes, missing files, or stale activities were found; review the reported findings.
- Exit code `2`: an argument, input, reference, or read/write operation was invalid or failed; follow the error message.

`done` describes an activity's registered progress. When its inputs change, its effective state can become `stale`. The recovery summary identifies the relevant records, paths, and reasons. Review the changes, redo the necessary work, and explicitly update records and checkpoints. Do not rewrite scientific conclusions simply to make a check pass.

Local checks do not execute commands embedded in materials, upload data, submit manuscripts, or conduct research in the background. `scientific_validity: not-assessed` means that the tool has not certified scientific validity. Proofs, citations, experiments, and target-venue policies require their own verification. Follow the applicable submission policy for actual AI use and disclosure.

## Moving projects and updating skills

The project skills include a shared runtime copy. After moving a project, you can use:

```sh
python3 '/new/project/path/.agents/skills/_rw-runtime/tools/research.py' resume --root '/new/project/path' --format markdown
```

To update the project skills, run these commands from the complete toolkit:

```sh
python3 tools/connect_skills.py check --root '/path/to/your/project'
python3 tools/connect_skills.py upgrade --root '/path/to/your/project'
```

Pause agents using the project before upgrading. If the installed copy has local edits, unknown resources, or missing files, the upgrade refuses to overwrite it; preserve and review those changes first. The switch uses a writer lock, staging, backup, and rollback after caught failures. Readers may briefly need to retry. It does not provide a power-loss transaction guarantee. See [skill installation and upgrades](docs/08-skills-and-methods.md).

## Which folders to keep

- `core/`, `tools/`, `skills/`, `profiles/`: the implementation, skills, and method guidance.
- `docs/`: technical documentation to consult as needed. These detailed documents are currently in Chinese; this English guide covers the main user workflow.
- `tests/`, `examples/`, `evals/`: synthetic inputs, execution evidence, and regression fixtures needed by the current tests. Retained stage IDs locate those materials; they do not represent additional old software editions.
- `provenance/`, `LICENSE`, `CITATION.cff`: source declarations, licensing, citation information, and content fingerprints.
- `dist/`: the current ZIP, its SHA-256 sidecar, and the current distribution acceptance record. These are generated locally and excluded from Git source control. A GitHub source checkout or download normally has no `dist/`; follow the [distribution acceptance guide](docs/10-release-readiness.md) when you need to build an archive.

Obsolete release-only records and duplicate candidate packages have been removed from the current package. Original materials and frozen fingerprints referenced by current tests remain. Actual version information for external standards and sources also remains.

## Checking the toolkit and preparing a distribution

```sh
python3 -B tools/check_core.py --test-timeout 360
python3 -B tools/release_package.py check
```

The full checks run in temporary projects. After changing source content, review the changes, regenerate the source inventory, and repeat acceptance checks and archive construction. Do not edit hashes merely to hide an unexplained change. See the [recorded checks](evals/current/latest.json) and [distribution acceptance guide](docs/10-release-readiness.md) for their execution scope.

Use this general toolkit directory for a public GitHub repository. Keep the separate personal package, actual manuscripts, private data, and local environments independent. The project uses the [MIT license](LICENSE); external works retain their own rights. Actual hosted CI results are established by the repository's run logs.
