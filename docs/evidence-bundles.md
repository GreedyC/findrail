# Portable evidence bundles (source format)

The source tree defines a strict, portable JSON v1 codec for moving selected
citations and notes. This is distinct from portable source snapshot ZIP v1, which
transfers indexed sources. The codec has no storage, HTTP, file access, network
access, or import behavior. It is not part of the published alpha.4 binary.

## JSON contract

The UTF-8 payload is exactly one object with exactly these required fields:

```json
{"format":"findrail-evidence-bundle","version":1,"title":"Research","sources":[{"alias":"s1","kind":"filesystem","display_name":"Notes"}],"entries":[{"source_alias":"s1","relative_path":"topic/note.md","media_type":"text/markdown","content_hash":"0000000000000000000000000000000000000000000000000000000000000000","page":0,"start_char":0,"text":"selected excerpt","note":"why it matters"}]}
```

No unknown, missing, or duplicate fields are accepted at any depth. Sources have
exactly `alias`, `kind`, and `display_name`. Aliases are unique `s1` through
`s40`, and every source must be referenced by an entry. Kinds are exactly
`filesystem`, `github`, or `archive`. Display name is only a user hint for
explicit remapping; it does not authorize choosing a source or destination.

Entries have exactly `source_alias`, `relative_path`, `media_type`,
`content_hash`, `page`, `start_char`, `text`, and `note`. Array order is retained;
repeated citations are not coalesced, including when their notes differ.
`content_hash` is the indexed content's 64-character lowercase SHA-256 value; it
does not authenticate an author or source. Page is zero for non-PDF and 1–100000
for PDF. `start_char` is a Unicode code-point offset in the indexed body (or PDF
page), never a byte or UTF-16 offset. No Unicode normalization is performed.
Text contains only the selected excerpt; selecting the whole visible preview
stores that preview as the excerpt. There is no duplicate full-preview field.

Paths are slash-separated relative paths. Absolute paths, drive and UNC paths,
backslashes, NUL, empty components, `.` and `..` components are rejected. Paths
are not rewritten to make a citation appear to match another document. A source
whose real path cannot meet these rules must produce an export error.

The format never contains absolute roots, URIs, destination/source/document/
collection IDs, `original_identity`, or timestamp authority. Destination
matching requires a later explicit operation that verifies current indexed data;
the bundle itself must never select a path or authorize a write.

## Bounds and integrity

| Value | Limit |
|---|---:|
| Raw JSON | 4 MiB |
| JSON nesting depth | 16 |
| Title | nonblank, 256 UTF-8 bytes |
| Sources / entries | 40 / 40 |
| Display name | 512 bytes |
| Relative path | 2,048 bytes and 512 code points |
| Entry metadata (excluding text and note) | 16 KiB |
| Selected text, each / total | nonempty, 256 KiB and 65,536 code points / 2 MiB |
| Note | 2,048 bytes |
| Start offset | 0–2,147,483,647 |

Integers must be JSON integer tokens; fractional and overflowing values are
invalid. Empty source and entry arrays are allowed with a valid title. Readers
reject invalid UTF-8, duplicate keys, unknown fields, trailing values/data and
oversized input before constructing a bundle. Limits are bounded codec-owned
buffers, not a process RSS guarantee. Nothing is silently truncated or evicted.

The canonical encoder preserves source/entry order and every string exactly;
its SHA-256 digest detects transfer inconsistency only. It is not a signature,
proof of authorship, or proof that an indexed source is trustworthy.

Bundles preserve historical selected evidence, not a live link. If an indexed
document has changed, moved, been forgotten, or is otherwise no longer current,
the historical citation cannot automatically be restored to the current
collection. Any future restore workflow must explicitly compare current indexed
data and let the user remap; it must not trust the bundle's display name or hash
as authority.
