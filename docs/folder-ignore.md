# Folder ignore rules (source builds)

A regular UTF-8 `.findrailignore` directly in an explicitly selected filesystem
root adds exclusions for that root. Findrail reads but never creates or edits it.
It is root-only: nested files, `.gitignore`, Git configuration, parent folders,
home-directory settings, GitHub sources and imported archives do not participate.
The file itself is always hidden from indexing. Rules cannot override hidden,
dependency, sensitive-name, symlink/special-file, index-directory, format,
encoding, size or extraction limits.

The language is intentionally smaller than Git's. Lines use LF or CRLF; one
initial UTF-8 BOM is allowed. Empty lines and first-character `#` lines are
comments. `!` negates an earlier user exclusion. `\#` and `\!` quote a literal
first character. Other backslashes, classes, continuation, controls, absolute
paths, traversal and malformed patterns are errors. Unescaped trailing ASCII
spaces are ignored; leading/internal spaces are significant. Filenames ending
in a space are outside this initial rule syntax.

`/` separates segments. A leading slash anchors to the root; a middle slash
makes the pattern root-relative; a pattern without slashes matches a basename
at every depth. A trailing slash matches directories only. `*` and `?` match
within one segment; `**` is a complete segment matching zero or more segments.
Last matching user rule wins. For example:

```text
*.log                       # basename at any depth
/scratch/                   # root-level directory only
notes/**/draft-?.md         # zero or more intermediate directories
/notes/*
!/notes/keep.md             # keep this file, but not a pruned parent
\#literal.md
\!literal.md
```

An excluded directory is pruned; a later descendant negation cannot recover
it unless its parent remained traversable. Rules are case-sensitive on every
OS. Limits: 64 KiB file, 256 rules, 1,024 UTF-8 bytes / 64 segments per rule,
4,096 bytes / 256 segments per checked path.

Rule edits do not immediately erase indexed text. The previous searchable
snapshot remains until a complete scan succeeds; malformed, unreadable or
changing policy fails the scan and preserves the old snapshot/report. A
successful exclusion scan logically prunes documents, not cryptographically
erases disk/WAL bytes. Filesystem consistency is optimistic and bounded, not a
global filesystem lock. Watchers reconcile root policy changes; periodic scans
remain the recovery fallback.

Preview a bounded set of metadata-only decisions without opening the index:

```sh
findrail explain-path "/path/to/notes" --path notes.md --path build/generated.md
findrail explain-path "/path/to/notes" --path build/generated.md --json
findrail explain-path "/path/to/notes" --path build/generated.md --show-rule
```

The JSON format has `version: 1`; status codes describe path-policy/metadata,
not actual indexing. PDF/DOCX source-specific settings, encoding, extraction
success and committed presence cannot be inferred. `--show-rule` explicitly
includes a matched rule; normal diagnostics never persist rule text or document
contents. Source builds only; this is not a shipped alpha.2 capability.

GitHub remains its bounded public text snapshot and archives remain frozen
imports. Neither uses these filesystem rules; portable v1 is unchanged. See
[connector behavior](connectors.md) and [local refresh semantics](local-alpha.md).
