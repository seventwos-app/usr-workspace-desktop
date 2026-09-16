![Build](https://github.com/seventwos-app/usr-workspace-desktop/actions/workflows/build_desktop_and_deploy.yaml/badge.svg)

# Seventwos Workspace for Desktop

This package is the Electron wrapper app for the Seventwos Workspace desktop client. It is inherited from
Element Desktop and, at this stage, still packages the upstream Element Web webapp bundle. See the
[repository README](../../README.md) for the Seventwos Workspace rebrand status and provenance.

# First Steps

Before you do anything else, fetch the dependencies:

```
pnpm install
```

# Providing the upstream web bundle

This repository deliberately does not contain `apps/web`. The Electron wrapper is not independent of a web UI bundle:
every build must opt in to an exact upstream release or provide a separately verified bundle.

```
# Fetch and verify an exact signed upstream release, then apply the Seventwos release config.
pnpm run fetch --cfgdir seventwos.org/release v1.12.27
```

Importing the upstream release key is a separate, explicit operation:

```
pnpm run fetch --importkey
```

Custom HTTPS bundle URLs are supported for local work, but the fetch script cannot authenticate them. Verify the
bundle independently before use. Release CI instead requires both an exact HTTPS URL and SHA-256 digest.

Moving `develop` bundles and implicit version selection are rejected. Do not add or depend on `apps/web`.

# Building

## Native Build

TODO: List native pre-requisites

Optionally, [build the native modules](https://github.com/element-hq/element-web/blob/develop/docs/native-node-modules.md),
which include support for searching in encrypted rooms and secure storage. Skipping this step is fine, you just won't have those features.

Then, run

```
pnpm run build
```

This will do a couple of things:

- Run the `setversion` script to set the local package version to match whatever
  version of the upstream bundle you installed above.
- Run electron-builder to build a package. The package built will match the operating system
  you're running the build process on.

## Docker

Alternatively, you can also build using docker, which will always produce the linux package:

```
# Run this once to make the docker image
pnpm run docker:setup

pnpm run docker:install
# if you want to build the native modules (this will take a while)
pnpm run docker:build:native
pnpm run docker:build
```

After running, the packages should be in `dist/`.

# Starting

If you'd just like to run the electron app locally for development:

```
pnpm start
```

# Config

If you'd like the packaged Seventwos Workspace app to have a configuration file, you can create a
config directory and place `config.json` in there, then specify this directory
with the `--cfgdir` option to `pnpm run fetch`, eg:

```
mkdir myconfig
cp /path/to/my/config.json myconfig/
pnpm run fetch --cfgdir myconfig
```

The checked-in Seventwos variants intentionally provide no homeserver, identity server, telemetry, rageshake, maps,
call, or Scalar endpoints. Add only operated Seventwos services in an explicit config. The planned update endpoint is
`https://workspace.seventwos.org/desktop/update/`, but automatic updates remain disabled unless
`enable_auto_update` is deliberately set to `true` after that service is operational.

# Release readiness workflow

`Build Seventwos Desktop Artifacts` is manual and artifact-only. It requires an exact upstream web bundle HTTPS URL
and SHA-256 digest, builds unsigned packages, and never publishes them. It has no release-event trigger, deployment
permissions, Element credentials, Element package-service integration, or inherited secret access.

`Desktop Validation` is the required release-branch, PR, and merge-queue safety gate. It runs desktop source and script
type checks, validates the remaining workflow definitions and checked-in Seventwos JSON configs, and runs the desktop
unit suite. It does not fetch a web bundle, package applications, sign artifacts, publish releases, or contact
deployment services.

No signing secrets are accepted because Seventwos does not yet have Apple or Windows signing accounts. When those
accounts exist, add signing in a reviewed change using protected environments and Seventwos-prefixed secrets only.
Do not add credentials to this repository.

# Profiles

To run multiple instances of the desktop app for different accounts, you can
launch the executable with the `--profile` argument followed by a unique
identifier, e.g `seventwos-workspace-desktop --profile Work` for it to run a separate profile and
not interfere with the default one.

Alternatively, a custom location for the profile data can be specified using the
`--profile-dir` flag followed by the desired path.

# User-specified config.json

- `%APPDATA%\$NAME\config.json` on Windows
- `$XDG_CONFIG_HOME/$NAME/config.json` or `~/.config/$NAME/config.json` on Linux
- `~/Library/Application Support/$NAME/config.json` on macOS

In the paths above, `$NAME` is determined by the installed app. Legacy upstream installations can use `Element-$PROFILE`, `Riot`, or
`Riot-$PROFILE`.

You may also specify a different path entirely for the `config.json` file by
providing the `--config $YOUR_CONFIG_JSON_FILE` to the process, or via the
`ELEMENT_DESKTOP_CONFIG_JSON` environment variable.

# Translations

See this repository's translation workflow and developer documentation when they are available.

# Report bugs & give feedback

If you run into any bugs or have feedback you'd like to share, please let us know on GitHub.

To help avoid duplicate issues, please [view existing issues](https://github.com/seventwos-app/usr-workspace-desktop/issues?q=is%3Aopen+is%3Aissue+sort%3Areactions-%2B1-desc) first or [create a new issue](https://github.com/seventwos-app/usr-workspace-desktop/issues/new/choose) if you cannot find it.

## Copyright & License

Copyright (c) 2016-2017 OpenMarket Ltd

Copyright (c) 2017 Vector Creations Ltd

Copyright (c) 2017-2025 New Vector Ltd

Seventwos distributes this fork under the GNU Affero General Public License v3 only.
See [LICENSE-AGPL-3.0](../../LICENSE-AGPL-3.0) for the applicable terms.

Unless required by applicable law or agreed to in writing, software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
