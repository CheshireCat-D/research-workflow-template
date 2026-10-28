#!/usr/bin/env python3
"""Offline last-value query comparison. Python 3.11+, standard library only.

Run: python run.py --input-dir DIR --output-dir NEW
The contract counts logical key comparisons, index writes and lookups,
not elapsed time or Python interpreter instructions. Each workload builds
its own index once. Validation operations are separate from route costs.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def linear(records, queries):
    values, steps = [], []
    for key in queries:
        value, comparisons = None, 0
        for record_key, record_value in records:
            comparisons += 1
            if key == record_key:
                value = record_value
        values.append(value)
        steps.append(comparisons)
    return values, steps


def indexed(records, queries):
    index, writes, construction = {}, 0, []
    for position, (key, value) in enumerate(records, 1):
        # Trace is correctness evidence, not an additional cost-model unit.
        previous = index.get(key)
        index[key] = value
        writes += 1
        construction.append({'record_position': position, 'key': key,
                             'value': value, 'previous_value': previous})
    values, lookups = [], 0
    for key in queries:
        values.append(index.get(key))
        lookups += 1
    return values, writes, lookups, construction, index


def reference(records, key):
    # Independent correctness oracle: first match from the right.
    return next((value for record_key, value in reversed(records)
                 if record_key == key), None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    if args.output_dir.exists() or args.output_dir.is_symlink():
        parser.error('output directory must not already exist')
    input_paths = {name: args.input_dir/name for name in
                   ['task.md', 'contract.md', 'records.csv', 'queries.json', 'draft.md']}
    before = {name: sha256(path) for name, path in input_paths.items()}
    # Explicitly reread the supplied semantics and draft as reproducibility inputs.
    contract = input_paths['contract.md'].read_text(encoding='utf-8')
    input_paths['task.md'].read_text(encoding='utf-8')
    input_paths['draft.md'].read_text(encoding='utf-8')
    if not contract.strip():
        raise ValueError('empty contract')
    with input_paths['records.csv'].open(encoding='utf-8',newline='') as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ['key','value']:
            raise ValueError('CSV columns must be key,value')
        records = tuple((row['key'], int(row['value'])) for row in reader)
    workload = json.loads(input_paths['queries.json'].read_text(encoding='utf-8'))
    queries = tuple(workload['queries'])
    lengths = workload['prefix_lengths']
    if not all(isinstance(q,str) for q in queries):
        raise ValueError('queries must be strings')
    if not all(type(m) is int and 0 < m <= len(queries) for m in lengths):
        raise ValueError('prefix lengths must be positive and within queries')
    workloads=[]
    for m in lengths:
        selected=queries[:m]
        lvalues, comparisons = linear(records,selected)
        ivalues, writes, lookups, construction, index = indexed(records,selected)
        expected=[reference(records,q) for q in selected]
        trace=[{'query_position':i,'key':q,'L_value':lv,'I_value':iv,
                'oracle_value':ev,'equal':lv==iv==ev,
                'L_comparisons':lc,'I_lookups':1,'miss':ev is None}
               for i,(q,lv,iv,ev,lc) in enumerate(zip(selected,lvalues,ivalues,expected,comparisons),1)]
        if not all(t['equal'] for t in trace):
            raise AssertionError('route disagreement')
        ltotal=sum(comparisons)
        itotal=writes+lookups
        workloads.append({'query_count':m,'L_build_cost':0,'L_query_cost':ltotal,
                          'L_total_cost':ltotal,'I_build_cost':writes,
                          'I_query_cost':lookups,'I_total_cost':itotal,
                          'L_total_over_I_total':ltotal/itotal if itotal else None,
                          'I_total_lower':itotal<ltotal,
                          'all_returns_equal':True,'query_trace':trace,
                          'I_build_trace':construction,'final_index':index})
    after={name:sha256(path) for name,path in input_paths.items()}
    if before!=after:
        raise AssertionError('input changed during computation')
    n=len(records)
    key_counts=Counter(k for k,v in records)
    query_counts=Counter(queries)
    result={
        'schema_version':'1.0','deterministic':True,
        'semantics':'last record value for duplicate key; null on miss; immutable input',
        'cost_model':{'L':'one comparison per record per query, full forward scan',
                      'I':'one write per record, then one lookup per query',
                      'workload_boundary':'independent cold build for each prefix; no index shared across prefixes',
                      'not_counted':'parsing, validation/oracle, instrumentation, allocation, hashing internals, I/O; no wall-clock speed claim'},
        'input_sha256':before,'inputs_unchanged':before==after,
        'record_count':n,'distinct_keys':len(key_counts),
        'duplicate_record_count':n-len(key_counts),'key_frequencies':dict(key_counts),
        'query_count':len(queries),'query_frequencies':dict(query_counts),
        'repeated_query_occurrences':len(queries)-len(query_counts),
        'all_query_return_values':[reference(records,q) for q in queries],
        'all_query_miss_count':sum(reference(records,q) is None for q in queries),
        'workloads':workloads,
        'algebra':{'L_total':'n*m','I_total':'n+m',
                   'I_strictly_lower_condition':'(n-1)*m > n',
                   'first_integer_m_for_I_strictly_lower':n//(n-1)+1 if n>1 else None,
                   'ratio_upper_limit_for_fixed_n':'n, approached from below as m grows for n>0'},
        'timing':{'measured_performance':False,
                  'note':'execution.json separately records process duration as execution metadata, not route timings'}
    }
    args.output_dir.mkdir(parents=True,exist_ok=False)
    (args.output_dir/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'all_returns_equal':True,'inputs_unchanged':True,
                      'workloads':[{'m':w['query_count'],'L':w['L_total_cost'],'I':w['I_total_cost']} for w in workloads]}))


if __name__=='__main__':
    main()
