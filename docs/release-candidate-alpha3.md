# alpha.3 release-candidate rehearsal (not a release)

This document records preparation evidence only. It does not mean alpha.3 is
published, signed, or certified for every user/platform. Published downloads
remain alpha.2. No release was created by this documentation work.

## Candidate scope

Candidate version: `0.1.0-alpha.3` (explicit build override only). Current main
at the start of this documentation task was
`ed249148d8b01a17480b3acfeaf077bc7dc4395c`; the packaged-candidate PR #31 head
was `8d6f629ac3824a86d77cf9f61b681923c20321fc`, based on release-pipeline PR #30
head `38e9a044e8c186d8ced2659444cf746804e48c91`. Do not treat this report's
documentation commit as a rebuilt package revision. Current schema is 6
(migrations 1–6); published alpha.2 is legacy schema 2 and legacy DOCX is disabled
by default. The PR #31 runs validate its submitted candidate head, not an eventual
post-merge main/release SHA.

## Artifact and platform status

| Target | Cross-compilation | Native package build | Archive + checksum | Extracted native packaged journey | Actual interactive browser / installed editor |
|---|---|---|---|---|---|
| linux-amd64 | not used as acceptance evidence | passed on Linux runner | passed | passed in PR #31 packaged-native | Candidate browser smoke pending; editor install not run |
| linux-arm64 | not used as acceptance evidence | passed on Linux ARM runner | passed | passed in PR #31 packaged-native | Candidate browser smoke pending; editor install not run |
| darwin-amd64 | not used as acceptance evidence | passed on macOS Intel runner | passed | passed in PR #31 packaged-native | Finder/Gatekeeper and candidate browser smoke not run |
| darwin-arm64 | not used as acceptance evidence | passed on macOS ARM runner | passed | passed in PR #31 packaged-native | Finder/Gatekeeper and candidate browser smoke not run |
| windows-amd64 | not used as acceptance evidence | passed on Windows runner | passed | passed in PR #31 packaged-native | Candidate browser smoke pending; editor install not run |

PR #30 CI, race, UI and native packaged checks passed, including five native
package targets; PR #31's packaged-native matrix also passed for all five targets.
See [PR #30 checks](https://github.com/Lephiziel/findrail/actions/runs/38240473871),
[PR #30 packaged matrix](https://github.com/Lephiziel/findrail/actions/runs/38241009225),
[PR #31 latest checks](https://github.com/Lephiziel/findrail/actions/runs/38242300031),
and [PR #31 packaged matrix](https://github.com/Lephiziel/findrail/actions/runs/38242299947).
PR #31 also has a separate failed Windows check run
([run](https://github.com/Lephiziel/findrail/actions/runs/38242262198)); a later
Windows check run passed. Report both; do not erase the earlier failure.

Cross-compilation is not used as evidence for native execution; the named native
jobs build, package, extract and run on the target OS/architecture. The PR #27
[evidence browser run](https://github.com/Lephiziel/findrail/actions/runs/38144655363)
passed its feature browser journey, but does not establish the packaged alpha.3
empty-start/Add-folder/restart workflow. PR #31's manual candidate-browser
workflow is not shown as executed. PR #29's [editor checks](https://github.com/Lephiziel/findrail/actions/runs/38214019150)
passed the client matrix and Linux extension-host interaction; this is not an
installed VS Code editor/VSIX test. Manual macOS Finder/Gatekeeper behavior is
not evidenced. Pending/not-run checks remain pending.

## Upgrade / rollback contract and outstanding work

Published alpha.2 tag `v0.1.0-alpha.2` resolves to
`7573802a45962702a66eeecc8fb79a4ac2d680db`; it has only migrations 001–002 and
schema 2. PR #31's synthetic legacy fixture exercises the packaged migration to
schema 6 and confirms legacy DOCX remains disabled. Its upgrade journey backs up
and restores the stopped whole data directory separately, retaining WAL/SHM when
present; it does not run the old alpha.2 binary against schema 6. Never point an
old binary at schema 6. No reverse migration exists. Migration-failure rollback,
manual browser interaction, installed editor/VSIX, Gatekeeper/Finder behavior,
and real-user retrieval remain distinct checks and must not be inferred from the
native package matrix.

## Dated historical evidence (schema 4; not current readiness)

The earlier rehearsal recorded on 2026-10-12 for source
`6f32727fb8eed1d804e0ed48049ca8ef577376e1` tested schema 4 / migrations 1–4 and
the then-current package matrix. Those results are historical only: they do not
prove schema-6 migration, PR #22–28 behavior, PR #30–31 candidate checks, or
readiness of the current candidate. Keep them for provenance, not as current
release evidence.

For post-publication source-only → released wording, use the separate
[promotion checklist](release-alpha3-promotion.md). It is intentionally not
applied by this preparation PR.
