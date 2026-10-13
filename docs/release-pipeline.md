# Release candidate pipeline

The alpha release workflow is a preparation pipeline until the repository owner
intentionally changes `build/package/VERSION` on `main`. A push to `main` runs
the full reusable CI, five native package jobs, a real packaged browser journey,
installed VSIX checks, exact-set aggregation, reusable verification, and a
read-only published-release state check. Only after every
gate succeeds can the final job create a release. Pull requests rehearse the
same gates with publication disabled and app version alpha.3. Publication is
restricted to the canonical repository's main push or explicit main dispatch;
PR and fork previews have read-only permissions.

## Preview rehearsal (agent 05 handoff)

For candidate app version `0.1.0-alpha.3`, use **Actions → Package rehearsal
(no release) → Run workflow** with `candidate_sha` set to the exact commit SHA.
The workflow checks out that SHA (not a PR merge ref), builds through
`scripts/package.py --version 0.1.0-alpha.3 --require-clean`, and executes each
extracted binary from a temporary path containing spaces and Unicode. It cannot
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

## Alpha.3 asset contract

The aggregate contains exactly these eight files (no staging extras):

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

The generated manifest includes the five platform archives and the one VSIX.
Archive bytes are not compared across operating systems/toolchains. Native
verification checks BUILD-INFO revision/version/target/cleanliness and invokes
the executable version command; Linux additionally runs upgrade and browser/API
smokes. The Linux browser job consumes that exact native archive, starts an
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
