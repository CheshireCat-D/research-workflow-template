# Same-project review and delivery

Use the [review desk](../scripts/review_desk.py) when a researcher wants to compare actual figures, leave feedback, recover decisions or share a revised manuscript. An ordinary single report can use the existing review guidance directly.

## Prepare the review

Work in an initialized RWT project. Save each version under a distinct project-relative path and register the files as local evidence or artifacts through the normal RWT tools. Registered artifact IDs survive a directory move. Keep older bytes when later readers need the old version. Put `review.json` in the project root, using the project's actual references. For example:

```json
{
  "id": "DFigure",
  "title": "Revised manuscript and figure",
  "candidates": ["artifact:FIG", "artifact:FIG2"],
  "deliverables": ["artifact:BRIEF2"],
  "evidence": ["evidence:Edata"],
  "supersedes": {
    "artifact:FIG2": "artifact:FIG",
    "artifact:BRIEF2": "artifact:BRIEF"
  },
  "checks": [{"label": "Independent review", "status": "pending"}]
}
```

Choose the deliverables for the intended reader. Include every supporting file needed to open a standalone report, including images referenced by its Markdown, editable sources or a rendered PDF when requested. Candidates may be figures or other local files. Superseded candidates stay visible for comparison and cannot be picked or packaged as the current choice. To reinstate an earlier version, explicitly revise the supersession map and review the new plan. Omit candidates for a feedback-only manuscript review. `evidence`, `supersedes` and `checks` are optional. A distinct plan ID starts a separate decision history in the same project.

Each check records a label and one of `checked`, `pending`, `failed` or `not-run`, with an optional `note`. Use `checked` only for work actually done and supply its registered report as `evidence`. The optional `against` object maps material references to SHA-256 values from the actual check. Supply the report's own digest and the digests of the specific files it inspected. A matching report and at least one matching target are labeled `checked (bound files match)`; an incomplete baseline shows `file set unverified`, and any mismatch shows `needs recheck`. These are declared checks. The desk verifies file identity and leaves scientific assessment to the reviewer. For estimates shared by the brief, figure or caption, apply the [result-surface check](../../rw-figures/references/result-surfaces.md) and register its actual report before citing it here.

## See the files and save a choice

From the project directory in a connected project, run:

```sh
python3 .agents/skills/rw-review/scripts/review_desk.py serve
```

Open the loopback URL printed in the terminal. View the candidates, select one or request changes, enter the actual reviewer or delegated operator and the reason, then save. The same command later reads the saved decision, earlier choices, feedback, superseded paths and outstanding checks. Stop the local server with Ctrl-C. From the source checkout or extracted user ZIP, call `skills/rw-review/scripts/review_desk.py serve --root PROJECT` instead. All modes accept `--plan` for another project-relative plan path.

The desk writes a native RWT decision and a recovery checkpoint in one transaction. Each decision carries the plan identity and exact registered versions and hashes viewed. Saving verifies the page token inside the native project lock. Reload a stale tab after files, the plan or the decision change. Reconcile changed material before recording a new decision. The web form records what the operator entered; identify a delegated AI or test operator honestly. Accepting a candidate and independently reviewing a paper are separate actions.

For an authorized choice already made outside the browser, read the JSON from `manifest`, inspect the matching materials, then use `save --expect TOKEN --choice artifact:FIG2 --by NAME --feedback TEXT`. For feedback use `--choice request-changes`; with no candidates, `accept-materials` accepts the listed deliverables. `save` returning 1 means the decision was saved and native recovery found other project issues. Exit 2 signals an input, version or file error.

## Export

```sh
python3 .agents/skills/rw-review/scripts/review_desk.py html > review-snapshot.html
python3 .agents/skills/rw-review/scripts/review_desk.py manifest > review-manifest.json
python3 .agents/skills/rw-review/scripts/review_desk.py pack --output revision-2.zip
```

`html` produces a read-only snapshot for offline viewing. It embeds small figure previews and small PDF downloads (up to 4 MiB per file), text excerpts, feedback and material names. In the live desk, full registered files can also be downloaded. Review snapshots and full manifests disclose project-internal review details; share them with the intended readers.

Extract the ZIP and open its root `index.html` in an ordinary browser. The reader links to the original manuscript and displays UTF-8 Markdown and plain-text deliverables up to 256 KiB directly on the page. Markdown headings, paragraphs, simple tables, code and emphasis render offline. Relative image and attachment links work when the target file is in the package; other link labels remain text. The selected image and declared checks follow the current text. A manifest link gives the file hashes. The page and its files work offline. By default the ZIP leaves decision feedback and operator names in the native project. When those details are intended for the recipient, add `--include-feedback` to include the latest decision only. Review notes written in the actual deliverables and declared check fields remain part of those materials.

The ZIP contains explicitly listed deliverables and the selected current candidate, using their relative project hierarchy under `files/`. Its `manifest.json` reports each member hash, decision status and declared checks. Other candidates and raw evidence stay in the project unless deliberately listed as deliverables. A pending selection or check stays visible in a draft reading package. Use a new output name for each revision. ZIP creation checks the actual bytes, rejects concurrent changes to the review, and preserves an existing archive. It publishes the completed local ZIP via an exclusive hard link. On FAT/exFAT or a network share that lacks hard links, create it on a hard-link-capable project or temporary volume and then copy the completed ZIP to the destination.
