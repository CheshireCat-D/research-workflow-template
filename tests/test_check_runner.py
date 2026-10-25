"""Check-runner completion, timeout reporting and CLI timeout validation."""
from pathlib import Path
import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rw_check_runner', ROOT / 'tools/check_core.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class CheckRunnerTests(unittest.TestCase):
    def test_frontmatter_supports_nonempty_folded_and_literal_descriptions(self):
        for marker in ('>', '>-', '>+', '|', '|-', '|+'):
            with self.subTest(marker=marker):
                fields = runner.skill_metadata('---\nname: rw-example\ndescription: ' + marker +
                    '\n  Read a specific\n  research record.\nmetadata:\n  short-description: Example\n---\n')
                self.assertEqual(fields['name'], 'rw-example')
                self.assertIn('research record.', fields['description'])
        self.assertEqual(runner.skill_metadata('---\nname: "rw-example"\ndescription: \'Read a record\'\n---\n')['description'],
                         'Read a record')

    def test_frontmatter_rejects_empty_or_structured_discovery_values(self):
        invalid = ('description: >-\n', 'description: >-\n  \n',
                   'description: ""\n', 'description: [a, b]\n',
                   'description: false\n', 'description: text\ndescription: duplicate\n')
        for field in invalid:
            with self.subTest(field=field), self.assertRaises(ValueError):
                runner.skill_metadata('---\nname: rw-example\n' + field + '---\n')

    def test_installed_links_use_nested_document_parent_and_decoded_paths(self):
        payload = {
            'rw-example/references/nested/start.md':
                b'[protocol](../../../_rw-runtime/core/protocol.md#scope)\n'
                b'[schemas](../../../_rw-runtime/core/schemas/)\n'
                b'[note](<../a%20note.md>)',
            'rw-example/references/a note.md': b'# Note',
            '_rw-runtime/core/protocol.md': b'# Protocol',
            '_rw-runtime/core/schemas/project.json': b'{}',
        }
        self.assertEqual(runner.payload_link_errors(payload), [])

    def test_installed_link_check_reports_missing_and_escaping_resources(self):
        errors = runner.payload_link_errors({'rw-example/SKILL.md':
            b'[missing](../_rw-runtime/missing.md)\n![outside](../../secret.png)'})
        self.assertEqual(len(errors), 2)
        self.assertEqual({row['target'] for row in errors},
                         {'_rw-runtime/missing.md', '../secret.png'})

    def test_installed_links_cover_reference_definitions_and_ignore_code_and_urls(self):
        payload = {'rw-example/SKILL.md': b'[protocol][p]\n[p]: ../_rw-runtime/protocol.md\n'
            b'`[code](missing.md)`\n```md\n[example](missing.md)\n```\n'
            b'[web](https://example.invalid/guide)\n[part](#section)',
            '_rw-runtime/protocol.md': b'# Protocol'}
        self.assertEqual(runner.payload_link_errors(payload), [])

    def test_source_links_accept_angles_and_encoded_spaces_without_scanning_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'a note.md').write_text('# Note\n', encoding='utf-8')
            document = root / 'guide.md'
            document.write_text('[note](<a%20note.md#section>)\n'
                '`[example](missing.md)`\n```md\n[example](missing.md)\n```\n',
                encoding='utf-8')
            self.assertEqual(runner.source_link_errors(root), [])
            with document.open('a', encoding='utf-8') as stream:
                stream.write('[missing](<absent%20note.md>)\n')
            self.assertEqual(runner.source_link_errors(root),
                [{'document': 'guide.md', 'link': 'absent%20note.md'}])

    def invoke(self, outcome, arguments):
        output, errors = io.StringIO(), io.StringIO()
        with mock.patch.object(runner.subprocess, 'run', side_effect=outcome) as run:
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                status = runner.main(arguments)
        self.assertEqual(errors.getvalue(), '')
        return status, json.loads(output.getvalue()), run

    def test_timeout_reports_failed_json_with_partial_output_and_configured_limit(self):
        expired = subprocess.TimeoutExpired(['unittest'], 0.25,
                                            output=b'partial stdout\n', stderr=b'partial stderr \xff\n')
        status, report, run = self.invoke(expired, ['--test-timeout', '0.25'])
        self.assertEqual(status, 1)
        self.assertFalse(report['passed'])
        check = next(x for x in report['checks'] if x['check'] == 'actual-unit-and-cli-tests')
        self.assertFalse(check['passed'])
        self.assertTrue(check['detail']['timed_out'])
        self.assertEqual(check['detail']['tests_run'], 0)
        self.assertIsNone(check['detail']['exit_code'])
        self.assertEqual(check['detail']['timeout_seconds'], 0.25)
        self.assertIn('partial stdout', check['detail']['output'])
        self.assertIn('partial stderr', check['detail']['output'])
        self.assertIn('\ufffd', check['detail']['output'])
        self.assertEqual(run.call_args.kwargs['timeout'], 0.25)

    def test_completed_suite_retains_test_count_and_default_timeout(self):
        complete = subprocess.CompletedProcess(['unittest'], 0, '', 'Ran 2 tests in 0.001s\n\nOK\n')
        status, report, run = self.invoke(lambda *a, **k: complete, [])
        self.assertEqual(status, 0)
        self.assertTrue(report['passed'])
        check = next(x for x in report['checks'] if x['check'] == 'actual-unit-and-cli-tests')
        self.assertTrue(check['passed'])
        self.assertFalse(check['detail']['timed_out'])
        self.assertEqual(check['detail']['tests_run'], 2)
        self.assertEqual(check['detail']['exit_code'], 0)
        self.assertEqual(run.call_args.kwargs['timeout'], 180)

    def test_completed_failed_suite_remains_failed(self):
        complete = subprocess.CompletedProcess(['unittest'], 1, '', 'Ran 1 test in 0.001s\n\nFAILED\n')
        status, report, _ = self.invoke(lambda *a, **k: complete, ['--test-timeout', '30'])
        self.assertEqual(status, 1)
        self.assertFalse(report['passed'])
        check = next(x for x in report['checks'] if x['check'] == 'actual-unit-and-cli-tests')
        self.assertEqual(check['detail']['tests_run'], 1)
        self.assertEqual(check['detail']['exit_code'], 1)
        self.assertFalse(check['detail']['timed_out'])

    def test_broken_generated_layout_is_a_failed_check_even_if_unit_suite_passes(self):
        payload = dict(runner.build_payload())
        payload['rw-workflow/references/broken.md'] = b'[missing](missing.md)'
        complete = subprocess.CompletedProcess(['unittest'], 0, '', 'Ran 2 tests in 0.001s\n\nOK\n')
        with mock.patch.object(runner, 'build_payload', return_value=payload):
            status, report, _ = self.invoke(lambda *a, **k: complete, [])
        self.assertEqual(status, 1)
        check = next(x for x in report['checks'] if x['check'] == 'installed-layout-document-links')
        self.assertFalse(check['passed'])
        self.assertTrue(any(x['document'].endswith('broken.md') for x in check['detail']))

    def test_invalid_timeout_is_rejected_before_running_checks(self):
        for value in ('0', '-1', 'nan', 'inf', 'not-a-number'):
            with self.subTest(value=value):
                output, errors = io.StringIO(), io.StringIO()
                with mock.patch.object(runner, 'export_schemas') as schemas:
                    with mock.patch.object(runner.subprocess, 'run') as run:
                        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                            with self.assertRaises(SystemExit) as caught:
                                runner.main(['--test-timeout', value])
                self.assertEqual(caught.exception.code, 2)
                self.assertEqual(output.getvalue(), '')
                self.assertIn('--test-timeout', errors.getvalue())
                schemas.assert_not_called()
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
