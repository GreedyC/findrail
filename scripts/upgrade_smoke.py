#!/usr/bin/env python3
"""Exercise packaged alpha.2 schema-2 and published-alpha.3 schema-6 upgrades."""
import argparse
import hashlib
import json
import pathlib
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))


def create_schema2(directory, source_root):
    folder_id = 'fs_' + hashlib.sha256(str(source_root).encode()).hexdigest()
    dbpath = directory / 'findrail.db'
    db = sqlite3.connect(dbpath)
    for name in ('001_init.sql', '002_local_alpha.sql'):
        db.executescript((ROOT / 'internal/store/sqlite/migrations' / name).read_text())
    db.execute('INSERT INTO sources(id,kind,name,root,max_text_bytes,max_pdf_bytes) VALUES(?,?,?,?,?,?)',
               (folder_id, 'filesystem', 'Synthetic PDF source', str(source_root), 1048576, 16777216))
    db.execute("""INSERT INTO documents(id,source_id,title,uri,path,content,content_hash,size_bytes,modified_at,scan_token,media_type,page_count)
               VALUES('legacy-pdf-doc',?,'guide.pdf',?,'guide.pdf','intro oldcandidateevidence','synthetic-hash',27,'2026-01-01T00:00:00Z','old-token','application/pdf',2)""",
               (folder_id, (source_root / 'guide.pdf').as_uri()))
    db.executescript("""
      INSERT INTO document_pages(document_id,page_number,content)
        VALUES('legacy-pdf-doc',1,'intro'),('legacy-pdf-doc',2,'oldcandidateevidence retained page two');
    """)
    db.close()
    return dbpath, folder_id


def directory_digest(directory):
    """Hash a stopped data directory including any SQLite WAL/SHM sidecars."""
    digest = hashlib.sha256()
    for path in sorted(p for p in pathlib.Path(directory).rglob('*') if p.is_file()):
        digest.update(path.relative_to(directory).as_posix().encode())
        digest.update(b'\0')
        digest.update(path.read_bytes())
    return digest.hexdigest()


def invoke(binary, args):
    cwd = pathlib.Path(args[args.index('--data-dir') + 1]).parent
    return subprocess.run([str(binary), *args], text=True, capture_output=True, timeout=20, check=True, cwd=cwd)


def free_port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def configure_legacy_docx(binary, data, cwd, folder_id):
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    authority = f'127.0.0.1:{port}'
    base = 'http://' + authority
    process = subprocess.Popen([str(binary), 'start', '--data-dir', str(data), '--no-open', '--addr', authority],
                               cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(base + '/api/v1/capabilities', timeout=1) as response:
                    if json.load(response).get('management'):
                        break
            except (OSError, urllib.error.URLError):
                if process.poll() is not None:
                    raise RuntimeError('packaged start exited: ' + process.stderr.read())
                time.sleep(.05)
        else:
            raise RuntimeError('packaged start management endpoint did not become ready')

        def get(path):
            request = urllib.request.Request(base + path, headers={'Origin': base})
            with urllib.request.urlopen(request, timeout=3) as response:
                return json.load(response)

        legacy = next(source for source in get('/api/v1/sources')['sources'] if source['id'] == folder_id)
        if legacy.get('max_docx_bytes', 0) != 0:
            raise RuntimeError('legacy DOCX policy unexpectedly enabled')
        token = get('/api/v1/session')['token']
        headers = {'Origin': base, 'Content-Type': 'application/json', 'Sec-Fetch-Site': 'same-origin', 'X-Findrail-Token': token}
        request = urllib.request.Request(base + '/api/v1/sources/' + folder_id + '/configure',
                                         data=json.dumps({'max_docx_bytes': 8388608}).encode(), method='POST', headers=headers)
        with urllib.request.urlopen(request, timeout=3) as response:
            job = json.load(response)['job']
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            job = get('/api/v1/jobs/' + job['id'])
            if job['status'] in ('succeeded', 'failed', 'canceled'):
                break
            time.sleep(.05)
        if job['status'] != 'succeeded':
            db = sqlite3.connect(data / 'findrail.db')
            state = db.execute('SELECT kind,root,max_text_bytes,max_pdf_bytes,max_docx_bytes,length(registration_token),revision FROM sources WHERE id=?', (folder_id,)).fetchone()
            db.close()
            raise RuntimeError('legacy DOCX configure job failed: ' + str(job) + '; persisted source state=' + repr(state))
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=2)


def upgrade_alpha3_schema6(candidate, published_alpha3, root, source_root):
    if published_alpha3 is None:
        raise SystemExit('published alpha.3 binary required to verify stopped-backup restore')
    data = root / 'alpha3-schema6-data'
    data.mkdir()
    dbpath, source_id = create_schema2(data, source_root)
    db = sqlite3.connect(dbpath)
    for name in ('003_github_snapshots.sql', '004_docx_policy.sql',
                 '005_archive_sources.sql', '006_indexing_reports.sql'):
        db.executescript((ROOT / 'internal/store/sqlite/migrations' / name).read_text())
    db.execute("INSERT INTO indexing_reports(source_id,report_id,snapshot_id,report_json,committed_at,operation,finished_at,indexed_documents,skipped_files,pruned_directories,coverage,reasons_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
               (source_id, 'synthetic-alpha3-report', 'synthetic-alpha3-snapshot', '{}',
                '2026-10-13T12:00:00Z', 'index', '2026-10-13T12:00:00Z', 1, 0, 0,
                'filesystem_candidates', '[]'))
    db.commit()
    if db.execute('PRAGMA user_version').fetchone()[0] != 6:
        raise SystemExit('synthetic published alpha.3 fixture is not schema 6')
    before = {
        'sources': db.execute('SELECT COUNT(*) FROM sources').fetchone()[0],
        'source_provenance': db.execute('SELECT id,kind,name,root FROM sources ORDER BY id').fetchall(),
        'documents': db.execute('SELECT COUNT(*) FROM documents').fetchone()[0],
        'document_provenance': db.execute('SELECT id,source_id,title,uri,path,media_type,page_count FROM documents ORDER BY id').fetchall(),
        'hash': db.execute("SELECT content_hash FROM documents WHERE id='legacy-pdf-doc'").fetchone()[0],
        'search': db.execute("SELECT COUNT(*) FROM documents_fts WHERE documents_fts MATCH 'oldcandidateevidence'").fetchone()[0],
        'pages': db.execute("SELECT page_number,content FROM document_pages WHERE document_id='legacy-pdf-doc' ORDER BY page_number").fetchall(),
        'report': db.execute('SELECT report_id,report_json,indexed_documents FROM indexing_reports WHERE source_id=?', (source_id,)).fetchone(),
    }
    db.close()
    if before['sources'] != 1 or before['documents'] != 1 or before['search'] != 1 or before['pages'][1][0] != 2:
        raise SystemExit('synthetic alpha.3 schema-6 baseline evidence is invalid')
    # Prove the fixture is readable by the real old executable before migration.
    old_listing = json.loads(invoke(published_alpha3, ['sources', '--data-dir', str(data), '--json']).stdout)
    old_search = json.loads(invoke(published_alpha3, ['search', '--data-dir', str(data), '--json', 'oldcandidateevidence']).stdout)
    if len(old_listing['sources']) != 1 or old_search['total'] != 1 or old_search['results'][0].get('page') != 2:
        raise SystemExit('published alpha.3 cannot read the schema-6 baseline')

    backup = root / 'stopped-alpha3-schema6-backup'
    shutil.copytree(data, backup)
    stopped_digest = directory_digest(backup)
    listing = json.loads(invoke(candidate, ['sources', '--data-dir', str(data), '--json']).stdout)
    if len(listing['sources']) != 1:
        raise SystemExit('schema-6 migration lost source provenance')
    search_result = json.loads(invoke(candidate, ['search', '--data-dir', str(data), '--json', 'oldcandidateevidence']).stdout)
    if search_result['total'] != 1 or search_result['results'][0]['page'] != 2:
        raise SystemExit('schema-6 migration lost search or PDF page provenance')
    report = json.loads(invoke(candidate, ['source-report', '--data-dir', str(data), '--source', source_id, '--json']).stdout)
    if report.get('available') is not True or report['report'].get('indexed_documents') != 1:
        raise SystemExit('schema-6 indexing report did not survive migration')
    upgraded = sqlite3.connect(dbpath)
    schema = upgraded.execute('PRAGMA user_version').fetchone()[0]
    after = {
        'sources': upgraded.execute('SELECT COUNT(*) FROM sources').fetchone()[0],
        'source_provenance': upgraded.execute('SELECT id,kind,name,root FROM sources ORDER BY id').fetchall(),
        'documents': upgraded.execute('SELECT COUNT(*) FROM documents').fetchone()[0],
        'document_provenance': upgraded.execute('SELECT id,source_id,title,uri,path,media_type,page_count FROM documents ORDER BY id').fetchall(),
        'hash': upgraded.execute("SELECT content_hash FROM documents WHERE id='legacy-pdf-doc'").fetchone()[0],
        'search': upgraded.execute("SELECT COUNT(*) FROM documents_fts WHERE documents_fts MATCH 'oldcandidateevidence'").fetchone()[0],
        'pages': upgraded.execute("SELECT page_number,content FROM document_pages WHERE document_id='legacy-pdf-doc' ORDER BY page_number").fetchall(),
        'report': upgraded.execute('SELECT report_id,report_json,indexed_documents FROM indexing_reports WHERE source_id=?', (source_id,)).fetchone(),
    }
    collection_tables = upgraded.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('evidence_collections','evidence_collection_entries') ORDER BY name").fetchall()
    upgraded.close()
    if schema != 8 or before != after or len(collection_tables) != 2:
        raise SystemExit(f'published alpha.3 upgrade was not additive/preserved (schema={schema}, before={before}, after={after})')

    # Persist a named collection through a real candidate server restart.
    port = free_port(); authority = f'127.0.0.1:{port}'; base = 'http://' + authority
    def start_candidate():
        return subprocess.Popen([str(candidate), 'start', '--data-dir', str(data), '--no-open', '--addr', authority],
                                cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    process = start_candidate()
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError('schema-8 candidate server exited: ' + process.stderr.read())
            try:
                with urllib.request.urlopen(base + '/api/v1/capabilities', timeout=1) as response:
                    if json.load(response).get('collection_persistence'):
                        break
            except (OSError, urllib.error.URLError):
                time.sleep(.05)
        else:
            raise RuntimeError('schema-8 candidate collections did not become available')
        with urllib.request.urlopen(urllib.request.Request(base + '/api/v1/session', headers={'Origin': base}), timeout=3) as response:
            token = json.load(response)['token']
        headers = {'Origin': base, 'Content-Type': 'application/json', 'Sec-Fetch-Site': 'same-origin', 'X-Findrail-Token': token}
        req = urllib.request.Request(base + '/api/v1/collections', data=json.dumps({'title': 'Alpha.3 upgrade journey'}).encode(), method='POST', headers=headers)
        with urllib.request.urlopen(req, timeout=3) as response:
            collection_id = json.load(response)['id']
    finally:
        process.terminate(); process.communicate(timeout=8)
    process = start_candidate()
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError('candidate restart exited: ' + process.stderr.read())
            try:
                with urllib.request.urlopen(base + '/api/v1/capabilities', timeout=1):
                    break
            except (OSError, urllib.error.URLError):
                time.sleep(.05)
        else:
            raise RuntimeError('candidate restart did not become ready')
        with urllib.request.urlopen(urllib.request.Request(base + '/api/v1/session', headers={'Origin': base}), timeout=3) as response:
            restored_token = json.load(response)['token']
        request = urllib.request.Request(base + '/api/v1/collections/' + collection_id,
            headers={'Origin': base, 'X-Findrail-Token': restored_token})
        with urllib.request.urlopen(request, timeout=3) as response:
            restored_collection = json.load(response)
        if restored_collection.get('title') != 'Alpha.3 upgrade journey':
            raise SystemExit('schema-8 collection did not restore after candidate process restart')
    finally:
        process.terminate(); process.communicate(timeout=8)
    restored = root / 'restored-alpha3-backup'
    shutil.copytree(backup, restored)
    if directory_digest(restored) != stopped_digest:
        raise SystemExit('stopped schema-6 backup restore changed bytes')
    invoke(published_alpha3, ['sources', '--data-dir', str(restored), '--json'])
    restored_search = json.loads(invoke(published_alpha3, ['search', '--data-dir', str(restored), '--json', 'oldcandidateevidence']).stdout)
    if restored_search['total'] != 1 or restored_search['results'][0].get('page') != 2:
        raise SystemExit('published alpha.3 cannot search its restored schema-6 backup')
    restored_db = sqlite3.connect(restored / 'findrail.db')
    restored_schema = restored_db.execute('PRAGMA user_version').fetchone()[0]
    restored_collection_table = restored_db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='evidence_collections'").fetchone()[0]
    restored_db.close()
    if restored_schema != 6 or restored_collection_table:
        raise SystemExit('published alpha.3 did not read its restored schema-6 backup unchanged')
    if directory_digest(restored) != stopped_digest:
        raise SystemExit('published alpha.3 changed its restored stopped backup')
    print(f'Synthetic alpha.3 schema-6 fixture migrated to schema 8 with search, source/document provenance, indexing report, and collection tables; stopped backup restored and opened read-only by the published alpha.3 binary; new collection {collection_id!r} restored after candidate restart. No downgrade attempted.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=pathlib.Path)
    parser.add_argument('--alpha3-binary', type=pathlib.Path)
    args = parser.parse_args()
    binary = args.binary.resolve()
    with tempfile.TemporaryDirectory(prefix='findrail-upgrade-') as temp:
        root = pathlib.Path(temp); data = root / 'legacy data'; data.mkdir()
        source_root = root / 'synthetic originals'; source_root.mkdir()
        from smoke import docx_fixture
        (source_root / 'legacy.docx').write_bytes(docx_fixture('legacydocxconfiguredphrase preserved original'))
        dbpath, folder_id = create_schema2(data, source_root)
        historical = sqlite3.connect(dbpath)
        before_state = {
            'sources': historical.execute('SELECT COUNT(*) FROM sources').fetchone()[0],
            'documents': historical.execute('SELECT COUNT(*) FROM documents').fetchone()[0],
            'hash': historical.execute("SELECT content_hash FROM documents WHERE id='legacy-pdf-doc'").fetchone()[0],
            'search': historical.execute("SELECT COUNT(*) FROM documents_fts WHERE documents_fts MATCH 'oldcandidateevidence'").fetchone()[0],
            'pages': historical.execute("SELECT page_number,content FROM document_pages WHERE document_id='legacy-pdf-doc' ORDER BY page_number").fetchall(),
        }
        historical.close()
        if before_state['sources'] != 1 or before_state['documents'] != 1 or before_state['search'] != 1 or before_state['pages'][1][0] != 2:
            raise SystemExit('synthetic alpha.2 baseline inventory/search/PDF evidence invalid')
        before = directory_digest(data)
        backup = root / 'stopped full backup'
        shutil.copytree(data, backup)
        backup_hash = directory_digest(backup)
        if before != backup_hash: raise SystemExit('backup hash differs')
        listing = json.loads(invoke(binary, ['sources', '--data-dir', str(data), '--json']).stdout)
        if len(listing['sources']) != 1: raise SystemExit('migration lost alpha.2 source')
        result = json.loads(invoke(binary, ['search', '--data-dir', str(data), '--json', 'oldcandidateevidence']).stdout)
        if result['total'] != 1 or result['results'][0]['page'] != 2: raise SystemExit('migration lost PDF FTS/page evidence')
        updated = sqlite3.connect(dbpath)
        schema = updated.execute('PRAGMA user_version').fetchone()[0]
        after_state = {
            'sources': updated.execute('SELECT COUNT(*) FROM sources').fetchone()[0],
            'documents': updated.execute('SELECT COUNT(*) FROM documents').fetchone()[0],
            'hash': updated.execute("SELECT content_hash FROM documents WHERE id='legacy-pdf-doc'").fetchone()[0],
            'search': updated.execute("SELECT COUNT(*) FROM documents_fts WHERE documents_fts MATCH 'oldcandidateevidence'").fetchone()[0],
            'pages': updated.execute("SELECT page_number,content FROM document_pages WHERE document_id='legacy-pdf-doc' ORDER BY page_number").fetchall(),
        }
        policies = updated.execute('SELECT max_docx_bytes FROM sources WHERE id=?', (folder_id,)).fetchone()
        updated.close()
        from package import schema_version
        expected_schema = schema_version()
        if schema != expected_schema or policies != (0,): raise SystemExit(f'schema-{expected_schema} migration state mismatch')
        if before_state != after_state: raise SystemExit('migration changed the recorded inventory, content hash, FTS or PDF pages')
        report = json.loads(invoke(binary, ['source-report', '--data-dir', str(data), '--source', folder_id, '--json']).stdout)
        if report.get('available') is not False or report.get('availability') != 'not_yet_available':
            raise SystemExit('schema migration fabricated a source report')
        configure_legacy_docx(binary, data, root, folder_id)
        sources = json.loads(invoke(binary, ['sources', '--data-dir', str(data), '--json']).stdout)['sources']
        legacy = next(source for source in sources if source['id'] == folder_id)
        if legacy['max_docx_bytes'] != 8388608: raise SystemExit('DOCX policy was not persisted across restart')
        result = json.loads(invoke(binary, ['search', '--data-dir', str(data), '--json', 'legacydocxconfiguredphrase']).stdout)
        if result['total'] != 1: raise SystemExit('explicitly configured legacy DOCX was not indexed')
        restored = root / 'rollback restore'
        shutil.copytree(backup, restored)
        if directory_digest(restored) != before:
            raise SystemExit('whole-directory rollback restore differed')
        restored_db = sqlite3.connect(restored / 'findrail.db')
        restored_schema = restored_db.execute('PRAGMA user_version').fetchone()[0]
        restored_state = restored_db.execute("SELECT id,content_hash FROM documents WHERE id='legacy-pdf-doc'").fetchone()
        restored_db.close()
        if restored_schema != 2 or restored_state != ('legacy-pdf-doc', 'synthetic-hash'):
            raise SystemExit('rollback did not preserve the original schema-2 fixture')
        print(f'Packaged alpha.2 schema-2 upgrade passed: source inventory, FTS/PDF page, schema-{expected_schema} disabled DOCX default, unavailable pre-scan diagnostics, Configure/index/restart, stopped full-directory rollback including sidecars; restored schema remains 2. No reverse migration was attempted.')
        upgrade_alpha3_schema6(binary, args.alpha3_binary.resolve() if args.alpha3_binary else None, root, source_root)


if __name__ == '__main__': main()
