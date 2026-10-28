#!/usr/bin/env python3
"""Recompute cage-level 2 x 2 descriptive contrasts using Python stdlib."""
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(input_dir):
    source = input_dir / 'observations.csv'
    cages = defaultdict(list)
    seen_animals = set()
    row_count = 0
    with source.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['block', 'cage', 'F', 'E', 'animal', 'gain']:
            raise ValueError('Unexpected CSV columns')
        for row in reader:
            row_count += 1
            if any(value is None or value == '' for value in row.values()):
                raise ValueError('Missing value')
            f, e = int(row['F']), int(row['E'])
            gain = float(row['gain'])
            if f not in (0, 1) or e not in (0, 1) or not math.isfinite(gain):
                raise ValueError('Invalid factor level or gain')
            identity = (row['block'], row['cage'], row['animal'])
            if identity in seen_animals:
                raise ValueError('Duplicate animal within cage')
            seen_animals.add(identity)
            cages[(row['block'], row['cage'])].append((f, e, row['animal'], gain))
    if not cages:
        raise ValueError('No observations')
    cage_ids = [key[1] for key in cages]
    if len(cage_ids) != len(set(cage_ids)):
        raise ValueError('Cage identifier reused across blocks')
    cage_summary = []
    by_block = defaultdict(dict)
    by_cell = defaultdict(list)
    for (block, cage), observations in sorted(cages.items()):
        levels = {(o[0], o[1]) for o in observations}
        if len(levels) != 1:
            raise ValueError('A cage received multiple factor combinations')
        if len(observations) != 2:
            raise ValueError('Design requires two animals per cage')
        f, e = next(iter(levels))
        if (f, e) in by_block[block]:
            raise ValueError('Multiple cages for one block x treatment cell')
        gains = [o[3] for o in observations]
        avg = mean(gains)
        record = {'block': block, 'cage': cage, 'F': f, 'E': e,
                  'n_animals': len(gains), 'mean_gain_g': avg,
                  'animal_gains_g': gains, 'within_cage_sample_sd_g': stdev(gains)}
        cage_summary.append(record)
        by_block[block][(f, e)] = avg
        by_cell[(f, e)].append(record)
    expected = {(0, 0), (1, 0), (0, 1), (1, 1)}
    block_results = []
    for block, cell in sorted(by_block.items()):
        if set(cell) != expected:
            raise ValueError('Incomplete block: all four cells required')
        y00, y10, y01, y11 = (cell[k] for k in [(0,0),(1,0),(0,1),(1,1)])
        block_results.append({'block': block,
            'cell_means_g': {f'F{f}E{e}': cell[(f,e)] for f,e in [(0,0),(1,0),(0,1),(1,1)]},
            'cages_per_cell': {f'F{f}E{e}': 1 for f,e in sorted(expected)},
            'F_simple_at_E0_g': y10-y00, 'F_simple_at_E1_g': y11-y01,
            'E_simple_at_F0_g': y01-y00, 'E_simple_at_F1_g': y11-y10,
            'F_marginal_g': ((y10+y11)-(y00+y01))/2,
            'E_marginal_g': ((y01+y11)-(y00+y10))/2,
            'interaction_g': (y11-y01)-(y10-y00)})
    cell_results = []
    for (f,e), records in sorted(by_cell.items()):
        cell_results.append({'F': f, 'E': e, 'n_cages': len(records),
            'n_animal_records': sum(r['n_animals'] for r in records),
            'equal_cage_mean_gain_g': mean(r['mean_gain_g'] for r in records)})
    metrics = ['F_simple_at_E0_g','F_simple_at_E1_g','E_simple_at_F0_g',
               'E_simple_at_F1_g','F_marginal_g','E_marginal_g','interaction_g']
    overall = {name: mean(r[name] for r in block_results) for name in metrics}
    spread = {}
    for name in ['F_marginal_g','E_marginal_g','interaction_g']:
        values = [r[name] for r in block_results]
        spread[name] = {'values': values, 'min': min(values), 'max': max(values),
                        'sample_sd_across_blocks_g': stdev(values) if len(values)>1 else None,
                        'description': 'Descriptive block dispersion; no population interval or significance claim.'}
    return {'analysis': 'Cage means, within-block contrasts, then equally weighted block average',
        'unit': 'g per stated unit time; actual duration unspecified',
        'contrast_convention': 'Level 1 minus level 0; interaction=(F1E1-F0E1)-(F1E0-F0E0)',
        'counts': {'animal_records': row_count, 'cages': len(cages), 'blocks': len(by_block),
                   'animals_per_cage': sorted({len(v) for v in cages.values()}),
                   'cells_per_block': sorted({len(v) for v in by_block.values()}),
                   'missing_values': 0, 'excluded_records': 0,
                   'independent_treatment_unit': 'cage; assignments are blocked, not 24 independent animal assignments'},
        'cage_means': cage_summary, 'by_block': block_results,
        'by_treatment_cell': cell_results, 'overall_equal_block_contrasts': overall,
        'descriptive_block_dispersion': spread,
        'inference_limit': 'Original offline synthetic example; 3 blocked cage replicates per treatment. No real-animal efficacy or universal additivity is established.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error('output directory must not already exist')
    results = analyze(args.input_dir)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    output = args.output_dir / 'results.json'
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    manifest = {'inputs': {'observations.csv': sha256(args.input_dir/'observations.csv')},
                'outputs': {'results.json': sha256(output)}, 'algorithm': 'run.py',
                'deterministic': True}
    (args.output_dir/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'output': str(output), 'counts': results['counts'],
                      'contrasts': results['overall_equal_block_contrasts']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
