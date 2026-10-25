# Contributing

Use Python 3.11+ and the standard library. From the repository root:

```sh
python3 -B tools/check_core.py --test-timeout 360
python3 -B tools/release_package.py check
```

Keep the core offline, project paths relative and record updates explicit. Follow the existing distinction between record integrity, executed work and the scientific support for a claim. A new skill should have a narrow description, use the shared bridge, and add a realistic task evaluation when its behavior changes materially. Do not duplicate the full workflow in a discipline profile.

For task evaluations, freeze raw synthetic or shareable inputs before execution. Keep grading criteria and expected answers out of the executor's context. Retain actual artifacts, failures, source access and independent content-review limits. Tests should rerun code or check meaningful state; word matching does not establish scientific correctness.

New content needs a clear source and license. External methodological sources are cited rather than copied. After reviewing added or changed files, refresh the provenance inventory with `python3 -B tools/release_package.py index`, then rerun checks. The inventory records declared origin and bytes; it does not independently establish copyright ownership.

Do not put credentials, restricted research material or real patient/interview records in issues, pull requests or examples. Use a minimal synthetic reproduction. Publication, external uploads and actual studies remain separate actions under their applicable permissions.

Skill discovery frontmatter supports a single-line plain or quoted `name`, and a nonempty plain/quoted `description` or an indented `>`, `>-`, `>+`, `|`, `|-`, `|+` description block. The dependency-free checker validates this subset; it does not load arbitrary YAML structures or tags. Check both maintained Markdown links and the generated project-runtime layout when adding nested skill references.
