# Release process for packages in this monorepo

The packages and modules in this repository (`packages/*` and `modules/*`) are private,
repository-internal libraries. They are consumed only via the pnpm workspace protocol
(`workspace:*`) by `apps/desktop` and by each other, and are not published to any npm
registry. Version numbers in their `package.json` files are informational, tracking
internal API compatibility between packages, and do not correspond to published releases.

To bump an internal package's version (for example after a breaking API change):

1. Update `package.json` with the new version. One way to do this is
   `pnpm version --no-git-tag-version <major|minor|patch>`. Or just do it manually.

2. Commit to a release prep branch, and open a PR.

No further publishing step is required or available for this repository. If a
package here should ever be published independently, that will require setting up
a dedicated publish workflow and reviewing registry/ownership metadata first.
