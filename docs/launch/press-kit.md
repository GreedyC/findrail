# Findrail: project facts and media

Checked on 2026-10-12. Findrail is an Apache-2.0 open-source project built in Go.
The current published local alpha is `0.1.0-alpha.2`.
The merged alpha.3 preparation work has not published a new release.

## Short description

Local keyword search for folders of notes, code and text PDFs, with matching
passages, PDF page numbers and original file locations.

## Editor description

Findrail is an open-source Go app for developers who keep notes, code and
technical PDFs in different folders. Select a folder, search words you remember,
preview the indexed text and copy the original file location. Text PDF results
preserve their page numbers. Local folders refresh while the app runs. The
released alpha includes standalone archives for Linux, macOS and Windows, a
CLI and an optional loopback web interface. Keyword search requires no model,
account, document upload or external database.

## Try the released workflow

1. Download and extract an [alpha.2 archive](https://github.com/Lephiziel/findrail/releases/tag/v0.1.0-alpha.2).
   Compare it against the release's `SHA256SUMS.txt`.
2. In the extracted directory, run `./findrail demo` on Linux / macOS, or
   `.\findrail.exe demo` on Windows. Open the printed local URL if the browser
   does not appear.
3. Search `idempotency`. The three fictional matches are a Markdown note,
   Go code and a two-page text PDF.
4. Preview `webhook-runbook.pdf`, inspect page 2 and use **Copy location**.
   The location includes `#page=2`; it does not launch a desktop PDF viewer.
5. Stop with Ctrl+C. To try your own folder, run `./findrail start /path/to/notes`
   or `.\findrail.exe start "C:\Users\YOU\Documents\Notes"`.

No Go installation is needed for these archives. They are unsigned alpha
binaries; macOS may require an explicit allowance in Privacy & Security.
The [demo guide](../demo.md) includes a synthetic live-refresh test.

## Candidate first path — not a download offer

After the archive is actually released: download the standalone archive, verify
its checksum against the manifest from that release, extract, start into an empty
index, choose **Add folder**, find a technical document, inspect Preview and the
PDF page, save two exact passages with a note, download Markdown, then restart.
No initial MCP, GitHub, VS Code or source build is needed. Until publication,
use alpha.2 for the released workflow above; candidate notes are not asset links.
See [install/upgrade](../../build/package/INSTALL.txt), [candidate notes](../release-notes-alpha3-candidate.md),
and the [manual smoke sheet](../release-smoke-alpha3.md).

## Version boundaries

| Capability | Published alpha.2 archives | Main / alpha.3 candidate (not yet released) | Separate distribution |
|---|---|---|---|
| Local text, Markdown and common code files | Included | Included | — |
| Text PDFs, page attribution, snapshot preview, Copy location | Included | Included | — |
| Folder refresh, `start`, three-document `demo` | Included | Included | — |
| Copy preview text as Markdown with its source | Not included | Included | — |
| Scoped read-only stdio MCP | Not included | Included; [configuration](../mcp.md) | — |
| Commit-pinned public GitHub file snapshots | Not included | Included; [instructions](../github.md) | — |
| Empty-index onboarding and web source management | Not included | Included; [instructions](../source-management.md) | — |
| Bounded DOCX body-text indexing; legacy sources disabled by default | Not included | Included; [supported subset](../docx.md) | — |
| Advanced lexical queries and format/path/title filters | Not included | Included; [query semantics](../search-query.md) | — |
| Read-only offline `doctor` | Not included | Included | — |
| Portable snapshots | Not included | Indexed plaintext and provenance, not original files; import is frozen, not a frozen database; [scope](../portable-snapshots.md) | — |
| Indexing report | Not included | Last committed successful scan only, not failed-attempt history; [details](../indexing-diagnostics.md) | — |
| `.findrailignore` | Not included | Root-only rules; failed policy scan retains prior committed content/report; [syntax](../folder-ignore.md) | — |
| Evidence collection | Not included | In-tab only; reload clears it; explicit Markdown download; [scope](../evidence-collections.md) | — |
| `evaluate` | Not included | Read-only Literal path sets, 1–100 cases, at most 100 results/case; incomplete is error; mismatch nonzero after full report; [details](../search-evaluation.md) | — |
| VS Code read-only client | Not included | Requires compatible server/client API v1; [setup](../vscode.md) | VSIX installable locally; not published on Marketplace/Open VSX |
| Connector kit | Not included | Experimental; independent adoption not established; [guide](../connectors.md) | — |
| Marketplace / Open VSX listings | Not published | Not published | Not published |
| OCR, semantic retrieval, private GitHub | Not included | Not implemented | — |

Search is literal keyword retrieval, not an AI answer or a promise of semantic
recall. The app searches explicitly indexed sources and previews saved text.
The current web interface is loopback only. GitHub refresh is manual; repository
issues, PR discussions, remote PDFs and private repositories are not indexed.
An MCP client may forward returned evidence to its own AI provider. Local
indexing does not establish another client's privacy policy.

## Media

- [37-second original web recording](../assets/demo.mp4)
- [Animated preview](../assets/demo.gif)
- [PNG from the recording](../assets/demo.png)
- [Three-document demo instructions](../demo.md)

The recording uses synthetic documents and shows the narrower old alpha.2 demo
workflow. It is not a performance benchmark, a customer testimonial, or a demo
of the new source management, portable imports, collections or evaluation. It is
not evidence for candidate/release UI checks; use the manual smoke sheet for that.

## Links and feedback

- [Source](https://github.com/Lephiziel/findrail)
- [Alpha.2 release](https://github.com/Lephiziel/findrail/releases/tag/v0.1.0-alpha.2)
- [Alpha feedback](https://github.com/Lephiziel/findrail/issues/3)
- [Architecture](../architecture.md)
- [License](../../LICENSE)

A useful first report is the OS, version, whether the app started, whether a
remembered word led to the right original document, and one obstacle. Public
feedback should use synthetic or redacted examples. Archive downloads and
repository stars are not counts of independent active users.
