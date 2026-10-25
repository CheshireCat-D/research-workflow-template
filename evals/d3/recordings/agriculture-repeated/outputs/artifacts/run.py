#!/usr/bin/env python3
"""Frozen-protocol analysis. Python 3 standard library only; no random sampling.
From PROJECT: python3 artifacts/run.py
Outputs numeric JSON and audited plot/season/block/visit CSV intermediates.
"""
import csv, hashlib, itertools, json, math, statistics, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = time.perf_counter()
def read_csv(rel):
    with (ROOT / rel).open(newline="") as f:
        return list(csv.DictReader(f))
def save_csv(rel, rows):
    with (ROOT / rel).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def mean(x): return statistics.mean(x)
def summarize(x):
    # Four block differences, not plants or visits; t interval is approximate.
    n = len(x); estimate = mean(x); se = statistics.stdev(x) / math.sqrt(n)
    t975_df3 = 3.182446305284263
    null_stats = [mean([s*v for s,v in zip(signs,x)])
                  for signs in itertools.product([-1,1], repeat=n)]
    p = sum(abs(t) >= abs(estimate)-1e-10 for t in null_stats) / len(null_stats)
    return {"block_differences_cm": x, "estimate_cm": estimate, "n_randomized_pairs": n,
            "randomization_se_estimate_cm": se, "approximate_t95_df": n-1,
            "approximate_t95_cm": [estimate-t975_df3*se, estimate+t975_df3*se],
            "exact_sign_flip_two_sided_p": p, "assignments_enumerated": len(null_stats),
            "minimum_possible_two_sided_p": 2/(2**n),
            "exact_additive_shift_95_confidence_set": "all real numbers: only 16 assignments, minimum p=0.125",
            "null_distribution_cm": null_stats}

plots = read_csv("inputs/plots.csv"); observations = read_csv("inputs/observations.csv")
assert len(plots)==8 and len(observations)==192
plotmap={r["plot_id"]:r for r in plots}; assert len(plotmap)==8
blocks=sorted({r["block_id"] for r in plots}); assert len(blocks)==4
for b in blocks:
    pr=[r for r in plots if r["block_id"]==b]
    assert len(pr)==2 and {r["treatment"] for r in pr}=={"mulch","control"}
assert all(r["randomized_before_season"]=="2025" and r["allocation_held_through"]=="2026" for r in plots)
seen=set(); plantsets=defaultdict(set); by_psd=defaultdict(list); data=[]
for row in observations:
    plot=row["plot_id"]; plant=row["plant_id"]; season=int(row["season"]); day=int(row["day"]); height=float(row["canopy_height_cm"])
    assert plot in plotmap and season in [2025,2026] and day in [30,60,90] and math.isfinite(height)
    key=(plot,plant,season,day); assert key not in seen; seen.add(key)
    plantsets[(plot,season,day)].add(plant); by_psd[(plot,season,day)].append(height)
    data.append((plotmap[plot]["block_id"],plot,plant,season,day,plotmap[plot]["treatment"],height))
for plot in plotmap:
    base=plantsets[(plot,2025,30)]; assert len(base)==4
    for season in [2025,2026]:
        for day in [30,60,90]: assert plantsets[(plot,season,day)]==base and len(by_psd[(plot,season,day)])==4
assert len({x[2] for x in data})==32
plot_seasons=[]
for plot in sorted(plotmap):
    for season in [2025,2026]:
        plot_seasons.append({"block_id":plotmap[plot]["block_id"], "plot_id":plot,
                             "treatment":plotmap[plot]["treatment"], "season":season,
                             "day90_mean_cm":mean(by_psd[(plot,season,90)]),"n_plants":4})
lookup={(r["plot_id"],r["season"]):r["day90_mean_cm"] for r in plot_seasons}
plot_primary=[{"block_id":plotmap[plot]["block_id"],"plot_id":plot,"treatment":plotmap[plot]["treatment"],
               "equal_two_season_day90_mean_cm":mean([lookup[(plot,s)] for s in [2025,2026]])} for plot in sorted(plotmap)]
block_rows=[]; visit_rows=[]
for b in blocks:
    ids={r["treatment"]:r["plot_id"] for r in plots if r["block_id"]==b}
    diffs=[lookup[(ids["mulch"],s)]-lookup[(ids["control"],s)] for s in [2025,2026]]
    block_rows.append({"block_id":b,"mulch_plot":ids["mulch"],"control_plot":ids["control"],
                       "difference_2025_cm":diffs[0],"difference_2026_cm":diffs[1],
                       "primary_equal_season_difference_cm":mean(diffs),
                       "season_difference_2026_minus_2025_cm":diffs[1]-diffs[0]})
    for s in [2025,2026]:
        for day in [30,60,90]:
            m=mean(by_psd[(ids["mulch"],s,day)]);c=mean(by_psd[(ids["control"],s,day)])
            visit_rows.append({"block_id":b,"season":s,"day":day,"mulch_plot_mean_cm":m,"control_plot_mean_cm":c,"difference_cm":m-c})
primary=summarize([r["primary_equal_season_difference_cm"] for r in block_rows])
s2025=summarize([r["difference_2025_cm"] for r in block_rows]);s2026=summarize([r["difference_2026_cm"] for r in block_rows])
interaction=summarize([r["season_difference_2026_minus_2025_cm"] for r in block_rows])
allvisit=summarize([mean([v["difference_cm"] for v in visit_rows if v["block_id"]==b]) for b in blocks])
by_t={t:[r[6] for r in data if r[5]==t] for t in ["mulch","control"]}
naive_diff=mean(by_t["mulch"])-mean(by_t["control"])
naive_se=math.sqrt(sum(statistics.variance(by_t[t])/len(by_t[t]) for t in by_t))
trajectory=[{"season":s,"day":d,"mean_block_difference_cm":mean([v["difference_cm"] for v in visit_rows if v["season"]==s and v["day"]==d])} for s in [2025,2026] for d in [30,60,90]]
result={"input_sha256":{rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel in ["inputs/protocol.md","inputs/plots.csv","inputs/observations.csv"]},
        "design":{"blocks":4,"randomized_plots":8,"independent_randomized_pairs":4,"plants":32,"rows":192,"seasons":2,"visits_per_season":3,"treatment_reassigned_between_seasons":False,"complete_no_replacement":True},
        "estimand":"Equal weight over this site's four blocks and specified 2025/2026 seasons; mulch minus control at day 90 after averaging 4 plants per plot-season. Randomization targets paired finite-plot treatment effect, assuming no cross-plot interference and a well-defined held treatment.",
        "inference_notes":["Enumeration flips both seasons jointly within each original block; plant/day/season rows are never independent treatment replicates.","Sign-flip p is exact for the endpoint-specific sharp null, not the weak null of zero average heterogeneous effect.","The t(df=3) interval uses sample SD of four block differences/2 and a small-sample working approximation; no exact 95% coverage claim. Sample variance includes possible block effect heterogeneity.","For the change endpoint the sharp null means no treatment effect on the 2026-minus-2025 within-plot change, allowing equal effects across seasons.","Additive-shift inversion at two-sided alpha=.05 cannot exclude any value with 4 pairs; the exact 95% set is uninformative.","Season-specific and interaction comparisons were specified but no multiplicity-adjusted confirmatory claim is made."],
        "primary":primary,"season_2025":s2025,"season_2026":s2026,"season_difference_2026_minus_2025":interaction,
        "trajectory_descriptive":trajectory,
        "draft_diagnostic":{"all_visit_equal_weight_effect":allvisit,"naive_192_independent_rows":{"status":"invalid inference; diagnostic only","n_per_treatment":{t:len(by_t[t]) for t in by_t},"estimate_cm":naive_diff,"invalid_independence_se_cm":naive_se,"invalid_normal95_cm":[naive_diff-1.96*naive_se,naive_diff+1.96*naive_se]},"reason":"All-visit pooling changes the endpoint. Its sign and interval cannot replace the frozen mature day-90 two-season endpoint."},
        "configuration":{"seed":"not applicable: deterministic complete enumeration","stdlib_only":True,"excluded_rows":0,"imputed_rows":0,"assertions":"design completeness and full repeated plant identity checked"}}
save_csv("artifacts/plot_season.csv",plot_seasons);save_csv("artifacts/plot_primary.csv",plot_primary)
save_csv("artifacts/block_contrasts.csv",block_rows);save_csv("artifacts/visit_contrasts.csv",visit_rows)
(ROOT/"artifacts/results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":"completed","elapsed_seconds":time.perf_counter()-START,"primary_cm":primary["estimate_cm"],"primary_t95_cm":primary["approximate_t95_cm"],"primary_randomization_p":primary["exact_sign_flip_two_sided_p"],"season_2025_cm":s2025["estimate_cm"],"season_2026_cm":s2026["estimate_cm"],"season_difference_cm":interaction["estimate_cm"],"all_visit_effect_cm":allvisit["estimate_cm"],"files_written":["artifacts/results.json","artifacts/plot_season.csv","artifacts/plot_primary.csv","artifacts/block_contrasts.csv","artifacts/visit_contrasts.csv"]},ensure_ascii=False))
