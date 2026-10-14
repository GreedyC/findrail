# Findrail README assets

## Branding

`findrail-mark.svg` and the light/dark wordmarks are original vector assets.
They extend the rounded, two-line mark already used by the application header,
using Findrail's existing green and paper palette. They contain no third-party
logos, embedded fonts, scripts or external resources. The wordmarks use a system
sans-serif font and the README selects a variant with a `picture` element.
They are distributed under the repository's Apache-2.0 license.

## Published alpha.3 screenshots

`overview-alpha3.png`, `search-alpha3.png` and `preview-alpha3.png` are direct browser captures of the
actual published Linux amd64 `0.1.0-alpha.3` binary running the built-in
three-document demo on 2026-10-14. The archive checksum was verified against
the release before extraction:

```text
b8e9d606e6487745a9f96d4453114e7ef6ec74fcde242a7da20a059462b3b9e9
```

The source release is
[`v0.1.0-alpha.3`](https://github.com/Lephiziel/findrail/releases/tag/v0.1.0-alpha.3),
revision `d5dc1bec50efcb3c26d09e9b24b14cf3c0b2f4cb`, schema 6.
The screenshots use fictional Markdown, Go and PDF documents. Temporary paths
belong to the isolated demo. No personal documents or normal index were used.

To reproduce the state, run `./findrail demo`, search `idempotency`, then
open **Preview** on `webhook-runbook.pdf`. Check **Page 2 / 2**. The PNGs are
browser screenshots, with no composited UI or added results. They demonstrate
search and PDF evidence, not performance or alpha.4 desktop/collection behavior.

The capture ran in [README media workflow 38511760352](https://github.com/Lephiziel/findrail/actions/runs/38511760352).
Reproduce it with `python3 scripts/readme_media.py /path/to/published/findrail
--output /path/to/captures`, using Selenium 4.35.0 and a matching Chrome/driver,
or run **README media (published alpha.3)** in GitHub Actions. The workflow has
read-only repository permissions and uploads screenshots as an artifact;
it does not commit files, change a release or publish an index.

## Historical media

`demo.mp4`, `demo.gif` and `demo.png` retain the older alpha.2 recording.
They should not be labeled as alpha.3 or alpha.4 demonstrations. See
[demo instructions](../demo.md).
