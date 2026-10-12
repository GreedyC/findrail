# alpha.3 post-release promotion checklist (for task 06)

This is a source-only → released promotion plan. Do not apply it before an
authorized release exists. It has no future asset URLs: populate them only by
copying and verifying URLs from the real published release page.

## Verify first

- [ ] Confirm the actual `v0.1.0-alpha.3` release exists and is the expected
  prerelease; verify tag, full source SHA, release notes and publication time.
- [ ] Download each listed Linux amd64/arm64, macOS amd64/arm64, and Windows
  amd64 archive from that release. Verify exact basenames against that same
  release's `SHA256SUMS.txt`; inspect embedded INSTALL, BUILD-INFO and notices.
- [ ] Record native packaged execution separately from cross-compilation. Check
  actual browser smoke, installed editor/VSIX, and manual macOS
  Finder/Gatekeeper independently; leave any unrun result marked unrun.
- [ ] Verify the VSIX API v1 requirements and the real absence/presence of
  Marketplace and Open VSX listings. Never infer publication from a local VSIX.

## Only after verification: promotion patch

1. In `README.md`, change the current-release label and clearly name alpha.3 as
   published. Add version-specific archive and checksum links only by copying
   verified URLs from the release; retain alpha.2 as the previous available
   version rather than deleting its links.
2. In `docs/launch/press-kit.md`, change the release status and matrix column
   from “current source build / candidate” to “published alpha.3” only for
   verified features. Keep a separate VSIX row; mark Marketplace/Open VSX
   unpublished unless those exact listings are verified.
3. In `docs/launch/README.md` and `docs/ru/overview.md` / `docs/ru/launch.md`,
   replace source-only wording with released wording only for the features in
   the verified package. Keep limitations, schema-6 rollback guidance and
   platform/manual-test caveats.
4. Promote `docs/release-notes-alpha3.md` to the actual release notes after
   comparing it with shipped contents and correcting any differences. Keep
   candidate rehearsal evidence dated and distinct from release certification.
5. Check every changed link and asset URL against the public release. Do not
   create a link for a missing architecture, checksum, Marketplace, or Open VSX
   listing. Update the checklist with the verified SHA, URLs, and evidence.

This file is guidance for the separately authorized release task, not permission
to change VERSION, create a tag, publish, or send external messages now.
