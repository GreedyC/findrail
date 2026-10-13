# alpha.3 release-candidate rehearsal (not a release)

This records reviewed preparation evidence on 2026-10-13. Published downloads
remain alpha.2. Alpha.3 is not published, signed or certified for every user or
platform. No release was created by this documentation work.

## Candidate identity

Candidate app version is `0.1.0-alpha.3`, supplied as an explicit packaging
override; `build/package/VERSION` remains alpha.2. Current schema is 6 with
migrations 1–6. Published alpha.2 uses schema 2; its legacy folders keep DOCX
disabled until explicitly enabled. Other existing source policies are preserved.

The reviewed packaged-journey PR #31 head is
`150956a572b1070a893babe8a2522579dc0c853f`. It passed full
[CI](https://github.com/Lephiziel/findrail/actions/runs/38333847081),
[five native packaged targets](https://github.com/Lephiziel/findrail/actions/runs/38333847086),
and the real [packaged browser journey](https://github.com/Lephiziel/findrail/actions/runs/38333847047).
It was merged as `6bce0eb9bad5655047b134ded03041179b3349fd`.
These results establish the named PR head, not a rebuilt package at its merge
commit, this documentation commit, or a future release commit.

## Reviewed platform evidence

The table describes the complete PR #30 candidate at
`d572444e0b7216f3972591b08bde8e1e2eda6b2f`, verified in the
[full candidate gate](https://github.com/Lephiziel/findrail/actions/runs/38335973540).

| Target | Native archive/checksum/provenance and CLI checks | Actual packaged Chromium journey | Installed VSIX | Manual desktop checks |
|---|---|---|---|---|
| linux-amd64 | Passed in the complete gate | Passed: empty start, UI Add folder, selected text, PDF page 2, DOCX, Markdown bytes, reload/restart | Passed in VS Code 1.95, isolated installed VSIX + extracted candidate | One-person smoke not recorded |
| linux-arm64 | Passed in the complete gate on Linux ARM | Not run | Not run | Not run |
| darwin-amd64 | Passed in the complete gate on macOS Intel | Not run | Not run | Finder/Gatekeeper not run |
| darwin-arm64 | Passed in the complete gate on macOS ARM | Not run | Not run | Finder/Gatekeeper not run |
| windows-amd64 | Passed in the complete gate on Windows | Not run | Not run | One-person smoke not recorded |

The packaged harness checks exact executable version and clean BUILD-INFO
SHA/version/native target. It exercises the ten-case synthetic Literal evaluation
corpus, complete negative JSON report and nonzero status, missing-index
noncreation, legacy-index read-only rejection, and incomplete results above 100.
It also runs search, MCP, portable snapshot, ignore-policy, diagnostics and
upgrade checks. Synthetic evaluation verifies result sets, not real-user recall,
ranking quality, OCR or semantic search.

Cross-compilation is not acceptance evidence for native execution. Browser
interaction above uses the extracted Linux archive, not a fresh Go build or a
pre-indexed `serve` substitute. Other platforms' native CLI/API checks do not
certify browser, editor or desktop behavior. Development extension-host checks
are distinct from an installed VSIX against an extracted candidate.

## Release pipeline review

The reviewed PR #30 head `d572444e0b7216f3972591b08bde8e1e2eda6b2f` passed
the [complete candidate gate](https://github.com/Lephiziel/findrail/actions/runs/38335973540):
full reusable CI, all five native packages,
[installed VSIX host](https://github.com/Lephiziel/findrail/actions/runs/38335973540/job/115096836097),
[packaged browser](https://github.com/Lephiziel/findrail/actions/runs/38335973540/job/115096836098),
exact eight-file aggregation and reusable final verification. The same head also
passed [ordinary CI](https://github.com/Lephiziel/findrail/actions/runs/38335973527)
and [package rehearsal](https://github.com/Lephiziel/findrail/actions/runs/38335973519).
PR #30 was merged as `d4c1569a242249ae74392438499842b2e51eae7c`.

The gate's `release-assets-d572444e0b7216f3972591b08bde8e1e2eda6b2f` artifact
contains five native archives, `findrail-readonly-0.1.0.vsix`,
`release-manifest.json` and `SHA256SUMS.txt`. Manifest hashes/sizes, exact source
revision, clean BUILD-INFO, target/version and VSIX identity were checked before
and after artifact download. The VSIX version is independently `0.1.0`. Preview
publication/state jobs were skipped; this passing rehearsal created no release.
See [pipeline contract](release-pipeline.md). Its archives remain tied to this PR
head, not this later documentation commit or a future release SHA.

Earlier review runs exposed a fresh-extraction directory conflict
([run 38334077194](https://github.com/Lephiziel/findrail/actions/runs/38334077194))
and a macOS diagnostics smoke race
([run 38334368434](https://github.com/Lephiziel/findrail/actions/runs/38334368434)).
Both were fixed in the reviewed branch: the safe extractor creates its own
fresh destination; Configure diagnostics bind to the completed job while the
source endpoint may already expose a later successful watcher refresh. The
persisted DOCX policy and actual search exclusion remain asserted. The installed
VSIX runner was also moved under the installed extension directory so its UI
stubs share that extension's API; the first detached runner hung and its
[superseded run](https://github.com/Lephiziel/findrail/actions/runs/38334992543)
was canceled. Findrail still loads the installed bundle,
while only the bootstrap is a development extension. Host tests have a bounded
timeout, and superseded PR previews cancel without canceling main publication.
PR #31's first browser review run also exposed hidden-dialog status text
([run 38333229559](https://github.com/Lephiziel/findrail/actions/runs/38333229559));
its corrected head passed the browser run linked above. The earlier Windows
[run 38242262198](https://github.com/Lephiziel/findrail/actions/runs/38242262198)
failed with a connection reset in an HTTP smoke; the reviewed head's Windows
checks subsequently passed. These failed runs remain dated evidence, not current
passing results.

## Upgrade and remaining manual work

Published alpha.2 tag `v0.1.0-alpha.2` resolves to
`7573802a45962702a66eeecc8fb79a4ac2d680db`; it contains migrations 001–002.
The synthetic legacy fixture is generated from those historical SQL migrations,
not by opening a new database with the current writable store. The packaged
journey verifies schema 2 → 6, retained source/PDF-page evidence, legacy DOCX
disabled until configured, and backup/restore of the stopped whole data directory
including any WAL/SHM files. The separately restored copy is checked to remain
schema 2. It does not run an old binary against schema 6 or attempt a reverse
migration. Never point an older binary at the upgraded index.

Storage migration-failure tests, packaged upgrade/restore, automated Chromium,
installed editor, manual Finder/Gatekeeper and real-user retrieval are distinct
checks. A [10–15 minute human smoke](release-smoke-alpha3.md) on one accessible
computer remains unrecorded; it does not require a five-OS certification matrix.
Optional new demo media is not a release blocker. A final release commit must
rebuild and verify every asset at that exact SHA after an authorized VERSION
change; candidate archives cannot be relabeled as the final release.

## Historical schema-4 evidence

The earlier rehearsal recorded on 2026-10-12 for source
`6f32727fb8eed1d804e0ed48049ca8ef577376e1` tested schema 4 / migrations 1–4.
It is historical only and does not establish schema-6 readiness or the current
candidate. The initial preparation main was
`ed249148d8b01a17480b3acfeaf077bc7dc4395c`; independent initial PR heads were
#30 `38e9a044e8c186d8ced2659444cf746804e48c91` and
#31 `8d6f629ac3824a86d77cf9f61b681923c20321fc`.

Use the separate [promotion checklist](release-alpha3-promotion.md) only after
an authorized release and its real asset URLs have been verified.
