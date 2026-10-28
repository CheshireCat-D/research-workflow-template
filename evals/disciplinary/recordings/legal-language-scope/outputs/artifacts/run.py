#!/usr/bin/env python3
"""Replay this case's reviewed Boolean model from supplied Chinese/English facts.

Only Python 3.11+ standard library. Example:
  python artifacts/run.py --input-dir inputs --output-dir /path/to/new-results
The output directory must not already exist. Normative text must exactly match
this case's reviewed nonblank lines (outer whitespace is ignored); any changed,
extra, removed or reordered normative line is rejected. Applicant facts remain
dynamic. This is a closed-case replay, not an automatic legal interpreter.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re

# Closed-case support contract: every normative line must match this reviewed
# packet. Applicant facts are parsed independently below, not frozen here.
SUPPORTED_NORMATIVE_LINES = ('# 原创虚构法域“澄湾”', '这是离线合成材料，不对应任何真实法律；两种语言文本在本虚构法域具有共同权威，制定机关文书D0明确未规定优先语言。下列为截至虚构2030-06-01的完整相关条款，未发生修法。', 'D0 第1条：本规则中英文本同等权威。', '第2条（定义）：合格申请人指年满18岁的本地居民；本地居住条件用R表示，年龄条件用A表示。', 'Section 2: An eligible applicant is a local resident aged eighteen years or older.', '第5条：合格申请人完成培训或者处于获准监督之下，得申请许可；但第7条禁止者除外。', 'Section 5: An eligible applicant who has completed training or is under approved supervision may apply for a permit, except a person prohibited under section 7.', '第7条：正在执行禁止令的申请人不得适用第5条。', 'Section 7: An applicant subject to an active prohibition order is excluded from section 5.', '第9条：对拒绝申请的决定可在送达后15日内请求复核。复核权不改变第5条实体条件。')


def read_inputs(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    texts, hashes = {}, {}
    for name in ('source-packet.md', 'draft.md', 'task.md'):
        raw = (root / name).read_bytes()
        texts[name] = raw.decode('utf-8')
        hashes[name] = hashlib.sha256(raw).hexdigest()
    return texts, hashes


def parse_source(source: str) -> tuple[int, int, list[dict], dict]:
    normative_lines, applicant_lines = [], []
    applicant_block_started = False
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith('申请人'):
            applicant_block_started = True
            applicant_lines.append(line)
        else:
            if applicant_block_started:
                raise ValueError('Unsupported content after applicant facts; renewed legal review required')
            normative_lines.append(line)
    if tuple(normative_lines) != SUPPORTED_NORMATIVE_LINES:
        raise ValueError('Unsupported normative text: the complete reviewed rule block must match; '
                         'added, removed, changed or reordered conditions require renewed legal review')
    if not applicant_lines:
        raise ValueError('No applicant facts found')
    # The complete normative block is validated before extracting known values.
    normalized_source = '\n'.join(normative_lines)
    patterns = {
        'D0_1': r'^D0 第1条：(.*)$',
        'zh_2': r'^第2条（定义）：(.*)$',
        'en_2': r'^Section 2: (.*)$',
        'zh_5': r'^第5条：(.*)$',
        'en_5': r'^Section 5: (.*)$',
        'zh_7': r'^第7条：(.*)$',
        'en_7': r'^Section 7: (.*)$',
        'zh_9': r'^第9条：(.*)$',
    }
    clauses = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, normalized_source, re.MULTILINE)
        if match is None:
            raise ValueError('Missing recognized clause: ' + key)
        clauses[key] = match.group(1)
    age = re.search(r'合格申请人指年满(\d+)岁的本地居民', clauses['zh_2'])
    if age is None:
        raise ValueError('Unsupported eligibility definition')
    threshold = int(age.group(1))
    words = {18: 'eighteen'}
    if words.get(threshold) is None or (
        'local resident aged ' + words[threshold] + ' years or older'
    ) not in clauses['en_2']:
        raise ValueError('Unreviewed bilingual age correspondence')
    days = re.search(r'送达后(\d+)日内请求复核', clauses['zh_9'])
    if days is None:
        raise ValueError('Unsupported review deadline')
    applicants = []
    pattern = (r'^申请人(?P<name>[^：\n]+)：年龄(?P<age>\d+)，'
               r'(?P<residence>非本地居民|本地居民)，'
               r'(?P<training>未完成培训|完成培训)，'
               r'(?P<supervision>处于获准监督下|无监督)，'
               r'(?P<prohibition>无禁止令|有正在执行的禁止令)。$')
    for line in applicant_lines:
        match = re.fullmatch(pattern, line)
        if match is None:
            raise ValueError('Unsupported applicant facts: ' + line)
        m = match.groupdict()
        facts = {'A': int(m['age']) >= threshold,
                 'R': m['residence'] == '本地居民',
                 'T': m['training'] == '完成培训',
                 'S': m['supervision'] == '处于获准监督下',
                 'P': m['prohibition'] == '有正在执行的禁止令'}
        applicants.append({'name': m['name'], 'age': int(m['age']),
                           'source_line': line, 'facts': facts})
    return threshold, int(days.group(1)), applicants, clauses


def factored(A: bool, R: bool, T: bool, S: bool, P: bool) -> bool:
    return A and R and (T or S) and not P


def distributed(A: bool, R: bool, T: bool, S: bool, P: bool) -> bool:
    return (A and R and T and not P) or (A and R and S and not P)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    if args.output_dir.exists() or args.output_dir.is_symlink():
        parser.error('output directory must not already exist')
    texts, input_hashes = read_inputs(args.input_dir)
    try:
        threshold, days, applicants, clauses = parse_source(texts['source-packet.md'])
    except ValueError as exc:
        parser.error(str(exc))
    wrong_models = {
        'draft_any_single_condition_ignoring_prohibition': lambda a,r,t,s,p: a or r or t or s,
        'training_required': lambda a,r,t,s,p: a and r and t and not p,
        'prohibition_omitted': lambda a,r,t,s,p: a and r and (t or s),
    }
    rows, differences = [], {key: [] for key in wrong_models}
    distribution_differences = []
    for bits in itertools.product((False, True), repeat=5):
        facts = dict(zip(('A','R','T','S','P'), bits))
        q, expanded = factored(*bits), distributed(*bits)
        row = {'facts': facts, 'factored': q, 'distributed': expanded,
               'wrong_models': {key: bool(fn(*bits)) for key,fn in wrong_models.items()}}
        rows.append(row)
        if q != expanded:
            distribution_differences.append(row)
        for key in wrong_models:
            if q != row['wrong_models'][key]:
                differences[key].append(row)
    for item in applicants:
        item['may_apply_under_section_5'] = factored(**item['facts'])
        item['review_rule'] = {'if_refusal_decision_served': True,
                               'request_within_days_after_service': days,
                               'changes_substantive_conditions': False,
                               'service_or_refusal_facts_given': False,
                               'automatic_grant_established': False}
    result = {
        'input_sha256': input_hashes,
        'interpretive_model': 'A and R and (T or S) and not P',
        'model_origin': 'Agent clause analysis of supplied sections 2, 5, 7; enumeration is not legal authority.',
        'parsed_age_threshold': threshold,
        'parsed_review_days_after_service': days,
        'authority': {'coequal_languages': True, 'priority_language_defined': False},
        'recognized_clauses': clauses,
        'input_policy': {'normative_text': 'Exact ordered reviewed nonblank lines; added, removed, changed or reordered content is rejected.',
                         'normalization': 'Blank lines and outer line whitespace only.',
                         'applicant_facts': 'Parsed afresh from the provided input with the documented closed grammar.'},
        'applicants': applicants,
        'enumeration': {'variables': ['A','R','T','S','P'], 'rows': rows,
                        'row_count': len(rows), 'eligible_row_count': sum(x['factored'] for x in rows),
                        'distribution_difference_count': len(distribution_differences),
                        'distribution_differences': distribution_differences,
                        'wrong_model_difference_counts': {k:len(v) for k,v in differences.items()},
                        'wrong_model_differences': differences},
        'limits': ['Closed fictional material only; no real jurisdiction or precedent.',
                   'Boolean model is assigned by the recorded clause analysis, not discovered by enumeration.',
                   'Only this exact reviewed normative block is supported; any other normative text is rejected pending legal review.',
                   'May apply is not a determination of final permit grant.'],
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'rows':len(rows),'distribution_differences':len(distribution_differences),
                      'applicants':{x['name']:x['may_apply_under_section_5'] for x in applicants},
                      'wrong_model_difference_counts':{k:len(v) for k,v in differences.items()}},ensure_ascii=False))


if __name__ == '__main__':
    main()
