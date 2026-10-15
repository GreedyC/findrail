# Diagnostics and support report

`findrail doctor` performs bounded, offline inspection. It never opens the writer,
repairs the database, or runs a migration. Its JSON format remains
`report_version: 1`; `index_schema` is the actual SQLite `user_version`, while
`current_write_schema` is the schema this binary writes. A newer schema is an
error. An older schema is reported as needing a backed-up upgrade; doctor does
not promise that every intermediate version can be read. The ordinary read-only
store and the special schema-5 source-report profile are separate contracts.
An absent data directory or index is a normal first-run state and is not created
by doctor. `--show-paths` is an explicit CLI-only opt-in.

The web UI offers an explicit **Diagnostics** dialog when the backend advertises
the capability. The report is generated locally and is limited to 16 KiB. It
contains application and Go/platform versions, actual/current schema, safe check
codes, and aggregate source/policy counts. It never includes filesystem paths,
source/document names or IDs, indexed content, search queries, credentials,
environment, command arguments, logs, cookies, or raw operating-system/database
errors. The browser downloads `findrail-diagnostics.json` only after the user
chooses **Download report**. There is no report upload or remote telemetry.

The endpoint uses the existing local read backend and retains the server's
loopback, Host and Origin checks. It does not open a writer or trigger indexing.
If inspection is unavailable, the UI offers retry and does not retain a stale
report after the dialog closes.
