#!/usr/bin/env python3
"""Bounded CLI smoke for root ignore decisions; uses only a private temp tree."""
import json, os, pathlib, subprocess, sys, tempfile

binary = pathlib.Path(sys.argv[1]).resolve()
if not binary.exists() and pathlib.Path(str(binary) + ".exe").exists():
    binary = pathlib.Path(str(binary) + ".exe")
with tempfile.TemporaryDirectory(prefix="findrail ignore ") as temp:
    root = pathlib.Path(temp) / "notes with spaces"
    data = pathlib.Path(temp) / "private index"
    root.mkdir()
    (root / "skip.md").write_text("uniquetoken hidden", encoding="utf-8")
    (root / "keep.md").write_text("uniquetoken retained", encoding="utf-8")
    (root / ".findrailignore").write_text("skip.md\n", encoding="utf-8")
    args = [str(binary), "explain-path", str(root), "--path", "skip.md", "--path", "keep.md", "--json"]
    result = subprocess.run(args, capture_output=True, text=True, timeout=10, check=True)
    payload = json.loads(result.stdout)
    assert payload["version"] == 1 and payload["policy_present"]
    assert [row["status"] for row in payload["results"]] == ["excluded_user_rule", "eligible_by_path_policy"]
    def run(*argv, success=True):
        completed = subprocess.run([str(binary), *map(str, argv)], capture_output=True, text=True, timeout=20)
        assert (completed.returncode == 0) == success, completed.stderr
        return completed
    run("index", "--data-dir", data, root)
    assert "1 matches" in run("search", "--data-dir", data, "retained").stdout
    assert "0 matches" in run("search", "--data-dir", data, "hidden").stdout
    (root / ".findrailignore").write_text("[invalid\n", encoding="utf-8")
    run("index", "--data-dir", data, root, success=False)
    assert "1 matches" in run("search", "--data-dir", data, "retained").stdout
    (root / ".findrailignore").write_text("", encoding="utf-8")
    run("index", "--data-dir", data, root)
    assert "1 matches" in run("search", "--data-dir", data, "hidden").stdout
    (root / ".findrailignore").write_text("skip.md\n!skip.md\n", encoding="utf-8")
    run("index", "--data-dir", data, root)
    assert "1 matches" in run("search", "--data-dir", data, "hidden").stdout
    bad = subprocess.run([str(binary), "explain-path", str(root), "--path", "../secret"], capture_output=True, timeout=10)
    assert bad.returncode != 0
print("ignore policy explanation smoke passed")
