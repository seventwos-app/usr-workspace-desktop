# @element-hq/element-web-shared-utils

Internal, standalone utilities shared across Seventwos Workspace for Desktop packages. This package is
inherited from Element Web and is not published or maintained as a standalone public library by this
fork.

The package provides string-based HTML sanitization and URL validation for
untrusted Matrix-compatible formatted content.

## Usage

```ts
import { isUrlPermitted, sanitizeHtml } from "@element-hq/element-web-shared-utils";

const safeHtml = sanitizeHtml(untrustedHtml);
const canOpen = isUrlPermitted(untrustedUrl);
```

The package does not import React, access browser globals, or depend on
Element Web application code.

## Rendering transforms

The default sanitizer applies the shared Element Web rendering and safety
policy, including safe link handling, MXC-only images, and removal of inline
styles. The `transformTags` option is a trusted application extension point:
providing a transform for a tag replaces that tag's shared rendering transform.
Applications should only use this for a deliberately narrower or explicitly
trusted rendering context. Anchor URL validation and the sanitizer's attribute
and URL checks remain active.

## Copyright & License

Copyright (c) 2026 Element Creations Ltd.

This software is licensed under the terms described in the repository license
files.

## Versioning

This package is private and internal to this monorepo (see [`../RELEASING.md`](../RELEASING.md)); it is not published to any registry.
