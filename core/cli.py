"""Small standard-library command line interface; never runs commands from records."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import __version__

from .model import RECORD_KINDS
from .bundle import catalog_view, build_payload, install
from .project import SCOPE, initialize, register, register_batch, show, configure, checkpoint, inspect, catalog, recovery_view
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
    init.add_argument('--connect-skills', action='store_true',
                      help='Also install the nine project-local skills from this toolkit')
    reg = commands.add_parser('register', help='Register one JSON record; updates preserve the previous version')
    reg.add_argument('--root', default='.', help='Project root; defaults to the current directory only')
    reg.add_argument('--kind', choices=RECORD_KINDS, required=True)
    reg.add_argument('--file', required=True, help='JSON record file, or - to read bounded JSON from stdin')
    reg.add_argument('--replace', action='store_true')
    reg.add_argument('--expected-version', type=int)
    batch = commands.add_parser('register-batch', help='Register an ordered JSON array in one commit after validation')
    batch.add_argument('--root', default='.', help='Project root; defaults to the current directory only')
    batch.add_argument('--file', required=True, help='JSON batch file, or - for stdin')
    for sub in (reg, batch):
        sub.add_argument('--next-action', help='Also save a checkpoint and return the inspected recovery state in one commit')
        sub.add_argument('--activity', help='Checkpoint activity; requires --next-action')
        sub.add_argument('--note', help='Checkpoint note; requires --next-action')
    query = commands.add_parser('show', help='Read a full registered envelope or ID/version summaries without creating a lock')
    query.add_argument('--root', default='.', help='Project root; defaults to the current directory only')
    query.add_argument('--kind', choices=RECORD_KINDS)
    query.add_argument('--id')
    query.add_argument('--data-only', action='store_true', help='Export one editable record; requires --kind and --id')
    query.add_argument('--edit', nargs='+', action='extend', metavar='KIND:ID',
                       help='Export editable batch records with fixed expected versions; exclusive with kind/id/data-only')
    config = commands.add_parser('configure', help='Update supported project configuration; does not certify venue or governance compliance')
    config.add_argument('--root', default='.', help='Project root; defaults to the current directory only')
    config.add_argument('--add-discipline', action='append', default=[])
    config.add_argument('--add-method', action='append', default=[])
    config.add_argument('--mode', choices=['light', 'structured', 'reproducible'])
    config.add_argument('--venue')
    config.add_argument('--interest')
    config.add_argument('--deadline')
    config.add_argument('--budget')
    config.add_argument('--add-capability', action='append', default=[])
    config.add_argument('--governance-applicability', choices=['unknown', 'applicable', 'not-applicable'])
    config.add_argument('--add-governance-requirement', action='append', default=[])
    for command in ('check', 'status', 'resume'):
        sub = commands.add_parser(command, help='Read-only registration and freshness inspection')
        sub.add_argument('--root', default='.', help='Project root; defaults to the current directory only')
        if command == 'resume':
            sub.add_argument('--format', choices=['json', 'markdown'], default='json')
    cp = commands.add_parser('checkpoint', help='Save current fingerprints and a recovery next action')
    cp.add_argument('--root', default='.', help='Project root; defaults to the current directory only')
    cp.add_argument('--next-action', required=True)
    cp.add_argument('--activity')
    cp.add_argument('--note')
    cp.add_argument('--report', action='store_true', help='Return the inspected recovery state with this checkpoint')
    return p


def recovery_markdown(result):
    """Render the same inspected snapshot with actionable freshness details."""
    lines = ['# Research recovery', '', 'Scientific validity: not assessed.', '',
             'Revision: ' + str(result['revision']), '',
             'Checkpoint status: ' + result['checkpoint']['status'], '',
             'Needs review: ' + str(result['needs_review']).lower(), '',
             '## Project context', '']
    configuration = result['configuration']
    context = [('Title', configuration['title']), ('Question / interest', configuration['interest']),
               ('Disciplines', configuration['disciplines']), ('Methods', configuration['methods']),
               ('Venue', configuration['deliverable']['venue']),
               ('Deadline', configuration['resources']['deadline']), ('Budget', configuration['resources']['budget']),
               ('Available capabilities', configuration['resources']['available_capabilities'])]
    lines.extend(label + ': ' + json.dumps(value, ensure_ascii=False) for label, value in context)
    tracking = result['file_tracking']
    lines.extend(['', '## File tracking', '',
                  'Bound local files: ' + str(tracking['local_file_count']),
                  'Local paths: ' + json.dumps(tracking['local_files'], ensure_ascii=False),
                  'Sources without local evidence: ' + json.dumps(tracking['source_ids_without_local_evidence'], ensure_ascii=False),
                  'Source locators identify materials; their file contents are not inspected. '
                  'Link a local evidence record through source_ids to track a local copy. '
                  'Bound paths can be missing or changed; review the findings below.',
                  '', '## Findings', ''])
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
            if args.connect_skills:
                # Validate the toolkit before creating a project. Installation
                # still checks it again and never touches global skills.
                build_payload()
            result = initialize(args.output, args.title, interest=args.interest,
                                disciplines=args.discipline, methods=args.method,
                                mode=args.mode, language=args.language, entry=args.entry)
            if args.connect_skills:
                try:
                    result['skill_connection'] = install(args.output)
                    result['passed'] = result['skill_connection']['passed']
                except (CoreError, OSError, ValueError) as exc:
                    # Retain the initialized project and report the real partial
                    # state; re-running init would correctly refuse this path.
                    result['passed'] = False
                    result['initialized'] = True
                    result['skill_connection'] = {
                        'passed': False,
                        'errors': [{'code': getattr(exc, 'code', 'io_or_input_error'),
                                    'message': getattr(exc, 'message', str(exc))}],
                    }
                    result['next_action'] = (
                        'The project was initialized. Inspect the connection error, '
                        'then use tools/connect_skills.py install --root with the '
                        'existing project path; do not run init again.')
        elif args.command == 'register':
            result = register(args.root, args.kind, read_input(args.file), replace=args.replace,
                              expected_version=args.expected_version, next_action=args.next_action,
                              activity=args.activity, note=args.note)
        elif args.command == 'register-batch':
            result = register_batch(args.root, read_input(args.file), next_action=args.next_action,
                                    activity=args.activity, note=args.note)
        elif args.command == 'show':
            result = show(args.root, kind=args.kind, identifier=args.id, data_only=args.data_only,
                          edit_refs=args.edit)
        elif args.command == 'configure':
            result = configure(args.root, add_disciplines=args.add_discipline,
                               add_methods=args.add_method, mode=args.mode, venue=args.venue,
                               interest=args.interest, deadline=args.deadline, budget=args.budget,
                               add_capabilities=args.add_capability,
                               governance_applicability=args.governance_applicability,
                               add_governance_requirements=args.add_governance_requirement)
        elif args.command == 'checkpoint':
            result = checkpoint(args.root, args.next_action, activity=args.activity, note=args.note,
                                with_recovery=args.report)
        else:
            with ProjectFiles(args.root) as files:
                result = inspect(files)
            if args.command == 'resume':
                result = recovery_view(result)
                if args.format == 'markdown':
                    print(recovery_markdown(result))
                    return 0 if result['passed'] else 1
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
        return 0 if not isinstance(result, dict) or result.get('passed', True) else 1
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
