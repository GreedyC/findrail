# Roadmap

This roadmap describes product scope and release gates. It is not a promise of
dates. Status changes require working code and evidence.

| Stage | Outcome | Release gate | Status |
|---|---|---|---|
| R00 · Foundation | Local index, keyword search, CLI, browser UI, contracts, CI | Lifecycle / rollback tests and a runnable demo | Implemented; local validation recorded separately |
| R01 · Local alpha | PDF text, bounded DOCX body snapshots, watcher, source diagnostics, folder ignore rules, preview and evidence export | Lifecycle checks and read-only literal evaluation; broader real-user retrieval validation | Published, with saved named collections in alpha.4; broader independent retrieval validation remains open |
| R02 · Connected search | Read-only GitHub, local + remote combined search, secure credentials | Resume, rate limit, revocation, and deletion tests | Public file snapshots/manual refresh and web management are published; private repositories and resumable sync remain planned |
| R03 · Extensions | Versioned connector SDK, examples, conformance harness | Independent contributor creates an adapter from docs | Experimental conformance kit and separate-module example implemented; independent-contributor gate and API stabilization remain open |
| R04 · Optional semantics | Passage chunking, opt-in embedding backend, hybrid ranking | Better retrieval on labeled corpus without losing exact-match quality | Planned |
| R05 · Daily access | Native desktop launcher; read-only VS Code client ([setup](vscode.md)) | Single-instance lifecycle, archive install/uninstall and native platform journeys | Published in alpha.4 after five native package jobs and the owner's reported short check. Manual GUI coverage on every platform is not established. VS Code is separately distributed for API v1. |
| R06 · Public beta | Onboarding, releases, migrations, exports, operational documentation | Upgrade / stopped-backup restore / uninstall journeys and cross-platform QA | Alpha.4 is published at schema 7, with persistent evidence collections and verified upgrade/backup journeys. This remains an alpha; broader installation and return-use evidence is still needed. |
| R07 · Community platform | Connector catalog, governance, optional operated services | Organic contributions and demonstrated demand | Planned |

## First complete public product

The local + GitHub alpha should include a coherent onboarding journey, Markdown /
text / PDF support, two source types, continuous updates, source filters,
evidence previews, original-location opening on supported clients, and a source
health panel. Ship a useful workflow rather than many disconnected adapters.

## Current delivery priority

As of 14 October 2026, alpha.4 is published with desktop launchers, opt-in
original-file opening and named evidence collections. Its five native targets,
browser journey, installed VSIX and upgrade checks passed on the release
revision. Public downloads were verified separately; see the
[release record](release-alpha4-verification.md). Historical alpha.3 remains
immutable at schema 6; alpha.4 uses schema 7.

The next priority is getting a small number of people through installation,
actual document recovery and voluntary return-use reports. Use those reports
to select the next product change. Search-evaluation work can continue in its
documented contribution lane; new connectors and semantic retrieval remain
separate roadmap decisions.

## Contribution lanes

Document extraction, filesystem edge cases, search evaluation, client
accessibility, connector conformance, distribution, and translations can proceed
as separate community contributions once their contracts are documented.

## Deferred decisions

Email ingestion, OCR, cross-device encrypted sync, and team authorization involve
additional storage, permissions, and packaging work. They remain explicit future
designs. The foundation does not support them.
