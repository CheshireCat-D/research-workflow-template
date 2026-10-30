#!/usr/bin/env python3
"""Validate a frozen pilot and summarize supplied adjudications; never invokes a model."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys


FROZEN_SHA256 = '67574361112904429701845488db896e792b41a2849c5c86d8e8a441af6fa475'
HEX = re.compile(r'[0-9a-f]{64}\Z')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def load(path):
    def bad_constant(value):
        raise ValueError('non-finite JSON number: ' + value)
    return json.loads(path.read_text(encoding='utf-8'),
                      object_pairs_hook=unique_object, parse_constant=bad_constant)


def local_file(root, name):
    if not isinstance(name, str) or not name:
        raise ValueError('missing relative file path')
    rel = PurePosixPath(name)
    if rel.is_absolute() or '..' in rel.parts or '\\' in name:
        raise ValueError('unsafe file path: ' + name)
    path = root.joinpath(*rel.parts)
    if any(root.joinpath(*rel.parts[:i]).is_symlink()
           for i in range(1, len(rel.parts) + 1)):
        raise ValueError('symlink forbidden: ' + name)
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('missing or escaped file: ' + name)
    return path


def check_hash(path, expected):
    if not isinstance(expected, str) or not HEX.fullmatch(expected):
        raise ValueError('invalid SHA256 for ' + str(path))
    if sha(path) != expected:
        raise ValueError('bad SHA256: ' + str(path))


def bound_file(root, binding):
    if not isinstance(binding, dict):
        raise ValueError('missing file binding')
    path = local_file(root, binding['path'])
    check_hash(path, binding['sha256'])
    return path


def nonnegative(value, label, integer=False):
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(label + ' must be numeric or null')
    if not math.isfinite(value) or value < 0 or (integer and not isinstance(value, int)):
        raise ValueError(label + ' must be finite and nonnegative')


def summarize(root):
    root = Path(root)
    freeze_path = local_file(root, 'freeze.json')
    check_hash(freeze_path, FROZEN_SHA256)
    freeze = load(freeze_path)
    for name, expected in freeze['files'].items():
        check_hash(local_file(root, name), expected)
    key = load(local_file(root, 'reference-key.json'))
    config = load(local_file(root, freeze['configuration_file']))
    expected_pairs = {(t, a) for t in freeze['tasks'] for a in freeze['arms']}
    if {(p['task_id'], p['arm']) for p in freeze['trial_plan']} != expected_pairs:
        raise ValueError('trial plan is not the complete Cartesian product')
    seen, trial_ids, submissions = set(), set(), set()
    rows, incomplete, config_values = [], [], {}
    directory = root / 'trials'
    if directory.is_symlink():
        raise ValueError('symlink trials directory')
    trial_paths = sorted(directory.glob('*.json')) if directory.exists() else []
    for path in trial_paths:
        trial = load(local_file(root, path.relative_to(root).as_posix()))
        pair = (trial['task_id'], trial['arm'])
        if pair not in expected_pairs:
            raise ValueError('unknown task/arm: ' + repr(pair))
        if pair in seen:
            raise ValueError('duplicate task/arm: ' + repr(pair))
        seen.add(pair)
        trial_id = trial['trial_id']
        if not isinstance(trial_id, str) or not trial_id or trial_id in trial_ids:
            raise ValueError('missing or duplicate trial_id')
        trial_ids.add(trial_id)
        if trial['freeze_sha256'] != FROZEN_SHA256:
            raise ValueError('trial uses a different freeze: ' + trial_id)
        task_name = 'tasks/' + pair[0] + '.md'
        if trial['task_sha256'] != freeze['files'][task_name]:
            raise ValueError('trial task hash mismatch: ' + trial_id)
        execution = load(bound_file(root, trial['execution']))
        if execution.get('schema_version') != 1 or trial.get('schema_version') != 1:
            raise ValueError('unsupported record schema')
        if execution['requested_configuration'] != config:
            raise ValueError('requested configuration changed: ' + trial_id)
        status = execution['status']
        if status not in ('not-run', 'executed', 'failed'):
            raise ValueError('unknown execution status')
        issues = []
        if status != 'executed':
            issues.append('execution:' + status)
        if status == 'failed' and not execution.get('failure'):
            raise ValueError('failed execution lacks failure reason')
        for name in ('duration_seconds', 'tool_calls', 'output_tokens',
                     'network_calls', 'output_unicode_characters', 'output_bytes'):
            nonnegative(execution.get(name), name, integer=name != 'duration_seconds')
        if execution.get('tool_calls') is not None and execution['tool_calls'] > 8:
            issues.append('tool-budget-exceeded')
        if execution.get('network_calls') is not None and execution['network_calls'] > 0:
            issues.append('network-use')
        if not isinstance(execution['violations'], list):
            raise ValueError('violations must be a list')
        issues.extend('reported-violation:' + str(v) for v in execution['violations'])
        isolation = execution['context_isolation']
        if isolation.get('evidence') != 'instruction-only' or isolation.get('os_audited') is not False:
            raise ValueError('isolation evidence exceeds frozen protocol')
        if isolation.get('same_metadata_catalogue_visible') is not True:
            issues.append('metadata-catalogue-differs')
        effective = execution['effective_configuration']
        required_config = {'model', 'reasoning_effort', 'temperature', 'seed',
                           'hard_output_token_limit'}
        if set(effective) != required_config:
            raise ValueError('effective configuration fields missing or unexpected')
        unknown = []
        for name, observation in effective.items():
            value, source = observation.get('value'), observation.get('source')
            if value is None:
                if source != 'unknown':
                    raise ValueError('null configuration must state source unknown')
                unknown.append(name)
            else:
                if not isinstance(source, str) or not source or source == 'unknown':
                    raise ValueError('known configuration lacks actual source')
                config_values.setdefault(name, set()).add(json.dumps(value, sort_keys=True))
        allowed = {task_name: freeze['files'][task_name],
                   'executor-prompt.md': freeze['files']['executor-prompt.md'],
                   'templates/execution.template.json':
                       freeze['files']['templates/execution.template.json']}
        arm = pair[1]
        allowed.update({name: digest for name, digest in freeze['guidance_sha256'].items()
                        if ((arm == 'rwt' and name.startswith('rwt/')) or
                            (arm == 'critical-thinking' and name.startswith('competitor/')))})
        required_reads = {task_name, *freeze['required_guidance'][arm]}
        if arm == 'rwt':
            required_reads.add(freeze['method_guidance'][pair[0]])
        read_names = set()
        for item in execution['actual_reads']:
            name, digest = item['logical_name'], item['sha256']
            if name in read_names:
                raise ValueError('duplicate read entry: ' + name)
            read_names.add(name)
            if not isinstance(digest, str) or not HEX.fullmatch(digest):
                raise ValueError('invalid read SHA256')
            if name not in allowed:
                issues.append('forbidden-read:' + name)
            elif digest != allowed[name]:
                raise ValueError('actual read hash mismatch: ' + name)
        if status == 'executed' and not required_reads <= read_names:
            issues.append('required-guidance-or-task-not-read:' +
                          ','.join(sorted(required_reads - read_names)))
        row = {'trial_id': trial_id, 'task_id': pair[0], 'arm': arm,
               'execution_status': status, 'score': None,
               'max_score': key['tasks'][pair[0]]['max_score'],
               'effective_configuration_unknown': sorted(unknown),
               'duration_seconds': execution.get('duration_seconds'),
               'tool_calls': execution.get('tool_calls'),
               'output_tokens': execution.get('output_tokens')}
        report_binding = trial.get('report')
        if report_binding is not None:
            report = bound_file(root, report_binding)
            raw = report.read_bytes()
            chars = len(raw.decode('utf-8'))
            row['output_bytes'], row['output_unicode_characters'] = len(raw), chars
            if chars > 5000:
                issues.append('output-budget-exceeded')
            for name, actual in [('output_bytes', len(raw)),
                                 ('output_unicode_characters', chars)]:
                if execution.get(name) is not None and execution[name] != actual:
                    raise ValueError('recorded output size mismatch: ' + trial_id)
        elif status == 'executed':
            issues.append('missing-report')
        blind = trial.get('blind') or {}
        submission = blind.get('submission_id')
        if submission:
            if submission in submissions:
                raise ValueError('duplicate anonymous submission_id')
            submissions.add(submission)
        if blind.get('arm_revealed_to_judge') is not False:
            issues.append('blindness-not-established')
        adjudication_binding = blind.get('adjudication')
        if adjudication_binding is None:
            issues.append('unscored')
        else:
            judgment = load(bound_file(root, adjudication_binding))
            if judgment.get('scored') is not True:
                issues.append('unscored')
            else:
                if report_binding is None or status != 'executed':
                    raise ValueError('score attached to a missing/failed execution')
                if (judgment['submission_id'] != submission or
                        judgment['task_id'] != pair[0] or
                        judgment['report_sha256'] != report_binding['sha256']):
                    raise ValueError('adjudication binding mismatch')
                if judgment.get('arm_visibility') != 'hidden-by-instruction':
                    issues.append('judge-not-blinded')
                if judgment.get('os_audited') is not False:
                    raise ValueError('judge isolation claim exceeds protocol')
                rubric = {c['id']: c for c in key['tasks'][pair[0]]['criteria']}
                scores = {}
                for criterion in judgment['criteria']:
                    name, score = criterion['id'], criterion['score']
                    if name in scores or name not in rubric:
                        raise ValueError('duplicate or unknown criterion')
                    if type(score) is not int or not 0 <= score <= rubric[name]['max_score']:
                        raise ValueError('invalid criterion score')
                    if not str(criterion.get('evidence', '')).strip() or not str(
                            criterion.get('rationale', '')).strip():
                        raise ValueError('score lacks evidence/rationale')
                    scores[name] = score
                if set(scores) != set(rubric):
                    raise ValueError('missing scored criterion')
                if judgment['verdict'] not in ('supported', 'unsupported', 'unclear'):
                    raise ValueError('invalid extracted verdict')
                if not isinstance(judgment['invented_major_objections'], list):
                    raise ValueError('invented major objections must be listed')
                row.update(score=sum(scores.values()), criteria=scores,
                           reported_verdict=judgment['verdict'],
                           invented_major_objections=judgment['invented_major_objections'])
        if issues:
            incomplete.append({'trial_id': trial_id, 'issues': issues})
        rows.append(row)
    missing = [{'task_id': t, 'arm': a} for t, a in sorted(expected_pairs - seen)]
    mismatches = [name for name, values in config_values.items() if len(values) > 1]
    complete = not missing and not incomplete and not mismatches
    return {'study_id': freeze['study_id'],
            'status': 'complete' if complete else 'incomplete',
            'meaning_of_complete': 'record closure only; no general accuracy estimate',
            'expected_trials': len(expected_pairs), 'recorded_trials': len(rows),
            'scored_trials': sum(row['score'] is not None for row in rows),
            'missing': missing, 'incomplete_trials': incomplete,
            'known_effective_configuration_mismatches': mismatches,
            'configuration_evidence': 'reported observations; unknown values preserved',
            'context_isolation_evidence': freeze['isolation_evidence'],
            'results': sorted(rows, key=lambda row: (row['task_id'], row['arm']))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--allow-incomplete', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = summarize(args.root)
    except (ValueError, KeyError, TypeError, OSError, UnicodeError) as exc:
        print(json.dumps({'status': 'invalid', 'error': str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'complete' or args.allow_incomplete else 1


if __name__ == '__main__':
    sys.exit(main())
