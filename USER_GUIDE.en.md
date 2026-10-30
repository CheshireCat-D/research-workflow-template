# Research Workflow Template: Introduction and User Guide

[中文使用说明](中文介绍与使用说明.md) · [English overview](README.en.md)

This toolkit helps researchers work with an AI assistant from an initial research interest through question formation, literature comparison, candidate validation, proofs or experiments, manuscript writing, and delivery checks.

It supports natural sciences, engineering, medicine and health, agriculture and life sciences, humanities, social sciences, and law. These fields share question management and source traceability, while proofs, statistical analysis, experiments, historical interpretation, and legal analysis require their own validation methods.

## How the toolkit works

You do the research with an assistant in Codex or another compatible skill host. The toolkit stores questions, statements, materials, relationships, and next actions. The command-line tools register and inspect this information; the skills guide the assistant's research work. The local commands need no API key or additional Python packages. Access to literature databases still depends on the accounts and permissions you actually have.

Only one current edition is maintained. Its distribution is named `research-workflow-template.zip`; older editions do not accumulate under numbered filenames. Updates are identified by the source inventory and SHA-256 content fingerprints. Data formats, individual records, Python, and external tools retain the version information needed for compatibility and traceability.

## First use: create a separate research project

Use Python 3.11 or later on Windows, macOS or Linux. Platform implementation and actually executed verification are recorded separately in the [platform guide](docs/11-linux-validation.md).

Open the toolkit folder in Codex. In a terminal, change to the same folder and run:

```sh
python3 tools/research.py init --output '../my-research' --title 'My research question' --interest 'The area I want to investigate' --connect-skills
```

On Windows PowerShell, run the same tools with the Python launcher:

```powershell
py -3 -X utf8 tools/research.py init --output "../my-research" --title "My research question" --connect-skills
```

Check `py -3 --version` for Python 3.11 or later. If the launcher is unavailable, replace `py -3` with the installed `python`. Project-root arguments may use native paths; material paths stored inside project records use `/` on every platform.

On Windows, choose an ordinary local project directory such as `C:\Research\my-project`. This version rejects reparse points, including junctions, symbolic links and cloud placeholders; network and cloud-synchronized directories are outside the verified target.

Replace `../my-research` with a new directory that does not yet exist. Initialization refuses to overwrite an existing directory. Keep your manuscript, data, and results in the new project; the toolkit folder holds the tools and skills.

After these commands, open the new research project in Codex and describe your interest, available materials or current task. Initialization is complete; continue in this project.

You do not need to fill every field before starting or list the skill names in every request. Once the project skills are connected, the host assistant selects skills for the current task. Successful installation and file-integrity checks do not establish that the host interface has actually invoked a skill.

For a separate skill-copy diagnostic, use `python3 tools/connect_skills.py check --root PROJECT`; it is not required after initialization or every recovery.

## Start with an interest, even without a topic

If you have not created a project, the assistant can perform the initialization above for you. Open the extracted toolkit in an agent that can read local directories and execute commands, then ask:

> Read the user guide, check the environment, and initialize a separate research project beside the toolkit with the required skills. My discipline / research area is […], my current interests and ideas are […], my existing knowledge, literature, materials and available resources are […], my time limit is […], and I hope to publish in the journal […]. If the topic is unsettled, help narrow the question. Compare the evidence, main objections and feasibility of suitable candidates, then choose one minimum check. Proceed when the information is sufficient; ask only about gaps that affect the next action. Preserve actual sources, outputs and a recoverable next step. After the first step, give the actual output path, a short conclusion, its saved / registered status and the next action.

If the journal is undecided, write “undecided” and continue the research already possible. The target journal guides audience, scope and submission requirements; it is not an acceptance prediction.

The assistant saves known interests, deadlines, resources and goals in project configuration, with material details in actual notes and source records. For a question card, analysis or manuscript you will continue using, ask: “Save and register this, and give me its file path.” A discussion or temporary sentence edit can simply return text. Configuration and correction commands are described under daily operations below.

A chat interface may use the guide for discussion or editing according to its actual attachment capabilities. Uploading a file does not establish skill installation or local execution. Initialization, registration and recovery require real directory and command access. A brand or model name alone does not establish one-click compatibility.

## If you already have a manuscript or research materials

For a project already created with this toolkit, run from the toolkit root and replace the project path with its actual location:

```sh
python3 tools/research.py resume --root '/path/to/your/project' --format markdown
```

If you are already in the research project root, use its installed runtime:

```sh
python3 .agents/skills/_rw-runtime/tools/research.py resume --format markdown
```

One recovery already includes configuration, the next action, file changes and stale activities; there is no need to run `status`, `check` and `show` in sequence. Omitting `--root` uses only the current directory, without searching parents or initializing a project.

Tell the assistant whether you need topic selection, literature positioning, proof review, experimental analysis, editing, or a response to reviewers. If your question is already settled, enter at the relevant stage; there is no requirement to restart topic selection.

For a manuscript that has not been registered, you can begin with a local task. When you need persistent management, create a new RWT project beside the original folder, retain the originals, copy only materials needed now, and agree which working copies to edit thereafter. External or controlled materials can retain a locator; local checks do not track changes to those originals. Parent paths, absolute material paths and symbolic links do not replace intake. Complete [material-intake and correction examples](docs/user-package-guide.en.md) are also included in the current user package.

For a new conversation, open the same research project. Ask the assistant to read its configuration, records and recovery summary, check material changes, then continue the saved next action. Do not initialize it again.

## Try the complete public-data project

The user ZIP includes a reproducible example. From the toolkit folder, run:

```sh
python3 -B examples/public-penguins/run_project.py --output ../penguins-project
```

This retrieves one pinned CC0 dataset, produces tables and editable figures, registers the actual outputs, and verifies a saved recovery state. Use a new output directory. Add `--input FILE` for an offline local CSV; its identity is checked before describing it as the pinned public input. This example needs no model or additional Python package.

For literature metadata, `skills/rw-literature/scripts/search_crossref.py` accepts `--query` and `--output`, with bounded cursor pagination and saved response fingerprints. It sends the query to Crossref and provides metadata rather than verified full text.

## What the nine skills do

| Skill | Suitable tasks |
|---|---|
| `rw-workflow` | Coordinate the workflow, read project state, and plan the next action |
| `rw-question` | Clarify interests, research questions, scope, and feasibility |
| `rw-literature` | Examine and compare sources, position existing work, and identify evidence gaps |
| `rw-innovation` | Develop concrete mechanisms, constructions, or testable ideas |
| `rw-candidates` | Compare existing candidate directions and assess them adversarially |
| `rw-validation` | Select minimum validation, proof checks, or experimental checks for the method |
| `rw-writing` | Draft, polish, translate and compress; preserve author voice and necessary qualifications while removing boilerplate and defensive framing |
| `rw-review` | Self-review, structured or multiple simulated reviews, referee responses, cross-material consistency and submission preparation |
| `rw-figures` | Create or inspect data figures and editable schematics, preserving sources and scientific meaning |

Manuscripts state results, evidence and necessary conditions directly. Execution notes and review coverage belong in work records. Writing and review share the [prose guidance](skills/rw-writing/SKILL.md) to avoid repetitive disclaimer sentences.

Combine specialist methods as needed. Finite numerical checks cannot replace a mathematical proof. Clinical, field, interview, and historical materials each have their own evidence, permission, and ethics requirements. See [disciplinary and method adaptation](docs/02-disciplinary-adaptation.md) for details.

When a delivery includes several materials, such as a manuscript, figures, supplements, slides, or code, or an updated fact affects other materials, you can ask the assistant to check consistency. It first identifies the fact and its established authoritative basis, then checks the relevant expressions and records conflicts or justified exceptions in the existing review report. A read-only request adds no project records. For example: “Check the definitions, conditions, and values for the same result across these materials, and state what you actually checked.” See the [cross-material review reference](skills/rw-review/references/cross-material-consistency.md) for the procedure.

For legal research, initialize with `--discipline law --method legal-analysis` and use the [legal project template](profiles/templates/legal-research.md). Record jurisdiction, relevant dates, the basis for authority and precedential status, and precise citations. Keep doctrinal interpretation, comparative description, normative proposals, and empirical effects distinct. Legal metadata can use `source.extensions.legal`; successful registration does not certify legal meaning or validity. The added [legal tasks](evals/legal/README.md) use fictional jurisdictions and have a limited testing scope.

For a citation audit, say: “Check the source support for each claim in this passage, then find missing, partial or irrelevant citations and suggest specific corrections.” The assistant checks separately verifiable parts of compound claims and explains cross-source synthesis in the existing notes or review report.

See the [seven disciplinary examples](evals/disciplinary/README.md) for original synthetic inputs, actual analyses and short manuscripts, separate agent reviews, and reproducible checks. Use them as worked examples, then create a separate project for your own materials.

For daily use, download `research-workflow-template.zip` from Releases. Cases and maintenance tests are in the source repository; download GitHub's `Source code` archive when you need them offline.

For a data-to-delivery walkthrough, run the [paired-pen example](examples/paired-pens/README.md) to reproduce the figures shown in the promotional demonstration, then use the [table and manuscript example](examples/submission-table/README.md) to create aligned tables, editable source and an actual file manifest. Analysis and source generation use standard-library Python; PDF compilation needs the TeX environment listed in the example. See the [research-quality tasks](evals/quality/README.md) for real retrieval, review controls and adaptation to changed resources.

For a real public-data walkthrough, see the [penguin analysis](examples/public-penguins/README.md) and its [independent base-R review](evals/public-data/assessment.md). The [first-use records](evals/usability/README.md) separate AI-agent exercises from future human feedback. The user ZIP also includes a minimal offline batch-registration example; successes or difficulties can be reported through the [feedback form](https://github.com/CheshireCat-D/research-workflow-template/issues/new?template=first-use-feedback.yml).

## Review, revision responses and submission materials

These capabilities use the existing `rw-review` entry and expand only for the requested task:

- **Structured review:** “Prepare a structured peer-review draft with locations, evidence, impact and testable actions.” Apply the proof, experimental, data or interpretation obligations relevant to the manuscript rather than one article template.
- **Multiple simulated reviewers:** “Produce two reviewer reports without showing either reviewer the other report, then synthesize disagreements and important findings.” Isolated reports are used when multiple reviewers are requested; complete and freeze them before synthesis. Nature-style or broad-readership criteria apply only when the target calls for them. Simulations do not impersonate actual journal referees or editorial decisions.
- **Point-by-point response:** “Compare the referee comments with the current revision and map each comment to the actual change, current location and verification status.” Distinguish completed changes from planned work and retain evidence-based disagreement.
- **Revision planning and coverage:** “Split the comments into tasks, arrange dependencies against the deadline and available effort, then check each reply and manuscript location.” Handle simple comments directly; use the bundled read-only checker for omissions, dependency cycles, effort budgets and actual text excerpts when a structured plan is useful.
- **Submission preparation:** “Use the supplied journal requirements to organize the current manuscript, figures, supplements and required declarations, with a file list and explicit gaps.” Check the actual target, prepare delivery copies and verify file identity. Record preparation separately from submission; do not upload or contact a journal automatically.

Reuse the existing review report and, when persistence is needed, `artifact` and `activity` records. A read-only review still returns a report without creating a second review ledger.

Mode details: [structured and multiple reviews](skills/rw-review/references/review-modes.md), [referee responses](skills/rw-review/references/review-response.md), and [submission delivery](skills/rw-review/references/submission-delivery.md).

## Common daily operations

Usually, you can describe the task in chat and let the assistant register the work. Run the commands below from the toolkit root; inside a research project, use the installed runtime path shown above:

| Purpose | Command |
|---|---|
| Recover the project and inspect changes | `python3 tools/research.py resume --root PROJECT --format markdown` |
| Export selected records with their versions | `python3 tools/research.py show --root PROJECT --edit evidence:E1 activity:A1` |
| Save records and the next action together | `python3 tools/research.py register-batch --root PROJECT --file BATCH.json --next-action 'The specific next action'` |
| Save only a stopping point and inspect findings | `python3 tools/research.py checkpoint --root PROJECT --next-action 'The specific next action' --report` |
| List disciplines, methods and entry points | `python3 tools/research.py options` |
| Save an interest, deadline and resources | `python3 tools/research.py configure --root PROJECT --interest 'Current question' --deadline 'Within four weeks' --add-capability 'Existing CSV and R environment'` |

Replace `PROJECT` with the project path, quoting spaces, and `E1` / `A1` with existing IDs. `show --edit` returns a batch array with each record's kind, data, replacement flag and fixed `expected_version`. Edit it and pass it directly to `register-batch`; no separate version query is needed. If a version conflicts, read and compare changes again rather than just changing the number. Single-record `register` also accepts `--next-action`. The combined save returns `recovery`, so another recovery command is unnecessary. Use a separate `checkpoint --report` only when records have not changed.

For a targeted query, `show --kind statement --id S1` remains available. `--edit` cannot be combined with `--kind`, `--id` or `--data-only`. See the [CLI guide](docs/07-core-usage.md) for JSON, standard input and replacement details. `configure --budget` saves a budget; repeat `--add-capability` as needed and omit unknown items. Use `--venue` for the target journal and `--add-method` for another method. Recovery returns the saved startup information in `configuration`.

`options` also separates declared method guidance from explicit variant bindings in task records. Records without a variant remain method-level evidence; neither category certifies an entire specialty or method. [Subfield navigation](profiles/selection.md) gives entry examples for education, economics/management, psychology, philosophy and arts. Project copies do not include the full evaluation materials and report that evidence as unavailable locally.

The project's `project.json` and `records/registry.json` are the authoritative machine-readable records. `PROJECT.md` holds author notes. Recording a target journal or governance requirement records a choice; it does not certify compliance or approval.

## Understanding check results

- Exit code `0`: the requested registration or file/reference check passed.
- Exit code `1`: recovery found changes, missing files or stale activities. A combined save may already be committed; inspect `registered` / `checkpoint_saved` and `recovery` before retrying.
- Exit code `2`: an argument, input, reference, or read/write operation was invalid or failed; follow the error message.

`done` describes an activity's registered progress. When its inputs change, its effective state can become `stale`. The recovery summary identifies the relevant records, paths, and reasons. Review changes and do the necessary work, then update evidence, artifacts and activities from upstream to downstream and save them with the next action. Register `done` again only after actually completing that work. Refreshing old status or a checkpoint does not redo the work. Do not rewrite scientific conclusions simply to make a check pass. Validation failures before commit write nothing; after a write error, recover and confirm the actual saved state first.

`file_tracking` lists bound local files and source IDs without local evidence. `source.locator` stores identity only. To track file changes, register local `evidence`, connect it to the source through `source_ids`, and use that evidence as the activity input. Coverage and actual file drift are separate information; external locators are not automatically read.

Local checks do not execute commands embedded in materials, upload data, submit manuscripts, or conduct research in the background. `scientific_validity: not-assessed` means that the tool has not certified scientific validity. Proofs, citations, experiments, and target-venue policies require their own verification. Follow the applicable submission policy for actual AI use and disclosure.

## Moving projects and updating skills

The project skills include a shared runtime copy. After moving the complete project, run from its new root:

```sh
python3 .agents/skills/_rw-runtime/tools/research.py resume --format markdown
```

To update the project skills, run these commands from the complete toolkit:

```sh
python3 tools/connect_skills.py upgrade --root '/path/to/your/project'
```

Pause agents using the project before upgrading. If the installed copy has local edits, unknown resources, or missing files, the upgrade refuses to overwrite it; preserve and review those changes first. The switch uses a writer lock, staging, backup, and rollback after caught failures. Readers may briefly need to retry. It does not provide a power-loss transaction guarantee. See [skill installation and upgrades](docs/08-skills-and-methods.md).

## Which folders to keep

The following is the full source repository's maintenance layout. The final user ZIP contains runtime resources, concise bilingual guides, licensing and attribution. Tests, evaluation cases, development change records and previous editions are excluded. Its separate [user-package guide](docs/user-package-guide.en.md) focuses on daily work.

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
python3 -B tools/package_user.py check
```

The full checks run in temporary projects. After changing source content, review the changes, regenerate the source inventory, and repeat acceptance checks and archive construction. Do not edit hashes merely to hide an unexplained change. See the [recorded checks](evals/current/latest.json) and [distribution acceptance guide](docs/10-release-readiness.md) for their execution scope.

Use this general toolkit directory for a public GitHub repository. Keep the separate personal package, actual manuscripts, private data, and local environments independent. The project uses the [MIT license](LICENSE); external works retain their own rights. Actual hosted CI results are established by the repository's run logs.
