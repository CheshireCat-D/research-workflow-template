# English user guide

This user package supports local research work. An assistant in Codex or another compatible skill host executes the nine skills; the Python tools save materials, statements, evidence relations, progress and recovery state. Use Python 3.11+ on Windows, macOS or Linux. The core provides native local project I/O, skill connection and recovery; actual platform verification is recorded separately in the source repository.

## First use

Extract the archive, enter `research-workflow-template`, and run:

```sh
python3 tools/research.py init --output ../my-research --title 'My research question' --connect-skills
```

On Windows PowerShell, run the same tools with the Python launcher:

```powershell
py -3 -X utf8 tools/research.py init --output "../my-research" --title "My research question" --connect-skills
```

Check `py -3 --version` for Python 3.11 or later. If the launcher is unavailable, replace `py -3` with the installed `python`. Project-root arguments may use native paths; material paths stored inside project records use `/` on every platform.

On Windows, choose an ordinary local project directory such as `C:\Research\my-project`. This version rejects reparse points, including junctions, symbolic links and cloud placeholders; network and cloud-synchronized directories are outside the verified target.

Choose an output directory that does not exist, and quote paths containing spaces. Open `my-research` in a compatible host and describe your interest, available materials or current task. Keep the toolkit and research project in separate directories. Installation writes only to the selected project's `.agents/skills/`; it does not change global skills.

For a separate skill-copy diagnostic, use `python3 tools/connect_skills.py check --root PROJECT`; it is not a required step after initialization.

If the discipline or method is known, add options such as `--discipline law --method legal-analysis` to `init`. Read valid IDs with `options`. Otherwise omit them and update the configuration later with `configure`.

## Start with an interest, even without a topic

If you have not created a project, the assistant can perform the initialization above for you. If you already ran those commands, describe your task in the new project. To ask the assistant to create the project, open the extracted toolkit in an agent that can read local directories and execute commands, then ask:

> Read the user guide, check the environment, and initialize a separate research project beside the toolkit with the required skills. My discipline / research area is […], my current interests and ideas are […], my existing knowledge, literature, materials and available resources are […], my time limit is […], and I hope to publish in the journal […]. If the topic is unsettled, help narrow the question. Compare the evidence, main objections and feasibility of suitable candidates, then choose one minimum check. Proceed when the information is sufficient; ask only about gaps that affect the next action. Preserve actual sources, outputs and a recoverable next step. After the first step, give the actual output path, a short conclusion, its saved / registered status and the next action.

If the journal is undecided, write “undecided” and continue the research already possible. The target journal guides audience, scope and submission requirements; it is not an acceptance prediction.

The assistant saves known interests, deadlines, resources and goals in the project, with material details in actual notes and source records. You do not need to write registration JSON. For a question card, analysis or manuscript that you will continue using, ask: “Save and register this, and give me its file path.” A discussion or temporary sentence edit can simply return text.

To save or revise startup information manually, run from the toolkit root and replace `PROJECT` with the project path. Omit unknown items:

```sh
python3 tools/research.py configure --root PROJECT --interest 'Compare strata in existing animal body-mass data' --deadline '2026-11-30' --venue 'undecided' --add-capability 'Existing CSV and an available R environment'
```

Use IDs from `options` for disciplines and methods. Use `--budget` for a budget and repeat `--add-capability` for several capabilities. Recovery returns these values in `configuration`. Review the effect of a configuration change before saving a new checkpoint.

A chat interface may use the guide for discussion or editing according to its actual attachment capabilities. Uploading a file does not establish skill installation or local execution. Initialization, registration and recovery require real directory and command access. A brand or model name alone does not establish one-click compatibility.

## Try the complete public-data project

The user ZIP includes a reproducible example. From the toolkit folder, run:

```sh
python3 -B examples/public-penguins/run_project.py --output ../penguins-project
```

This retrieves one pinned CC0 dataset, produces tables and editable figures, registers the actual outputs, and verifies a saved recovery state. Use a new output directory. Add `--input FILE` for an offline local CSV; its identity is checked before describing it as the pinned public input. This example needs no model or additional Python package.

For literature metadata, `skills/rw-literature/scripts/search_crossref.py` accepts `--query` and `--output`, with bounded cursor pagination and saved response fingerprints. It sends the query to Crossref and provides metadata rather than verified full text.

## How the nine skills work together

| Skill | Purpose |
|---|---|
| `rw-workflow` | Select the next action, recover the project and coordinate delivery |
| `rw-question` | Clarify the question, scope and key terms |
| `rw-literature` | Find and read sources; check identity, citations and actual support |
| `rw-innovation` | Develop candidate mechanisms, conjectures and minimum checks |
| `rw-candidates` | Compare the evidence, obstacles and feasibility of directions |
| `rw-validation` | Apply the proof, computation, experiment or interpretation obligations |
| `rw-writing` | Draft, naturally revise, translate and compress; preserve the argument, author voice and necessary qualifications while removing boilerplate and defensive framing |
| `rw-figures` | Produce and inspect research figures, separating data, structure and visual appearance |
| `rw-review` | Review, optional multiple simulated reports, point-by-point responses and submission preparation; check relevant shared facts |

Manuscripts state results, evidence and necessary conditions directly. Execution notes and review coverage belong in work records. Writing and review share the prose guidance in `rw-writing` to avoid repetitive disclaimer sentences.

The English guide covers user operations. Detailed skill and method instructions are primarily Chinese and are intended for the assistant to read as needed; ask it to explain the steps and produce your outputs in your preferred language.

Describe the task directly, for example: “Read these materials and help me define a small testable question.” For several materials, ask: “Check the definitions, conditions and values for the same result in the manuscript and figures, and state what you actually checked.” A read-only request does not add project records.

Discipline and method guidance is in `profiles/`; shared protocols are in `core/`. They do not certify an entire specialty. Mathematical proofs, numerical observations, legal interpretations, ethics permissions and venue requirements each need their own evidence.

For a citation audit, say: “Check support for each claim, find missing, partial or irrelevant citations, and suggest specific corrections.” The assistant uses existing notes and reports to check compound claims and cross-source synthesis.

The source repository provides [seven disciplinary worked examples](https://github.com/CheshireCat-D/research-workflow-template/tree/main/evals/disciplinary), with synthetic inputs, actual analyses and manuscripts, separate agent reviews, and regression checks. Test materials stay in the source repository; download GitHub's `Source code` archive for offline access. Create a separate project for your own work.

To reproduce the same case shown in the promotional example, run the source-only [paired-pen calculation](https://github.com/CheshireCat-D/research-workflow-template/tree/main/examples/paired-pens), then generate [aligned tables and editable manuscript source](https://github.com/CheshireCat-D/research-workflow-template/tree/main/examples/submission-table). Table/source preparation uses the submission-delivery branch of `rw-review`. Analysis and source generation need standard-library Python; PDF compilation additionally needs the listed TeX packages.

## Review, revision responses and submission materials

These capabilities use the existing `rw-review` entry and expand only for the requested task:

- **Structured review:** “Prepare a structured peer-review draft with locations, evidence, impact and testable actions.” Apply the proof, experimental, data or interpretation obligations relevant to the manuscript rather than one article template.
- **Multiple simulated reviewers:** “Produce two reviewer reports without showing either reviewer the other report, then synthesize disagreements and important findings.” Isolated reports are used when multiple reviewers are requested; complete and freeze them before synthesis. Nature-style or broad-readership criteria apply only when the target calls for them. Simulations do not impersonate actual journal referees or editorial decisions.
- **Point-by-point response:** “Compare the referee comments with the current revision and map each comment to the actual change, current location and verification status.” Distinguish completed changes from planned work and retain evidence-based disagreement.
- **Revision planning and coverage:** “Split the comments into tasks, arrange dependencies against the deadline and available effort, then check each reply and manuscript location.” Handle simple comments directly; use the bundled read-only checker for omissions, dependency cycles, effort budgets and actual text excerpts when a structured plan is useful.
- **Submission preparation:** “Use the supplied journal requirements to organize the current manuscript, figures, supplements and required declarations, with a file list and explicit gaps.” Check the actual target, prepare delivery copies and verify file identity. Record preparation separately from submission; do not upload or contact a journal automatically.

Reuse the existing review report and, when persistence is needed, `artifact` and `activity` records. A read-only review still returns a report without creating a second review ledger.

## Daily recovery and registration

Usually the assistant handles these operations. Start a session from the research project root with one recovery command:

```sh
python3 .agents/skills/_rw-runtime/tools/research.py resume --format markdown
```

Project commands use only the current directory when `--root` is omitted; they do not search parents or initialize a project. From the toolkit root, use `python3 tools/research.py resume --root PROJECT --format markdown` instead. The summary already includes configuration, the next action, file changes and stale activities. There is no need to run `status`, `check` and `show` in sequence. Use `show --kind statement --id S1` only when you need that record.

After the actual work and review, save this session's records and next action together. Run this command from the toolkit root; `PROJECT` is the project path and `INPUT.json` is an ordered batch array:

```sh
python3 tools/research.py register-batch --root PROJECT --file INPUT.json --next-action 'Check the next original source'
```

Single-record `register --kind KIND --file INPUT.json` also accepts `--next-action`. Add `--activity ID` / `--note TEXT` when useful; both require a next action. The returned `recovery` includes the check after saving, so another `resume` is unnecessary. To save only a stopping point, use `checkpoint --root PROJECT --next-action 'Next action' --report`.

Recovery and queries are read-only; redirecting an export is a caller write. If a save exits 1, inspect `registered` / `checkpoint_saved`: the records may already be saved while recovery still reports findings. Do not blindly retry. A field, version, reference or checkpoint validation failure before commit writes nothing. After a write error, recover and confirm the actual saved state first. Saving does not change `scientific_validity: not-assessed`.

`file_tracking.local_files` lists bound local paths; `source_ids_without_local_evidence` lists source IDs without local evidence bindings. A locator alone does not track file contents. Coverage does not mark external sources stale or replace reading them. See the public [CLI guide](https://github.com/CheshireCat-D/research-workflow-template/blob/main/docs/07-core-usage.md) for complete arguments and JSON examples.

### A minimal offline registration example

From the toolkit root, save the following as `statement-batch.json` and replace `PROJECT` with an initialized project path. Batch input is an array whose items contain `kind` and `record`; the bundled `core/schemas/` documents the record fields. This example registers a synthetic observation. Choose a new ID if `S1` already exists.

```json
[
  {"kind": "statement", "record": {"id": "S1", "text": "This is a synthetic observation for registration practice.", "type": "empirical", "scope": "Offline interface practice"}}
]
```

```sh
python3 tools/research.py register-batch --root PROJECT --file statement-batch.json --next-action 'Check the actual basis for this observation'
```

### Connect existing materials and detect changes

If an existing folder has no `project.json`, create a new RWT project beside it; do not run `init` over that folder. Keep the originals and copy only the ordinary files needed now into the new project, such as `notes/data.csv`. Confirm the destination file does not already exist. Agree to update this working copy inside the project thereafter, so RWT does not inspect an old copy while work continues elsewhere. Materials that cannot be copied, or must remain in an external workspace, can use `external` / `controlled` locations and access notes; local checks do not detect changes to those originals. Parent paths, absolute material paths and symbolic links cannot bypass this choice.

Ask the assistant: “Keep the original folder, connect the selected materials to a new project, tell me which files to update from now on, save the source and local evidence records, and give the first output path.”

After the material exists at `PROJECT/notes/data.csv`, save the following as UTF-8 `material-batch.json`. This records material intake; no statistical analysis has been performed. Use new IDs if these IDs already exist.

```json
[
  {"kind": "source", "record": {"id": "SRC-MATERIAL", "title": "Existing CSV material", "locator": "notes/data.csv", "version": "working-copy-1", "content_access": "not-read"}},
  {"kind": "evidence", "record": {"id": "E-MATERIAL", "type": "local-material", "description": "Working copy for subsequent analysis", "provenance": "Copied from an existing material folder; originals retained", "location": {"kind": "local", "path": "notes/data.csv"}, "source_ids": ["SRC-MATERIAL"]}},
  {"kind": "activity", "record": {"id": "A-MATERIAL", "title": "Connect existing material", "status": "done", "inputs": ["evidence:E-MATERIAL"], "note": "Working copy placed in the project and registered; analysis has not started."}}
]
```

```sh
python3 tools/research.py register-batch --root PROJECT --file material-batch.json --activity A-MATERIAL --next-action 'Read notes/data.csv and check variables and the analysis unit'
```

`source` stores identity. Local `evidence` linked through `source_ids` binds the file fingerprint. Changing `notes/data.csv` after this example makes recovery report the changed file and stale activity. Review the change, do the affected work and update evidence, artifacts and activities from upstream to downstream, then save them with the next action. Register `done` again only after actually completing the work; otherwise use its real progress. Refreshing an old `done` record or saving another checkpoint does not perform the review.

### Correct existing records

Use `show --edit` to export selected records as an editable batch array. It includes `kind`, `record`, `replace:true` and a fixed `expected_version`, so a separate version query is unnecessary:

```sh
python3 tools/research.py show --root PROJECT --edit source:SRC-MATERIAL > source-edit.json
# Edit record to reflect the correction; keep expected_version.
python3 tools/research.py register-batch --root PROJECT --file source-edit.json --next-action 'Review the effect of the source correction on subsequent work'
```

For several records, use `--edit evidence:E-MATERIAL activity:A-MATERIAL` in upstream-to-downstream order. Actually review the work before recording the activity's real progress. If someone updates the same ID after export, saving the old version is rejected. Read again and compare changes; do not just increase the version number. A source correction can also make downstream activities stale; address the recovery findings.

`--edit` cannot be combined with `--kind`, `--id` or `--data-only`. Ordinary queries and single-record replacement remain available. Do not feed a query wrapper back as a record or directly edit the registry. On PowerShell, replace `python3` with `py -3 -X utf8`. To avoid shell-dependent output encodings, ask the assistant to save JSON with UTF-8 file tools or use:

```powershell
py -3 -X utf8 -c "from pathlib import Path; import subprocess,sys; data=subprocess.check_output([sys.executable,'tools/research.py','show','--root','PROJECT','--edit','source:SRC-MATERIAL']); Path('source-edit.json').write_bytes(data)"
```

## Moving and updating

An installed project contains its required guidance and runtime. After moving the complete project, run from its root:

```sh
python3 .agents/skills/_rw-runtime/tools/research.py resume --format markdown
```

For a new conversation, open this same research project and ask: “Read the configuration, records and recovery summary, check material changes, then continue the saved next action.” The installed command also works when the toolkit has moved. To inspect installed resources separately, run `python3 .agents/skills/_rw-runtime/tools/connect_skills.py check --installed-only --root .`; this is not required at every recovery.

To update the toolkit, obtain the new current user package and keep the research project. Pause assistants using the project, then run from the new toolkit:

```sh
python3 tools/connect_skills.py upgrade --root PROJECT
```

An installed copy with local edits, missing files or unknown files is not overwritten. Preserve and review those changes first. An upgrade has a brief reader-switch gap and rollback after caught failures; it does not provide a power-loss transaction guarantee. The public [skill connection guide](https://github.com/CheshireCat-D/research-workflow-template/blob/main/docs/08-skills-and-methods.md) describes these boundaries.

## Feedback

Use the [first-use feedback form](https://github.com/CheshireCat-D/research-workflow-template/issues/new?template=first-use-feedback.yml) for successes or difficulties. Include the OS, Python, agent, intended task, step reached and actual error. Issues are public; use a privacy-clean synthetic reproduction. The form does not request a name or email, and the toolkit does not send usage records automatically.

The [first-use records](https://github.com/CheshireCat-D/research-workflow-template/tree/main/evals/usability) describe two isolated AI-agent simulations; human feedback is collected separately. The [public penguin-data case](https://github.com/CheshireCat-D/research-workflow-template/tree/main/examples/public-penguins) provides reproducible analysis and figures, with links to independent checks and the recorded project recovery.

## Package contents and boundaries

The package contains the current `core/`, `skills/`, `profiles/`, catalog resources, two command entry points, bilingual guides, MIT license and source attribution. `USER-PACKAGE-MANIFEST.json` identifies the current file bytes. Evaluation cases, tests, development records and previous editions are outside this user package. Complete evidence and maintenance tools are in the [source repository](https://github.com/CheshireCat-D/research-workflow-template). Evaluation references shown by `options` belong to that repository; they are not local files in the user package.

The tools register metadata offline. They do not execute commands found in sources, upload data or submit manuscripts. Scientific validity, novelty, ethics approval and actual submission status are checked separately. Keep actual manuscripts, private data, credentials and personal skills independent. Optional plotting programs depend on the task; the core requires no third-party Python packages.
