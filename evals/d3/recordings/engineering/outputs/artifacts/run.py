"""Offline requirement acceptance runner. Python standard library only.

From any working directory: python3 /path/to/PROJECT/artifacts/run.py
Default writes artifacts/results.json. Replaying frozen baseline:
  python3 artifacts/run.py --implementation inputs/gate.py --results artifacts/prototype-results.json
"""
from pathlib import Path
from fractions import Fraction
from itertools import combinations_with_replacement
import argparse
import copy
import csv
import hashlib
import json
import math
import platform
import sys
import time
import traceback
import types

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


def local_path(value):
    path = ROOT / value
    if Path(value).is_absolute() or '..' in Path(value).parts:
        raise ValueError('paths must be project-relative')
    return path


def oracle(limit, window, requests):
    """Definition-based independent oracle; retains all accepted history."""
    history = {}
    results = []
    width = Fraction(window)
    for client, timestamp in requests:
        t = Fraction(timestamp)
        accepted = history.setdefault(client, [])
        count = sum(1 for past in accepted if 0 <= t - past < width)
        permitted = count < limit
        if permitted:
            accepted.append(t)
        results.append(permitted)
    return results


def run(implementation):
    module = types.ModuleType('subject_gate')
    exec(compile(implementation.read_text(encoding='utf-8'), str(implementation), 'exec'), module.__dict__)
    Gate = module.WindowGate
    cases = []

    def check(name, requirements, operation):
        try:
            details = operation()
            cases.append({'name': name, 'requirements': requirements, 'passed': True, 'details': details})
        except Exception as exc:
            cases.append({'name': name, 'requirements': requirements, 'passed': False,
                          'error_type': type(exc).__name__, 'error': str(exc),
                          'traceback': traceback.format_exc()})

    def sequence(limit, window, requests, expected):
        gate = Gate(limit, window)
        got = [gate.allow(client, timestamp) for client, timestamp in requests]
        assert got == expected, f'expected {expected!r}, actual {got!r}; requests={requests!r}'
        assert all(type(x) is bool for x in got), 'allow must return bool'
        return {'expected': expected, 'actual': got}

    scenarios = [
        ('quota-repeated', ['R1'], 3, 10, [('a', 0)] * 4, [True, True, True, False]),
        ('open-left-exact', ['R2'], 1, 10, [('a', 0), ('a', 10)], [True, True]),
        ('rejection-not-counted', ['R2', 'R3'], 2, 10, [('a', 0), ('a', 1), ('a', 9), ('a', 10), ('a', 11)], [True, True, False, True, True]),
        ('client-isolation', ['R1', 'R4'], 1, 10, [('a', 100), ('b', 0), ('a', 101), ('b', 10)], [True, True, False, True]),
        ('fractional-window', ['R2', 'R9'], 1, 0.5, [('a', 0.25), ('a', 0.5), ('a', 0.75)], [True, False, True]),
        ('float-neighbors', ['R2', 'R9'], 1, 1, [('a', 0), ('a', math.nextafter(1.0, 0.0)), ('a', 1.0)], [True, False, True]),
        ('large-int-resolution', ['R2', 'R9'], 1, 1, [('a', 2**53), ('a', 2**53+1)], [True, True]),
        ('huge-int-timestamp', ['R2', 'R6', 'R9'], 1, 1, [('a', 10**400), ('a', 10**400+1)], [True, True]),
        ('huge-int-window', ['R2', 'R5', 'R9'], 1, 10**400, [('a', 0), ('a', 10**400)], [True, True]),
        ('huge-int-limit', ['R1', 'R5', 'R9'], 10**400, 1, [('a', 0), ('a', 0)], [True, True]),
        ('long-idle-gap', ['R1', 'R2'], 2, 5, [('a', 0), ('a', 0), ('a', 1000), ('a', 1000), ('a', 1000)], [True, True, True, True, False]),
        ('mixed-numeric-boundary', ['R2', 'R9'], 1, 0.5, [('a', 10**400), ('a', 10**400+1)], [True, True]),
    ]
    for name, tags, limit, window, requests, expected in scenarios:
        check(name, tags, lambda l=limit, w=window, q=requests, e=expected: sequence(l, w, q, e))

    def invalid_constructor(limit, window):
        try:
            Gate(limit, window)
        except ValueError:
            return 'ValueError'
        raise AssertionError('invalid constructor did not raise ValueError')

    bad_limits = [True, False, 0, -1, 1.0, '1', None, [], float('nan'), float('inf')]
    bad_windows = [True, False, 0, -1, -0.5, float('nan'), float('inf'), -float('inf'), '1', None, [], complex(1)]
    for i, value in enumerate(bad_limits):
        check(f'invalid-limit-{i}', ['R5'], lambda x=value: invalid_constructor(x, 10))
    for i, value in enumerate(bad_windows):
        check(f'invalid-window-{i}', ['R5'], lambda x=value: invalid_constructor(3, x))

    def invalid_request(client, timestamp):
        gate = Gate(2, 10)
        gate.allow('existing', 2)
        before = copy.deepcopy(vars(gate))
        try:
            gate.allow(client, timestamp)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid request did not raise ValueError')
        assert vars(gate) == before, 'invalid request mutated state or created client'
        assert gate.allow('existing', 3) is True, 'exception prevented later valid request'
        assert gate.allow('new', 0) is True, 'exception poisoned another client'
        return 'ValueError; complete state unchanged; later valid requests accepted'

    for i, client in enumerate(['', True, False, None, 1, [], {}]):
        check(f'invalid-client-{i}', ['R6', 'R8'], lambda x=client: invalid_request(x, 3))
    bad_timestamps = [True, False, -1, -0.5, float('nan'), float('inf'), -float('inf'), '2', None, [], complex(2)]
    for i, timestamp in enumerate(bad_timestamps):
        for client in ('existing', 'new'):
            check(f'invalid-time-{client}-{i}', ['R6', 'R8'], lambda c=client, x=timestamp: invalid_request(c, x))
    check('time-reversal-atomic', ['R7', 'R8'], lambda: invalid_request('existing', 1))

    def rejected_watermark():
        gate = Gate(1, 10)
        assert gate.allow('a', 0) is True
        assert gate.allow('a', 5) is False
        before = copy.deepcopy(vars(gate))
        try:
            gate.allow('a', 4)
        except ValueError:
            pass
        else:
            raise AssertionError('denied request did not advance timestamp watermark')
        assert vars(gate) == before, 'time reversal mutated state'
        assert gate.allow('a', 10) is True, 'denial consumed future quota or boundary wrong'
        return 'denied t=5 makes t=4 illegal; t=10 accepted'
    check('rejected-watermark', ['R2', 'R3', 'R7', 'R8'], rejected_watermark)

    for limit in (1, 2, 3):
        for window in (1, 2, 3, 2.5):
            for index, times in enumerate(combinations_with_replacement(range(5), 5)):
                requests = [('reference', timestamp) for timestamp in times]
                expected = oracle(limit, window, requests)
                check(f'reference-{limit}-{window}-{index}', ['R1', 'R2', 'R3'],
                      lambda l=limit, w=window, q=requests, e=expected: sequence(l, w, q, e))

    with (ROOT / 'inputs/demo-traffic.csv').open(newline='', encoding='utf-8') as f:
        requests = [(row['client'], int(row['timestamp'])) for row in csv.DictReader(f)]
    check('demo-csv', ['R1', 'R2', 'R3', 'R4'], lambda: sequence(3, 10, requests, oracle(3, 10, requests)))
    coverage = {}
    for tag in sorted({tag for case in cases for tag in case['requirements']}):
        selected = [case for case in cases if tag in case['requirements']]
        coverage[tag] = {'total': len(selected), 'passed': sum(c['passed'] for c in selected),
                         'failed_cases': [c['name'] for c in selected if not c['passed']]}
    return cases, coverage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--implementation', default='artifacts/gate.py')
    parser.add_argument('--results', default='artifacts/results.json')
    args = parser.parse_args()
    started = time.perf_counter()
    implementation = local_path(args.implementation)
    cases, coverage = run(implementation)
    failures = [case for case in cases if not case['passed']]
    elapsed = time.perf_counter() - started
    inputs = ['inputs/requirements.md', 'inputs/gate.py', 'inputs/demo-traffic.csv', args.implementation, 'artifacts/run.py']
    result = {'implementation': args.implementation, 'passed': not failures,
              'total_cases': len(cases), 'passed_cases': len(cases) - len(failures), 'failed_cases': len(failures),
              'elapsed_seconds': elapsed, 'formal_run_limit_seconds': 10,
              'under_time_limit': elapsed < 10, 'seed': None, 'seed_note': 'deterministic; not applicable',
              'environment': {'python': sys.version, 'platform': platform.platform(), 'dependencies': 'Python standard library'},
              'command_from_project': ['python3', 'artifacts/run.py', '--implementation', args.implementation, '--results', args.results],
              'configuration': {'reference': {'limits': [1, 2, 3], 'windows': [1, 2, 3, 2.5], 'times': [0, 1, 2, 3, 4], 'sequence_length': 5, 'nondecreasing_sequences': 126, 'trajectories': 1512}, 'demo_limit': 3, 'demo_window': 10},
              'input_sha256': {name: hashlib.sha256(local_path(name).read_bytes()).hexdigest() for name in inputs},
              'requirement_coverage': coverage, 'cases': cases,
              'scope': 'Offline single-process single-thread in-memory acceptance; finite deterministic test evidence, no production/performance/security/distributed certification.'}
    local_path(args.results).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('implementation', 'passed', 'total_cases', 'passed_cases', 'failed_cases', 'elapsed_seconds', 'under_time_limit')}, ensure_ascii=False))
    for case in failures:
        print(f"FAIL {case['name']} {','.join(case['requirements'])}: {case['error_type']}: {case['error']}")
    return 0 if not failures and elapsed < 10 else 1

if __name__ == '__main__':
    raise SystemExit(main())
