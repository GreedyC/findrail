# Findrail

**You remember a word. Find the original.**

Findrail is an open-source, local-first search app built in Go. Choose folders
of notes, code, text PDFs and Word DOCX documents; search remembered words,
preview the matching source and copy its original location. Changes in those folders refresh the
index while the app runs. Keyword search needs no AI account and uploads no
documents. Alpha.3 also provides a scoped, read-only stdio MCP server.
Connected services and optional semantic retrieval are the next product stages.

**Status: local alpha.** The latest published release is [0.1.0-alpha.3](https://github.com/Lephiziel/findrail/releases/tag/v0.1.0-alpha.3).
This is testing software, not a stable release. See the
[version matrix](docs/launch/press-kit.md#version-boundaries) and
[verified release checks](docs/release-alpha3-verification.md). Private GitHub,
OCR, semantic search and desktop launching remain on the roadmap.

[Releases](https://github.com/Lephiziel/findrail/releases) ·
[Product](docs/product.md) · [Architecture](docs/architecture.md) ·
[Source management](docs/source-management.md) ·
[Indexing diagnostics](docs/indexing-diagnostics.md) ·
[Portable snapshots](docs/portable-snapshots.md) ·
[MCP integration](docs/mcp.md) ·
[Roadmap](docs/roadmap.md) · [VS Code client](docs/vscode.md) · [Contributing](CONTRIBUTING.md) ·
[Русский](docs/ru/overview.md)

[Older demo: this recording shows the narrower alpha.2 workflow, not newer
source-management, snapshot, collection or evaluation features.](docs/assets/demo.mp4)

[Try the three-document demo](docs/demo.md) ·
[Watch / download the 37-second video](docs/assets/demo.mp4) ·
[Give alpha feedback](https://github.com/Lephiziel/findrail/issues/3) ·
[Project facts and media](docs/launch/press-kit.md)

[Try the synthetic Turkish and English search evaluation](docs/search-evaluation.md).

Recorded from the running web interface using the fictional demo documents.
The video shows search, PDF page 2 and an automatic refresh after a note edit.
The GIF is a short preview; use the MP4 for the full recording and larger text.

## Install and try — published alpha.3

Download the archive for Linux, macOS or Windows from
[Releases](https://github.com/Lephiziel/findrail/releases), compare it against
`SHA256SUMS.txt`, and extract it. Go, Python and an external database are not required.
These alpha binaries are unsigned; macOS may require a per-app allowance in
Privacy & Security. Do not disable system-wide security protections. Each archive
contains installation instructions and license notices.

Direct downloads for **`0.1.0-alpha.3`**:

| Platform | Archive |
|---|---|
| Linux, x86-64 | [Linux amd64](https://github.com/Lephiziel/findrail/releases/download/v0.1.0-alpha.3/findrail_0.1.0-alpha.3_linux-amd64.tar.gz) |
| Linux, ARM64 | [Linux arm64](https://github.com/Lephiziel/findrail/releases/download/v0.1.0-alpha.3/findrail_0.1.0-alpha.3_linux-arm64.tar.gz) |
| macOS, Intel | [macOS amd64](https://github.com/Lephiziel/findrail/releases/download/v0.1.0-alpha.3/findrail_0.1.0-alpha.3_darwin-amd64.tar.gz) |
| macOS, Apple Silicon | [macOS arm64](https://github.com/Lephiziel/findrail/releases/download/v0.1.0-alpha.3/findrail_0.1.0-alpha.3_darwin-arm64.tar.gz) |
| Windows, x86-64 | [Windows amd64](https://github.com/Lephiziel/findrail/releases/download/v0.1.0-alpha.3/findrail_0.1.0-alpha.3_windows-amd64.zip) |

[Checksums](https://github.com/Lephiziel/findrail/releases/download/v0.1.0-alpha.3/SHA256SUMS.txt) · [Release manifest](https://github.com/Lephiziel/findrail/releases/download/v0.1.0-alpha.3/release-manifest.json) ·
[Optional VS Code VSIX](https://github.com/Lephiziel/findrail/releases/download/v0.1.0-alpha.3/findrail-readonly-0.1.0.vsix)

The VSIX is a separate client and needs a running Findrail server (API v1); it is
not required for the web workflow and is not published on Marketplace/Open VSX.
The previous [alpha.2 release](https://github.com/Lephiziel/findrail/releases/tag/v0.1.0-alpha.2)
remains available for a compatible pre-upgrade index. Before upgrading, stop
Findrail and back up the whole data directory; see
[upgrade and rollback](build/package/INSTALL.txt).

```bash
# Linux / macOS, inside the extracted directory:
./findrail start
```

```powershell
# Windows, inside the extracted directory:
.\findrail.exe start
```

Findrail opens the browser after the local listener is ready. If it does not,
open the URL printed in the terminal (normally **http://127.0.0.1:7766**).
A new index starts empty. In **Sources**, choose **Add folder** and enter the
absolute folder path on the computer running Findrail. Existing indexes resume
their registered sources; use a fresh `--data-dir` for an isolated empty start.

Search a remembered word in a note, code file, text PDF or DOCX document. Open
**Preview** to inspect the indexed text and use PDF page controls when present.
**Copy location** copies the original URI, including `#page=N` for PDF evidence;
browsers may restrict `file:` navigation. DOCX has no page-number claim.

Select two exact passages in Preview, add them to the evidence collection, add a
note, and download the Markdown citations. The collection is in-tab memory and
clears on reload; the downloaded file is separate. Keep `start` running for
folder refresh. Ctrl+C stops it; later `./findrail start` resumes the same index.
If you set `--data-dir`, use that same directory each time.

For the optional synthetic demo, stop Findrail and run `./findrail demo`
(Windows: `.\findrail.exe demo`), then search **idempotency**. The PDF match is
on page 2. The demo uses its own temporary workspace, removed on normal stop;
a forced kill can leave temporary files. See [demo instructions](docs/demo.md)
and the [manual smoke sheet](docs/release-smoke-alpha3.md).

### Build from source

Requires Go 1.26 or newer. No CGO is required.

```bash
git clone https://github.com/Lephiziel/findrail.git
cd findrail
go build -o bin/findrail ./cmd/findrail
./bin/findrail index --data-dir .findrail examples/notes
./bin/findrail search --data-dir .findrail "webhook"
./bin/findrail start --data-dir .findrail
```

Options precede positional arguments. If you use `--data-dir`, use the same
value for start, index, search and serve. `demo` always uses its own temporary
index and does not accept `--data-dir`.

The older `0.1.0-alpha.1` archives do not include `start` or `demo`. Download
`0.1.0-alpha.3` for the commands above, or use `index` followed by `serve` on the
older release.

### Start options

`start` indexes a folder and launches search in one command:

```bash
./bin/findrail start --data-dir .findrail /path/to/your/notes
# Later, resume the same registered folders:
./bin/findrail start --data-dir .findrail
```

The first command indexes the selected folder, starts automatic refresh and
attempts to open the local UI in your default browser. The terminal prints the
actual URL once the listener is bound. Keep it running; Ctrl+C stops the server.
Use `--no-open` on a headless machine, or open the printed URL manually if no
browser appears. Browser-opener startup failures do not stop search.

Options precede the folder. `--addr 127.0.0.1:7767` selects another local port;
network-facing addresses are rejected. Repeating `start DIRECTORY` applies the
chosen document-size limits to that folder, just like `index`; omitting DIRECTORY
resumes stored sources with their existing limits. Initial extraction errors
stop startup and preserve the prior committed inventory.

## Published alpha.3 behavior

The features below are included in the alpha.3 app archives, with the VS Code
client distributed as a separate VSIX. Older alpha.2 archives have a narrower
scope; see the [version matrix](docs/launch/press-kit.md#version-boundaries).

- A built-in three-document demo and one-command startup for your own folders.
- Explicit local folders containing UTF-8 text, Markdown and common source files.
- Text PDFs with original page numbers; a bounded extraction child process.
- Bounded offline DOCX plain-text body snapshots (no page numbers).
- Durable SQLite FTS5 search, BM25 ranking, Unicode terms and source filters.
- Opt-in Advanced queries and server-side format, indexed-path and title filters.
- Matching passages and plain-text previews of the indexed snapshot.
- Automatic refresh using directory notifications, debouncing and periodic scans.
- Source health: current refresh state, last success, errors and watcher fallback.
- Atomic full-source scans: failures preserve the previous inventory.
- Search reads the last committed snapshot while an update is in progress.
- CLI / JSON output, loopback web UI, read-only HTTP API and read-only stdio MCP (`findrail mcp`).
- Logical source removal, leaving original files untouched.
- Bounded committed indexing reports and process-local manual job progress.
- Optional read-only VS Code client for the alpha.3 server; see [setup](docs/vscode.md).
- Manual, commit-pinned public GitHub text snapshots with offline preview.
- Portable plaintext export and isolated frozen archive-source import.
- Empty-index onboarding and web source management (`start`).

See [alpha behaviour and limits](docs/local-alpha.md) and the
[validation report](docs/validation.md).

## Indexing and privacy

Text input defaults to **1 MiB per file**, configurable up to 32 MiB. PDFs default
to **16 MiB input**, with at most 500 pages, 1 MiB of extracted text and a 10-second
extraction deadline. Image-only / scanned PDFs are skipped: OCR is not included.
Malformed or encrypted PDFs fail the source scan, preserving its previous index.
DOCX input defaults to **8 MiB** (0 disables; configurable up to 16 MiB), with
bounded ZIP/XML parsing and no Office runtime. See [DOCX limits and scope](docs/docx.md).

Hidden entries, symlinks, dependency directories, binary / non-UTF-8 text and
common credential filenames are skipped. The index directory is excluded. This
policy cannot detect every secret inside an ordinary document.

The index stores plaintext text and original paths. It is **not encrypted at
rest**. On Unix, newly created directories and database files use private modes.
There is no runtime telemetry. See [data handling](docs/data-handling.md).

Schema upgrades are forward-only. Existing sources retain their previous format
policy; legacy DOCX remains disabled until explicitly enabled. Stop Findrail and
back up the entire data directory (including SQLite WAL/SHM) before upgrading.
An older binary cannot read schema 6; rollback means restoring the whole backup to
a separate location and using a binary compatible with that schema. See the
[complete install, upgrade, rollback and uninstall guide](build/package/INSTALL.txt).

## Commands

```bash
findrail index /path/to/notes
findrail index-github --path docs OWNER/REPO
findrail refresh-github SOURCE_ID
findrail start --no-open /path/to/notes
findrail start
findrail index --max-pdf-bytes 0 /path/to/text-only
findrail search --limit 10 "payment webhook"
findrail search --source SOURCE_ID --json "architecture"
findrail evaluate --queries examples/evaluation/queries.json --source SOURCE_ID --json
findrail sources --json
findrail source-report --data-dir .findrail --source SOURCE_ID
findrail serve --sync-interval 5m
findrail serve --no-sync
findrail watch --sync-interval 5m
findrail forget SOURCE_ID
findrail version
```

`watch` refreshes registered sources without starting HTTP. Periodic full refresh
is every five minutes by default; the minimum configurable interval is one
second. Native notifications normally trigger earlier scans.

Portable snapshots are CLI-first. Use `sources --json` to select a source, then
`export-source`, `inspect-export`, and `import-source`; imported snapshots are
independent, frozen sources. See [portable snapshots](docs/portable-snapshots.md)
for privacy, format and transfer details.

Default data directory: `$XDG_DATA_HOME/findrail` or `~/.local/share/findrail` on
Linux; `~/Library/Application Support/Findrail` on macOS;
`%LOCALAPPDATA%\Findrail` on Windows. Override with `--data-dir`.

## Product growth

| Capability | Local alpha | Next stages |
|---|---|---|
| Documents | Text / Markdown / code / PDF text / bounded DOCX body text | optional OCR |
| Sources | Local folders; public GitHub snapshots and frozen portable archive imports | Private GitHub, bookmarks, work tools |
| Freshness | File watching and full reconciliation | Resumable remote sync |
| Retrieval | Literal search, opt-in Advanced queries, source/format/path/title filters, PDF evidence, read-only result-set evaluation | Optional semantics |
| Clients | CLI, local web UI, HTTP, read-only stdio MCP and separately installed VS Code client (server/client API v1) | Desktop launcher, broader editor support |
| Extensions | Experimental connector kit; independent adoption not established | Stable SDK and conformance harness |

The advantage to validate is easy installation, useful retrieval, inspectable
sources and local ownership. Unified search already exists; user testing must
establish where Findrail helps. [Launch plan](docs/ru/launch.md).

## Repository layout

The project follows useful conventions from
[golang-standards/project-layout](https://github.com/golang-standards/project-layout)
and [official Go module guidance](https://go.dev/doc/modules/layout).

| Path | Responsibility |
|---|---|
| `cmd/findrail/` | Executable entry point |
| `internal/cli/`, `internal/config/` | Composition and commands |
| `internal/connectors/` | Source adapters |
| `internal/extract/`, `internal/ingest/` | Text / PDF extraction and atomic indexing |
| `internal/store/sqlite/`, `internal/search/` | Persistence, FTS and evidence |
| `internal/sync/` | Source discovery, watchers, retries and health |
| `internal/transport/` | HTTP, embedded UI and source-built stdio MCP |
| `internal/sourceapp/` | `start`-only source operations and in-memory jobs |
| `internal/semantic/` | Future semantic retrieval design |
| `pkg/connector/` | Experimental public connector contract |
| `api/`, `docs/` | Implemented API and product documentation |
| `build/`, `scripts/` | Distribution, smoke tests and developer tools |
| `examples/`, `test/`, `configs/`, `web/`, `deployments/` | Demo data and extension designs |

Tests live beside their packages. Future modules contain design notes, not
placeholder functions claiming implemented features.

## Development

```bash
go test ./...
go test -race ./...
go vet ./...
go mod verify
go build -o bin/findrail ./cmd/findrail
python3 scripts/smoke.py bin/findrail
python3 scripts/package.py
```

Contributions to extraction fixtures, search evaluation, accessibility and
platform installation are welcome. See [implementation tasks](docs/implementation-plan.md).

## License

Apache-2.0. The local product remains independently usable. Future hosted
services may charge for operated infrastructure. See [governance](GOVERNANCE.md).
