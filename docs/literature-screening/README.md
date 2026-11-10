# Which images show Bennu ejecting particles?

On 6 and 19 January 2019, OSIRIS-REx captured moving particles near asteroid Bennu. Figure 1 of the mission team's paper shows both events. A NASA article describes the same observations, and a later trajectory study uses an overlapping observation window. Counting three publications as three independent observations would misrepresent the evidence. [Original paper, Figure 1 and caption](https://science.gsfc.nasa.gov/sed/content/uploadFiles/publication_files/LaurettaHergenrother2019.pdf)

This example carries a literature screening decision into an RWT checkpoint. The reviewer chooses each report's disposition, records the passage read and writes the relationship to the claim. The [Python companion](prepare_batch.py) converts those decisions into ordinary RWT records, so the next session can see which question still needs work.

| Report | Screening decision | What the reviewer checked |
|---|---|---|
| [Lauretta et al., 2019](https://doi.org/10.1126/science.aay3544) | Include | Figure 1, panels A–D, its caption and the description of particle motion support the two dated events. The images leave the ejection mechanism open. |
| [NASA mission article, 2019](https://www.nasa.gov/missions/nasas-osiris-rex-mission-explains-bennus-mysterious-particle-events/) | Exclude as a second observation | The lead image caption and the reference to the December 6 paper identify the observations being retold. The source and exclusion reason stay in the project. |
| [Chesley et al., 2020](https://doi.org/10.1029/2019JE006363) | Defer | The abstract and introduction describe a longer observation window and an extension of the first analysis. Match the trajectory catalogue to the January image sequences before using it for this claim. |

Three selected reports were screened from a targeted public search on 10 November 2026. The evidence addresses the two events. Their frequency and physical causes remain open. The query, coverage, access levels and checked locations are in the [editable screening sheet](bennu.json).

## Reproduce the handoff

Use Python 3.11+ from the RWT **source checkout**. These commands run offline. Use a new project directory and a new batch filename. On Windows, substitute `py -3 -X utf8` for `python3`.

```sh
python3 tools/research.py init --output ../bennu-project --title "Bennu particle ejections" --language en --method evidence-synthesis
python3 -c "from shutil import copyfile; copyfile('docs/literature-screening/bennu.json', '../bennu-project/bennu.json')"
python3 docs/literature-screening/prepare_batch.py --root ../bennu-project --sheet bennu.json --output ../bennu-batch.json
```

Review the proposed batch. Only the primary paper has a claim relation. Save the reviewed records and the pending follow-up in one registration.

```sh
python3 docs/literature-screening/prepare_batch.py --root ../bennu-project --sheet bennu.json --register ../bennu-batch.json --next-action "Match the Chesley trajectory catalogue to the January images before counting additional observations."
python3 tools/research.py resume --root ../bennu-project
```

The first command saves **nine records** comprising one claim, three sources, two evidence records (the local decision sheet and the selected reading), one claim relation and two activities. The completed activity covers this screening pass. The pending activity holds the deferred report. The response includes `screening_sheet_verified`. A new process can recover the checkpoint, next action and pending activity.

The companion works with a separately unpacked user ZIP. Download [prepare_batch.py](prepare_batch.py) and [bennu.json](bennu.json) from the source repository, adjust their paths above and pass `--runtime PATH/TO/tools/research.py` when registering. The companion uses the existing `register-batch` and `show` commands.

## Use your own reports

Copy the sheet, give the screening pass a fresh `id` and supply your question, actual search coverage, inclusion criterion and a scoped claim. Each row needs a unique `key` and canonical `locator`. Record the version and URL read, the location within it, access level, decision and reason. Resolve DOI aliases, preprints, duplicated data and overlapping reports during screening.

An included report must identify a passage actually examined (`partial` or `full` access) and a reviewer-specified relation with its rationale and scope. The relation may support, qualify, challenge, contextualize or derive the claim. An excluded or deferred report keeps its identity and reason. Only included reports supply claim relations.

`--register` rebuilds the proposed batch from the current sheet and requires it to match the reviewed bytes. It submits those bytes through RWT and checks the digest RWT bound to the local sheet. If the sheet or batch changed before saving, review it and prepare a new batch. An existing record ID is a conflict. Use versioned edits for records already saved.

Keep the sheet stable during registration. The input file can still be edited by another process outside RWT's registry lock. A mismatch between the prepared and registered digests returns a review finding with `registered: true` and `screening_sheet_verified: false`. Inspect the saved records before continuing. After a clean save, changing the project copy of the sheet makes `resume` report the changed file, stale screening activity and stale checkpoint. To revise an existing registration, use the [versioned editing workflow](../07-core-usage.md) after rechecking the affected material. External links need a separate source check when their content changes.

## Recheck the example

```sh
python3 -B -m unittest discover -s tests -p test_literature_screening.py -v
```

The [regression cases](../../tests/test_literature_screening.py) cover relocation and recovery, duplicate imports, metadata-only evidence, deferred sources, changes before and after saving, and an input change during registration. For the comparison that motivated the handoff, see the [external skills review](../13-research-skill-landscape.md).
