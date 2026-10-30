"""Independent numerical checks against saved first-run artifacts; no refitting writes."""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import sklearn
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

root=Path(sys.argv[1]); source=Path(sys.argv[2])
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def rows(path):
    with path.open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))
audit=read(root/'results/audit.json'); result=read(root/'results/results.json')
model=read(root/'results/model.json'); data=rows(source/'data/hour_2011.csv')
manifest=read(source/'INPUT_MANIFEST.json')
for name,spec in manifest.items():
    assert hashlib.sha256((source/name).read_bytes()).hexdigest()==spec['sha256']
    assert len(rows(source/name))==spec['data_rows']
train=[r for r in data if r['dteday']<'2011-10-01']
holdout=[r for r in data if r['dteday']>='2011-10-01']
for hr in range(24):
    assert model['C0'][str(hr)]['mean']==statistics.mean(int(r['cnt']) for r in train if int(r['hr'])==hr)
    for wd in (0,1):
        assert model['C1'][f'{wd},{hr}']['mean']==statistics.mean(int(r['cnt']) for r in train if int(r['hr'])==hr and int(r['workingday'])==wd)
prediction=rows(root/'results/predictions.csv')
assert len(prediction)==len(holdout)==2203
for r,p in zip(holdout,prediction):
    assert (r['dteday'],int(r['hr']),int(r['cnt']))==(p['dteday'],int(p['hr']),int(p['cnt']))
for tag in ('C0','C1'):
    actual=[int(r['cnt']) for r in prediction]; predicted=[float(r[tag]) for r in prediction]
    assert math.isclose(mean_absolute_error(actual,predicted),result['all_observed'][tag]['MAE'],abs_tol=1e-12)
    assert math.isclose(root_mean_squared_error(actual,predicted),result['all_observed'][tag]['RMSE'],abs_tol=1e-12)
assert result==read(root/'replay_check/results.json')
for name in ['predictions.csv','daily_errors.csv','bootstrap_7d.csv','bootstrap_28d.csv']:
    assert (root/'results'/name).read_bytes()==(root/'replay_check'/name).read_bytes()
dates=rows(root/'results/calendar_coverage.csv')
missing_holdout=[r for r in dates if r['dteday']>='2011-10-01' and int(r['rows'])!=24]
summary={'verification':'passed','checks':['input SHA256 and row counts match provided manifest','all 72 saved means match independent statistics.mean','holdout row identities match predictions','MAE and RMSE match sklearn.metrics','frozen score replay results and 4 CSV artifacts match exactly'],
         'sklearn_version':sklearn.__version__,'model_sha256':hashlib.sha256((root/'results/model.json').read_bytes()).hexdigest(),
         'training_hours':len(train),'holdout_hours':len(holdout),'holdout_incomplete_dates':missing_holdout,
         'report_character_count':len((root/'report.md').read_text(encoding='utf-8')) if (root/'report.md').exists() else None}
(root/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
