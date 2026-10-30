"""Independent numerical checks; no network or third party dependencies."""
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import sys

workspace = Path(__file__).resolve().parent
input_dir = Path(sys.argv[1])
with (input_dir / "data/hour_2011.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))
model = json.loads((workspace / "model.json").read_text())
result = json.loads((workspace / "results.json").read_text())
training = [r for r in rows if r["dteday"] < "2011-10-01"]
testing = [r for r in rows if r["dteday"] >= "2011-10-01"]
for h in range(24):
    vals = [int(r["cnt"]) for r in training if int(r["hr"])==h]
    assert model["C0"][str(h)]["mean"] == float(Fraction(sum(vals),len(vals)))
    for w in range(2):
        vals1 = [int(r["cnt"]) for r in training if int(r["hr"])==h and int(r["workingday"])==w]
        assert model["C1"][f"{w},{h}"]["mean"] == float(Fraction(sum(vals1),len(vals1)))
with (workspace / "predictions.csv").open(newline="") as f:
    preds = list(csv.DictReader(f))
assert len(preds) == len(testing) == 2203
for r,p in zip(testing,preds):
    assert (r["dteday"],r["hr"]) == (p["date"],p["hr"])
    assert int(r["cnt"]) == int(p["actual"])
    assert float(p["C0"]) == model["C0"][r["hr"]]["mean"]
    assert float(p["C1"]) == model["C1"][r["workingday"]+","+r["hr"]]["mean"]
for m in ["C0", "C1"]:
    err = [float(p[m])-int(p["actual"]) for p in preds]
    q = result["overall"][m]
    assert math.isclose(q["MAE"],sum(map(abs,err))/len(err),abs_tol=1e-10)
    assert math.isclose(q["RMSE"],math.sqrt(sum(x*x for x in err)/len(err)),abs_tol=1e-10)
    assert math.isclose(q["bias_prediction_minus_actual"],sum(err)/len(err),abs_tol=1e-10)
dates = sorted({p["date"] for p in preds})
bydate = {d:[p for p in preds if p["date"]==d] for d in dates}
maxdiff = 0.0
for length in [7,28]:
    with (workspace / f"bootstrap_L{length}.csv").open(newline="") as f:
        reps = list(csv.DictReader(f))
    assert len(reps)==2000
    rng = random.Random(20261029)
    diffs,relatives = [],[]
    for replicate, recorded in enumerate(reps):
        drawn = []
        for block in range(math.ceil(len(dates)/length)):
            start = rng.randrange(len(dates))
            drawn += [dates[(start+j)%len(dates)] for j in range(length)]
        sampled = [p for d in drawn[:len(dates)] for p in bydate[d]]
        m0 = sum(abs(float(p["C0"])-int(p["actual"])) for p in sampled)/len(sampled)
        m1 = sum(abs(float(p["C1"])-int(p["actual"])) for p in sampled)/len(sampled)
        delta,relative = m0-m1,1-m1/m0
        maxdiff = max(maxdiff,abs(delta-float(recorded["absolute_improvement"])))
        assert int(recorded["n_sampled_hours"]) == len(sampled)
        assert math.isclose(delta,float(recorded["absolute_improvement"]),abs_tol=1e-9)
        assert math.isclose(relative,float(recorded["relative_improvement"]),abs_tol=1e-11)
        diffs.append(delta)
        relatives.append(relative)
    for values,key in [(diffs,"absolute_improvement_95ci"),(relatives,"relative_improvement_95ci")]:
        values.sort()
        for i,p in enumerate([.025,.975]):
            k = 1999*p
            a,b = math.floor(k),math.ceil(k)
            q = values[a]*(b-k)+values[b]*(k-a)
            assert math.isclose(q,result["bootstrap"][str(length)][key][i],abs_tol=1e-9)
verification = {"status":"passed", "python_version":sys.version, "independent_exact_mean_cells":72,
                "prediction_rows_checked":len(preds),"independent_expanded_hour_bootstrap_replicates_checked":4000,
                "bootstrap_max_absolute_delta_discrepancy":maxdiff,
                "report_characters":len((workspace/"report.md").read_text()),
                "model_sha256":hashlib.sha256((workspace/"model.json").read_bytes()).hexdigest()}
(workspace / "verification.json").write_text(json.dumps(verification,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(verification,ensure_ascii=False,indent=2))
