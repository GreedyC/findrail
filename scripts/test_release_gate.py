import pathlib
import sys
import unittest
import io
import json
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import release_gate
import release_assets
import test_release_assets


class ReleaseGateTests(unittest.TestCase):
    def test_only_expected_push_context_is_trusted(self):
        sha = 'a' * 40
        release_gate.validate_upstream('Lephiziel/findrail', 'push', 'main', sha, 'Lephiziel/findrail')
        for args in (('fork/findrail', 'push', 'main', sha), ('Lephiziel/findrail', 'pull_request', 'main', sha),
                     ('Lephiziel/findrail', 'push', 'feature', sha), ('Lephiziel/findrail', 'push', 'main', 'unknown')):
            with self.subTest(args=args), self.assertRaises(ValueError):
                release_gate.validate_upstream(*args, 'Lephiziel/findrail')

    def test_published_complete_alpha2_is_noop_after_main_moves(self):
        tag_sha = 'b' * 40
        names = sorted(release_gate.ALPHA2_ASSETS)
        assets = [{'name': name} for name in names]
        release = {'tag_sha': tag_sha}
        self.assertEqual(release_gate.existing_release_decision('0.1.0-alpha.2', 'c' * 40, tag_sha, release, assets), 'noop')

    def test_incomplete_or_ambiguous_release_is_never_noop(self):
        sha = 'd' * 40
        release = {'tag_sha': sha}
        assets = [{'name': name} for name in release_gate.ALPHA2_ASSETS if name != 'SHA256SUMS.txt']
        with self.assertRaises(ValueError): release_gate.existing_release_decision('0.1.0-alpha.2', 'e' * 40, sha, release, assets)
        with self.assertRaises(ValueError): release_gate.existing_release_decision('0.1.0-alpha.2', 'e' * 40, sha, None, assets)
        with self.assertRaises(ValueError): release_gate.existing_release_decision('0.1.0-alpha.2', 'e' * 40, None, release, assets, 'HTTP 500')

    def test_new_contract_rejects_manifest_sha_or_version_conflicts(self):
        sha = 'f' * 40
        release = {'tag_sha': sha, 'manifest': {'source_revision': '0' * 40, 'app_version': '0.1.0-alpha.3', 'assets': []}}
        with self.assertRaises(ValueError): release_gate.existing_release_decision('0.1.0-alpha.3', '1' * 40, sha, release, [])
        release['manifest'] = {'source_revision': sha, 'app_version': '0.1.0-alpha.2', 'assets': []}
        with self.assertRaises(ValueError): release_gate.existing_release_decision('0.1.0-alpha.3', '1' * 40, sha, release, [])

    def test_remote_checksum_mismatch_and_duplicate_are_rejected(self):
        import hashlib
        content = b'asset'
        good = hashlib.sha256(content).hexdigest()
        release_gate.verify_remote_checksums([{'name': 'a.zip', 'data': content}, {'name': 'SHA256SUMS.txt'}], f'{good}  a.zip\n')
        with self.assertRaises(ValueError): release_gate.verify_remote_checksums([{'name': 'a.zip', 'data': b'bad'}, {'name': 'SHA256SUMS.txt'}], f'{good}  a.zip\n')
        with self.assertRaises(ValueError): release_gate.verify_remote_checksums([{'name': 'a.zip', 'data': content}, {'name': 'SHA256SUMS.txt'}], f'{good}  a.zip\n{good}  a.zip\n')

    def test_existing_release_checks_the_embedded_revision_before_noop(self):
        import tempfile
        version, sha = '0.1.0-alpha.3', 'a' * 40
        for embedded_sha in (sha, 'b' * 40):
            with self.subTest(embedded_sha=embedded_sha), tempfile.TemporaryDirectory() as temp:
                root = pathlib.Path(temp)
                source, _ = test_release_assets.ReleaseAssetTests().candidate(root, embedded_sha)
                output = root / 'out'
                release_assets.assemble(source, output, version, embedded_sha)
                manifest_path = output / 'release-manifest.json'
                manifest = json.loads(manifest_path.read_text())
                manifest['source_revision'] = sha
                manifest_path.write_text(json.dumps(manifest))
                sums = output / 'SHA256SUMS.txt'
                sums.write_text(''.join(f'{release_assets.digest(p)}  {p.name}\n' for p in sorted(output.iterdir()) if p != sums))
                base = 'https://api.github.com/repos/Lephiziel/findrail'
                responses = {
                    base + '/releases/tags/v' + version: json.dumps({'assets': [
                        {'name': p.name, 'browser_download_url': 'https://release.invalid/' + p.name}
                        for p in output.iterdir()]}).encode(),
                    base + '/git/ref/tags/v' + version: json.dumps({'object': {'type':'commit', 'sha':sha}}).encode(),
                    **{'https://release.invalid/' + p.name: p.read_bytes() for p in output.iterdir()}}
                with patch.object(release_gate.urllib.request, 'urlopen', side_effect=lambda req, **kw: io.BytesIO(responses[req.full_url])):
                    if embedded_sha == sha:
                        self.assertEqual(release_gate.github_release_decision('Lephiziel/findrail', version, 'c' * 40, 'test'), 'noop')
                    else:
                        with self.assertRaisesRegex(ValueError, 'provenance'):
                            release_gate.github_release_decision('Lephiziel/findrail', version, 'c' * 40, 'test')


if __name__ == '__main__':
    unittest.main()
