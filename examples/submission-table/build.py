#!/usr/bin/env python3
"""Create a fresh, editable LaTeX delivery from the six-block paired-pens CSV.

Python 3.11+ standard library only. TeX compilation is an explicit later step.
"""
from pathlib import Path
from decimal import Decimal, InvalidOperation, localcontext
from itertools import product
import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys


FIELDS = ('block', 'control_mean_g', 'treatment_mean_g', 'difference_g')
NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,12})?\Z')
T5_REFERENCE = Decimal('2.5705818356363146')
MAX_INPUT_BYTES = 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def tex_text(value):
    """Escape an ASCII label as text, without interpreting TeX commands."""
    replacements = {
        '\\': r'\textbackslash{}', '{': r'\{', '}': r'\}', '&': r'\&',
        '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
        '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
    }
    return ''.join(replacements.get(char, char) for char in value)


def read_rows(data):
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError('Input exceeds the 1 MiB worked-example limit')
    try:
        content = data.decode('utf-8-sig')
    except UnicodeError as exc:
        raise ValueError('Input must be UTF-8 CSV') from exc
    reader = csv.DictReader(io.StringIO(content, newline=''), strict=True)
    if reader.fieldnames != list(FIELDS):
        raise ValueError('CSV columns must be: ' + ','.join(FIELDS))
    rows = list(reader)
    if len(rows) != 6:
        raise ValueError('This t5 worked example requires exactly six matched blocks')
    identifiers = set()
    for row in rows:
        if set(row) != set(FIELDS) or any(value is None for value in row.values()):
            raise ValueError('Every row must have exactly four fields')
        block = row['block']
        if (not 1 <= len(block) <= 24 or block.strip() != block or
                any(not 32 <= ord(char) <= 126 for char in block)):
            raise ValueError('Block labels must be 1-24 printable ASCII characters')
        if block in identifiers:
            raise ValueError('Block labels must be unique')
        identifiers.add(block)
        numbers = {}
        for field in FIELDS[1:]:
            value = row[field]
            if NUMBER.fullmatch(value) is None:
                raise ValueError('Measurements must be plain finite decimal numbers with at most 12 fractional digits')
            numbers[field] = Decimal(value)
            if abs(numbers[field]) > Decimal('1000000000'):
                raise ValueError('Measurement magnitude exceeds the worked-example limit')
        if numbers['treatment_mean_g'] - numbers['control_mean_g'] != numbers['difference_g']:
            raise ValueError('difference_g must equal treatment_mean_g minus control_mean_g')
    return rows


def summarize(rows):
    differences = [Decimal(row['difference_g']) for row in rows]
    with localcontext() as context:
        context.prec = 40
        n = Decimal(len(differences))
        estimate = sum(differences) / n
        variance = sum((value - estimate) ** 2 for value in differences) / (n - 1)
        se = (variance / n).sqrt()
        interval = ([str(estimate - T5_REFERENCE * se), str(estimate + T5_REFERENCE * se)]
                    if variance > 0 else None)
        observed = abs(sum(differences))
        extreme = sum(abs(sum(Decimal(sign) * value for sign, value in zip(signs, differences))) >= observed
                      for signs in product((-1, 1), repeat=len(differences)))
        return {
            'matched_blocks': len(differences),
            'contrast': 'feed B minus control',
            'mean_difference_g': str(estimate),
            'standard_error_g': str(se),
            'reference_95_interval_g': interval,
            'reference_interval_status': ('computed-reference' if interval is not None else 'not-computed-zero-variance'),
            'reference_t_df': 5,
            'reference_t_critical': str(T5_REFERENCE),
            'randomization_extreme': extreme,
            'randomization_total': 2 ** len(differences),
            'exact_two_sided_p': str(Decimal(extreme) / Decimal(2 ** len(differences))),
        }


def displayed(value, places=2):
    return format(Decimal(value), '.' + str(places) + 'f')


def column_format(values):
    width = max(len(value.lstrip('-').split('.')[0]) for value in values)
    precision = max(len(value.partition('.')[2]) for value in values)
    # A Computer Modern minus is wider than one digit; reserve two digit
    # widths for its sign without padding or changing the displayed tokens.
    width += 2 if any(value.startswith('-') for value in values) else 0
    return str(width) + '.' + str(precision)


def manuscript(rows, analysis):
    body = '\n'.join(tex_text(row['block']) + ' & ' + ' & '.join(row[field] for field in FIELDS[1:]) + r' \\'
                     for row in rows)
    columns = ' '.join('D{.}{.}{' + column_format([row[field] for row in rows]) + '}'
                       for field in FIELDS[1:])
    estimate = displayed(analysis['mean_difference_g'])
    interval = analysis['reference_95_interval_g']
    lower, upper = list(map(displayed, interval)) if interval is not None else (None, None)
    pvalue = displayed(analysis['exact_two_sided_p'], 4)
    summary_columns = ' '.join('D{.}{.}{' + column_format([value or '0.00']) + '}'
                               for value in (estimate, lower, upper, pvalue))
    summary_values = [estimate, lower or r'\multicolumn{1}{c}{---}',
                      upper or r'\multicolumn{1}{c}{---}', pvalue]
    interval_note = ('' if interval is not None else
                     '\nNo t reference interval is computed because the six observed differences\nhave zero sample variance.\n')
    return r'''\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[margin=25mm]{geometry}
\usepackage{booktabs}
\usepackage{dcolumn}
\setlength{\tabcolsep}{7pt}
\setlength{\belowcaptionskip}{7pt}
\renewcommand{\arraystretch}{1.15}
\title{Paired-pen analysis: a synthetic worked example}
\author{}
\date{}
\begin{document}
\maketitle
\noindent
Each row gives the mean for a control pen and a feed-B pen in the same
matched block. The allocation unit is the pen; the analysis compares six
block differences in 28-day gain. The contrast is feed B minus control.

\begin{table}[htbp]
\centering
\caption{Pen means and within-block differences in 28-day gain. All measurements are in grams.}
\label{tab:blocks}
\begin{tabular}{c ''' + columns + r'''}
\toprule
Block & \multicolumn{1}{c}{Control (g)} & \multicolumn{1}{c}{Feed B (g)} & \multicolumn{1}{c}{B$-$control (g)} \\
\midrule
\addlinespace[0.25em]
''' + body + r'''
\bottomrule
\end{tabular}
\end{table}

\begin{table}[htbp]
\centering
\caption{Summary of the paired contrast. Estimates and interval limits are displayed to two decimal places.}
\label{tab:summary}
\begin{tabular}{l ''' + summary_columns + r'''}
\toprule
 & & \multicolumn{2}{c}{Reference 95\% interval (g)} & \\
\cmidrule(lr){3-4}
Contrast & \multicolumn{1}{c}{Estimate (g)} & \multicolumn{1}{c}{Lower} & \multicolumn{1}{c}{Upper} & \multicolumn{1}{c}{Exact $P$} \\
\midrule
\addlinespace[0.25em]
Feed B minus control & ''' + ' & '.join(summary_values) + r''' \\
\bottomrule
\end{tabular}
\end{table}

\noindent
The reference interval uses independent, approximately normal block
differences and a Student $t$ distribution with five degrees of freedom.
The two-sided randomization calculation enumerates all 64 within-block
pen-label swaps under independent, equiprobable treatment allocation,
no cross-pen interference, and the sharp null of no treatment effect.
Table~\ref{tab:summary} reports the resulting contrast and uncertainty.
''' + interval_note + r'''
\end{document}
'''


def build(data_path, output):
    data_path, output = Path(data_path), Path(output)
    if data_path.is_symlink() or not data_path.is_file():
        raise ValueError('Input must be a regular CSV file, not a symbolic link')
    data = data_path.read_bytes()
    rows = read_rows(data)
    analysis = summarize(rows)
    tex = manuscript(rows, analysis).encode('utf-8')
    if os.path.lexists(output):
        raise ValueError('Output must be a new directory that does not exist')
    if not output.parent.is_dir():
        raise ValueError('Output parent directory must already exist')
    manifest = {
        'format_version': 1,
        'input': {'name': data_path.name, 'bytes': len(data), 'sha256': digest(data)},
        'files': {
            'paired-differences.csv': {'role': 'unchanged captured input', 'bytes': len(data), 'sha256': digest(data)},
            'main.tex': {'role': 'generated editable manuscript', 'bytes': len(tex), 'sha256': digest(tex),
                         'generated_from': 'paired-differences.csv'},
        },
        'analysis': analysis,
        'layout': {'text': 'left', 'block_codes': 'centered', 'measurements': 'decimal marker aligned',
                   'input_precision': 'retained in block rows and captured CSV', 'summary_precision': '2 decimals; P 4 decimals'},
        'checks': {'input_contract': 'passed', 'compilation': 'not-run', 'visual_review': 'not-run'},
        'compile_dependencies': ['pdfLaTeX', 'geometry', 'booktabs', 'dcolumn', 'T1 font encoding'],
        'scope': 'Six-block editable source delivery; publication requirements and actual compilation are separate checks.',
    }
    output.mkdir()
    try:
        (output / 'paired-differences.csv').write_bytes(data)
        (output / 'main.tex').write_bytes(tex)
        (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, allow_nan=False, indent=2) + '\n', encoding='utf-8')
    except BaseException:
        shutil.rmtree(output)
        raise
    return {'passed': True, 'files': 3, 'output': str(output), 'input_sha256': digest(data),
            'compilation': 'not-run', 'visual_review': 'not-run'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', required=True, help='paired-differences.csv produced by the paired-pens example')
    parser.add_argument('--output', required=True, help='new output directory; parent must already exist')
    args = parser.parse_args(argv)
    try:
        report = build(args.data, args.output)
    except (OSError, ValueError, InvalidOperation, csv.Error) as exc:
        print(json.dumps({'passed': False, 'error': str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
