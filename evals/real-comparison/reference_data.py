#!/usr/bin/env python3
"""Private scoring reference. Python standard library only; not an executor input.

No weather recoding, observed-value edits, missing-hour imputation, or test refit.
Provide --raw-dir containing the official ZIP and its three members, and --output NEW_DIR.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

RAW = None
OUT = None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def fit(train):
    # Every parameter comes from the pre-2011-10-01 training rows only.
    groups = [defaultdict(list), defaultdict(list)]
    for r in train:
        groups[0][r['hr']].append(int(r['cnt']))
        groups[1][r['workingday'] + ':' + r['hr']].append(int(r['cnt']))
    return {
        'model_version': 1,
        'train_before': '2011-10-01',
        'C0': {k: mean(v) for k, v in sorted(groups[0].items())},
        'C1': {k: mean(v) for k, v in sorted(groups[1].items())},
        'C1_unseen_cell_fallback': 'C0[hr]',
    }


def predict(model, r):
    a = model['C0'][r['hr']]
    b = model['C1'].get(r['workingday'] + ':' + r['hr'], a)
    return a, b


def losses(model, rows):
    g = defaultdict(lambda: [0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    for r in rows:
        y = int(r['cnt'])
        preds = predict(model, r)
        s = g[r['dteday']]
        s[0] += 1
        for m, pred in enumerate(preds):
            err = pred - y
            s[1 + m] += abs(err)
            s[3 + m] += err * err
            s[5 + m] += err
    return [g[k] for k in sorted(g)]


def summarize(day_stats):
    n = sum(x[0] for x in day_stats)
    vals = [sum(x[k] for x in day_stats) for k in range(1, 7)]
    m0, m1 = vals[0] / n, vals[1] / n
    day_m0 = mean(x[1] / x[0] for x in day_stats)
    day_m1 = mean(x[2] / x[0] for x in day_stats)
    return {
        'days': len(day_stats), 'hours': n,
        'C0_MAE': m0, 'C1_MAE': m1,
        'C0_RMSE': math.sqrt(vals[2] / n),
        'C1_RMSE': math.sqrt(vals[3] / n),
        'C0_bias_prediction_minus_actual': vals[4] / n,
        'C1_bias_prediction_minus_actual': vals[5] / n,
        'MAE_reduction_absolute': m0 - m1,
        'MAE_reduction_fraction': 1 - m1 / m0,
        'C0_day_equal_weight_MAE': day_m0,
        'C1_day_equal_weight_MAE': day_m1,
        'day_equal_weight_MAE_reduction_fraction': 1 - day_m1 / day_m0,
        'day_equal_weight_mean_MAE_difference': mean((x[1] - x[2]) / x[0] for x in day_stats),
    }


def quantile(xs, p):
    # Linear interpolation at (B-1)*p, equivalent to common type-7 quantiles.
    xs = sorted(xs)
    pos = (len(xs) - 1) * p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return xs[lo] + (pos - lo) * (xs[hi] - xs[lo])


def bootstrap(day_stats, block_days=7, seed=20261029, B=2000):
    rng = random.Random(seed)
    n_days = len(day_stats)
    absolute, relative = [], []
    for _ in range(B):
        indices = []
        for _ in range(math.ceil(n_days / block_days)):
            start = rng.randrange(n_days)
            indices.extend((start + j) % n_days for j in range(block_days))
        sample = [day_stats[i] for i in indices[:n_days]]
        n = sum(x[0] for x in sample)
        a = sum(x[1] for x in sample)
        b = sum(x[2] for x in sample)
        absolute.append((a - b) / n)
        relative.append(1 - b / a)
    return {
        'method': 'paired circular moving blocks of dates; pooled hourly metric',
        'block_days': block_days, 'B': B, 'seed': seed,
        'absolute_difference_percentile95': [quantile(absolute, p) for p in (0.025, 0.975)],
        'relative_reduction_percentile95': [quantile(relative, p) for p in (0.025, 0.975)],
        'interpretation': 'dependence-sensitive exploratory interval; requires suitable within-period stability',
    }


def audit(rows, daily):
    g = defaultdict(list)
    for r in rows:
        g[r['dteday']].append(r)
    daily_map = {r['dteday']: r for r in daily}
    ysum = sum(int(r['cnt']) for r in rows)
    return {
        'hour_rows': len(rows), 'day_rows': len(daily),
        'unique_dates_hour': len(g),
        'duplicate_date_hour_pairs': len(rows) - len({(r['dteday'], r['hr']) for r in rows}),
        'blank_cell_count_hour': sum(v == '' for r in rows for v in r.values()),
        'blank_cell_count_day': sum(v == '' for r in daily for v in r.values()),
        'full24_dates': sum(len(rs) == 24 for rs in g.values()),
        'hours_per_date_frequency': dict(sorted(Counter(len(rs) for rs in g.values()).items())),
        'absent_calendar_hour_slots': 24 * len(daily) - len(rows),
        'cnt_total_hour': ysum,
        'cnt_total_day': sum(int(r['cnt']) for r in daily),
        'cnt_identity_violations_hour': sum(int(r['cnt']) != int(r['casual']) + int(r['registered']) for r in rows),
        'cnt_identity_violations_day': sum(int(r['cnt']) != int(r['casual']) + int(r['registered']) for r in daily),
        'hour_to_day_cnt_disagreement_dates': sum(sum(int(r['cnt']) for r in rs) != int(daily_map[date]['cnt']) for date, rs in g.items()),
        'daily_mean_count': mean(int(r['cnt']) for r in daily),
        'rare_partial_dates': [{'date': date, 'hours': len(rs), 'cnt': sum(int(r['cnt']) for r in rs)} for date, rs in sorted(g.items()) if len(rs) < 18],
        'leaky_casual_plus_registered_MAE': mean(abs(int(r['cnt']) - int(r['casual']) - int(r['registered'])) for r in rows),
    }


def phase_output(model, rows, daily):
    ds = losses(model, rows)
    overall = summarize(ds)
    hourly_subgroups = {}
    for f in ('workingday', 'weathersit'):
        for v in sorted({r[f] for r in rows}):
            hourly_subgroups[f + '=' + v] = summarize(losses(model, [r for r in rows if r[f] == v]))
    return {
        'audit': audit(rows, daily),
        'overall': overall,
        'bootstrap7': bootstrap(ds, 7),
        'bootstrap28': bootstrap(ds, 28),
        'full24_dates_sensitivity': summarize([x for x in ds if x[0] == 24]),
        'subgroups': hourly_subgroups,
        'prediction_digest': hashlib.sha256(json.dumps([(r['dteday'], r['hr'], *predict(model, r)) for r in rows], separators=(',', ':')).encode()).hexdigest(),
    }


def main():
    global RAW, OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    RAW, OUT = args.raw_dir, args.output
    OUT.mkdir(exist_ok=False)
    hours = read(RAW / 'hour.csv')
    days = read(RAW / 'day.csv')
    train = [r for r in hours if r['dteday'] < '2011-10-01']
    holdout = [r for r in hours if '2011-10-01' <= r['dteday'] < '2012-01-01']
    new = [r for r in hours if r['dteday'] >= '2012-01-01']
    model = fit(train)
    model_path = OUT / 'reference_frozen_model.json'
    model_path.write_text(json.dumps(model, indent=2, sort_keys=True) + '\n')
    # Reload serialized artifact before 2012 evaluation: no retraining.
    frozen = json.loads(model_path.read_text())
    answer = {
        'protocol': {'train': ['2011-01-01', '2011-09-30'], 'holdout': ['2011-10-01', '2011-12-31'], 'external': ['2012-01-01', '2012-12-31'], 'threshold_fraction': 0.10, 'bias_sign': 'prediction minus actual', 'weather_used': False},
        'raw_sha256': {n: sha(RAW / n) for n in ('uci-bike-sharing.zip', 'hour.csv', 'day.csv', 'Readme.txt')},
        'model_file_sha256': sha(model_path),
        'train': audit(train, [r for r in days if r['dteday'] < '2011-10-01']),
        'year2011': audit([r for r in hours if r['yr'] == '0'], [r for r in days if r['yr'] == '0']),
        'phase1': phase_output(model, holdout, [r for r in days if '2011-10-01' <= r['dteday'] < '2012-01-01']),
        'phase2': phase_output(frozen, new, [r for r in days if r['yr'] == '1']),
        'daily_mean_year_growth_fraction': mean(int(r['cnt']) for r in days if r['yr'] == '1') / mean(int(r['cnt']) for r in days if r['yr'] == '0') - 1,
        'total_year_growth_fraction': sum(int(r['cnt']) for r in hours if r['yr'] == '1') / sum(int(r['cnt']) for r in hours if r['yr'] == '0') - 1,
    }
    answer_path = OUT / 'reference_answers.json'
    answer_path.write_text(json.dumps(answer, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: {'overall': answer[k]['overall'], 'bootstrap7': answer[k]['bootstrap7'], 'bootstrap28': answer[k]['bootstrap28'], 'full24': answer[k]['full24_dates_sensitivity']} for k in ('phase1', 'phase2')}, indent=2))


if __name__ == '__main__':
    main()
