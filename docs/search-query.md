# Search queries and filters (source builds)

Literal mode remains the default and preserves the existing tokenizer: punctuation
separates terms and terms are ANDed. Quotation marks, `OR`, `-`, and `*` have no
operator meaning in Literal mode. Advanced is opt-in.

## Advanced grammar

Advanced accepts whitespace-separated AND atoms and upper-case ASCII `OR`
branches. A branch must contain positive evidence. Prefix `-` excludes an atom
from that branch. Double quotes form a tokenizer phrase, with only `\"` and
`\\` escapes. One trailing `*` requests a token prefix (at least three letters
or numbers). Examples:

```sh
findrail search --mode advanced '"retry budget"' 
findrail search --mode advanced '"retry budget" OR backoff'
findrail search --mode advanced 'retry -deprecated'
findrail search --mode advanced 'idempot*'
findrail search --mode advanced --format pdf --path-prefix docs 'retry -deprecated'
```

PowerShell uses the same single-quoted examples. `OR` is the only Boolean
operator; use quotes to search reserved words or punctuation. Parentheses,
explicit AND/NOT/NEAR, and nested expressions are not supported. Queries are
limited to 256 Unicode code points, 32 atoms, and 8 branches. Phrase means an
FTS token phrase, not a byte substring: case and diacritic behavior follows the
bundled SQLite `unicode61 remove_diacritics 2` tokenizer. Prefix means token
prefix, not arbitrary substring. Literal title filtering is case-sensitive.
Unicode whitespace separates atoms. NUL and control characters are rejected;
CR/LF inside a quoted phrase is rejected. Lower-case `or` is a normal term.

In current schema-8 source builds, a long matching document can be browsed in
bounded passage windows. Literal search remains unchanged; the user can move to
the matching window, select an exact quote, and save its offset with a named
collection. The window is an indexed snapshot, bounded to 65,536 Unicode code
points and 256 KiB of UTF-8; it does not read an arbitrary source path. This
candidate behavior is not in published alpha.4, whose schema is 7.

The server filters `--format all|text|pdf|docx`, `--path-prefix` (relative,
forward-slash indexed path with segment boundary), and `--title-contains`
(literal case-sensitive substring) are ANDed with query and optional single
source scope. They are applied before total and limit. PDF/DOCX format comes
from indexed media type; filename extension is not authoritative. GitHub paths
are snapshot-relative paths.
Path filters allow at most 512 code points / 2,048 UTF-8 bytes and reject
absolute paths, backslashes, empty interior segments, `.` and `..`; one trailing
slash is normalized. Title filters allow 128 code points / 512 bytes. Neither
filter trims user-entered whitespace; `%` and `_` are literal characters.

Frozen `archive` sources use this same search engine, source scope, format/path/title
filters, preview budget, and PDF page evidence. Search and preview read only the
destination SQLite snapshot; original paths and URIs remain historical citations
and are never dereferenced.

```sh
findrail search --data-dir INDEX --path-prefix docs --title-contains runbook --json 'retry'
findrail search --data-dir INDEX --mode advanced --source SOURCE_ID --format pdf 'retry -deprecated'
```

HTTP exposes the same controls as `mode`, `format`, `path_prefix`, and
`title_contains` query parameters on `/api/v1/search`. Existing clients that omit
them remain Literal. The existing MCP `findrail_search` accepts optional fields
with the same names (query remains named `query`); its required `source_id`
continues to restrict each call to one allowlisted source.

## HTTP cursor pages (source builds)

When `/api/v1/capabilities` reports `search_pagination: true`, clients can use
the optional, read-only `GET /api/v1/search/pages` endpoint. An absent flag on
an older API v1 server means the capability is unavailable. Its defaults are
`mode=literal`, `format=all`, and `limit=20` (allowed range 1–100). All read
responses are `Cache-Control: no-store`. Keep the entire original query and
filter tuple, including the same limit, on every continuation request:

```sh
curl -G 'http://127.0.0.1:7766/api/v1/search/pages' \
  --data-urlencode 'q=retry budget' --data-urlencode 'mode=literal' \
  --data-urlencode 'source=SOURCE_ID' --data-urlencode 'format=text' \
  --data-urlencode 'path_prefix=docs' --data-urlencode 'title_contains=runbook' \
  --data-urlencode 'limit=20'
```

If `next_cursor` is a string, repeat those exact parameters and add its complete
opaque value as `cursor` (URL-encode it). Do not calculate or send an offset.
To retry a previous page, reuse the cursor saved for that page; cursors are
opaque, signed and bound to the query, mode, source, filters and limit. Changing
any part of that tuple requires restarting from the first page.

```sh
curl -G 'http://127.0.0.1:7766/api/v1/search/pages' \
  --data-urlencode 'q=retry budget' --data-urlencode 'mode=literal' \
  --data-urlencode 'source=SOURCE_ID' --data-urlencode 'format=text' \
  --data-urlencode 'path_prefix=docs' --data-urlencode 'title_contains=runbook' \
  --data-urlencode 'limit=20' --data-urlencode 'cursor=OPAQUE_CURSOR_FROM_PREVIOUS_RESPONSE'
```

Each cursor chain expires five minutes after its first page; clicking Next does
not extend that lifetime. A process restart invalidates usable cursors. A
structurally valid cursor carrying another public process epoch returns
`409 cursor_session_changed`; it is not a claim that a token with a destroyed
process MAC key can be authenticated. Any `409` (`cursor_expired`,
`cursor_stale`, or `cursor_session_changed`) means restart the search from its
first page. Data changes conservatively invalidate a chain, including commits
from note/collection changes; this is not limited to changes matching the query.

The response has `results`, `total`, `offset`, `returned`, `limit`,
`window_limit`, `next_cursor`, and `end_reason`. `total` is the full filtered
count even when the result window stops at 1,000 (`end_reason: "window_limit"`);
exactly 1,000 matches can end as `complete`. Each response, including its final
newline, is at most 524,288 bytes. The pager may return fewer results than
`limit` to fit that byte budget; its continuation begins at the next unreturned
row. Nullable cursor and end reason are JSON `null` when absent. Empty results
are `[]`. Results retain their original source, URI, identity and PDF page
attribution. Each snippet is capped at 1,024 Unicode code points, with an
explicit `snippet_truncated` boolean indicating whether that cap shortened it.

Errors retain a human-readable `error` string and add a stable `code`:

| HTTP | Codes and recovery |
|---|---|
| 400 | `cursor_invalid`, `cursor_mismatch`, `invalid_limit`, `invalid_search_page_request`: correct the parameters or restart the search. Query/filter validation retains `syntax`, `missing_positive_term`, `query_too_large`, `invalid_mode`, or `invalid_filter` and a Unicode `position`. |
| 404 | `search_page_unavailable`: this optional backend lacks page support and reports `search_pagination: false`. |
| 409 | `cursor_expired`, `cursor_stale`, `cursor_session_changed`: restart from the first page. |
| 429 | `search_page_busy`: bounded temporary pager admission pressure; retry later. |
| 500 | `page_result_too_large`: one required result cannot fit the byte budget. `search_page_unavailable` covers unknown internal errors or an oversized backend response. Neither returns partial page JSON. |
| 503 | `search_page_unavailable`: the pager is closed or unavailable. |
| 504 | `search_page_timeout`: the five-second request budget expired. A shorter caller deadline and client cancellation propagate to the pager. |

`serve`/`demo` remain read-only; page search adds no management capability. This
source-build endpoint does not add browser pagination controls, which are
planned separately, and is not included in the alpha.4 download.

Advanced PDF matching treats each page as a separate field for phrases, so a
phrase cannot cross a page boundary. Bare AND terms may occur on different
pages or in the title. Exclusions apply to the whole document. PDF citations
use a page with positive evidence; a title-only match has no page claim and
keeps the original URI. When several OR branches qualify, the first branch in
query order supplies page evidence. A page with all positive atoms is preferred;
positive-evidence page BM25 and then page number break ties. DOCX has no page
claims. GitHub citations retain the
full indexed commit URI. Search reads only the committed index snapshot.

Advanced search and the filters are source-build behavior and are not included
in the existing alpha.2 downloads.
