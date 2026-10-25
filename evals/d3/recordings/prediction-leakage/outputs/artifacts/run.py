#!/usr/bin/env python3
"""Deterministic standard-library reproduction. Run: python3 artifacts/run.py."""
from pathlib import Path
import csv
import hashlib
import io
import json
import platform
import sys
import time
import traceback
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts'

def digest(relative):
    raw = (ROOT / relative).read_bytes()
    return {'path':relative, 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}

def write_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def write_csv(name, rows, fields):
    with (OUT / name).open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def analyze(config):
    raw = (ROOT / config['data']).read_bytes()
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8'), newline='')))
    fields = ['record_id','subject_id','site','period','visit','visit_day','event90']
    if not rows or set(rows[0]) != set(fields):
        raise ValueError('missing or additional CSV fields')
    ids = set()
    subject_rows = {}
    for row in rows:
        if set(row) != set(fields) or any(value is None or value == '' for value in row.values()):
            raise ValueError('malformed or missing field')
        if row['record_id'] in ids:
            raise ValueError('duplicate record_id')
        ids.add(row['record_id'])
        for field in ['visit','visit_day','event90']:
            row[field] = int(row[field])
        if row['event90'] not in (0,1):
            raise ValueError('nonbinary outcome')
        subject_rows.setdefault(row['subject_id'], []).append(row)
    for subject, entries in subject_rows.items():
        if len({r['event90'] for r in entries}) != 1:
            raise ValueError('inconsistent subject label: ' + subject)
        if sorted((r['visit'],r['visit_day']) for r in entries) != [(1,0),(2,7)]:
            raise ValueError('expected day0/day7 pair: ' + subject)
    expected = set(config['splits']['S']['train_subjects']) | set(config['splits']['S']['test_subjects'])
    if set(subject_rows) != expected:
        raise ValueError('S split does not cover every input subject')
    subject_predictions = []
    record_predictions = []
    split_results = {}
    for split in ['R','S']:
        if split == 'R':
            training = [r for r in rows if r['visit'] == 1]
            testing = [r for r in rows if r['visit'] == 2]
        else:
            spec = config['splits']['S']
            training = [r for r in rows if r['subject_id'] in spec['train_subjects']]
            testing = [r for r in rows if r['subject_id'] in spec['test_subjects']]
        labels = {r['subject_id']:r['event90'] for r in training}
        prevalence = sum(labels.values()) / len(labels)
        test_subjects = sorted({r['subject_id'] for r in testing})
        overlap = sorted(set(labels) & set(test_subjects))
        grouped = {}
        for row in testing:
            p = float(labels[row['subject_id']]) if row['subject_id'] in labels else prevalence
            record_predictions.append({'split':split,'record_id':row['record_id'],'subject_id':row['subject_id'],'visit':row['visit'],'y':row['event90'],'p':p,'seen_in_training':row['subject_id'] in labels})
            grouped.setdefault(row['subject_id'], []).append((p,row['event90']))
        predictions = []
        for subject in test_subjects:
            values = grouped[subject]
            p = sum(x[0] for x in values) / len(values)
            y = values[0][1]
            predicted = int(p >= config['threshold'])
            pred = {'split':split,'subject_id':subject,'test_records':len(values),'p':p,'y':y,'predicted':predicted,'seen_in_training':subject in labels,'squared_error':(p-y)**2}
            predictions.append(pred)
            subject_predictions.append(pred)
        n = len(predictions)
        bins = []
        for spec in config['bins']:
            members = [p for p in predictions if p['p'] >= spec['lower'] and (p['p'] <= spec['upper'] if spec['right_closed'] else p['p'] < spec['upper'])]
            count = len(members)
            bins.append({'interval':'['+str(spec['lower'])+','+str(spec['upper'])+(']' if spec['right_closed'] else ')'),'n_subjects':count,'mean_predicted_probability':sum(p['p'] for p in members)/count if count else None,'event_rate':sum(p['y'] for p in members)/count if count else None})
        if sum(b['n_subjects'] for b in bins) != n:
            raise ValueError('calibration bin coverage mismatch')
        split_results[split] = {'n_train_records':len(training),'n_train_subjects':len(labels),'n_test_records':len(testing),'n_test_subjects':n,'train_subject_ids':sorted(labels),'test_subject_ids':test_subjects,'n_overlap_subjects':len(overlap),'overlap_subject_ids':overlap,'training_subject_event_rate':prevalence,'accuracy':sum(p['predicted']==p['y'] for p in predictions)/n,'brier_score':sum(p['squared_error'] for p in predictions)/n,'mean_predicted_probability':sum(p['p'] for p in predictions)/n,'observed_event_rate':sum(p['y'] for p in predictions)/n,'calibration_bins':bins,'subject_predictions':predictions,'evaluation_unit':'subject, equal weight'}
    write_csv('subject_predictions.csv',subject_predictions,['split','subject_id','test_records','p','y','predicted','seen_in_training','squared_error'])
    write_csv('record_predictions.csv',record_predictions,['split','record_id','subject_id','visit','y','p','seen_in_training'])
    return {'input_audit':{'n_records':len(rows),'n_subjects':len(subject_rows),'n_outcome_events':sum(entries[0]['event90'] for entries in subject_rows.values()),'sites':sorted({r['site'] for r in rows}),'periods':sorted({r['period'] for r in rows}),'missing_fields':0,'duplicate_record_ids':0,'inconsistent_subject_outcomes':0,'excluded_records':0,'raw_line_ending':'CRLF' if b'\r\n' in raw else 'LF'},'splits':split_results}

def main():
    started=time.perf_counter()
    result={'status':'running','started_utc':datetime.now(timezone.utc).isoformat(),'environment':{'python':sys.version,'executable':Path(sys.executable).name,'platform':platform.platform(),'machine':platform.machine()},'command':'python3 artifacts/run.py','failures':[]}
    code=0
    try:
        config=json.loads((OUT/'config.json').read_text(encoding='utf-8'))
        result['config']=config
        result['input_fingerprints']=[digest(path) for path in config['input_paths']]
        result['execution_fingerprints']=[digest('artifacts/config.json'),digest('artifacts/run.py')]
        result.update(analyze(config))
        result['status']='success'
    except Exception as exc:
        result['status']='failed'
        result['failures'].append({'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
        code=1
    result['elapsed_seconds']=time.perf_counter()-started
    write_json('results.json',result)
    print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],'splits':result.get('splits',{}),'failures':result['failures']},ensure_ascii=False))
    return code

if __name__ == '__main__':
    sys.exit(main())
