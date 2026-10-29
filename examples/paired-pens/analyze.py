#!/usr/bin/env python3
"""Reproduce the synthetic six-block paired-pen example with the standard library."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, InvalidOperation
from itertools import product
import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys

FIELDS = ('block', 'pen', 'treatment', 'bird_id', 'gain_g')
T5_975 = 2.5705818356363146
DECIMAL_GRAMS = re.compile(r'[+-]?[0-9]{1,9}(?:\.[0-9]{1,6})?\Z')


def read_observations(path):
    """Read the explicit six-block fixture contract before any output is created."""
    if path.is_symlink() or not path.is_file():
        raise ValueError('Input must be an ordinary CSV file, not a symbolic link')
    data = path.read_bytes()
    if len(data) > 1024 * 1024:
        raise ValueError('Input exceeds the 1 MiB example limit')
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig'), newline=''))
    if reader.fieldnames != list(FIELDS):
        raise ValueError('CSV columns must be exactly: ' + ','.join(FIELDS))
    pens, birds = {}, set()
    for line, row in enumerate(reader, 2):
        if None in row or any(value is None or not value.strip() for value in row.values()):
            raise ValueError(f'Incomplete or extra CSV fields at line {line}')
        block, pen, treatment, bird = (row[key].strip() for key in FIELDS[:-1])
        if any(len(value) > 100 for value in (block, pen, bird)):
            raise ValueError(f'Identifier too long at line {line}')
        if treatment not in ('control', 'B'):
            raise ValueError(f'Treatment must be control or B at line {line}')
        if bird in birds:
            raise ValueError(f'Duplicate bird_id at line {line}')
        birds.add(bird)
        raw_gain = row['gain_g'].strip()
        if DECIMAL_GRAMS.fullmatch(raw_gain) is None:
            raise ValueError(f'gain_g must be finite fixed-point grams at line {line}')
        try:
            gain = Fraction(Decimal(raw_gain))
        except (InvalidOperation, ValueError, OverflowError) as exc:
            raise ValueError(f'Invalid gain_g at line {line}') from exc
        if pen in pens:
            if pens[pen]['block'] != block or pens[pen]['treatment'] != treatment:
                raise ValueError(f'A pen must have one block and one treatment: {pen}')
        else:
            pens[pen] = {'block': block, 'treatment': treatment, 'gains': []}
        pens[pen]['gains'].append(gain)
    blocks = {}
    for pen, values in pens.items():
        if len(values['gains']) != 10:
            raise ValueError('This example requires exactly 10 individual observations per pen')
        block = blocks.setdefault(values['block'], {})
        if values['treatment'] in block:
            raise ValueError('Each block must contain one control pen and one B pen')
        block[values['treatment']] = pen
    if len(blocks) != 6 or len(pens) != 12 or any(set(pair) != {'control', 'B'} for pair in blocks.values()):
        raise ValueError('This example requires exactly six blocks, each with one control and one B pen')
    return data, pens, blocks


def decimal_grams(value):
    """Keep exact CSV values; six-place gains averaged over ten need seven places."""
    scaled = abs(value) * 10_000_000
    if scaled.denominator != 1:
        raise ValueError('CSV means and differences must have at most seven decimal places')
    whole, fraction = divmod(scaled.numerator, 10_000_000)
    digits = f'{fraction:07d}'.rstrip('0') or '0'
    return ('-' if value < 0 else '') + f'{whole}.{digits}'


def analyze(data, pens, blocks):
    means = {pen: sum(info['gains'], Fraction()) / len(info['gains'])
             for pen, info in pens.items()}
    pairs = []
    for block, allocation in sorted(blocks.items()):
        control, treatment = means[allocation['control']], means[allocation['B']]
        pairs.append((block, control, treatment, treatment - control))
    differences = [row[3] for row in pairs]
    estimate = sum(differences, Fraction()) / len(differences)
    variance = sum(((d - estimate) ** 2 for d in differences), Fraction()) / (len(differences) - 1)
    standard_error = math.sqrt(float(variance / len(differences)))
    interval = ([float(estimate) - T5_975 * standard_error,
                 float(estimate) + T5_975 * standard_error] if variance > 0 else None)
    # All labels move at pen level within their original matched blocks.
    observed = abs(sum(differences, Fraction()))
    extreme = sum(abs(sum((sign * d for sign, d in zip(signs, differences)), Fraction())) >= observed
                  for signs in product((-1, 1), repeat=len(differences)))
    assignments = 2 ** len(differences)
    p_value = Fraction(extreme, assignments)
    summary = {
        'data_origin': 'original synthetic demonstration; not a real animal experiment',
        'input_sha256': hashlib.sha256(data).hexdigest(),
        'contrast': 'B-control', 'experimental_unit': 'pen',
        'analysis_unit': 'matched-block pen-mean difference',
        'individual_observations': sum(len(v['gains']) for v in pens.values()),
        'pens': len(pens), 'matched_blocks': len(blocks), 'individuals_per_pen': 10,
        'estimate_g': float(estimate), 'estimate_fraction_g': str(estimate),
        'standard_error_g': standard_error,
        'reference_interval_95_g': interval,
        'reference_interval_status': ('calculated' if interval is not None else
                                      'not-estimable-zero-sample-variance'),
        'reference_interval_model': 'independent approximately normal matched-block differences',
        'reference_t_df': 5, 'reference_t_critical': T5_975,
        'randomization_test': {
            'null': 'sharp no-effect null; no between-pen interference',
            'assignment': 'independent fair whole-pen label swap in each matched block',
            'statistic': 'absolute mean paired difference; ties included',
            'assignments': assignments, 'at_least_as_extreme': extreme,
            'p_fraction': str(p_value), 'p_value': float(p_value),
        },
        'alpha': 0.05, 'significant_at_alpha': p_value < Fraction(1, 20),
    }
    pen_rows = [{'block': info['block'], 'pen': pen, 'treatment': info['treatment'],
                 'bird_count': len(info['gains']), 'mean_gain_g': decimal_grams(means[pen])}
                for pen, info in sorted(pens.items(), key=lambda item: (item[1]['block'], item[0]))]
    pair_rows = [{'block': b, 'control_mean_g': decimal_grams(c), 'treatment_mean_g': decimal_grams(t),
                  'difference_g': decimal_grams(d)} for b, c, t, d in pairs]
    return summary, pen_rows, pair_rows


def csv_text(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def report_text(summary):
    interval = summary['reference_interval_95_g']
    interval_line = (f'配对 t 参考95%区间：[{interval[0]:.1f}, {interval[1]:.1f}] g。'
                     if interval is not None else
                     '六个配对差相同，本例不报告 t 参考区间。')
    test = summary['randomization_test']
    conclusion = ('两组增重差异显著。' if summary['significant_at_alpha'] else
                  '两组增重差异不显著。')
    return f'''# 原创合成肉鸡饲喂数据：分析节选

## 设计与分析

6个匹配区组，每区组2栏，每栏10只；区组内按栏分配饲料。先计算栏均值，
再比较6个区组的“B减对照”配对差。120条个体记录是栏内子样本。

## 实算结果

- B−对照：{summary['estimate_g']:+.1f} g。
- {interval_line}
- {test['assignments']}种整栏标签互换，{test['at_least_as_extreme']}种至少同样极端，
  双侧精确 P = {test['p_value']:.4f}（{test['p_fraction']}）。

按显著性水平0.05，{conclusion}

## 方法与复算

数据为构造的演示材料。t 区间使用独立、近似正态区组差的工作模型，
自由度5及 t_(0.975,5)={T5_975}；它与随机化检验分别报告。
精确检验使用区组内独立、公平的整栏分配、无跨栏干扰及尖锐无效应零假设，计入相等统计量。
原输入SHA-256为 `{summary['input_sha256']}`。

本轮交付为原输入所导出的栏均值、配对差及结果。真实研究的下一步是结合目标群体、
有意义的最小差异和可靠的栏间变异资料设计样本量，并制定福利、缺失及死亡记录处理方案。
'''


def write_outputs(directory, summary, pen_rows, pair_rows):
    if not directory.parent.is_dir():
        raise ValueError('Output parent directory must already exist')
    if os.path.lexists(directory):
        raise ValueError('Output directory must not already exist')
    contents = {
        'summary.json': json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
        'pen-means.csv': csv_text(pen_rows),
        'paired-differences.csv': csv_text(pair_rows),
        'analysis.md': report_text(summary),
    }
    directory.mkdir(exist_ok=False)
    created = []
    try:
        for name, text in contents.items():
            path = directory / name
            with path.open('x', encoding='utf-8', newline='') as stream:
                created.append(path)
                stream.write(text)
    except BaseException:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        try:
            directory.rmdir()
        except OSError:
            pass
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(__file__).resolve().with_name('observations.csv'))
    parser.add_argument('--output', required=True, type=Path, help='A new directory under an existing parent')
    args = parser.parse_args(argv)
    try:
        data, pens, blocks = read_observations(args.input)
        summary, pen_rows, pair_rows = analyze(data, pens, blocks)
        write_outputs(args.output, summary, pen_rows, pair_rows)
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        print(json.dumps({'passed': False, 'error': str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps({'passed': True, 'output_directory': str(args.output),
                      'files': ['summary.json', 'pen-means.csv', 'paired-differences.csv', 'analysis.md'],
                      'estimate_g': summary['estimate_g'],
                      'p_value': summary['randomization_test']['p_value']}, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
