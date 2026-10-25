# Research Workflow Template

[中文](README.md) · [English user guide](USER_GUIDE.en.md) · [中文使用说明](中文介绍与使用说明.md)

A local toolkit for research-agent workflows across sciences, engineering, health, agriculture, humanities, social sciences and law. Eight skills guide question formation, literature work, innovation, candidate comparison, method validation, writing and review. A standard-library Python CLI records statements, sources, evidence, artifacts and recovery state; the host assistant performs the research work.

The [English user guide](USER_GUIDE.en.md) covers first use, all eight skills, daily commands, recovery, and upgrades. Detailed technical documents under `docs/` are currently in Chinese.

[Subfield navigation](profiles/selection.md) maps education, economics/management, psychology, philosophy and arts to existing methods and states untested areas. `options` separates declared guidance from explicit variant bindings in recorded tasks; these records do not certify a whole specialty.

Legal research uses the shared skills with a [legal method profile](profiles/methods/legal-analysis.md) and [project template](profiles/templates/legal-research.md), covering jurisdiction, relevant dates, legal authority, judgments and citation pinpoints. The added task evidence uses fictional jurisdictions; it does not certify real legal conclusions.

Only one current edition is maintained. The distribution is named `research-workflow-template.zip`, with content identity recorded by the source inventory and SHA-256. Record, schema and dependency versions remain where required for compatibility and traceability.

## Start a project

Use Python 3.11+ on macOS or Linux. POSIX writer locks do not support Windows.

```sh
python3 tools/research.py init --output ../my-research --title 'My research question'
python3 tools/connect_skills.py install --root ../my-research
python3 tools/connect_skills.py check --root ../my-research
```

Choose a new output directory. Open that project in a compatible skill host and describe the current task. Existing research can resume at the relevant activity. Initial installation refuses existing targets; explicit upgrades preserve local edits by refusing a modified bundle. Global skills and the separate personal package remain independent.

Use `show` for complete envelopes and record versions, `register --file -` or `register-batch` for bounded stdin imports, and `configure` for supported settings. [CLI usage](docs/07-core-usage.md) and [skill connection](docs/08-skills-and-methods.md) document the contracts and directory-switch recovery limits.

## Checks and evidence

```sh
python3 -B tools/check_core.py --test-timeout 360
python3 -B tools/release_package.py check
```

[Current checks](evals/current/latest.json), [release acceptance](docs/10-release-readiness.md) and [platform validation](docs/11-linux-validation.md) distinguish executed environments from untested targets. Active synthetic inputs, frozen task evidence and regression fixtures remain in `evals/`; obsolete release-stage reports are not shipped.

The core performs local registration and inspection, without executing commands embedded in sources, uploading data or submitting manuscripts. Software success is separate from scientific validity, ethics approval and venue compliance. The tool does not include a model API or a background research service. Hosted CI success must be established by an actual repository run.

Original implementation, guidance and synthetic examples use the [MIT license](LICENSE). Linked external works retain their own rights; see [provenance](provenance/ORIGIN.md), [method sources](profiles/sources.json), [contribution guidance](CONTRIBUTING.md) and [security boundaries](SECURITY.md). Creating or publishing a remote repository is a separate action.
