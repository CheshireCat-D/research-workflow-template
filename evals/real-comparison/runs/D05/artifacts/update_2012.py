#!/usr/bin/env python3
"""Audit supplied year slices and score the unchanged 2011 calendar means.

No fit function is called. Training rows are read solely to verify saved sums,
counts and means. Both years' evaluation calls reuse the original algorithm.
"""
import argparse
import collections
import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics
import sys
import time

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    start = time.perf_counter()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--prior-results', type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parent
    code = root/'analyze.py'
    spec = importlib.util.spec_from_file_location('frozen_analysis', code)
    a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=False)
    manifest_path = args.input_dir/'INPUT_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    inputs = {}
    datasets = {}
    audits = {}
    for year in (2011, 2012):
        folder = out/f'quality_{year}'
        folder.mkdir()
        hp = args.input_dir/f'data/hour_{year}.csv'
        dp = args.input_dir/f'data/day_{year}.csv'
        hf, hr = a.read_csv(hp)
        df, dr = a.read_csv(dp)
        for path, rows in ((hp,hr),(dp,dr)):
            name = path.relative_to(args.input_dir).as_posix()
            inputs[name] = sha(path)
            assert inputs[name] == manifest[name]['sha256']
            assert len(rows) == manifest[name]['data_rows']
        h = a.schema_audit(hf,hr,['dteday','hr'])
        d = a.schema_audit(df,dr,['dteday'])
        assert not any(h[k] or d[k] for k in ('duplicate_keys','blank_cells','count_identity_failures'))
        assert all(r['dteday'].startswith(f'{year}-') and int(r['yr']) == year-2011 for r in hr+dr)
        byday = collections.defaultdict(list)
        for r in hr:
            byday[r['dteday']].append(r)
        dates = a.date_range(f'{year}-01-01',f'{year}-12-31')
        daily = {r['dteday']:r for r in dr}
        coverage = []
        missing = []
        conflicts = []
        for day in dates:
            hours = {int(r['hr']) for r in byday[day]}
            absent = sorted(set(range(24))-hours)
            coverage.append({'dteday':day,'hours':len(byday[day]),'distinct_hours':len(hours),
                             'missing_hours':','.join(map(str,absent))})
            missing.extend({'dteday':day,'hr':hour} for hour in absent)
        discrepancies = []
        for day in sorted(set(byday)|set(daily)):
            for col in ('casual','registered','cnt'):
                observed = sum(int(r[col]) for r in byday[day])
                day_value = int(daily[day][col]) if day in daily else None
                if observed != day_value:
                    discrepancies.append({'dteday':day,'field':col,'hour_sum':observed,'day_value':day_value})
        for row in hr+dr:
            weekday = (dt.date.fromisoformat(row['dteday']).weekday()+1)%7
            working = int(weekday not in (0,6) and int(row['holiday']) == 0)
            if int(row['weekday']) != weekday or int(row['workingday']) != working:
                conflicts.append(row['dteday'])
        h.update({'expected_calendar_hours':24*len(dates),'missing_calendar_hours':len(missing),
                  'hours_per_day_distribution':dict(sorted(collections.Counter(len(byday[day]) for day in dates).items())),
                  'complete_24h_dates':sum(x['hours']==24 and x['distinct_hours']==24 for x in coverage),
                  'missing_calendar_dates':[day for day in dates if not byday[day]],
                  'invalid_hours':sum(not 0<=int(r['hr'])<=23 for r in hr),
                  'chronological_order':[(r['dteday'],int(r['hr'])) for r in hr] == sorted((r['dteday'],int(r['hr'])) for r in hr),
                  'cnt_total':sum(int(r['cnt']) for r in hr),
                  'cnt_min':min(int(r['cnt']) for r in hr),'cnt_max':max(int(r['cnt']) for r in hr)})
        d.update({'cnt_total':sum(int(r['cnt']) for r in dr),
                  'missing_calendar_dates':sorted(set(dates)-set(daily)),
                  'daily_mean':statistics.mean(int(r['cnt']) for r in dr)})
        audit = {'hour':h,'day':d,'hour_day_discrepancies':discrepancies,
                 'calendar_field_conflicts':conflicts,
                 'calendar_fields_constant_within_date':all(all(len({r[c] for r in rs})==1 for c in ('workingday','holiday','weekday')) for rs in byday.values()),
                 'hour_day_calendar_conflicts':sum(any(r[c]!=daily[day][c] for r in rs for c in ('workingday','holiday','weekday')) for day,rs in byday.items()),
                 'input_hashes':{'hour':sha(hp),'day':sha(dp)}}
        a.write_csv(folder/'calendar_coverage.csv',coverage,list(coverage[0]))
        a.write_csv(folder/'missing_calendar_hours.csv',missing,['dteday','hr'])
        a.write_json(folder/'audit.json',audit)
        datasets[year] = (hr,dr)
        audits[year] = audit

    model_hash = sha(args.model)
    model = json.loads(args.model.read_text(encoding='utf-8'))
    assert model_hash == 'dba591a44fff2d14514b4b38d00c8985e93f41cf2b1ab684a6abd2f2620d078d'
    assert model['training_input_sha256'] == inputs['data/hour_2011.csv']
    train = [r for r in datasets[2011][0] if r['dteday'] < '2011-10-01']
    assert (min(r['dteday'] for r in train),max(r['dteday'] for r in train),len(train),len({r['dteday'] for r in train})) == (
        model['training_start'],model['training_end'],model['training_rows'],model['training_dates'])
    groups = {'C0':collections.defaultdict(list),'C1':collections.defaultdict(list)}
    for r in train:
        groups['C0'][str(int(r['hr']))].append(int(r['cnt']))
        groups['C1'][f"{int(r['workingday'])},{int(r['hr'])}"].append(int(r['cnt']))
    for name in ('C0','C1'):
        assert set(groups[name]) == set(model[name])
        for key, values in groups[name].items():
            saved = model[name][key]
            assert saved['sum'] == sum(values) and saved['n'] == len(values)
            assert saved['mean'] == statistics.mean(values)
    summary = {key:model[key] for key in model if key not in ('C0','C1')}
    summary.update({'model_sha256':model_hash,'parameter_groups':{name:len(model[name]) for name in ('C0','C1')},
                    'training_count_total':sum(int(r['cnt']) for r in train),
                    'all_72_sums_counts_means_verified':True,
                    'C0_n_range':[min(x['n'] for x in model['C0'].values()),max(x['n'] for x in model['C0'].values())],
                    'C1_n_range':[min(x['n'] for x in model['C1'].values()),max(x['n'] for x in model['C1'].values())],
                    'parameter_examples':{'C0_08':model['C0']['8'],'C1_0_08':model['C1']['0,8'],'C1_1_08':model['C1']['1,8']},
                    'parameter_update':False,'2012_used_to_recover_parameters':False})
    a.write_json(out/'model_recovery.json',summary)

    holdout = [r for r in datasets[2011][0] if '2011-10-01'<=r['dteday']<='2011-12-31']
    replay = out/'history_replay'
    replay.mkdir()
    history = a.evaluate(a.predict(holdout,model),replay)
    original = json.loads((args.prior_results/'results.json').read_text(encoding='utf-8'))
    assert history == original
    replay_checks = {}
    for name in ('predictions.csv','daily_errors.csv','bootstrap_7d.csv','bootstrap_28d.csv'):
        replay_checks[name] = sha(replay/name) == sha(args.prior_results/name)
        assert replay_checks[name]

    predicted = a.predict(datasets[2012][0],model)
    result = a.evaluate(predicted,out)
    import sklearn
    from sklearn.metrics import mean_absolute_error, root_mean_squared_error
    metric_checks = {}
    for i in (0,1):
        y = [r['cnt'] for r in predicted]
        pred = [r[f'C{i}'] for r in predicted]
        for metric, function in (('MAE',mean_absolute_error),('RMSE',root_mean_squared_error)):
            measured = float(function(y,pred))
            expected = result['all_observed'][f'C{i}'][metric]
            assert math.isclose(measured,expected,rel_tol=1e-12,abs_tol=1e-12)
            metric_checks[f'C{i}_{metric}'] = measured
    annual = []
    for year in (2011,2012):
        audit = audits[year]
        annual.append({'year':year,'observed_hours':audit['hour']['rows'],'observed_dates':audit['day']['rows'],
                       'cnt_total':audit['day']['cnt_total'],'daily_mean':audit['day']['daily_mean']})
    growth = {'annual_total_growth':annual[1]['cnt_total']/annual[0]['cnt_total']-1,
              'daily_mean_growth':annual[1]['daily_mean']/annual[0]['daily_mean']-1}
    a.write_json(out/'annual.json',{'years':annual,**growth})
    a.write_csv(out/'annual.csv',annual,list(annual[0]))
    table = []
    for year,results in (('2011_holdout',history),('2012_all',result)):
        for subset,values in [('all_observed',results['all_observed']),('complete_24h_dates',results['complete_24h_dates']),
                              ('workingday_0',results['workingday']['0']),('workingday_1',results['workingday']['1'])]:
            row = {'period':year,'subset':subset,'hours':values['hours'],'dates':values['dates']}
            for name in ('C0','C1'):
                for key,value in values[name].items():
                    row[f'{name}_{key}'] = value
            row.update({k:v for k,v in values.items() if k not in ('C0','C1','hours','dates')})
            table.append(row)
    a.write_csv(out/'metric_comparison.csv',table,list(table[0]))
    assert sha(args.model) == model_hash
    a.write_json(out/'verification.json',{'status':'passed','training_parameters_verified':72,
                   'history_results_equal':history==original,'history_csv_byte_equality':replay_checks,
                   'sklearn_version':sklearn.__version__,'independent_2012_metric_values':metric_checks,
                   'model_hash_unchanged':True,'model_sha256':model_hash})
    provenance = {'input_hashes':inputs,'input_manifest_sha256':sha(manifest_path),
                  'code_hashes':{'update_2012.py':sha(__file__),'analyze.py':sha(code)},
                  'model_sha256':model_hash,'prior_results_sha256':sha(args.prior_results/'results.json'),
                  'refit':False,'seed':a.SEED,'B':a.B,'block_days':[7,28],
                  'bootstrap_interval':'percentile, linear interpolation at (B-1)*p; p=0.025,0.975',
                  'python':sys.version,'argv':sys.argv,'seconds':time.perf_counter()-start}
    a.write_json(out/'provenance.json',provenance)
    print(json.dumps({'annual':{'years':annual,**growth},'model_recovery':summary,
                      '2012_audit':audits[2012],'2012_results':result,
                      'verification':'passed'},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
