#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("resource_check", Path(__file__).with_name("search_resource_check.py"))
resource_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resource_check)


class GeneratorTests(unittest.TestCase):
    def corpus(self, seed):
        with tempfile.TemporaryDirectory(prefix="findrail-fixture-test-") as temp:
            root = Path(temp) / "source"
            root.mkdir()
            total = resource_check.generate(root, 100, seed, 9999999999)
            return resource_check.digest_file_manifest(root), total, len(list(root.iterdir()))

    def test_seed_identity_and_unicode_formats(self):
        first = self.corpus(42)
        self.assertEqual(first, self.corpus(42))
        self.assertNotEqual(first[0], self.corpus(43)[0])
        self.assertEqual(first[2], 100)
        self.assertLess(first[1], resource_check.MAX_BYTES)

    def test_failed_index_reports_failure_and_cleans_fixture(self):
        script = Path(__file__).with_name("search_resource_check.py")
        with tempfile.TemporaryDirectory(prefix="resource-failure-test-") as temp:
            root = Path(temp)
            binary = root / "failing-findrail"
            binary.write_text("#!/usr/bin/env python3\nraise SystemExit(1)\n", encoding="utf-8")
            binary.chmod(0o700)
            report = root / "report.json"
            before = set(Path(tempfile.gettempdir()).glob("findrail-resource-*"))
            result = subprocess.run([sys.executable, str(script), "--binary", str(binary), "--documents", "100", "--seed", "8", "--queries", "1", "--report", str(report)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            after = set(Path(tempfile.gettempdir()).glob("findrail-resource-*"))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(before, after)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "failed")
            self.assertNotIn(str(root), report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
