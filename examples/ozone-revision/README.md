# Which ozone estimates change after a revised reading?

In 1973, afternoon ozone was measured at Roosevelt Island and daily maximum temperature at LaGuardia Airport. Compare observed ozone on hot (at least 85 °F) and cooler days from May through September. May has no hot days, so the primary estimate gives June, July, August and September equal weight. June has ozone readings on just two of its six hot days. [Official data and measurement definitions](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/airquality.html)

Using the original measurements, the primary difference is **+40.16 ppb**. Pooling measured days over the same four months gives **+45.38 ppb**. Pooling over all five months gives **+47.90 ppb**. The experiment changes May 1 from 41 to 42 ppb in a separate in-memory copy. Only the five-month pooled difference changes, to **+47.88 ppb**. The edit is simulated. The estimates describe measured days at these sites.

From the extracted user toolkit or source checkout, run with Python 3.11+ and base R. The analysis uses R's bundled `datasets::airquality` and writes two labeled versions under the new project. Each includes the estimate and coverage tables, brief, editable figure, caption and single-page PDF.

```sh
python3 tools/research.py init --output ../ozone-project --title "New York ozone revision" --connect-skills
Rscript --vanilla examples/ozone-revision/run_case.R ../ozone-project/results
cd ../ozone-project
python3 .agents/skills/rw-validation/scripts/compare_results.py results/observed/estimates.csv results/simulation/estimates.csv
python3 .agents/skills/rw-figures/scripts/check_result_surfaces.py results/simulation/checks.json
```

The comparison matches stable estimate IDs at the precision of the tables. Two estimates should be unchanged and one changed. The five text checks compare the primary value in the brief, all three values printed in the SVG, and both June denominators in the caption. To inspect the PDF with Poppler installed, add `--render brief.pdf --page 1 --output preview.png` to the last command and open the PNG. The scientific calculation and text checks also run without Poppler.

To exercise a stale figure, copy `results/simulation` to a new directory, replace only its `figure.svg` with `results/observed/figure.svg`, and check the copy's `checks.json`. The five-month value should fail while the primary, four-month value and caption still match.

## When old and new tables use different layouts

The first brief's main table used groups as rows. The revision used the study role as its row label and added the weighting and time window. These excerpts include the columns the adapter needs. Additional original columns may remain in place.

`pooled.csv`

```csv
group,mean_ozone_ppb,hot_minus_other_ppb
Hot,77.23,
Other,29.33,
Hot minus other,,47.90
```

`estimates.csv`

```csv
role,weighting,months,hot_minus_other_ppb
Primary,Equal supported months,Jun Jul Aug Sep,40.16
Sensitivity,Equal measured days within group,Jun Jul Aug Sep,45.38
Previous primary,Equal measured days within group,May Jun Jul Aug Sep,47.90
```

From the toolkit root, supply either the original tables or the excerpts saved under those filenames. Choose a new output directory.

```sh
python3 examples/ozone-revision/adapt_legacy.py pooled.csv estimates.csv comparison-inputs
python3 skills/rw-validation/scripts/compare_results.py comparison-inputs/old.csv comparison-inputs/new.csv
```

The mapping uses the first brief's definition of “Hot minus other” as a pooled May–September contrast in ppb. It checks the revision's named periods and weights, and records the original file hashes, chosen IDs and exclusions in `mapping.json`. The separate Hot and Other means are outside this comparison. The result is **one unchanged and two added to the supplied tables**. The first brief already described the equal-month figure as a secondary check in prose. If that passage is also included as declared evidence, the unchanged results are the all-month and equal-month contrasts; the supported-month pooled comparison is newly reported. Adapt the explicit mappings to another study only after checking its own definitions.
