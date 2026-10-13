import io
import json
import pathlib
import sys
import tarfile
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import release_assets as release


class ReleaseAssetTests(unittest.TestCase):
    def candidate(self, root, revision='a' * 40, dirty=False):
        source = root / 'input'
        source.mkdir()
        for name, target in release.expected_archives('0.1.0-alpha.3').items():
            if target.startswith('windows-'):
                with zipfile.ZipFile(source / name, 'w') as zf:
                    def put(path, data):
                        info = zipfile.ZipInfo(path); info.external_attr = 0o100644 << 16; zf.writestr(info, data)
                    put(f'findrail_0.1.0-alpha.3_{target}/findrail.exe', b'fake')
                    put(f'findrail_0.1.0-alpha.3_{target}/BUILD-INFO.json', json.dumps({'version': '0.1.0-alpha.3', 'revision': revision, 'dirty': dirty, 'target': target}))
                    for item in ('INSTALL.txt', 'LICENSE', 'NOTICE', 'licenses/DEPENDENCIES.txt', 'licenses/Go-LICENSE.txt'):
                        put(f'findrail_0.1.0-alpha.3_{target}/{item}', 'fixture')
            else:
                with tarfile.open(source / name, 'w:gz') as tf:
                    stem = f'findrail_0.1.0-alpha.3_{target}'
                    data = {'version': '0.1.0-alpha.3', 'revision': revision, 'dirty': dirty, 'target': target}
                    members = {'findrail': b'fake', 'BUILD-INFO.json': json.dumps(data).encode(), 'INSTALL.txt': b'x', 'LICENSE': b'x', 'NOTICE': b'x', 'licenses/DEPENDENCIES.txt': b'x', 'licenses/Go-LICENSE.txt': b'x'}
                    for item, contents in members.items():
                        info = tarfile.TarInfo(f'{stem}/{item}'); info.size = len(contents); info.mode = 0o755 if item == 'findrail' else 0o644
                        tf.addfile(info, io.BytesIO(contents))
        with zipfile.ZipFile(source / release.VSIX, 'w') as zf:
            zf.writestr('extension/package.json', json.dumps({'version':'0.1.0', 'name':'findrail-readonly',
                'publisher':'findrail-local', 'main':'./dist/extension.js', 'extensionKind':['ui']}))
            for name in ('[Content_Types].xml', 'extension.vsixmanifest', 'extension/LICENSE.txt',
                         'extension/readme.md', 'extension/changelog.md', 'extension/dist/extension.js'):
                zf.writestr(name, 'fixture')
        return source, revision

    def test_assemble_exact_inventory_manifest_and_checksums(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); source, revision = self.candidate(root)
            output = root / 'release'
            result = release.assemble(source, output, '0.1.0-alpha.3', revision)
            self.assertEqual(result['schema_version'], 6)
            self.assertEqual(len(result['assets']), 6)
            self.assertEqual(release.verify(output, '0.1.0-alpha.3', revision), result)

    def test_missing_target_or_vsix_and_unknown_name_fail_closed(self):
        for remove in ('findrail-readonly-0.1.0.vsix', 'findrail_0.1.0-alpha.3_linux-arm64.tar.gz'):
            with self.subTest(remove=remove), tempfile.TemporaryDirectory() as temp:
                root = pathlib.Path(temp); source, _ = self.candidate(root); (source / remove).unlink()
                with self.assertRaises(ValueError): release.assemble(source, root / 'out', '0.1.0-alpha.3', 'a' * 40)

    def test_wrong_revision_dirty_metadata_and_checksum_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); source, revision = self.candidate(root); output = root / 'out'
            release.assemble(source, output, '0.1.0-alpha.3', revision)
            archive = output / 'findrail_0.1.0-alpha.3_linux-amd64.tar.gz'
            archive.write_bytes(archive.read_bytes() + b'corrupt')
            with self.assertRaises(ValueError): release.verify(output, '0.1.0-alpha.3', revision)

    def test_checksum_mismatch_is_rejected_independently(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); source, revision = self.candidate(root); output = root / 'out'
            release.assemble(source, output, '0.1.0-alpha.3', revision)
            sums = output / 'SHA256SUMS.txt'
            line = sums.read_text().splitlines()[0]
            sums.write_text('0' * 64 + line[64:] + '\n' + '\n'.join(sums.read_text().splitlines()[1:]) + '\n')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                release.verify(output, '0.1.0-alpha.3', revision)

    def test_dirty_and_unknown_provenance_are_rejected_during_assembly(self):
        for bad_revision, dirty in (('a' * 40, True), ('unknown', False)):
            with self.subTest(revision=bad_revision, dirty=dirty), tempfile.TemporaryDirectory() as temp:
                root = pathlib.Path(temp); source, _ = self.candidate(root, bad_revision, dirty)
                with self.assertRaises(ValueError): release.assemble(source, root / 'out', '0.1.0-alpha.3', 'a' * 40)

    def test_manifest_wrong_version_and_unsafe_duplicate_names_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); source, revision = self.candidate(root); output = root / 'out'
            release.assemble(source, output, '0.1.0-alpha.3', revision)
            with self.assertRaises(ValueError): release.verify(output, '0.1.0-alpha.4', revision)
            with self.assertRaises(ValueError): release.verify(output, '0.1.0-alpha.3', 'b' * 40)
            with (output / 'SHA256SUMS.txt').open('a') as sums: sums.write('0' * 64 + '  ../escape\n')
            with self.assertRaises(ValueError): release.verify(output, '0.1.0-alpha.3', revision)
            line = (output / 'SHA256SUMS.txt').read_text().splitlines()[0]
            (output / 'SHA256SUMS.txt').write_text(line + '\n' + line + '\n')
            with self.assertRaises(ValueError): release.verify(output, '0.1.0-alpha.3', revision)

    def test_another_extension_with_the_same_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); source, revision = self.candidate(root)
            archive = source / release.VSIX
            with zipfile.ZipFile(archive) as zf:
                members = {name: zf.read(name) for name in zf.namelist()}
            metadata = json.loads(members['extension/package.json'])
            metadata['publisher'] = 'another-publisher'
            members['extension/package.json'] = json.dumps(metadata).encode()
            with zipfile.ZipFile(archive, 'w') as zf:
                for name, content in members.items(): zf.writestr(name, content)
            with self.assertRaisesRegex(ValueError, 'VSIX identity'):
                release.assemble(source, root / 'out', '0.1.0-alpha.3', revision)


if __name__ == '__main__':
    unittest.main()
