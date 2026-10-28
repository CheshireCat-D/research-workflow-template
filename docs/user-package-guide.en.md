# English user guide

This user package supports local research work. An assistant in Codex or another compatible skill host executes the nine skills; the Python tools save materials, statements, evidence relations, progress and recovery state. Use Python 3.11+ on Windows, macOS or Linux. The core provides native local project I/O, skill connection and recovery; actual platform verification is recorded separately in the source repository.

## First use

Extract the archive, enter `research-workflow-template`, and run:

```sh
python3 tools/research.py options
python3 tools/research.py init --output ../my-research --title 'My research question'
python3 tools/connect_skills.py install --root ../my-research
python3 tools/connect_skills.py check --root ../my-research
```

On Windows PowerShell, run the same tools with the Python launcher:

```powershell
py -3 -X utf8 tools/research.py init --output "../my-research" --title "My research question"
py -3 -X utf8 tools/connect_skills.py install --root "../my-research"
py -3 -X utf8 tools/connect_skills.py check --root "../my-research"
```

Check `py -3 --version` for Python 3.11 or later. If the launcher is unavailable, replace `py -3` with the installed `python`. Project-root arguments may use native paths; material paths stored inside project records use `/` on every platform.

On Windows, choose an ordinary local project directory such as `C:\Research\my-project`. This version rejects reparse points, including junctions, symbolic links and cloud placeholders; network and cloud-synchronized directories are outside the verified target.

Choose an output directory that does not exist, and quote paths containing spaces. Open `my-research` in a compatible host and describe your interest, available materials or current task. Keep the toolkit and research project in separate directories. Installation writes only to the selected project's `.agents/skills/`; it does not change global skills.

If the discipline or method is known, add options such as `--discipline law --method legal-analysis` to `init`. Read valid IDs with `options`. Otherwise omit them and update the configuration later with `configure`.

## Start with an interest, even without a topic

Open the extracted toolkit in an agent that can read local directories and execute commands, then ask:

> Read the user guide, check the environment, and initialize a separate research project beside the toolkit with the required skills. My discipline / research area is […], my current interests and ideas are […], my existing knowledge, literature, materials and available resources are […], my time limit is […], and I hope to publish in the journal […]. If the topic is unsettled, help narrow the question. Compare the evidence, main objections and feasibility of suitable candidates, then choose one minimum check. Proceed when the information is sufficient; ask only about gaps that affect the next action. Preserve actual sources, outputs and a recoverable next step.

If the journal is undecided, write “undecided” and continue the research already possible. The target journal guides audience, scope and submission requirements; it is not an acceptance prediction.

A chat interface may use the guide for discussion or editing according to its actual attachment capabilities. Uploading a file does not establish skill installation or local execution. Initialization, registration and recovery require real directory and command access. A brand or model name alone does not establish one-click compatibility.

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

Describe the task directly, for example: “Read these materials and help me define a small testable question.” For several materials, ask: “Check the definitions, conditions and values for the same result in the manuscript and figures, and state what you actually checked.” A read-only request does not add project records.

Discipline and method guidance is in `profiles/`; shared protocols are in `core/`. They do not certify an entire specialty. Mathematical proofs, numerical observations, legal interpretations, ethics permissions and venue requirements each need their own evidence.

## Review, revision responses and submission materials

These capabilities use the existing `rw-review` entry and expand only for the requested task:

- **Structured review:** “Prepare a structured peer-review draft with locations, evidence, impact and testable actions.” Apply the proof, experimental, data or interpretation obligations relevant to the manuscript rather than one article template.
- **Multiple simulated reviewers:** “Produce two reviewer reports without showing either reviewer the other report, then synthesize disagreements and important findings.” Isolated reports are used when multiple reviewers are requested; complete and freeze them before synthesis. Nature-style or broad-readership criteria apply only when the target calls for them. Simulations do not impersonate actual journal referees or editorial decisions.
- **Point-by-point response:** “Compare the referee comments with the current revision and map each comment to the actual change, current location and verification status.” Distinguish completed changes from planned work and retain evidence-based disagreement.
- **Revision planning and coverage:** “Split the comments into tasks, arrange dependencies against the deadline and available effort, then check each reply and manuscript location.” Handle simple comments directly; use the bundled read-only checker for omissions, dependency cycles, effort budgets and actual text excerpts when a structured plan is useful.
- **Submission preparation:** “Use the supplied journal requirements to organize the current manuscript, figures, supplements and required declarations, with a file list and explicit gaps.” Check the actual target, prepare delivery copies and verify file identity. Record preparation separately from submission; do not upload or contact a journal automatically.

Reuse the existing review report and, when persistence is needed, `artifact` and `activity` records. A read-only review still returns a report without creating a second review ledger.

## Daily recovery and registration

From the toolkit root, replace `PROJECT` with the actual project path:

```sh
python3 tools/research.py resume --root PROJECT
python3 tools/research.py status --root PROJECT
python3 tools/research.py check --root PROJECT
python3 tools/research.py list --root PROJECT --kind statement
python3 tools/research.py show --root PROJECT --kind statement --id S1
```

`resume`, `status`, `check`, `list` and `show` are read-only commands. Replace `S1` with an existing record ID. Use `register --kind KIND --file INPUT.json` for one record and `register-batch --file INPUT.json` for a batch. Use `--file -` to read standard input. Changing an existing record requires explicit version replacement. Preserve project versions and dependencies; do not clear or directly edit the registry.

Save the next action at a stopping point:

```sh
python3 tools/research.py checkpoint --root PROJECT --next-action 'Check the next original source'
```

Use `python3 tools/research.py --help` and each subcommand's `--help` for arguments. Complete JSON examples and interface details are in the public [CLI guide](https://github.com/CheshireCat-D/research-workflow-template/blob/main/docs/07-core-usage.md).

## Moving and updating

An installed project contains its required guidance and runtime. After moving the complete project, run from its root:

```sh
python3 .agents/skills/_rw-runtime/tools/research.py resume --root .
python3 .agents/skills/_rw-runtime/tools/connect_skills.py check --installed-only --root .
```

To update the toolkit, obtain the new current user package and keep the research project. Pause assistants using the project, then run from the new toolkit:

```sh
python3 tools/connect_skills.py upgrade --root PROJECT
```

An installed copy with local edits, missing files or unknown files is not overwritten. Preserve and review those changes first. An upgrade has a brief reader-switch gap and rollback after caught failures; it does not provide a power-loss transaction guarantee. The public [skill connection guide](https://github.com/CheshireCat-D/research-workflow-template/blob/main/docs/08-skills-and-methods.md) describes these boundaries.

## Package contents and boundaries

The package contains the current `core/`, `skills/`, `profiles/`, catalog resources, two command entry points, bilingual guides, MIT license and source attribution. `USER-PACKAGE-MANIFEST.json` identifies the current file bytes. Evaluation cases, tests, development records and previous editions are outside this user package. Complete evidence and maintenance tools are in the [source repository](https://github.com/CheshireCat-D/research-workflow-template). Evaluation references shown by `options` belong to that repository; they are not local files in the user package.

The tools register metadata offline. They do not execute commands found in sources, upload data or submit manuscripts. Scientific validity, novelty, ethics approval and actual submission status are checked separately. Keep actual manuscripts, private data, credentials and personal skills independent. Optional plotting programs depend on the task; the core requires no third-party Python packages.
