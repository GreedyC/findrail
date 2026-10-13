# Evidence collections (source builds)

Named evidence collections are available when Findrail runs through writable
`start`. Collections are stored in the current data directory's SQLite database;
they are not included in published alpha.3 archives. `serve`, `demo`, MCP and
read-only composition retain the temporary in-page collection and expose no
collection persistence routes. The browser does not use localStorage, IndexedDB,
accounts, sharing, or hidden network requests.

## Collect, save and restore

Open a result's **Preview**, select a non-empty passage wholly inside the visible
preview and choose **Add to collection**, or deliberately choose **Use whole
visible preview**. Create a named collection and press **Save** to persist it.
Choose saved collections from the collection panel after restart. Notes, removal,
rename and ordering are saved explicitly with **Save**. The server assigns the
entry key and derives provenance from the current indexed document; the browser
cannot submit a URI, hash, title, source identity or page as authoritative data.
Exact source/document/content-hash/page/passage duplicates are rejected.

Stored entries are immutable historical evidence snapshots. A rescan with changed
content does not rewrite their passage/hash. **Open current indexed evidence** is a
separate action and may show the new version or report that it is unavailable.
PDF entries preserve a real selected page; a title-only PDF has page 0 and no page
locator. Text and DOCX do not claim a page. Truncated previews contain only the
visible indexed text, not a full original document.

## API and concurrency

Collection routes exist only in writable management composition and use the same
loopback authority, per-process session token, same-origin/cross-site guards and
strict JSON checks as other mutations. `GET /api/v1/collections` returns metadata
and entry counts; `GET /api/v1/collections/{id}` loads one bounded collection.
`POST /api/v1/collections` creates; `POST /api/v1/collections/{id}/entries`
pins a verified preview passage; `PUT /api/v1/collections/{id}` updates title,
notes, order and removals; `DELETE /api/v1/collections/{id}?revision=N` deletes.
Writes are capped at 512 KiB. Updates carry an integer revision and stale edits
return HTTP 409; the UI keeps local edits and requires reload/retry rather than
silently replacing newer data. SQLite transactions make pin, reorder/save, delete
and Forget atomic. Late collection loads are ignored if the user has selected a
different collection or edited local state.

## Limits and privacy

Limits are enforced in UTF-8 bytes, before commit, without truncation or eviction:

| Limit | Value |
|---|---:|
| Collections per data directory | 100 |
| Entries per collection | 40 |
| Preview text per entry | 256 KiB |
| Preview plus excerpt per collection | 2 MiB |
| Serialized metadata per entry (excluding preview, excerpt, note) | 16 KiB |
| Note | 2,048 bytes |
| Collection name | 256 bytes |
| Markdown export | 4 MiB |
| Serialized collection payload across data directory | 64 MiB |
| Feature-owned in-memory UTF-8 payload | 32 MiB |

The serialized-payload quota is the sum of UTF-8 bytes in each stored
`snapshot_json` value plus collection-name bytes; it excludes SQLite page/WAL overhead. The in-memory limit
accounts for bounded retained entry text, metadata, notes and simultaneous
feature-owned copies; it is not an RSS guarantee. List operations do not load
passages; one collection is loaded on demand. Export is bounded plain text, safely
rendered as text, and may contain private passages and local paths. Copy/download
cannot be recalled after issuance.

## Forget and backups

Deleting a source or pruning a document on a successfully committed scan removes
entries tied to it through SQLite foreign-key cascades in the same transaction.
Collection name and other entries remain. Changed documents keep historical
snapshots; failed/canceled scans do not purge from an uncommitted inventory. A
later source re-add cannot resurrect forgotten entries. Deletion is logical, not
forensic erasure; SQLite/WAL/filesystem remnants may be recoverable. The UI warns
before Forget. A stopped full data-directory backup includes collections. Portable
source snapshot v1 remains source-scoped and does not include unrelated collections
or notes.

Markdown uses Findrail's citation formatter. GitHub provenance stays pinned to its
indexed commit; archive provenance remains frozen. Export does not read original
files or authenticate them. A successful inventory is required before export;
inventory failure reports unavailable rather than claiming freshness. Check status
is only a point-in-time comparison to indexed evidence.

## Checks

The browser journeys are `python scripts/evidence_collection_smoke.py /path/to/findrail`
and `python scripts/persistent_collection_smoke.py /path/to/findrail`, with pinned
Selenium and matching local Chromium/ChromeDriver. They use synthetic documents
and local fixtures. They do not certify every browser, assistive technology or
OS-specific behavior.
