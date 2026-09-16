# Seventwos Workspace for Desktop

Seventwos Workspace for Desktop is the desktop client for the Seventwos workspace. It is built on top of a fork of [Element Web](https://github.com/element-hq/element-web) and is being evolved for people and agents to communicate and collaborate over [Matrix](https://matrix.org/).

The project retains Element's desktop approach: a TypeScript and React application packaged for the desktop with [Electron](https://www.electronjs.org/), communicating with Matrix through the [Matrix JS SDK](https://github.com/matrix-org/matrix-js-sdk). End-to-end encryption is handled by the Matrix Rust crypto stack compiled to WebAssembly, so the desktop client shares its cryptographic core with the iOS and Android clients while the application layer remains web technology.

## Relationship to the iOS and Android workspaces

[Seventwos Workspace for iOS](https://github.com/seventwos-app/usr-workspace-ios) and [Seventwos Workspace for Android](https://github.com/seventwos-app/usr-workspace-android) are forks of Element X, which are native clients built directly on the [Matrix Rust SDK](https://github.com/matrix-org/matrix-rust-sdk).

Element does not publish an Element X desktop client. The Element desktop application is maintained inside the Element Web monorepo and is built on the Matrix JS SDK, so this repository forks Element Web rather than Element X. The three workspaces therefore share product intent and a common Matrix protocol foundation, but not a single application codebase.

## Repository layout

This repository is a monorepo inherited from Element Web:

- `apps/web` — the browser application.
- `apps/desktop` — the Electron desktop application, previously maintained as `element-desktop`.
- `packages/` and `modules/` — shared libraries and optional modules.

## Status

This repository is in transition from its Element Web foundation to a separately authored Seventwos application layer.

The current code includes inherited Element Web and Element Desktop code, branding, and configuration. That inherited code remains subject to Element's licence terms and must not be represented as an independent Seventwos implementation. The transition will replace the inherited application layer with Seventwos code while retaining the desktop client architecture.

## Architecture

The intended desktop implementation includes:

- TypeScript and React.
- Electron packaging for macOS, Windows, and Linux.
- Matrix JS SDK integration.
- Client-side Matrix end-to-end encryption through the Rust crypto stack compiled to WebAssembly.
- Local encrypted search indexing through Seshat.
- Desktop notifications for encrypted messages.

Element Web is the upstream foundation and architectural reference for this workspace, not the target product identity.

## Repository role

The Seventwos workspace captures product intent and human direction. This repository captures the desktop implementation, review history, and upstream attribution.

Changes should make the transition from inherited application code explicit and auditable. New product code should follow the repository's architecture and contribution rules.

## Provenance and licence

The current codebase is derived from Element Web, which is multi-licensed under the GNU Affero General Public License v3, the GNU General Public License v3, or a paid Element Commercial License.

Copyright (c) 2014 - 2017 OpenMarket Ltd.

Copyright (c) 2017 Vector Creations Ltd.

Copyright (c) 2017 - 2025 New Vector Ltd.

See [LICENSE-AGPL-3.0](LICENSE-AGPL-3.0), [LICENSE-GPL-3.0](LICENSE-GPL-3.0), and [LICENSE-COMMERCIAL](LICENSE-COMMERCIAL) for the terms that apply to inherited code.

The licensing of future separately authored Seventwos components must be documented when those components are introduced. Their inclusion does not alter the licence obligations of inherited Element Web code.
