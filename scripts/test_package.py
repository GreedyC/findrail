import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import package


class PackageSafetyTests(unittest.TestCase):
    def test_platform_launcher_allowlists_are_explicit_and_present(self):
        self.assertEqual(set(package.RESOURCE_FILES), {'linux', 'darwin', 'windows'})
        for platform, members in package.RESOURCE_FILES.items():
            with self.subTest(platform=platform):
                self.assertTrue(members)
                for source, destination in members.items():
                    self.assertTrue((package.ROOT / source).is_file(), source)
                    self.assertNotIn('..', pathlib.PurePosixPath(destination).parts)
        self.assertIn('Findrail.app/Contents/Info.plist', package.RESOURCE_FILES['darwin'].values())
        self.assertIn('launcher/linux/findrail.desktop', package.RESOURCE_FILES['linux'].values())

    @unittest.skipIf(os.name == 'nt', 'POSIX desktop installer')
    def test_linux_user_installer_escapes_package_paths_and_keeps_data_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = pathlib.Path(temporary)
            package_root = base / 'Findrail space & 100% "quoted"' / 'candidate'
            resources = package_root / 'launcher/linux'
            resources.mkdir(parents=True)
            for name in ('findrail.desktop', 'install-user.sh', 'uninstall-user.sh'):
                shutil.copyfile(package.ROOT / 'packaging/desktop/linux' / name, resources / name)
            launcher = package_root / 'findrail-desktop'
            launcher.write_text('#!/bin/sh\nexit 0\n', encoding='utf-8')
            launcher.chmod(0o755)
            home, xdg = base / 'home', base / 'xdg'
            home.mkdir()
            env = {**os.environ, 'HOME': str(home), 'XDG_DATA_HOME': str(xdg)}
            result = subprocess.run(['sh', str(resources / 'install-user.sh')], env=env,
                                    capture_output=True, text=True, check=True)
            installed = (xdg / 'applications/findrail.desktop').read_text(encoding='utf-8')
            escaped = str(package_root).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%')
            self.assertIn(f'Exec="{escaped}/findrail-desktop"', installed)
            self.assertNotIn('@INSTALL_DIR@', installed)
            self.assertIn('Installed user menu entry', result.stdout)
            self.assertFalse((home / '.local/share/findrail').exists())

    def test_go_license_fallback_retains_all_three_conditions(self):
        self.assertIn('Neither the name of Google LLC', package.GO_LICENSE_FALLBACK)
        self.assertIn('specific prior written permission', package.GO_LICENSE_FALLBACK)

    def test_manifest_rejects_paths_duplicates_and_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / 'candidate.tar.gz').write_bytes(b'archive')
            digest = package.hashlib.sha256(b'archive').hexdigest()
            for text in (f'{digest}  ../escape.tar.gz\n', f'{digest}  candidate.tar.gz\n{digest}  candidate.tar.gz\n', '0' * 64 + '  candidate.tar.gz\n'):
                (root / 'SHA256SUMS.txt').write_text(text)
                with self.assertRaises(ValueError): package.verify_manifest(root)

    def test_extract_rejects_traversal_and_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); archive = root / 'bad.tar.gz'
            with tarfile.open(archive, 'w:gz') as tf:
                info = tarfile.TarInfo('pkg/../../escape'); info.size = 1
                import io
                tf.addfile(info, io.BytesIO(b'x'))
            with self.assertRaises(ValueError): package.extract_verified(archive, root / 'out')
            with tarfile.open(archive, 'w:gz') as tf:
                info = tarfile.TarInfo('pkg/link'); info.type = tarfile.SYMTYPE; info.linkname = '../../escape'
                tf.addfile(info)
            with self.assertRaises(ValueError): package.extract_verified(archive, root / 'out')

    def test_zip_rejects_windows_separator_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = pathlib.Path(temp) / 'bad.zip'
            with zipfile.ZipFile(archive, 'w') as zf:
                zf.writestr('pkg/..\\..\\escape', b'bad')
            with self.assertRaises(ValueError): package.extract_verified(archive, pathlib.Path(temp) / 'out')

    def test_extract_rejects_duplicate_and_file_directory_conflicts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            for members in ((('pkg/a', b'a'), ('pkg/a', b'b')),
                            (('pkg/a', b'a'), ('pkg/a/b', b'b'))):
                archive = root / 'bad.tar.gz'
                with tarfile.open(archive, 'w:gz') as tf:
                    for name, data in members:
                        info = tarfile.TarInfo(name); info.size = len(data)
                        import io
                        tf.addfile(info, io.BytesIO(data))
                with self.subTest(members=members), self.assertRaises(ValueError):
                    package.extract_verified(archive, root / ('out-' + str(len(list(root.iterdir())))))

    def test_safe_basename(self):
        for name in ('../a', 'a/b', 'C:\\a', ''):
            self.assertFalse(package.safe_basename(name))
        self.assertTrue(package.safe_basename('findrail_0.1.0-alpha.3_linux-amd64.tar.gz'))


if __name__ == '__main__':
    unittest.main()
