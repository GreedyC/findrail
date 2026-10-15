#!/usr/bin/env python3
"""Validate an already extracted Findrail candidate (never builds the product)."""
import argparse
import hashlib
import json
import os
import pathlib
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def command(args, *, ok=True, timeout=120):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", timeout=timeout)
    if (result.returncode == 0) != ok:
        raise AssertionError(f"command {args!r}: exit={result.returncode}\n{result.stdout}\n{result.stderr}")
    return result


def db_fingerprint(path):
    if not path.exists():
        return None
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        state = {"schema": connection.execute("PRAGMA user_version").fetchone()[0]}
        for table in ("sources", "documents", "document_pages"):
            try:
                state[table] = connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            except sqlite3.OperationalError:
                state[table] = None
        return hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()
    finally:
        connection.close()


def validate_candidate(binary, revision, version):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("candidate SHA must be a full commit SHA")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+-alpha\.[0-9]+", version):
        raise ValueError("candidate version must be an exact alpha version")
    build_info = binary.parent / "BUILD-INFO.json"
    metadata = json.loads(build_info.read_text(encoding="utf-8"))
    system = {"Linux": "linux", "Darwin": "darwin", "Windows": "windows"}.get(platform.system())
    machine = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine().lower())
    target = f"{system}-{machine}"
    if (not system or not machine or metadata.get("dirty") is not False or
            (metadata.get("revision"), metadata.get("version"), metadata.get("target")) != (revision, version, target)):
        raise ValueError("BUILD-INFO.json must match candidate SHA/version, be clean, and target this runner")
    actual = command([str(binary), "version"]).stdout.strip()
    if actual != f"findrail {version}":
        raise ValueError(f"candidate executable version mismatch: {actual!r}")
    return metadata


def evaluate(binary, scratch):
    documents = ROOT / "examples/evaluation/documents"
    queries_file = ROOT / "examples/evaluation/queries.json"
    data = scratch / "evaluation-data"
    indexed = json.loads(command([str(binary), "index", "--data-dir", str(data), "--json", str(documents)]).stdout)
    source = indexed["source"]["id"]
    before = db_fingerprint(data / "findrail.db")
    result = json.loads(command([str(binary), "evaluate", "--data-dir", str(data), "--source", source,
                                 "--queries", str(queries_file), "--json"]).stdout)
    after = db_fingerprint(data / "findrail.db")
    assert before == after, "evaluate changed meaningful SQLite state"
    cases = result.get("results", [])
    assert len(cases) == 10 and result.get("passed") == 10 and result.get("failed") == 0, result
    assert [case.get("query") for case in cases] == [case["query"] for case in json.loads(queries_file.read_text(encoding="utf-8"))], result
    for case in cases:
        assert case["actual_paths"] == sorted(case["actual_paths"]), case
        assert case["expected_paths"] == sorted(case["expected_paths"]), case

    # A deliberately mismatched corpus must report every comparison before failing.
    negative = scratch / "negative-queries.json"
    entries = json.loads(queries_file.read_text(encoding="utf-8"))
    entries[0]["expected_paths"] = ["definitely-not-a-result.md"]
    negative.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    failed = command([str(binary), "evaluate", "--data-dir", str(data), "--source", source,
                      "--queries", str(negative), "--json"], ok=False)
    report = json.loads(failed.stdout)
    assert len(report.get("results", [])) == 10 and report.get("failed") == 1, report
    assert db_fingerprint(data / "findrail.db") == before

    missing = scratch / "missing-evaluation-index"
    command([str(binary), "evaluate", "--data-dir", str(missing), "--source", "missing",
             "--queries", str(queries_file), "--json"], ok=False)
    assert not missing.exists(), "missing-index evaluate created a data directory"

    # Legacy schema rejection must be read-only (schema-2 fixture is exercised by upgrade_smoke).
    legacy = scratch / "legacy-evaluate"
    legacy.mkdir()
    db = sqlite3.connect(legacy / "findrail.db")
    db.execute("PRAGMA user_version=2")
    db.execute("CREATE TABLE marker(value TEXT)")
    db.execute("INSERT INTO marker VALUES('unchanged')")
    db.commit(); db.close()
    legacy_before = hashlib.sha256((legacy / "findrail.db").read_bytes()).hexdigest()
    command([str(binary), "evaluate", "--data-dir", str(legacy), "--source", source,
             "--queries", str(queries_file), "--json"], ok=False)
    assert hashlib.sha256((legacy / "findrail.db").read_bytes()).hexdigest() == legacy_before

    many_docs, many_data = scratch / "many-matches", scratch / "many-match-index"
    many_docs.mkdir()
    for number in range(101):
        (many_docs / f"match-{number:03}.md").write_text("boundedmanymarker\n", encoding="utf-8")
    many_index = json.loads(command([str(binary), "index", "--data-dir", str(many_data), "--json", str(many_docs)]).stdout)
    many_queries = scratch / "many-queries.json"
    many_queries.write_text(json.dumps([{"query": "boundedmanymarker", "expected_paths": []}]), encoding="utf-8")
    too_many = command([str(binary), "evaluate", "--data-dir", str(many_data), "--source",
                        many_index["source"]["id"], "--queries", str(many_queries), "--json"], ok=False)
    assert "incomplete search results" in too_many.stderr, too_many.stderr

    # explain-path contract is ROOT followed by --path RELATIVE.
    explained = json.loads(command([str(binary), "explain-path", str(documents), "--path", "kahve.md", "--json"]).stdout)
    assert explained["results"][0]["path"] == "kahve.md", explained
    return {"case": "evaluate", "status": "passed", "comparisons": 10,
            "read_only_fingerprint": before, "negative_report_complete": True,
            "missing_index_noncreating": True, "legacy_index_unmodified": True,
            "over_100_matches_incomplete": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=pathlib.Path, help="path to extracted findrail executable")
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--candidate-version", required=True)
    parser.add_argument("--alpha3-binary", type=pathlib.Path, required=True,
                        help="extracted published alpha.3 binary used to verify stopped-backup restore")
    parser.add_argument("--alpha4-binary", type=pathlib.Path, required=True,
                        help="extracted published alpha.4 binary used to verify schema-7 backup restore")
    parser.add_argument("--report", type=pathlib.Path, help="write per-case JSON report")
    parser.add_argument("--skip-browser", action="store_true")
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    if not os.access(binary, os.X_OK):
        raise SystemExit("candidate binary is not executable")
    metadata = validate_candidate(binary, args.candidate_sha, args.candidate_version)
    cases = []
    with tempfile.TemporaryDirectory(prefix="findrail packaged journey ") as directory:
        scratch = pathlib.Path(directory)
        cases.append(evaluate(binary, scratch))
        smokes = ["search_smoke.py", "mcp_smoke.py", "portable_smoke.py", "diagnostics_smoke.py", "ignore_policy_smoke.py"]
        for smoke in smokes:
            command([sys.executable, str(ROOT / "scripts" / smoke), str(binary)], timeout=300)
            cases.append({"case": smoke, "status": "passed"})
        command([sys.executable, str(ROOT / "scripts/upgrade_smoke.py"), str(binary),
                 "--alpha3-binary", str(args.alpha3_binary.resolve(strict=True)),
                 "--alpha4-binary", str(args.alpha4_binary.resolve(strict=True))], timeout=300)
        cases.extend([
            {"case": "alpha2_schema2_upgrade_restore", "status": "passed"},
            {"case": "alpha3_schema6_upgrade_restore", "status": "passed"},
            {"case": "published_alpha4_schema7_to_schema8_saved_collection_restore_and_atomic_rollback", "status": "passed"},
        ])
        command([sys.executable, str(ROOT / "scripts/desktop_launch_smoke.py"), str(binary)], timeout=90)
        cases.append({"case": "desktop_launch_smoke.py", "status": "passed"})
        if not args.skip_browser:
            command([sys.executable, str(ROOT / "scripts/packaged_browser_journey.py"), str(binary)], timeout=300)
            cases.append({"case": "packaged_browser_journey.py", "status": "passed"})
            cases.append({"case": "single_browser_schema8_folder_diagnostics_passage_collection_forget_quit_lifecycle", "status": "passed"})
            command([sys.executable, str(ROOT / "scripts/persistent_collection_smoke.py"), str(binary)], timeout=600)
            cases.append({"case": "persistent_collection_smoke.py", "status": "passed"})
            command([sys.executable, str(ROOT / "scripts/evidence_collection_smoke.py"), str(binary)], timeout=600)
            cases.append({"case": "evidence_collection_smoke.py", "status": "passed"})
    report = {"candidate_sha": args.candidate_sha, "candidate_version": args.candidate_version,
              "schema_version": metadata.get("schema_version"), "target": metadata.get("target"),
              "source_clean": metadata.get("dirty") is False,
              "binary": binary.name, "os": platform.platform(), "python": platform.python_version(),
              "go": metadata.get("go_version"), "browser_skipped": args.skip_browser, "cases": cases}
    encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
