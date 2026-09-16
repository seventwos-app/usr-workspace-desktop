# Seventwos Workspace for Desktop

Seventwos Workspace for Desktop is the desktop client for the Seventwos workspace. It is built on top of a fork of [Element Web](https://github.com/element-hq/element-web) and is being evolved for people and agents to communicate and collaborate over [Matrix](https://matrix.org/).

The project retains Element's desktop approach: a TypeScript and React application packaged for the desktop with [Electron](https://www.electronjs.org/), communicating with Matrix through the [Matrix JS SDK](https://github.com/matrix-org/matrix-js-sdk). End-to-end encryption is handled by the Matrix Rust crypto stack compiled to WebAssembly, so the desktop client shares its cryptographic core with the iOS and Android clients while the application layer remains web technology.

## Relationship to the iOS and Android workspaces

[Seventwos Workspace for iOS](https://github.com/seventwos-app/usr-workspace-ios) and [Seventwos Workspace for Android](https://github.com/seventwos-app/usr-workspace-android) are forks of Element X, which are native clients built directly on the [Matrix Rust SDK](https://github.com/matrix-org/matrix-rust-sdk).

Element does not publish an Element X desktop client. The Element desktop application is maintained inside the Element Web monorepo and is built on the Matrix JS SDK, so this repository forks Element Web rather than Element X. The three workspaces therefore share product intent and a common Matrix protocol foundation, but not a single application codebase.

## Repository layout

This repository is a monorepo inherited from Element Web. Since Seventwos Workspace for Desktop is a
standalone client, `apps/web` (the browser application) has been removed. The layout is:

- `apps/desktop` — the Electron desktop application, previously maintained as `element-desktop`.
- `packages/` and `modules/` — shared libraries and optional modules used to build `apps/desktop`.

The desktop app packages a pre-built web UI bundle at build time rather than compiling one locally in
this repository — see `apps/desktop/scripts/fetch-package.ts`. The dependency is explicit rather than
independent: local builds require an exact upstream release tag, and release-readiness CI requires an
exact HTTPS bundle URL plus SHA-256 digest. The repository does not contain or restore `apps/web`.
Replacing the inherited web bundle with a Seventwos-authored bundle remains future work.

## Status

This repository is in transition from its Element Web foundation to a separately authored Seventwos application layer.

The current code includes inherited Element Web and Element Desktop code, branding, and configuration. This fork redistributes that code under the GNU Affero General Public License v3 and must not be represented as an independently authored Seventwos implementation. The transition will replace the inherited application layer with Seventwos code while retaining the desktop client architecture.

## Architecture

The intended desktop implementation includes:

- TypeScript and React.
- Electron packaging for macOS, Windows, and Linux.
- Matrix JS SDK integration.
- Client-side Matrix end-to-end encryption through the Rust crypto stack compiled to WebAssembly.
- Local encrypted search indexing through Seshat.
- Desktop notifications for encrypted messages.

Element Web is the upstream foundation and architectural reference for this workspace, not the target product identity.

## Repository scope

This is the product repository for Seventwos Workspace for Desktop. It is the source of truth for the desktop application code, Electron packaging and platform integrations, build and test configuration, and release preparation.

Changes in this repository should directly support the desktop client. Shared services and cross-platform product material are maintained separately; the origins and licensing of upstream-derived code are documented below.

## Provenance and licence

This repository began as a fork of Element Web and is now maintained as Seventwos Workspace for Desktop.

Copyright (c) 2014 - 2017 OpenMarket Ltd.

Copyright (c) 2017 Vector Creations Ltd.

Copyright (c) 2017 - 2025 New Vector Ltd.

These upstream copyright notices are retained in recognition of the work on which this fork is based.

We license the repository-owned code under the GNU Affero General Public License v3 only. See [LICENSE-AGPL-3.0](LICENSE-AGPL-3.0) for the applicable terms. Third-party dependencies remain under their respective licences.

Our modifications and newly authored repository code use AGPL-3.0-only. When we distribute a modified version or make one available for users to interact with over a network, we provide the corresponding source as required by the AGPL.
