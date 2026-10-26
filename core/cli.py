"""Small standard-library command line interface; never runs commands from records."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import __version__

from .model import RECORD_KINDS
from .bundle import catalog_view
from .project import SCOPE, initialize, register, register_batch, show, configure, checkpoint, inspect, catalog
from .storage import CoreError, ProjectFiles, read_input


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CoreError('arguments', message)


def configure_cli_streams():
    """Keep the JSON/Markdown CLI contract UTF-8, including Windows pipes."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, 'reconfigure', None)
        if callable(reconfigure):
            reconfigure(encoding='utf-8', newline='\n')


def parser():
    p = Parser(description='Research metadata and recovery core. No scientific/ethics certification or network access.')
    p.add_argument('--version', action='version', version=__version__)
    commands = p.add_subparsers(dest='command', required=True)
    commands.add_parser('options', help='Read stable discipline/method IDs and available skill entries; no project needed')
    init = commands.add_parser('init', help='Create a new neutral project without overwriting a path')
    init.add_argument('--output', required=True)
    init.add_argument('--title', required=True)
    init.add_argument('--interest')
    init.add_argument('--discipline', action='append', default=[], help='Stable catalog ID; list with options')
    init.add_argument('--method', action='append', default=[], help='Stable catalog ID; list with options')
    init.add_argument('--mode', choices=['light', 'structured', 'reproducible'], default='light')
    init.add_argument('--language', default='zh')
    init.add_argument('--entry', default='question')
    reg = commands.add_parser('register', help='Register one JSON record; updates preserve the previous version')
    reg.add_argument('--root', required=True)
    reg.add_argument('--kind', choices=RECORD_KINDS, required=True)
    reg.add_argument('--file', required=True, help='JSON record file, or - to read bounded JSON from stdin')
    reg.add_argument('--replace', action='store_true')
    reg.add_argument('--expected-version', type=int)
    batch = commands.add_parser('register-batch', help='Atomically register an ordered JSON array; any failure rolls back the batch')
    batch.add_argument('--root', required=True)
    batch.add_argument('--file', required=True, help='JSON batch file, or - for stdin')
    query = commands.add_parser('show', help='Read a full registered envelope or ID/version summaries without creating a lock')
    query.add_argument('--root', required=True)
    query.add_argument('--kind', choices=RECORD_KINDS)
    query.add_argument('--id')
    config = commands.add_parser('configure', help='Update supported project configuration; does not certify venue or governance compliance')
    config.add_argument('--root', required=True)
    config.add_argument('--add-discipline', action='append', default=[])
    config.add_argument('--add-method', action='append', default=[])
    config.add_argument('--mode', choices=['light', 'structured', 'reproducible'])
    config.add_argument('--venue')
    config.add_argument('--governance-applicability', choices=['unknown', 'applicable', 'not-applicable'])
    config.add_argument('--add-governance-requirement', action='append', default=[])
    for command in ('check', 'status', 'resume'):
        sub = commands.add_parser(command, help='Read-only registration and freshness inspection')
        sub.add_argument('--root', required=True)
        if command == 'resume':
            sub.add_argument('--format', choices=['json', 'markdown'], default='json')
    cp = commands.add_parser('checkpoint', help='Save current fingerprints and a recovery next action')
    cp.add_argument('--root', required=True)
    cp.add_argument('--next-action', required=True)
    cp.add_argument('--activity')
    cp.add_argument('--note')
    return p


def recovery_markdown(result):
    """Render the same inspected snapshot with actionable freshness details."""
    lines = ['# Research recovery', '', 'Scientific validity: not assessed.', '',
             'Revision: ' + str(result['revision']), '',
             'Checkpoint status: ' + result['checkpoint']['status'], '',
             'Needs review: ' + str(result['needs_review']).lower(), '',
             '## Findings', '']
    if not result['findings']:
        lines.append('None reported by this local inspection.')
    for finding in result['findings']:
        details = [finding['code']]
        for key, value in finding.items():
            if key != 'code':
                details.append(key + ': ' + json.dumps(value, ensure_ascii=False))
        lines.append('- ' + '; '.join(details))
    lines.extend(['', '## Activities needing attention', ''])
    attention = [activity for activity in result['activities']
                 if activity['effective_status'] in ('stale', 'in-progress')]
    if not attention:
        lines.append('No stale or in-progress activities reported.')
    for activity in attention:
        lines.append('- ' + activity['id'] + ' — ' + json.dumps(activity['title'], ensure_ascii=False)
                     + ' (' + activity['effective_status'] + ')')
        for reason in activity['stale_reasons']:
            lines.append('  - ' + reason)
    lines.extend(['', '## Saved next action', '', result['next_action'], '',
                  result['recovery_instruction']])
    return '\n'.join(lines)


def user_runtime_context(toolkit):
    """A delivered user archive is portable guidance, not the source evidence tree."""
    marker = toolkit / 'USER-PACKAGE-MANIFEST.json'
    if not marker.is_file():
        return False
    try:
        value = json.loads(marker.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return False
    return (isinstance(value, dict) and value.get('format_version') == 1 and
            value.get('profile') == 'user-runtime' and
            value.get('prefix') == 'research-workflow-template')


def main(argv=None):
    configure_cli_streams()
    try:
        args = parser().parse_args(argv)
        if args.command == 'options':
            toolkit = Path(__file__).resolve().parents[1]
            choices = catalog_view(catalog(), toolkit,
                                   project_runtime=((toolkit/'bundle-manifest.json').is_file() or
                                                    user_runtime_context(toolkit)))
            skills = [dict(item) for item in choices['skills']]
            for item in skills:
                if ('entrypoint' in item and not (toolkit / item['entrypoint']).is_file() and
                        (toolkit.parent / item['id'] / 'SKILL.md').is_file()):
                    item['entrypoint'] = '../' + item['id'] + '/SKILL.md'
            result = {'passed': True, 'read_only': True, 'version': __version__,
                      'scope': 'Stable choices, declared guidance and explicit recorded binding availability only; not task validity.',
                      'resource_base': 'toolkit-root',
                      'scientific_validity': 'not-assessed',
                      'disciplines': choices['disciplines'], 'methods': choices['methods'],
                      'skills': skills, 'entry_activities': choices['activities'],
                      'workflow_modes': choices['workflow_modes']}
        elif args.command == 'init':
            result = initialize(args.output, args.title, interest=args.interest,
                                disciplines=args.discipline, methods=args.method,
                                mode=args.mode, language=args.language, entry=args.entry)
        elif args.command == 'register':
            result = register(args.root, args.kind, read_input(args.file), replace=args.replace,
                              expected_version=args.expected_version)
        elif args.command == 'register-batch':
            result = register_batch(args.root, read_input(args.file))
        elif args.command == 'show':
            result = show(args.root, kind=args.kind, identifier=args.id)
        elif args.command == 'configure':
            result = configure(args.root, add_disciplines=args.add_discipline,
                               add_methods=args.add_method, mode=args.mode, venue=args.venue,
                               governance_applicability=args.governance_applicability,
                               add_governance_requirements=args.add_governance_requirement)
        elif args.command == 'checkpoint':
            result = checkpoint(args.root, args.next_action, activity=args.activity, note=args.note)
        else:
            with ProjectFiles(args.root) as files:
                result = inspect(files)
            if args.command == 'resume':
                result['next_action'] = result['cursor']['next_action']
                result['needs_review'] = not result['passed']
                result['recovery_instruction'] = ('Review changed inputs and affected activities before following the saved next action.'
                                                  if not result['passed'] else 'Continue the recorded next action within its existing scope.')
                if args.format == 'markdown':
                    print(recovery_markdown(result))
                    return 0 if result['passed'] else 1
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
        return 0 if result.get('passed', True) else 1
    except CoreError as exc:
        result = {'passed': False, 'scope': SCOPE, 'scientific_validity': 'not-assessed',
                  'errors': [{'code': exc.code, 'message': exc.message}]}
    except (OSError, ValueError, RecursionError) as exc:
        result = {'passed': False, 'scope': SCOPE, 'scientific_validity': 'not-assessed',
                  'errors': [{'code': 'io_or_input_error', 'message': str(exc)}]}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 2


if __name__ == '__main__':
    sys.exit(main())
