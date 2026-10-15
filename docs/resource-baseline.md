# Search resource baseline (candidate tooling)

This reproducible harness measures the shipped CLI, not a ranking score. It
creates fictional text, Go, DOCX, and one-page PDF files; no evaluation corpus,
external data, network access, or downloaded binary is used. It is intended for
resource characterization before a search optimization is proposed.

## Run

Build the desired binary first, then run (Python 3.9+):

```sh
go build -o /tmp/findrail ./cmd/findrail
python3 scripts/search_resource_check.py --binary /tmp/findrail \
  --documents 100 --seed 42 --queries 5 --report /tmp/findrail-resource.json
```

To measure two already-built binaries on the same host with an identical fixture
and query workload, add `--compare /path/to/second/findrail`:

```sh
python3 scripts/search_resource_check.py --binary /tmp/findrail-alpha4 \
  --compare /tmp/findrail-candidate --documents 1000 --seed 42 \
  --queries 5 --report /tmp/findrail-comparison.json
```

The supported profiles are 100 (smoke), 1,000, 10,000, and 100,000. The latter
requires explicit `--allow-large`. Generation enforces a 256 MiB cap on both
extracted-text workload and total corpus file bytes, plus a 5-minute/30-minute
overall deadline (small/large profiles); each run
uses separate temporary source and data directories and removes both on success
or failure. `--queries` is 1–100 repetitions per named synthetic query. Reports
contain only bounded metadata and aggregate results, never argv, paths,
environment values, or generated contents. A failed/partial run is marked
failed and must not be used as a baseline.

The report captures fixture version, seed and corpus SHA-256; binary SHA-256,
version, revision, Go runtime and schema; host OS/architecture; indexing wall
time and indexed counts; DB/WAL/SHM aggregate size after indexing and before
server startup; loopback server startup, first HTTP query and repeated persistent
HTTP latency p50/p95; and bounded search/evidence response bytes. The first
query is **not** a cold OS-cache measurement. RSS is explicitly
unavailable because there is no portable supported child-process measurement
API in this harness. Search response bytes describe CLI JSON, not HTTP evidence.
Query IDs are fixed (`common`, `rare`); query text is not recorded. Result-shape
checks only establish that synthetic known terms returned matches; they are not
relevance or ranking metrics.

Run core engine allocation measurements separately:

```sh
go test ./internal/store/sqlite -run '^$' -bench '^BenchmarkSearch$' -benchmem
```

Setup/indexing is outside the timed loop. `ns/op`, `B/op`, and `allocs/op` apply
only to `Store.Search`, not CLI presentation or UI. The benchmark profiles are
100 and 1,000 documents. Use the same machine, binary build configuration,
fixture seed/version and query workload for comparisons; measurements on
different native hosts are not evidence of Go-code speedup.

## Measurements

### 2026-10-15 local candidate measurement

Host: Linux x86_64, Intel Core i7-10700KF @ 3.80 GHz, Go 1.27.2,
Python 3.14.8. Candidate binary was built natively from this task's base SHA
`db1c088470db1e5fd189d1d17f060fc265eb1976` (reported version `dev`, schema 7,
binary SHA-256 `7b7d8e5dd19f683307ee62585f2b7d8ae77938046b624f42b70316a00514049d`).
100 docs, seed 42, fixture v1, corpus SHA-256
`aad1896cf497474fdfff3edc99edd632b1dc689b432af727d16a9e035be1e070`,
18,308 extracted-text bytes; all 100 indexed, 25 synthetic PDF pages, no skips.
Indexing: 85.820 ms. DB+WAL+SHM after index/before server: 290,816 bytes.
Loopback server startup: 7.206 ms; two HTTP requests per fixed query ID, p50
1.244 ms / p95 1.244 ms; first common query 1.244 ms; search response 3,078
bytes; evidence response 746 bytes. Local smoke only, not a cold-cache result.

Engine benchmark on the same host (setup excluded): 100 docs, 865,355 ns/op,
40,365 B/op, 686 allocs/op; 1,000 docs, 2,464,729 ns/op, 40,269 B/op,
687 allocs/op. This benchmark output was run with the `testing.B` default
calibration; it is not an end-to-end latency claim. A 10,000-document sample
was also recorded on the same host: 10,000/10,000 indexed, 2,500 synthetic PDF
pages, 1,890,302 extracted-text bytes, fixture SHA-256
`ff2fd92f6ea7d328e4df6ab29cb269f1ce8774d90ea9ecabcadfff1b72476d3f`;
indexing 7,981.678 ms; DB+WAL+SHM 11,403,264 bytes; server startup 6.782 ms;
four HTTP searches p50 14.063 ms / p95 14.920 ms; first query 14.920 ms;
search response 3,045 bytes; evidence 749 bytes.
Do not infer a hotspot or claim an optimization from these observations. The
final integration candidate should be measured afresh; do not carry forward
results from an earlier SHA.

## Limitations

The harness uses the production `index` CLI and loopback `serve` HTTP API; it does
not benchmark OS cold-cache behavior or child RSS. The Go benchmark isolates
engine allocations but does not represent end-to-end
latency. PDF fixtures are synthetic, one page each. Filesystem, SQLite and
extractor behavior vary by host. Alpha package metadata may not expose a VCS
revision; reports use `unknown` where unavailable. No production search
semantics or schema are changed by this tooling.
