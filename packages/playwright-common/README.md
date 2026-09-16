# @element-hq/element-web-playwright-common

Set of Playwright & testcontainers utilities to make it easier to write tests for Element Web, Element Web Modules & Element Desktop.

The main export includes a number of fixtures and custom assertions as documented in JSDoc.

The `lib/testcontainers` export contains the following modules:

- `SynapseContainer` - A testcontainer for running a Synapse server
- `MatrixAuthenticationServiceContainer` - A testcontainer for running a Matrix Authentication Service
- `MailpitContainer` - A testcontainer for running a Mailpit SMTP server

There are a number of utils available in the `lib/utils` export.

## Releases

The API is versioned using semver, with the major version incremented for breaking changes.

To carry out a release, see the documentation at [`../RELEASING.md`](../RELEASING.md).

## Copyright & License

Copyright (c) 2026 Element Creations Ltd

Seventwos distributes this component under the GNU Affero General Public License v3 only.
See [LICENSE-AGPL-3.0](../../LICENSE-AGPL-3.0) for the applicable terms.
