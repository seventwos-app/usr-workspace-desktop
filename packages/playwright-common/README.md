# @element-hq/element-web-playwright-common

Internal set of Playwright & testcontainers utilities used to write tests for Seventwos Workspace for Desktop and its modules. This package is inherited from Element Web and is maintained here for use within this monorepo only.

The main export includes a number of fixtures and custom assertions as documented in JSDoc.

The `lib/testcontainers` export contains the following modules:

- `SynapseContainer` - A testcontainer for running a Synapse server
- `MatrixAuthenticationServiceContainer` - A testcontainer for running a Matrix Authentication Service
- `MailpitContainer` - A testcontainer for running a Mailpit SMTP server

There are a number of utils available in the `lib/utils` export.

## Releases

The API is versioned using semver, with the major version incremented for breaking changes.

This package is private and internal to this monorepo (see [`../RELEASING.md`](../RELEASING.md)); it is not published to any registry.

## Copyright & License

Copyright (c) 2026 Element Creations Ltd

Seventwos distributes this component under the GNU Affero General Public License v3 only.
See [LICENSE-AGPL-3.0](../../LICENSE-AGPL-3.0) for the applicable terms.
