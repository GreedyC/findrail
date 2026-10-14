# Release candidate pipeline

The alpha release workflow is a preparation pipeline until the repository owner
intentionally changes `build/package/VERSION` on `main`. A push to `main` runs
the full reusable CI, five native package jobs, a real packaged browser journey,
installed VSIX checks, exact-set aggregation, reusable verification, and a
read-only published-release state check. Only after every
gate succeeds can the final job create a release. Pull requests rehearse the
same gates with publication disabled and app version alpha.3. Publication is
restricted to the canonical repository's main push or explicit main dispatch;
PR and fork previews have read-only permissions. The unpublished alpha.4
candidate archives include native desktop launchers and target-specific install
resources; these are archive members, not additional release assets.

## Preview rehearsal (agent 05 handoff)

For an unpublished alpha.4 candidate, use **Actions → Package rehearsal
(no release) → Run workflow** with `candidate_sha` set to the exact commit SHA and
`candidate_version` explicitly set to `0.1.0-alpha.4`. `build/package/VERSION`
remains `0.1.0-alpha.3`; this source build is a rehearsal, not a published release.
The workflow checks out that SHA (not a PR merge ref), builds through
`scripts/package.py --version 0.1.0-alpha.4 --require-clean`, and executes each
extracted CLI and desktop binaries from a temporary path containing spaces and
Unicode. All five native targets exercise first/second desktop launch and PDF
child extraction through the packaged launcher using a
controlled native executable adapter on each target OS; these are lifecycle
checks, not manual viewer demonstrations. macOS uses the packaged app entrypoint;
Windows uses the GUI executable. Linux additionally migrates a synthetic schema-6
alpha.3 index, checks a stopped backup with the real published alpha.3 binary,
and retains the schema-2 upgrade path. The packaged browser journey tests native
original/folder actions through controlled local executable adapters and verifies
named collection restoration only after the candidate process stops and restarts.
It cannot
create or move tags, edit VERSION, or publish a release. The five artifacts are
named `candidate-<sha>-<target>` and retained for 14 days. A full asset rehearsal
uses **Alpha release candidate → Run workflow** with that SHA and `publish=false`;
set `candidate_version=0.1.0-alpha.3`; its `release-assets-<sha>` aggregate is
retained for 30 days. This path accepts only the exact head SHA of `main`, does
not edit VERSION, and cannot publish when `publish=false`.

Download the artifact from the run summary, extract it, then verify the complete
candidate set with the same revision and version:

```sh
python3 scripts/release_assets.py verify \
  --directory ./release-assets \
  --version 0.1.0-alpha.3 \
  --revision <candidate-sha>
```

The native artifacts contain only their archive and a small verification report;
no temporary indexes, user paths, credentials, or test databases are uploaded.

## Published alpha.3 asset contract

The immutable published alpha.3 contains exactly these eight files (no staging extras):

```text
findrail_0.1.0-alpha.3_linux-amd64.tar.gz
findrail_0.1.0-alpha.3_linux-arm64.tar.gz
findrail_0.1.0-alpha.3_darwin-amd64.tar.gz
findrail_0.1.0-alpha.3_darwin-arm64.tar.gz
findrail_0.1.0-alpha.3_windows-amd64.zip
findrail-readonly-0.1.0.vsix
release-manifest.json
SHA256SUMS.txt
```

The VSIX version remains the extension's own `0.1.0`; it is not renamed to the
application alpha version. Manifest asset digests and sizes are generated from
the final archive/VSIX bytes. `SHA256SUMS.txt` covers all six installation files
and `release-manifest.json`, but not itself. The manifest has this shape (the
actual generated values are authoritative):

```json
{
  "manifest_version": 1,
  "app_version": "0.1.0-alpha.3",
  "source_revision": "<40-character candidate commit SHA>",
  "schema_version": 6,
  "client_api_version": 1,
  "extension_version": "0.1.0",
  "assets": [
    {
      "basename": "findrail_0.1.0-alpha.3_linux-amd64.tar.gz",
      "kind": "archive",
      "target": "linux-amd64",
      "size": 12345678,
      "sha256": "<64-character SHA-256>"
    },
    {
      "basename": "findrail-readonly-0.1.0.vsix",
      "kind": "vsix",
      "size": 123456,
      "sha256": "<64-character SHA-256>"
    }
  ]
}
```

The published manifest is pinned to the historical alpha.3 tag SHA
`d5dc1bec50efcb3c26d09e9b24b14cf3c0b2f4cb`, schema 6, API 1 and extension 0.1.0.
The no-publish alpha.4 candidate records the schema read from
`internal/store/sqlite/sqlite.go`; packaging checks it against the contiguous
migration inventory, and archive BUILD-INFO must agree with the manifest. Unknown
candidate versions and malformed metadata fail closed. The generated manifest includes the five platform archives and the one VSIX.
Archive bytes are not compared across operating systems/toolchains. Native
verification checks BUILD-INFO revision/version/target/cleanliness and invokes
the CLI version command. Candidate archives use strict per-target member
allowlists for the CLI, desktop launcher, that target's install resources, build
metadata, product notices and bounded license inventory; historical alpha.3
retains its original archive member set. Extraction rejects traversal,
duplicate/conflicting paths, links and special files; launcher executable modes
are checked. Linux additionally runs upgrade and browser/API smokes. The Linux
browser job consumes that exact native archive, starts an
empty index, adds a folder in the UI, checks selected text/PDF-page citations
and Markdown download, and checks reload/restart. The installed client job runs
extension tests and compiled-server integration, then installs the actual VSIX
in isolated user-data/extensions directories and exercises it against the
extracted native candidate. Only the test bootstrap is loaded as a development
extension; Findrail must load from the installed extension directory.

## Gates and immutable-release behavior

Publication requires the exact same workflow run's full CI (including three-OS
Go checks, race and UI tests), five native package jobs, packaged browser journey,
installed VSIX checks, aggregate verification, and reusable final verification.
The generic CI workflow is additional evidence, not a substitute for these
required jobs. `release-state` has read-only contents permission and rejects API
errors, a tag without a release, an incomplete asset set, or a mismatched
tag/manifest revision. For the new contract, existing archives' embedded
BUILD-INFO and the VSIX identity are also verified before accepting a no-op.
A complete historical alpha.2 release is a no-op when
main advances with VERSION unchanged; its established contract is five archives
plus `SHA256SUMS.txt`, without a VSIX or manifest. The publisher has write
permission only in the final job, rechecks that the tag does not already exist,
and refuses to replace or move an existing tag/release.

## Source candidates after alpha.3

PR checks and main source checks package an unpublished alpha.4 candidate.
The version in build/package/VERSION continues to select the published release
for the read-only release-state gate. While that file remains alpha.3, main
verifies the unchanged historical alpha.3 assets and does not publish the
alpha.4 candidate. Publication additionally requires candidate and release
versions to match. Schema metadata comes from the candidate source migrations;
historical alpha.3 remains schema 6. No release assets or tags are replaced.
