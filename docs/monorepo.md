## Monorepo

Some words about the structure of monorepo we are using here.

### Structure

The monorepo is inherited from Element Web, which originally hosted both a web app and a desktop app side by side.
This repository has been trimmed to `apps/desktop` only, since the Seventwos Workspace for Desktop client is a
standalone desktop application and does not ship a browser-based build.

- `apps` - this directory holds the app we build, `seventwos-workspace-desktop` (previously maintained as `element-desktop`)
    - Things in here are not published to npm
    - Things in here have non-standard, repository-specific packaging/build steps (see [Packaging](./packaging.md))
    - Things in here are in lock-step versions with each other
    - Things in here support pre-releases & hotfixes
- `packages` - this directory holds internal libraries we maintain in order to build the `apps`
    - Things in here are private and are not published to npm (see [`../packages/RELEASING.md`](../packages/RELEASING.md))
    - Things in here respect SemVer for internal API compatibility purposes
    - Things in here are independently versioned
- `modules` - this directory holds some Seventwos Workspace for Desktop modules (inherited from Element Web/Desktop) we maintain in order to add environment-specific functionalities atop the bundled web app
    - Things in here are not published to npm

### Branches

- `develop` - this is the default branch and should always be buildable, this is what developers use as a base branch for their pull requests
- `staging` - this branch is used to build the latest/next release.
    - During a normal release cycle, `develop` is merged into `staging` to "cut" a release candidate
        - Additional changes such as version bumps & changelogs are committed on top
    - During a hotfix/security release, changes are directly cherry-picked to `staging` to "cut" a release based on the last release rather than `develop`
    - When a release is finished, i.e. we've shipped the final release for a given version, we merge `staging->develop` to maintain continuity
- `backport/*` - these branches are used for cherry-picking entire pull requests from `develop` to `staging`, either to patch a release candidate, or to perform a hotfix release
- `<username>/*` - these feature branches are used for development, and may branch off `develop` or another feature branch

### Tags

- `v*` - these tags are used by the releases shown in the Github Releases UI, as in, the overall app release group

Ultimately, the treatment of the 3 types of submodules we host in this repository is quite asymmetrical but this is by design,
to simplify processes around projects which do not need the complexities of the full upstream Element Web & Element Desktop monorepo.
