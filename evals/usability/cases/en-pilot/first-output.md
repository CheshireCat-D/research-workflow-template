# Advisor discussion note: synthetic CS pilot

Across three supplied synthetic seeds, candidate mean accuracy was 80.67% versus 79.00% for baseline: a gain of 1.67 percentage points. Mean training time rose from 19.0 to 21.0 seconds (+2.0 seconds; +10.5%). This is a small illustrative accuracy/time tradeoff in the supplied file.

| Seed | Baseline accuracy | Candidate accuracy | Difference | Baseline time | Candidate time |
|---|---:|---:|---:|---:|---:|
| 1 | 78.0% | 81.0% | +3.0 pp | 18 s | 21 s |
| 2 | 80.0% | 82.0% | +2.0 pp | 20 s | 22 s |
| 3 | 79.0% | 79.0% | +0.0 pp | 19 s | 20 s |

Candidate had higher accuracy in two rows and tied in one; every candidate row took longer to train. Differences are matched by seed ID for description. The CSV does not establish common splits, independent runs, timing conditions, sample counts, or uncertainty of the underlying accuracy estimates. These are synthetic pilot observations, so this table provides no real-benchmark performance claim or significance result.

## Tomorrow's decision and next steps

1. Discuss whether an illustrative +1.67 pp accuracy gain would justify roughly 10.5% more training time; choose a primary metric and an acceptable time budget before a real comparison.
2. Select one real task and document the dataset/version, fixed train/validation/test split, preprocessing fitted on training data only, baseline/candidate versions, hardware, and timing procedure.
3. Prespecify the seed list and run both methods under the same protocol, retaining every run and failure. Verify that seed matching means comparable conditions before paired inference; choose the number of runs to match the precision needed for the advisor's decision.
4. Re-run the analysis on the resulting data, report variability and the accuracy/time tradeoff, and decide whether a larger study is warranted. Keep this synthetic pilot separate from those results.

## Reproduce and resume

From the project directory, run `python3 scripts/analyze_pilot.py` to regenerate the descriptive outputs. The preserved input is `data/results.csv`; machine-readable results are `outputs/summary.json` and `outputs/seed_differences.csv`.

Next time run `python3 .agents/skills/_rw-runtime/tools/research.py resume --root .` first. Then complete the real-run protocol in `notes/next-run-protocol.md` with the advisor. No real benchmark has been run.
