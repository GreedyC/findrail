# Roadmap

This roadmap describes product scope and release gates. It is not a promise of
dates. Status changes require working code and evidence.

| Stage | Outcome | Release gate | Status |
|---|---|---|---|
| R00 · Foundation | Local index, keyword search, CLI, browser UI, contracts, CI | Lifecycle / rollback tests and a runnable demo | Implemented; local validation recorded separately |
| R01 · Local alpha | PDF text, bounded DOCX body snapshots, watcher, source diagnostics, folder ignore rules, preview and session evidence export | Real-user retrieval validation remains open; lifecycle checks and read-only literal evaluation implemented | Code implemented in source builds; user validation pending |
| R02 · Connected search | Read-only GitHub, local + remote combined search, secure credentials | Resume, rate limit, revocation, and deletion tests | Public file snapshots/manual refresh implemented; web management is source-build only; private and resumable sync planned |
| R03 · Extensions | Versioned connector SDK, examples, conformance harness | Independent contributor creates an adapter from docs | Experimental conformance kit and separate-module example implemented; independent-contributor gate and API stabilization remain open |
| R04 · Optional semantics | Passage chunking, opt-in embedding backend, hybrid ranking | Better retrieval on labeled corpus without losing exact-match quality | Planned |
| R05 · Daily access | Native desktop launcher; read-only VS Code client ([setup](vscode.md)) | Single-instance lifecycle, archive install/uninstall and native platform journeys | Launcher/install resources are in the unpublished alpha.4 candidate; five-target native acceptance remains a release gate. VS Code is separately distributed for API v1. |
| R06 · Public beta | Onboarding, releases, migrations, exports, operational documentation | Upgrade / stopped-backup restore / uninstall journeys and cross-platform QA | Published alpha.3 is schema 6. Source tree and unpublished alpha.4 candidate use schema 7, with persistent evidence collections; candidate package validation is ongoing. |
| R07 · Community platform | Connector catalog, governance, optional operated services | Organic contributions and demonstrated demand | Planned |

## First complete public product

The local + GitHub alpha should include a coherent onboarding journey, Markdown /
text / PDF support, two source types, continuous updates, source filters,
evidence previews, original-location opening on supported clients, and a source
health panel. Ship a useful workflow rather than many disconnected adapters.

## Current delivery priority

As of 14 October 2026, PRs #38–42 are integrated on main. Published alpha.3
archives remain immutable at schema 6. Main packages a no-publish alpha.4
candidate at schema 7; native, browser, upgrade and installed-client evidence
must pass on one exact candidate SHA before any separate release decision.

Finish a coherent new release and make the compatible VSIX independently
downloadable before the next wider editorial wave. Then use installation,
actual document recovery and voluntary return-use reports to select the next
product change. More connectors or semantic retrieval are not a release gate.

## Contribution lanes

Document extraction, filesystem edge cases, search evaluation, client
accessibility, connector conformance, distribution, and translations can proceed
as separate community contributions once their contracts are documented.

## Deferred decisions

Email ingestion, OCR, cross-device encrypted sync, and team authorization involve
additional storage, permissions, and packaging work. They remain explicit future
designs. The foundation does not support them.
