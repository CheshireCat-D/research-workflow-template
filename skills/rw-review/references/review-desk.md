# Same-project review and delivery

Handle review, revision and author feedback in the conversation. Use the [review desk tools](../scripts/review_desk.py) when the task needs project-bound figure choices, feedback history or a reading package. The assistant prepares the plan and saves the user's stated choices. Open the browser when requested or when side-by-side previews help the researcher decide.

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

## Save a choice from the conversation

From the connected project directory, the assistant reads the current material references and token:

```sh
python3 .agents/skills/rw-review/scripts/review_desk.py manifest
```

Inspect the matching materials, use the choice and feedback already supplied in the conversation, then run `save --expect TOKEN --choice artifact:FIG2 --by NAME --feedback TEXT`. For feedback use `--choice request-changes`; with no candidates, `accept-materials` accepts the listed deliverables. Identify the user or delegated AI operator accurately. If the user delegated the choice, record the assistant's own reason. Ask for a choice only when it remains unresolved and affects the task.

`save` writes the native decision and recovery checkpoint together. It binds the plan, registered material versions and hashes, and verifies the token inside the project lock. Reconcile changed material before saving a new decision. Exit 1 means the choice was saved and recovery found other project issues. Exit 2 signals an input, version or file error. A saved choice records the operator's decision; independent review follows the actual review evidence.

From the source checkout or extracted toolkit, use `skills/rw-review/scripts/review_desk.py MODE --root PROJECT`. All modes accept `--plan` for another project-relative plan path.

## Open the optional browser view

```sh
python3 .agents/skills/rw-review/scripts/review_desk.py serve
```

Open the printed loopback URL to compare candidates, view earlier choices and feedback, and save a decision. Use the same project and plan for later revisions. Reload a stale tab after files, the plan or the decision change. Stop the server with Ctrl-C when finished.

## Export

For a reading package, the assistant runs `pack` directly using the selected files. Choose another export only when its separate output is needed.

```sh
python3 .agents/skills/rw-review/scripts/review_desk.py html > review-snapshot.html
python3 .agents/skills/rw-review/scripts/review_desk.py manifest > review-manifest.json
python3 .agents/skills/rw-review/scripts/review_desk.py pack --output revision-2.zip
```

`html` produces a read-only snapshot for offline viewing. It embeds small figure previews and small PDF downloads (up to 4 MiB per file), text excerpts, feedback and material names. In the live desk, full registered files can also be downloaded. Review snapshots and full manifests disclose project-internal review details; share them with the intended readers.

Extract the ZIP and open its root `index.html` in an ordinary browser. The reader links to the original manuscript and displays UTF-8 Markdown and plain-text deliverables up to 256 KiB directly on the page. Markdown headings, paragraphs, simple tables, code and emphasis render offline. Relative image and attachment links work when the target file is in the package; other link labels remain text. The selected image and declared checks follow the current text. A manifest link gives the file hashes. The page and its files work offline. By default the ZIP leaves decision feedback and operator names in the native project. When those details are intended for the recipient, add `--include-feedback` to include the latest decision only. Review notes written in the actual deliverables and declared check fields remain part of those materials.

The ZIP contains explicitly listed deliverables and the selected current candidate, using their relative project hierarchy under `files/`. Its `manifest.json` reports each member hash, decision status and declared checks. Other candidates and raw evidence stay in the project unless deliberately listed as deliverables. A pending selection or check stays visible in a draft reading package. Use a new output name for each revision. ZIP creation checks the actual bytes, rejects concurrent changes to the review, and preserves an existing archive. It publishes the completed local ZIP via an exclusive hard link. On FAT/exFAT or a network share that lacks hard links, create it on a hard-link-capable project or temporary volume and then copy the completed ZIP to the destination.
