# Research Workflow Template

[中文](README.md) · [English user guide](USER_GUIDE.en.md) · [中文使用说明](中文介绍与使用说明.md)

A local toolkit for research-agent workflows across sciences, engineering, health, agriculture, humanities, social sciences and law. Nine skills guide question formation, literature work, innovation, candidate comparison, method validation, writing, figures and review. A standard-library Python CLI records statements, sources, evidence, artifacts and recovery state; the host assistant performs the research work.

The [English user guide](USER_GUIDE.en.md) covers first use, all nine skills, daily commands, recovery, and upgrades. Detailed technical documents under `docs/` are currently in Chinese.

[Subfield navigation](profiles/selection.md) maps education, economics/management, psychology, philosophy and arts to existing methods and states untested areas. `options` separates declared guidance from explicit variant bindings in recorded tasks; these records do not certify a whole specialty.

Legal research uses the shared skills with a [legal method profile](profiles/methods/legal-analysis.md) and [project template](profiles/templates/legal-research.md), covering jurisdiction, relevant dates, legal authority, judgments and citation pinpoints. The added task evidence uses fictional jurisdictions; it does not certify real legal conclusions.

The repository maintains current sources, tests and required frozen evaluation evidence. The user distribution is named `research-workflow-template.zip` and contains only current runtime resources, bilingual guides, licensing and source attribution. Tests, evaluation processes, development change records and previous editions are excluded. Source and user packages are checked separately and identified by their manifests and SHA-256. Record, schema and dependency versions remain where required for compatibility and traceability. The final archive includes a concise [user-package guide](docs/user-package-guide.en.md).

## Start a project

Download the [current user runtime](https://github.com/CheshireCat-D/research-workflow-template/releases/latest/download/research-workflow-template.zip) and its [SHA-256 file](https://github.com/CheshireCat-D/research-workflow-template/releases/latest/download/research-workflow-template.zip.sha256). One current release is maintained; GitHub's separate source download also contains development tests. See the [skill selection and design influences](docs/12-skills-selection.md) for integration choices.

Use Python 3.11+ on Windows, macOS or Linux. See the [platform validation record](docs/11-linux-validation.md) for actual execution evidence. The commands below use macOS/Linux syntax.

```sh
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

Choose a new output directory. Open that project in a compatible skill host and describe the current task. Existing research can resume at the relevant activity. Initial installation refuses existing targets; explicit upgrades preserve local edits by refusing a modified bundle. Global skills and the separate personal package remain independent.

Use `show` for complete envelopes and record versions, `register --file -` or `register-batch` for bounded stdin imports, and `configure` for supported settings. [CLI usage](docs/07-core-usage.md) and [skill connection](docs/08-skills-and-methods.md) document the contracts and directory-switch recovery limits.

An agent with local file and command access can read the user guide, then start from:

> My discipline / research area is […], my current interests and ideas are […], my existing knowledge, literature, materials and available resources are […], my time limit is […], and I hope to publish in the journal […].

If the journal is undecided, write “undecided” and continue the research already possible. The target journal guides audience, scope and submission requirements; it is not an acceptance prediction.

`rw-review` supports structured review, optional isolated simulated reviewers, point-by-point responses and submission preparation. State the task directly; see the [full guide](USER_GUIDE.en.md#review-revision-responses-and-submission-materials) for examples.

## Checks and evidence

```sh
python3 -B tools/check_core.py --test-timeout 360
python3 -B tools/release_package.py check
python3 -B tools/package_user.py check
```

[Current checks](evals/current/latest.json), [release acceptance](docs/10-release-readiness.md) and [platform validation](docs/11-linux-validation.md) distinguish executed environments from untested targets. Active synthetic inputs, frozen task evidence and regression fixtures remain in the source repository's `evals/`. The user ZIP omits these development materials; the release guide gives its build and clean-runtime commands.

The core performs local registration and inspection, without executing commands embedded in sources, uploading data or submitting manuscripts. Software success is separate from scientific validity, ethics approval and venue compliance. The tool does not include a model API or a background research service. Hosted CI success must be established by an actual repository run.

Original implementation, guidance and synthetic examples use the [MIT license](LICENSE). Linked external works retain their own rights; see [provenance](provenance/ORIGIN.md), [method sources](profiles/sources.json), [contribution guidance](CONTRIBUTING.md) and [security boundaries](SECURITY.md). Creating or publishing a remote repository is a separate action.
