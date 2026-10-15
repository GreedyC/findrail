# Alpha.5 source candidate verification

This record is for an unpublished source candidate, not a release announcement.
The public version remains `0.1.0-alpha.4`; the public alpha.4 tag, release and
eight assets are unchanged. Candidate archives are named alpha.5, built from a
clean exact source SHA, and report schema 8, API 1 and VSIX 0.1.0. Do not use
their schema-8 data directory with the published alpha.4 binary.

## Exact candidate

The reviewed source SHA and the CI run links are recorded with the pull request.
The PR's Alpha release candidate workflow must run every required gate on its
head SHA: source CI (including Go/vet/race/UI), all five native package jobs,
the extracted Linux browser journey, installed read-only VSIX, exact eight-file
aggregate, reusable asset verification, and the read-only release-state check
where applicable. A skipped or absent required job is not a pass. Main-push
release-state evidence is distinct from PR preview evidence; publisher must
remain skipped and no release may be created.

## Required candidate cases

- Production-packaged native Linux binary: exact version/revision/schema/target,
  safe extraction into fresh owned paths, archive resources, executable modes,
  CLI/search/MCP/diagnostics/portable snapshot, and desktop first/second owner,
  Quit/drain and packaged PDF child checks.
- Native CI, not cross-build, covers linux-amd64, linux-arm64, darwin-amd64,
  darwin-arm64 and windows-amd64. Native controlled adapters are not manual
  viewer, Gatekeeper or SmartScreen demonstrations.
- Legacy lifecycle: schema 2 and 6 paths remain; the actual published alpha.4
  binary creates the schema-7 synthetic index, committed indexing report and
  saved collection with notes/order. Candidate migration checks search,
  provenance, report, collection order/note and default legacy passage offset
  zero. A complete stopped backup is restored and read by actual alpha.4;
  alpha.4 rejects candidate schema 8 without changing it. An induced migration
  failure preserves the schema-7 data directory byte-for-byte. No downgrade is
  attempted.
- Extracted native Linux browser journey covers fresh start, folder selection,
  diagnostics download/schema, late Literal and DOCX passage selection,
  collection save/note/order/export/restart, PDF page 2, Advanced fallback,
  keyboard/focus, changed evidence/Forget invalidation and purge, and Quit.
  `serve --no-sync` and demo remain read-only with temporary collections.
- Generated VS Code and Claude Desktop MCP configs are exercised with their
  recorded executable/argument arrays by the SDK integration test. MCP protocol
  smoke and installed read-only VSIX are separate checks; neither claims a GUI
  session in a third-party AI client or VS Code extension host beyond the test
  host that actually ran.
- The resource comparison uses the actual alpha.4 Linux amd64 release binary
  and extracted candidate on the same Linux host, with the same seeded 100-file
  synthetic workload and two measured queries after warmup. It characterizes
  resources only, not retrieval quality. Large profiles are separate runs.

## Scope and limitations

Only product behavior exercised by the exact-SHA reports is claimed. Browser
automation uses a controlled local environment and synthetic files. Cross-build
is not native execution. The browser is not a manual test of every browser or
assistive technology. The SDK test is not a third-party client GUI test. Unsigned
macOS/Windows release dialogs and every external viewer remain manual platform
coverage unless an explicit controlled native test says otherwise. Candidate
results do not change alpha.4's shipped behavior or its historical verification
record.
