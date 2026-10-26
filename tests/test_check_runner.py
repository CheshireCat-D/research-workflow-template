"""Check-runner completion, timeout reporting and CLI timeout validation."""
from pathlib import Path
from copy import deepcopy
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
    def test_bounded_failure_output_retains_early_and_late_stacks(self):
        early = ('=' * 70 + '\nERROR: early_native_failure (storage.Test)\n' +
                 '-' * 70 + '\nTraceback (most recent call last):\n' +
                 'early frame\n' * 2000 + 'PermissionError: early lock failure\n')
        late = ('=' * 70 + '\nFAIL: late_native_failure (bundle.Test)\n' +
                '-' * 70 + '\nTraceback (most recent call last):\n' +
                'late frame\n' * 2000 + 'AssertionError: late publication failure\n')
        output = ('test progress\n' * 1000 + early + late +
                  'Ran 188 tests in 1.000s\n\nFAILED (failures=1, errors=1)\n')
        captured = runner.bounded_test_output(output, 3000)
        self.assertLessEqual(len(captured), 3000)
        for expected in ('ERROR: early_native_failure', 'PermissionError: early lock failure',
                         'FAIL: late_native_failure', 'AssertionError: late publication failure',
                         'Ran 188 tests', 'FAILED (failures=1, errors=1)'):
            self.assertIn(expected, captured)

    def test_bounded_output_preserves_short_reports_and_timeout_tail(self):
        short = 'Ran 1 test in 0.001s\n\nOK\n'
        self.assertEqual(runner.bounded_test_output(short), short)
        captured = runner.bounded_test_output('progress\n' * 1000 + 'last partial output', 1000)
        self.assertLessEqual(len(captured), 1000)
        self.assertTrue(captured.endswith('last partial output'))

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

    def test_frontmatter_rejects_ambiguous_yaml_plain_scalars_and_syntax(self):
        invalid = ('123', '-1.5', '.Inf', '+.inf', '.NaN', '0xFF', '1e3', '12:34',
                   'True', 'YES', 'off', 'NULL', '~', '2026-10-25',
                   '2026-10-25T09:15:00Z', 'true # boolean comment',
                   'Validate: research arguments', 'Read # a comment', '- item',
                   '@reserved', '%directive', '`code`', ']closing', '}closing', ',flow')
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                runner.skill_metadata('---\nname: rw-example\ndescription: ' + value + '\n---\n')

    def test_frontmatter_keeps_quoted_scalars_and_safe_prose_as_strings(self):
        examples = {
            '"123"': '123',
            "'true # literal'": 'true # literal',
            '"Validate: research arguments"': 'Validate: research arguments',
            'Review C# and https://example.invalid/source': 'Review C# and https://example.invalid/source',
            '2026-10-25 migration guide': '2026-10-25 migration guide',
            '检查数学与法学论证：保留限定': '检查数学与法学论证：保留限定',
        }
        for value, expected in examples.items():
            with self.subTest(value=value):
                fields = runner.skill_metadata('---\nname: rw-example\ndescription: ' + value + '\n---\n')
                self.assertEqual(fields['description'], expected)

    def test_catalog_rejects_duplicate_stable_ids_without_dictionary_collapse(self):
        catalog = json.loads((ROOT/'design/catalog.json').read_text(encoding='utf-8'))
        cases = json.loads((ROOT/'design/scenarios.json').read_text(encoding='utf-8'))['cases']
        self.assertEqual(runner.catalog_reference_errors(catalog, cases), [])
        for group, label in (('disciplines', 'discipline'), ('methods', 'method'), ('skills', 'skill')):
            with self.subTest(group=group):
                changed = deepcopy(catalog)
                changed[group].append(deepcopy(changed[group][0]))
                errors = runner.catalog_reference_errors(changed, cases)
                self.assertIn('Repeated '+label+' ID: '+changed[group][0]['id'], errors)
        duplicate_cases = deepcopy(cases) + [deepcopy(cases[0])]
        self.assertIn('Repeated scenario ID: '+cases[0]['id'],
                      runner.catalog_reference_errors(catalog, duplicate_cases))

    def test_catalog_rejects_bad_suggestions_and_variant_lists(self):
        catalog = json.loads((ROOT/'design/catalog.json').read_text(encoding='utf-8'))
        cases = json.loads((ROOT/'design/scenarios.json').read_text(encoding='utf-8'))['cases']
        for mutation, expected in (
            ('unknown-suggestion', 'Unknown suggested method: '),
            ('repeated-suggestion', 'Repeated suggested methods: '),
            ('repeated-variant', 'Repeated method variants: '),
            ('repeated-supported', 'Repeated supported variants: '),
            ('unknown-supported', 'Unknown supported variant: '),
        ):
            with self.subTest(mutation=mutation):
                changed = deepcopy(catalog)
                discipline = changed['disciplines'][0]
                method = changed['methods'][0]
                if mutation == 'unknown-suggestion':
                    discipline['suggested_methods'].append('not-a-real-method')
                elif mutation == 'repeated-suggestion':
                    discipline['suggested_methods'].append(discipline['suggested_methods'][0])
                elif mutation == 'repeated-variant':
                    method['variants'].append(method['variants'][0])
                elif mutation == 'repeated-supported':
                    method['implementation']['supported_variants'].append(method['implementation']['supported_variants'][0])
                else:
                    method['implementation']['supported_variants'].append('not-a-real-variant')
                errors = runner.catalog_reference_errors(changed, cases)
                self.assertTrue(any(error.startswith(expected) for error in errors), errors)

    def test_ignored_generated_and_private_trees_do_not_break_source_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'guide.md').write_text('# Maintained guide\n', encoding='utf-8')
            for name in ('.git', '.venv', 'venv', 'build', 'dist', '__pycache__',
                         '.agents', '.research', 'private-data', 'local-config', 'node_modules'):
                folder = root/name
                folder.mkdir()
                (folder/'generated.md').write_text('[Generated only](missing.md)\n', encoding='utf-8')
                (folder/'generated.py').write_text('not valid Python!!!\n', encoding='utf-8')
            self.assertEqual(runner.source_link_errors(root), [])
            self.assertEqual(list(runner.source_files(root, '.py')), [])
            (root/'docs').mkdir()
            (root/'docs'/'maintained.md').write_text('[Missing maintained target](missing.md)\n', encoding='utf-8')
            self.assertEqual(runner.source_link_errors(root),
                             [{'document': 'docs/maintained.md', 'link': 'missing.md'}])

    def test_bad_catalog_file_fails_the_real_static_check_even_when_suite_succeeds(self):
        # A real temporary catalog is read by main; only the expensive unittest
        # child is stubbed. Existing resources are copied without Git/build data.
        from tools.release_package import inventory
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, data in inventory(ROOT).items():
                target = root/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            path = root/'design/catalog.json'
            catalog = json.loads(path.read_text(encoding='utf-8'))
            catalog['disciplines'][0]['suggested_methods'].append('not-a-real-method')
            path.write_text(json.dumps(catalog), encoding='utf-8')
            complete = subprocess.CompletedProcess(['unittest'], 0, '', 'Ran 2 tests in 0.001s\n\nOK\n')
            with mock.patch.object(runner, 'ROOT', root):
                status, report, _ = self.invoke(lambda *args, **kwargs: complete, [])
            self.assertEqual(status, 1)
            check = next(item for item in report['checks'] if item['check']=='design-reference-consistency')
            self.assertFalse(check['passed'])
            self.assertTrue(any('Unknown suggested method:' in error
                                for error in check['detail']['invalid_references']))

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
        self.assertEqual(run.call_args.kwargs['encoding'], 'utf-8')
        self.assertEqual(run.call_args.args[0][1:3], ['-X', 'utf8'])

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
