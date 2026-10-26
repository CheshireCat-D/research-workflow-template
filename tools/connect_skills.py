#!/usr/bin/env python3
"""Explicit project-local skill connection; never alters user/global skills."""
from pathlib import Path
import argparse
import json
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.bundle import SCOPE, install, check, upgrade
from core.storage import CoreError
from core.cli import configure_cli_streams


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CoreError('arguments', message)


def main(argv=None):
    configure_cli_streams()
    try:
        parser = Parser(description='Connect research skills to one initialized project; no global installation.')
        commands = parser.add_subparsers(dest='command', required=True)
        for command in ('install', 'check', 'upgrade'):
            sub = commands.add_parser(command)
            sub.add_argument('--root', required=True)
            if command == 'check':
                sub.add_argument('--installed-only', action='store_true',
                                 help='Check copied files without requiring the source repository')
        args = parser.parse_args(argv)
        runtime_root = Path(__file__).resolve().parents[1]
        installed_context = (runtime_root.name == '_rw-runtime' and
                             (runtime_root / 'bundle-manifest.json').is_file())
        if args.command == 'install':
            result = install(args.root)
        elif args.command == 'upgrade':
            result = upgrade(args.root)
        else:
            result = check(args.root, compare_source=not (args.installed_only or installed_context))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
        return 0 if result['passed'] else 1
    except CoreError as exc:
        result = {'passed': False, 'scope': SCOPE,
                  'errors': [{'code': exc.code, 'message': exc.message}]}
    except (OSError, ValueError, RecursionError) as exc:
        result = {'passed': False, 'scope': SCOPE,
                  'errors': [{'code': 'io_or_input_error', 'message': str(exc)}]}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
