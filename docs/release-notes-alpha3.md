# Findrail 0.1.0-alpha.3

> Publisher text prepared for promotion only. Do not publish or present as a
> released version until the real release, checksums, assets and URLs have been
> verified. See [post-release promotion checklist](release-alpha3-promotion.md).

Findrail is a local-first search app for notes, code and technical documents.
Alpha.3 adds a simpler empty-index start and folder selection, with Preview and
PDF-page evidence. A first-use path is: choose a folder, find a technical note or
PDF, inspect the indexed evidence, save two passages with a note, download the
Markdown citations, and restart Findrail.

## Highlights

- Portable source snapshots preserve indexed plaintext and provenance. They do
  not contain original files or a frozen database; imported sources are
  independent and frozen.
- Source reports show the last committed successful indexing run, not a history
  of failed attempts. Root-only `.findrailignore` rules are supported; a failed
  policy scan retains the previous committed content/report.
- Evidence collections are in-tab memory and disappear on reload. Explicit
  Markdown download is separate and can contain private text/paths.
- The read-only `evaluate` command checks Literal result path sets for 1–100
  cases, with up to 100 results per case. Incomplete cases are errors; mismatches
  return nonzero after the complete report.
- Connector conformance tooling remains experimental; independent adoption is
  not established. The separate read-only VS Code VSIX requires Findrail
  server/client API v1 and is not a Marketplace/Open VSX release.

## Upgrade, rollback and removal

Alpha.2 uses schema 2; alpha.3 uses schema 6 with forward migrations 1–6. Stop
all Findrail processes and back up the entire data directory, including SQLite
WAL/SHM when present, before upgrading. Legacy sources keep DOCX disabled until
explicitly enabled. Reverse migrations do not exist. Never open schema 6 with an
older binary: rollback restores the whole stopped backup to a separate location
and uses a compatible binary. To uninstall, stop all processes and remove the
extracted app directory; remove the data directory separately only if its
plaintext indexed copy is no longer needed. Original files are untouched. Read
the included INSTALL.txt before upgrading or removing data.

## Limitations

Findrail stores indexed text and provenance as local plaintext. OCR, semantic
retrieval, private GitHub, automatic updates, code signing and notarization are
not included. Public GitHub refresh remains manual. Native package checks do not
certify every browser/editor/platform interaction. See the candidate report for
the exact validation scope and remaining manual checks.
