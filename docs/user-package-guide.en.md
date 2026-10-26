# English user guide

This user package supports local research work. An assistant in Codex or another compatible skill host executes the nine skills; the Python tools save materials, statements, evidence relations, progress and recovery state. Use Python 3.11+ on macOS or Linux. Windows writer locks are not supported.

## First use

Extract the archive, enter `research-workflow-template`, and run:

```sh
python3 tools/research.py options
python3 tools/research.py init --output ../my-research --title 'My research question'
python3 tools/connect_skills.py install --root ../my-research
python3 tools/connect_skills.py check --root ../my-research
```

Choose an output directory that does not exist, and quote paths containing spaces. Open `my-research` in a compatible host and describe your interest, available materials or current task. Keep the toolkit and research project in separate directories. Installation writes only to the selected project's `.agents/skills/`; it does not change global skills.

If the discipline or method is known, add options such as `--discipline law --method legal-analysis` to `init`. Read valid IDs with `options`. Otherwise omit them and update the configuration later with `configure`.

## How the nine skills work together

| Skill | Purpose |
|---|---|
| `rw-workflow` | Select the next action, recover the project and coordinate delivery |
| `rw-question` | Clarify the question, scope and key terms |
| `rw-literature` | Find and read sources; check identity, citations and actual support |
| `rw-innovation` | Develop candidate mechanisms, conjectures and minimum checks |
| `rw-candidates` | Compare the evidence, obstacles and feasibility of directions |
| `rw-validation` | Apply the proof, computation, experiment or interpretation obligations |
| `rw-writing` | Draft, polish, translate and compress while preserving the argument and author intent |
| `rw-figures` | Produce and inspect research figures, separating data, structure and visual appearance |
| `rw-review` | Review, revise and compare shared facts across materials when relevant |

Describe the task directly, for example: “Read these materials and help me define a small testable question.” For several materials, ask: “Check the definitions, conditions and values for the same result in the manuscript and figures, and state what you actually checked.” A read-only request does not add project records.

Discipline and method guidance is in `profiles/`; shared protocols are in `core/`. They do not certify an entire specialty. Mathematical proofs, numerical observations, legal interpretations, ethics permissions and venue requirements each need their own evidence.

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
