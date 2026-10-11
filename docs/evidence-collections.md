# Browser evidence collections (source builds)

Evidence collections are available in the source-built embedded browser UI. They
are not part of published alpha archives. Search and preview retain their existing
read-only HTTP contract; collection actions never write to the index or transmit
notes/passages to a service.

## Collect and inspect

Open a search result's **Preview**, select a non-empty passage wholly inside the
visible preview, then choose **Add to collection**. Alternatively, deliberately
select **Use whole visible preview**. This saves the visible indexed snapshot and
passage without another retrieval. A duplicate exact source/document/hash/page/
passage is not added twice. The collection panel allows inspection, notes, ordering,
and removal. **Open current indexed evidence** is a separate action; it does not
change the saved snapshot. PDFs keep their actual page; title-only PDF results have
no page claim. Text and DOCX have no page citation. A truncated preview contains
only the visible indexed text; it is not the complete original document.

Collections exist only in page memory. Reloading or closing the tab clears them.
No browser storage, query persistence, account, sharing, or original-file access is
used.

## Limits and privacy

The implementation limits collections to 40 entries, 256 KiB UTF-8 preview text
per entry, 2 MiB aggregate retained preview/excerpt text, 16 KiB metadata per
entry, 2,048 UTF-8 bytes per note, 256 UTF-8 bytes for the title, and 4 MiB for
Markdown. Entries are not silently evicted or truncated. With these limits, the
retained collection data is bounded by 2 MiB preview/excerpt text + 640 KiB entry
metadata + 80 KiB notes (about 2.71 MiB retained state). During rendering, the
bounded row DOM and snapshot copies can each add up to a comparable amount. GET
parsing is capped at 1 MiB for source inventory and 2 MiB per evidence body; the
reader checks actual streamed bytes. Export text, its manual-copy field, and a
download Blob are individually capped at 4 MiB and replaced/revoked on the next
export, clear, removal or page teardown. A conservative feature-owned UTF-8
payload accounting bound is 32 MiB across retained state and simultaneous bounded
copies (browser runtime/engine bookkeeping is implementation-specific and is not
an RSS guarantee). Export may contain private passages and local file paths; a
downloaded or copied export cannot be recalled by later removing an index entry.

## Snapshot checks and provenance

**Check current snapshots** explicitly compares each saved snapshot with the
current indexed evidence. It does not read live files, authenticate the file, or
provide continuous authorization. A changed snapshot remains saved as historical
evidence; a missing document or removed source is purged from this page's
collection. A failed inventory request does not prove removal. Checks are
best-effort and cannot make removal atomic with data already retrieved or
exported. Export first requires a successful source inventory check, but does not
automatically recheck document freshness.

Markdown uses Findrail's existing citation formatter. File URIs remain local
provenance, not public download links. GitHub provenance remains pinned to its
indexed commit. Imported archive provenance is frozen and historical. Exports are
plain text, not a persistent notebook, backup of original documents, authenticated
citation format, or AI summary. Clipboard failure presents the same bounded
Markdown in a read-only field for manual selection. Download is explicit and uses
the fixed `findrail-evidence.md` filename.

## Reproducible browser smoke

The dedicated workflow installs matched Chrome for Testing/ChromeDriver using the
test-only pinned `@puppeteer/browsers==2.10.6` installer and pinned
`selenium==4.35.0`, then builds Findrail and runs
`python scripts/evidence_collection_smoke.py /path/to/findrail`. Locally, install
Chromium and a matching ChromeDriver, install that Selenium version in a virtual
environment, build `./cmd/findrail`, and run the same command. The compiled
journey uses temporary synthetic text/PDF/DOCX, a CLI-imported archive, and a
locally seeded pinned-GitHub document with no public network calls. It exercises
selected/whole-preview and duplicate pins, separate PDF pages/title-only page 0,
DOCX no-page provenance, notes/order, changed and missing snapshots, delayed
responses during note/order/removal/clear/export/source-removal mutations, the
real clipboard where supported and denied-permission fallback, downloaded bytes,
Escape/focus restoration, clear/reload, 375px layout, and actual Chromium 200%
page zoom at 375px physical width. It does not certify every
assistive-technology/native-browser behavior or every possible timing
permutation.
