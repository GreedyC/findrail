import io
import json
import pathlib
import sys
import tarfile
import tempfile
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import release_assets as release


class ReleaseAssetTests(unittest.TestCase):
    def candidate(self, root, revision='a' * 40, dirty=False, version='0.1.0-alpha.4', schema=None):
        source = root / 'input'
        source.mkdir()
        schema = release.contract_schema(version) if schema is None else schema
        for name, target in release.expected_archives(version).items():
            stem = pathlib.Path(name).name.removesuffix('.tar.gz').removesuffix('.zip')
            info = {'version': version, 'revision': revision, 'dirty': dirty,
                    'target': target, 'schema_version': schema}
            members = {'BUILD-INFO.json': json.dumps(info).encode(),
                       'INSTALL.txt': b'x', 'LICENSE': b'x', 'NOTICE': b'x',
                       'licenses/DEPENDENCIES.txt': b'x', 'licenses/Go-LICENSE.txt': b'x'}
            if target.startswith('windows-'):
                members['findrail.exe'] = b'fake'
                with zipfile.ZipFile(source / name, 'w') as zf:
                    for path, data in members.items():
                        item = zipfile.ZipInfo(f'{stem}/{path}')
                        item.external_attr = (0o100755 if path == 'findrail.exe' else 0o100644) << 16
                        zf.writestr(item, data)
            else:
                members['findrail'] = b'fake'
                with tarfile.open(source / name, 'w:gz') as tf:
                    for path, data in members.items():
                        item = tarfile.TarInfo(f'{stem}/{path}')
                        item.size = len(data)
                        item.mode = 0o755 if path == 'findrail' else 0o644
                        tf.addfile(item, io.BytesIO(data))
        with zipfile.ZipFile(source / release.VSIX, 'w') as zf:
            zf.writestr('extension/package.json', json.dumps({'version': '0.1.0', 'name': 'findrail-readonly',
                'publisher': 'findrail-local', 'main': './dist/extension.js', 'extensionKind': ['ui']}))
            for name in ('[Content_Types].xml', 'extension.vsixmanifest', 'extension/LICENSE.txt',
                         'extension/readme.md', 'extension/changelog.md', 'extension/dist/extension.js'):
                zf.writestr(name, 'fixture')
        return source, revision

    def test_candidate_manifest_archive_metadata_and_checksums(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); source, revision = self.candidate(root); output = root / 'release'
            manifest = release.assemble(source, output, '0.1.0-alpha.4', revision)
            self.assertEqual(manifest['schema_version'], 6)
            self.assertEqual(len(manifest['assets']), 6)
            self.assertEqual(release.verify(output, '0.1.0-alpha.4', revision), manifest)

    def test_candidate_schema_is_source_derived_and_supports_next_migration(self):
        with patch.object(release.package, 'schema_version', return_value=7):
            self.assertEqual(release.contract_schema('0.1.0-alpha.4'), 7)
        self.assertEqual(release.contract_schema('0.1.0-alpha.3'), 6)
        with self.assertRaises(ValueError): release.contract_schema('0.1.0-alpha.5')

    def test_historical_alpha3_contract_keeps_schema_six(self):
        self.assertEqual(release.contract_schema('0.1.0-alpha.3'), 6)

    def test_historical_alpha3_schema_remains_verifiable_when_source_advances(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source, revision = self.candidate(root, version='0.1.0-alpha.3', schema=6)
            output = root / 'release'
            with patch.object(release.package, 'schema_version', return_value=7):
                release.assemble(source, output, '0.1.0-alpha.3', revision)
                self.assertEqual(release.verify(output, '0.1.0-alpha.3', revision)['schema_version'], 6)

    def test_exact_assets_provenance_schema_and_checksum_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); source, revision = self.candidate(root); output = root / 'release'
            release.assemble(source, output, '0.1.0-alpha.4', revision)
            (output / 'unexpected').write_text('no')
            with self.assertRaisesRegex(ValueError, 'asset set'): release.verify(output, '0.1.0-alpha.4', revision)
            (output / 'unexpected').unlink()
            sums = output / 'SHA256SUMS.txt'
            sums.write_text(sums.read_text() + sums.read_text().splitlines()[0] + '\n')
            with self.assertRaises(ValueError): release.verify(output, '0.1.0-alpha.4', revision)

    def test_fake_schema_dirty_and_wrong_revision_are_rejected(self):
        for revision, dirty, schema in (('b' * 40, False, 6), ('a' * 40, True, 6), ('a' * 40, False, 7)):
            with self.subTest(revision=revision, dirty=dirty, schema=schema), tempfile.TemporaryDirectory() as temp:
                root = pathlib.Path(temp); source, _ = self.candidate(root, revision, dirty, schema=schema)
                with self.assertRaises(ValueError): release.assemble(source, root / 'out', '0.1.0-alpha.4', 'a' * 40)

    def test_fake_extension_and_unknown_version_are_rejected(self):
        with self.assertRaises(ValueError): release.contract_schema('0.1.0-alpha.9')


if __name__ == '__main__':
    unittest.main()
