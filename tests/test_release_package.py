"""Packaging invariants with isolated tiny source fixtures, no external services."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from platform_support import symlink_or_skip
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('release_package',ROOT/'tools/release_package.py')
release=importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def snapshot(root):
    return {p.relative_to(root).as_posix():(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


class ReleasePackages(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='rw-release-unit-')
        self.base=Path(self.temp.name)
        self.source=self.base/'source'
        self.source.mkdir()
        for name in release.REQUIRED:
            p=self.source/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('MIT License\n' if name=='LICENSE' else 'Synthetic package fixture.\n', encoding='utf-8')
        release.index(self.source)

    def tearDown(self):
        self.temp.cleanup()

    def test_inventory_check_is_read_only_and_matches_explicit_public_files(self):
        before=snapshot(self.source)
        result=release.check(self.source)
        self.assertTrue(result['passed'])
        self.assertEqual(before,snapshot(self.source))
        self.assertEqual(result['files'],len(release.REQUIRED)+1)

    def test_archives_are_identical_despite_names_and_mtimes_and_verify_without_extracting(self):
        first=self.base/'first.zip';second=self.base/'second.zip'
        release.build(first,self.source)
        for p in self.source.rglob('*'):
            if p.is_file():os.utime(p,(1700000000,1700000000))
        release.build(second,self.source)
        self.assertEqual(first.read_bytes(),second.read_bytes())
        before=snapshot(self.base)
        self.assertTrue(release.verify(first)['passed'])
        self.assertEqual(before,snapshot(self.base))

    def test_current_archive_has_one_fixed_root_and_preserves_its_manifest(self):
        archive=self.base/'research-workflow-template.zip'
        result=release.build(archive,self.source)
        self.assertEqual(result['version'],'current')
        self.assertEqual(result['prefix'],'research-workflow-template')
        with zipfile.ZipFile(archive) as package:
            self.assertEqual({name.split('/')[0] for name in package.namelist()},
                             {'research-workflow-template'})
            manifest=json.loads(package.read('research-workflow-template/'+release.ARCHIVE_MANIFEST))
            self.assertEqual(manifest['prefix'],result['prefix'])
            self.assertEqual(manifest['version'],result['version'])
            self.assertEqual(set(manifest['files']),set(release.inventory(self.source)))
        verified=release.verify(archive)
        self.assertEqual(verified['prefix'],result['prefix'])
        self.assertEqual(verified['version'],result['version'])

    def test_chinese_root_guide_is_inventoried_and_delivered_with_original_bytes(self):
        guide=self.source/'中文介绍与使用说明.md'
        guide.write_text('# 中文介绍与使用说明\n\n只保留当前发行副本。\n',encoding='utf-8')
        release.index(self.source)
        archive=self.base/'with-chinese-guide.zip'
        result=release.build(archive,self.source)
        with zipfile.ZipFile(archive) as package:
            self.assertEqual(package.read(result['prefix']+'/'+guide.name),guide.read_bytes())
        self.assertTrue(release.verify(archive)['passed'])

    def test_only_reviewed_original_case_images_are_accepted_and_delivered(self):
        for name, expected in release.BINARY_SOURCE_ASSETS.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            data = (ROOT / name).read_bytes()
            self.assertEqual(release.digest(data), expected)
            path.write_bytes(data)
        release.index(self.source)
        archive = self.base / 'with-reviewed-images.zip'
        release.build(archive, self.source)
        with zipfile.ZipFile(archive) as package:
            for name in release.BINARY_SOURCE_ASSETS:
                self.assertEqual(package.read(release.ARCHIVE_ROOT + '/' + name), (ROOT / name).read_bytes())
        self.assertTrue(release.verify(archive)['passed'])
        unknown = self.source / 'evals/other-image.png'
        unknown.write_bytes(next((ROOT / name).read_bytes() for name in release.BINARY_SOURCE_ASSETS))
        with self.assertRaisesRegex(release.ReleaseError, 'Unexpected binary source'):
            release.index(self.source)

    def test_changed_image_is_rejected_even_with_consistent_archive_hashes(self):
        name = next(iter(release.BINARY_SOURCE_ASSETS))
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / name).read_bytes())
        release.index(self.source)
        archive = self.base / 'image-original.zip'
        release.build(archive, self.source)
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(release.ReleaseError, 'Unreviewed binary source bytes'):
            release.index(self.source)
        with zipfile.ZipFile(archive) as package:
            prefix = release.ARCHIVE_ROOT + '/'
            captured = {n[len(prefix):]: package.read(n) for n in package.namelist()}
        captured[name] += b'changed'
        inventory = json.loads(captured[release.INDEX])
        inventory['files'][name]['sha256'] = release.digest(captured[name])
        captured[release.INDEX] = release.encoded(inventory)
        manifest = json.loads(captured[release.ARCHIVE_MANIFEST])
        for changed in (name, release.INDEX):
            manifest['files'][changed] = release.digest(captured[changed])
        captured[release.ARCHIVE_MANIFEST] = release.encoded(manifest)
        changed_archive = self.base / 'image-rehashed.zip'
        with zipfile.ZipFile(changed_archive, 'w') as package:
            for relative, data in captured.items():
                package.writestr(prefix + relative, data)
        with self.assertRaisesRegex(release.ReleaseError, 'unreviewed_binary_source'):
            release.verify(changed_archive)

    def test_missing_bilingual_guides_block_source_check_and_build_even_after_reindexing(self):
        for name in ('中文介绍与使用说明.md','USER_GUIDE.en.md','README.en.md'):
            with self.subTest(name=name):
                guide=self.source/name
                original=guide.read_bytes()
                guide.unlink()
                release.index(self.source)
                before=snapshot(self.source)
                report=release.check(self.source)
                self.assertFalse(report['passed'])
                self.assertEqual(report['errors'],[{'code':'required_file_missing','path':name}])
                archive=self.base/'missing-guide.zip'
                with self.assertRaises(release.ReleaseError):release.build(archive,self.source)
                self.assertFalse(archive.exists())
                self.assertEqual(before,snapshot(self.source))
                guide.write_bytes(original)
                release.index(self.source)

    def test_missing_bilingual_guides_block_self_consistent_archive_verification(self):
        original=self.base/'complete.zip'
        release.build(original,self.source)
        with zipfile.ZipFile(original) as package:
            prefix=release.ARCHIVE_ROOT+'/'
            captured={name[len(prefix):]:package.read(name) for name in package.namelist()}
        for name in ('中文介绍与使用说明.md','USER_GUIDE.en.md','README.en.md'):
            with self.subTest(name=name):
                entries=dict(captured)
                del entries[name]
                index=json.loads(entries[release.INDEX])
                del index['files'][name]
                entries[release.INDEX]=release.encoded(index)
                manifest=json.loads(entries[release.ARCHIVE_MANIFEST])
                del manifest['files'][name]
                manifest['files'][release.INDEX]=release.digest(entries[release.INDEX])
                entries[release.ARCHIVE_MANIFEST]=release.encoded(manifest)
                archive=self.base/'missing-guide.zip'
                with zipfile.ZipFile(archive,'w') as package:
                    for relative,data in entries.items():package.writestr(prefix+relative,data)
                before=snapshot(self.base)
                with self.assertRaises(release.ReleaseError):release.verify(archive)
                self.assertEqual(before,snapshot(self.base))

    def test_legacy_versioned_root_verifies_but_mismatched_root_is_rejected(self):
        original=self.base/'current.zip'
        release.build(original,self.source)
        old_root='research-workflow-template-0.1.0rc3'
        for version,accepted in (('0.1.0rc3',True),('0.1.0rc2',False)):
            with self.subTest(version=version):
                target=self.base/('legacy-'+version+'.zip')
                with zipfile.ZipFile(original) as source,zipfile.ZipFile(target,'w') as output:
                    for info in source.infolist():
                        relative=info.filename.split('/',1)[1]
                        data=source.read(info)
                        if relative==release.ARCHIVE_MANIFEST:
                            manifest=json.loads(data)
                            manifest.update(version=version,prefix=old_root)
                            data=json.dumps(manifest).encode('utf-8')
                        renamed=zipfile.ZipInfo(old_root+'/'+relative,info.date_time)
                        renamed.create_system=info.create_system
                        renamed.external_attr=info.external_attr
                        output.writestr(renamed,data)
                before=snapshot(self.base)
                if accepted:
                    verified=release.verify(target)
                    self.assertEqual(verified['version'],version)
                    self.assertEqual(verified['prefix'],old_root)
                else:
                    with self.assertRaises(release.ReleaseError):
                        release.verify(target)
                self.assertEqual(before,snapshot(self.base))

    def test_index_drift_blocks_build_without_reindexing_or_overwriting(self):
        (self.source/'README.md').write_text('Reviewed content changed.\n', encoding='utf-8')
        before=snapshot(self.source)
        self.assertFalse(release.check(self.source)['passed'])
        with self.assertRaises(release.ReleaseError):release.build(self.base/'blocked.zip',self.source)
        self.assertFalse((self.base/'blocked.zip').exists())
        self.assertEqual(before,snapshot(self.source))

    def test_build_validates_and_archives_one_captured_source_snapshot(self):
        original_inventory=release.inventory
        captured=[]
        def edit_after_capture(root):
            entries=original_inventory(root)
            captured.append(entries)
            (self.source/'README.md').write_text('Edited after source capture.\n', encoding='utf-8')
            return entries
        archive=self.base/'captured.zip'
        with mock.patch.object(release,'inventory',side_effect=edit_after_capture) as inventory:
            result=release.build(archive,self.source)
        self.assertTrue(result['passed'])
        self.assertEqual(inventory.call_count,1)
        with zipfile.ZipFile(archive) as package:
            prefix=result['prefix']+'/'
            archived={name:package.read(prefix+name) for name in captured[0]}
        self.assertEqual(archived,captured[0])
        declared=json.loads(archived[release.INDEX])['files']
        for name,data in archived.items():
            if name!=release.INDEX:
                self.assertEqual(declared[name]['sha256'],hashlib.sha256(data).hexdigest())
        self.assertTrue(release.verify(archive)['passed'])
        self.assertFalse(release.check(self.source)['passed'])

    def test_existing_archive_and_link_are_not_overwritten(self):
        p=self.base/'keep.zip';p.write_bytes(b'Keep')
        with self.assertRaises(FileExistsError):release.build(p,self.source)
        self.assertEqual(p.read_bytes(),b'Keep')
        link=self.base/'link.zip';symlink_or_skip(self, link, p)
        with self.assertRaises(FileExistsError):release.build(link,self.source)
        self.assertEqual(p.read_bytes(),b'Keep')

    def test_link_and_credential_like_source_rejected_before_inventory_update(self):
        p=self.source/'docs';p.mkdir()
        outside=self.base/'outside.txt';outside.write_text('Not included', encoding='utf-8')
        symlink_or_skip(self, p/'linked.md', outside)
        with self.assertRaises(release.ReleaseError):release.inventory(self.source)
        (p/'linked.md').unlink()
        (p/'bad.md').write_text('ghp_'+'a'*36, encoding='utf-8')
        with self.assertRaises(release.ReleaseError):release.index(self.source)
        self.assertEqual(outside.read_text(encoding='utf-8'),'Not included')

    def test_archive_payload_change_and_unlisted_entries_are_rejected(self):
        original=self.base/'original.zip';release.build(original,self.source)
        for changed in ('payload','extra'):
            target=self.base/(changed+'.zip')
            with zipfile.ZipFile(original) as source,zipfile.ZipFile(target,'w') as output:
                for info in source.infolist():
                    data=source.read(info.filename)
                    if changed=='payload' and info.filename.endswith('/README.md'):data=b'Changed payload\n'
                    output.writestr(info,data)
                if changed=='extra':output.writestr('unexpected.txt','unlisted')
            with self.assertRaises(release.ReleaseError):release.verify(target)

    def rewrite_listed_payload(self,original,target,updates):
        """Keep the outer manifest consistent with chosen replacement bytes."""
        with zipfile.ZipFile(original) as source:
            entries={info.filename:(info,source.read(info.filename)) for info in source.infolist()}
        marker=next(name for name in entries if name.endswith('/'+release.ARCHIVE_MANIFEST))
        prefix=marker.rsplit('/',1)[0]+'/'
        manifest=json.loads(entries[marker][1])
        for name,data in updates.items():
            full=prefix+name
            entries[full]=(entries[full][0],data)
            manifest['files'][name]=hashlib.sha256(data).hexdigest()
        entries[marker]=(entries[marker][0],json.dumps(manifest).encode())
        with zipfile.ZipFile(target,'w') as output:
            for info,data in entries.values():output.writestr(info,data)

    def test_rehashed_release_manifest_cannot_hide_stale_internal_provenance(self):
        original=self.base/'original.zip';release.build(original,self.source)
        target=self.base/'rehashed-payload.zip'
        self.rewrite_listed_payload(original,target,{'README.md':b'Changed payload\n'})
        before=snapshot(self.base)
        with self.assertRaises(release.ReleaseError):release.verify(target)
        self.assertEqual(before,snapshot(self.base))

    def test_rehashed_release_manifest_cannot_hide_invalid_provenance_records(self):
        original=self.base/'original.zip';release.build(original,self.source)
        for problem in ('missing-record','wrong-origin','wrong-license','non-object-index'):
            with self.subTest(problem=problem):
                declared=json.loads((self.source/release.INDEX).read_bytes())
                if problem=='missing-record':del declared['files']['README.md']
                elif problem=='wrong-origin':declared['files']['README.md']['origin']='unreviewed'
                elif problem=='wrong-license':declared['files']['README.md']['license']='unknown'
                else:declared=[]
                target=self.base/(problem+'.zip')
                self.rewrite_listed_payload(original,target,{release.INDEX:json.dumps(declared).encode()})
                with self.assertRaises(release.ReleaseError):release.verify(target)

    def test_non_object_archive_manifests_return_structured_cli_errors(self):
        original=self.base/'original.zip';release.build(original,self.source)
        for number,manifest in enumerate(([],None,'manifest',17,True)):
            with self.subTest(manifest=manifest):
                target=self.base/('manifest-'+str(number)+'.zip')
                with zipfile.ZipFile(original) as source,zipfile.ZipFile(target,'w') as output:
                    for info in source.infolist():
                        data=source.read(info.filename)
                        if info.filename.endswith('/'+release.ARCHIVE_MANIFEST):
                            data=json.dumps(manifest).encode()
                        output.writestr(info,data)
                before=snapshot(self.base)
                result=subprocess.run([sys.executable,'-X','utf8','-I','-B',str(ROOT/'tools/release_package.py'),
                                       'verify','--archive',str(target)],
                                      capture_output=True,text=True, encoding='utf-8',timeout=20)
                self.assertEqual(result.returncode,2,result.stdout+result.stderr)
                self.assertEqual(result.stderr,'')
                report=json.loads(result.stdout)
                self.assertFalse(report['passed'])
                self.assertEqual(report['errors'][0]['code'],'release_error')
                self.assertEqual(before,snapshot(self.base))

    def test_parent_path_archive_is_rejected_without_extraction(self):
        archive=self.base/'escape.zip'
        with zipfile.ZipFile(archive,'w') as output:output.writestr('../escape.txt','Do not extract')
        before=snapshot(self.base)
        with self.assertRaises(release.ReleaseError):release.verify(archive)
        self.assertEqual(before,snapshot(self.base))
        self.assertFalse((self.base.parent/'escape.txt').exists())


if __name__=='__main__':unittest.main()
