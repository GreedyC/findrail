import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import release_gate


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


if __name__ == '__main__':
    unittest.main()
