import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import packaged_journey as journey


class CandidateIdentityTests(unittest.TestCase):
    def test_identity_requires_clean_native_exact_version(self):
        sha, version = "a" * 40, "0.1.0-alpha.3"
        good = {"revision": sha, "version": version, "dirty": False, "target": "linux-amd64"}
        cases = [({}, f"findrail {version}", True),
                 ({"dirty": True}, f"findrail {version}", False),
                 ({"dirty": None}, f"findrail {version}", False),
                 ({"target": "linux-arm64"}, f"findrail {version}", False),
                 ({"revision": "b" * 40}, f"findrail {version}", False),
                 ({"version": "0.1.0-alpha.30"}, f"findrail {version}", False),
                 ({}, "findrail 0.1.0-alpha.30", False)]
        with tempfile.TemporaryDirectory() as temp:
            binary = pathlib.Path(temp) / "findrail"
            for changes, output, accepted in cases:
                with self.subTest(changes=changes, output=output):
                    (binary.parent / "BUILD-INFO.json").write_text(json.dumps(good | changes))
                    with patch.object(journey.platform, "system", return_value="Linux"), \
                         patch.object(journey.platform, "machine", return_value="x86_64"), \
                         patch.object(journey, "command", return_value=SimpleNamespace(stdout=output)):
                        if accepted:
                            self.assertEqual(journey.validate_candidate(binary, sha, version), good)
                        else:
                            with self.assertRaises(ValueError): journey.validate_candidate(binary, sha, version)


if __name__ == "__main__":
    unittest.main()
