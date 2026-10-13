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

    def test_alpha3_published_sha_is_immutable_and_unknown_contract_fails_closed(self):
        sha = release_gate.ALPHA3_REVISION
        names = {f'findrail_0.1.0-alpha.3_{target}' + ('.zip' if target.startswith('windows-') else '.tar.gz')
                 for target in ('linux-amd64', 'linux-arm64', 'darwin-amd64', 'darwin-arm64', 'windows-amd64')}
        names.add('findrail-readonly-0.1.0.vsix')
        manifest = {'manifest_version': 1, 'source_revision': sha, 'app_version': '0.1.0-alpha.3',
                    'schema_version': 6, 'client_api_version': 1, 'extension_version': '0.1.0',
                    'assets': [{'basename': name} for name in names]}
        release = {'tag_sha': sha, 'manifest': manifest}
        names |= {'release-manifest.json', 'SHA256SUMS.txt'}
        self.assertEqual(release_gate.existing_release_decision('0.1.0-alpha.3', '1' * 40, sha, release,
                         [{'name': name} for name in names]), 'noop')
        with self.assertRaisesRegex(ValueError, 'historical revision'):
            release_gate.existing_release_decision('0.1.0-alpha.3', '1' * 40, 'a' * 40,
                {'tag_sha': 'a' * 40, 'manifest': {**manifest, 'source_revision': 'a' * 40}},
                [{'name': name} for name in names])
        with self.assertRaisesRegex(ValueError, 'unknown published'):
            release_gate.existing_release_decision('0.1.0-alpha.4', '1' * 40, sha, release, [])


if __name__ == '__main__':
    unittest.main()
