# Independent check of the public penguin example

The frozen descriptive analysis passed the independent numerical and content review: 92 checks, no failures, and no required scientific correction. The largest absolute numerical difference was 4.547473508864641e-12 g, within the 1e-8 comparison tolerance. The reviewed Python analysis was read after the independent calculations; it was neither imported nor executed to obtain those calculations.

## Scientific result

The input contains 344 records; 333 have species, sex and body mass available and also support the island-by-year analysis. Sex is missing for 11 records, mass for two, with both missing for those same two records. Thus 11 records are excluded, rather than the sum of the two missing counts.

|Species|Male minus female mean / g|Comparable strata, all positive|Stratum minimum–maximum / g|Common-weight difference / g|Unknown-sex assignment range / g|
|---|---:|---:|---:|---:|---:|
|Adelie|674.7|9|300.0–833.1|676.3|627.2–677.8|
|Chinstrap|411.8|3|250.0–655.6|411.8|411.8–411.8|
|Gentoo|805.1|3|724.5–934.2|805.0|749.9–811.0|

The full 27-cell species-by-island-by-year grid has 15 comparable strata and 12 without observations. Empty cells are not zero differences. Adelie covers all three islands; Chinstrap only Dream; Gentoo only Biscoe. The data's year field covers 2007–2009. All observed stratum differences are positive, while their magnitudes vary; this is sample-level directional consistency, not evidence of equal magnitudes.

Group counts, means, sample standard deviations, medians and ranges; stratum identities and counts; all 344 row masks and missing reasons; common-weight estimates; exhaustive unknown-sex assignments; and the rounded manuscript/SVG numbers agreed with the independent results. The assignment ranges enumerate 32, one and 16 possible assignments of known masses with missing sex. They are not confidence intervals. The manuscript appropriately limits its conclusions to this observational sample, distinguishes single-island coverage, and proposes checking individual/nest identifiers, sampling and measurement timing before population inference. It does not claim randomization, verified independence, significance, causality or reproduction of the original paper's model.

## Reproduce the independent calculations

Download the simplified CSV from this pinned source:

<https://raw.githubusercontent.com/allisonhorst/palmerpenguins/8957207b78d6ccd1b4654a9dd9c9041b657478ab/inst/extdata/penguins.csv>

Its SHA-256 must be:

```text
f204db2c753b0937caac3cb35258562c14f073e4bbc76be24b4c51ce22767a93
```

From the repository root, using an existing R installation:

```sh
Rscript evals/public-data/independent_check.R PATH-TO-DATA.csv NEW-OUTPUT
```

Both arguments are required. The output directory must not exist and its parent must exist. The script uses base R only and does not download data. The repository does not bundle the raw CSV or the generated row audit; a local run produces the full independent numerical outputs for inspection.

The portable script was actually run on the same verified real CSV with R 4.6.1 into a fresh directory. All eight resulting CSVs matched the original independent R outputs cell for cell and byte for byte. CSV line endings were checked separately: both independent runs used LF, with no line-ending difference. Calls without arguments and with an existing output directory were rejected. Only the shebang, explicit arguments and output-creation guard changed from the originally executed R script; the scientific calculation body is unchanged.

## Evidence and scope

The compact provenance projection is retained without field changes at `recording.json` → `independent_review.frozen_assessment`. It records the original input, reviewed code/plan/output hashes, original assessment hashes, original and portable R script hashes, and the 92-check summary. Its original published path, commit and byte hash are retained alongside the object; no separate duplicate JSON is distributed. Complete temporary logs and duplicate numerical tables remain outside the source package.

The nested `current_resources_sha256` identifies resources in that frozen publication, including this report before its record locator changed. The enclosing `published_files` map identifies the files currently distributed. Moving the object does not renew the scientific review or replace its original identities.

The original review first froze its scientific input, code and products, calculated independently, and then compared the frozen products. Those originals remained unchanged. The source metadata was read; this reviewer did not fetch the original paper or verify its study design. The original study's methods and the parent agent's visual check are separate evidence layers. The original SVG check covered XML, labels and coordinates. This reviewer's Quick Look rendering attempt failed with exit 255 (`sandbox initialization failed: invalid data type of path filter; expected pattern, got boolean`), so this assessment does not claim a successful visual layout review.

The hashes bind this assessment to the original frozen analysis. The publication integration's Python CSV line-ending normalization is recorded separately; this assessment is not certification of arbitrary subsequent changes. This is evidence of a local real-data R execution and an independent review. Repository CI's separate offline Python fixture does not rerun the independent R analysis or human/visual review, and does not require R or network access.
