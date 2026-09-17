---
type: Reference
status: draft
---

# Upstream Tracking

This fork tracks [element-hq/element-web](https://github.com/element-hq/element-web),
licensed AGPL-3.0. This document is the seventwos record of our sync
state with upstream; update it (and add a `log.md` entry) every time
`develop` is rebased/merged against upstream.

## Fork relationship

* **Upstream**: `element-hq/element-web`, default branch `develop`.
* **Our branch**: `develop` (this repo's default branch).
* **Sync model**: pull-based. We periodically merge or rebase upstream
  `develop` into ours; we do not push changes upstream.

## Last known sync point

* **Recorded**: 2026-09-17
* **Our `develop` HEAD**: `965736155137fff89e1ae087b77fb6a341add1ad`
* **Upstream `develop` HEAD at time of recording**: `90e3d43efd97f5855d283cd30114eed8d3423992`
* **Divergence**: upstream was **27 commits ahead** of our last sync point
  (per `gh api repos/element-hq/element-web/compare/<our-sha>...<upstream-sha>`).

## Upstream changes since fork

No upstream sync has been performed yet since this tracking document was
created; the 27-commit gap above is outstanding. Record each sync as a
dated entry below once performed.

### Sync log

* _(none yet — this document was seeded before the first tracked sync)_

## Process for the next sync

1. Compare current `develop` HEAD against upstream `develop` HEAD.
2. Merge or rebase upstream changes into `develop`.
3. Re-run `python3 scripts/okf/validate_okf_markdown.py --all` to confirm
   the `documentation/` bundle is unaffected.
4. Update this file's **Last known sync point** and append a **Sync log**
   entry summarizing what upstream changed (feature areas, breaking
   changes, version bumps) and any adaptation needed on our side.
5. Add a corresponding `log.md` entry.
