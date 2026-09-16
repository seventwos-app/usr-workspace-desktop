/*
Copyright 2026 Element Creations Ltd.

SPDX-License-Identifier: AGPL-3.0-only
Please see LICENSE in the repository root for full details.
*/

import { type KnipConfig } from "knip";

// Specify this as knip loads config files which may conditionally load plugins
process.env.GITHUB_ACTIONS = "1";

export default {
    workspaces: {
        "packages/shared-components": {
            entry: ["src/index.ts!", "scripts/**"],
            project: [
                "**/*.{js,cjs,mjs,jsx,ts,cts,mts,tsx,mdx,pcss}!",
                "!scripts/**!",
                "!src/test/**!",
                "!src/**/test-*!",
                "!src/**/*-{mock,mocks,snapshot,actions}.*!",
            ],
        },
        "packages/playwright-common": {
            entry: ["src/fixtures/index.ts!", "src/testcontainers/index.ts!"],
            project: [
                "**/*.{js,cjs,mjs,jsx,ts,cts,mts,tsx,pcss}!",
                "!src/flaky-reporter.ts!",
                "!src/stale-screenshot-reporter.ts!",
            ],
            ignoreDependencies: [
                // Used in playwright-screenshots.sh
                "wait-on",
            ],
            ignoreBinaries: ["awk"],
        },
        "packages/module-api": {},
        "apps/desktop": {
            entry: ["src/preload.cts!", "electron-builder.ts!", "scripts/**", "hak/**"],
            project: ["**/*.{js,ts,pcss}"],
            ignoreDependencies: [
                // Brought in via hak scripts
                "matrix-seshat",
            ],
            ignoreBinaries: [
                // Used to build seshat (optional)
                "rustc",
                // Used by the fetch-package script (optional)
                "gpg",
                // Used for the macOS universal builds
                "lipo",
            ],
        },
        "modules": {
            project: ["**/*.{js,cjs,mjs,jsx,ts,cts,mts,tsx,pcss}!", "!playwright/**!"],
            ignoreDependencies: [
                // Used by Playwright to serve the built web app.
                "serve",
            ],
        },
        "modules/*": {
            entry: ["src/index.ts{x,}!"],
            project: [
                "**/*.{js,cjs,mjs,jsx,ts,cts,mts,tsx,pcss}!",
                "!src/tests/**!",
                "!e2e/**!",
                "!src/setupTests.ts!",
            ],
        },
        ".": {
            entry: ["scripts/**", "docs/**"],
        },
    },
    ignoreDependencies: [
        // Used by multiple packages, raises a false positive for some reason
        "events",
        // Used as a workaround for api-extractor not supporting typescript 7.0
        "@typescript/old",
    ],
    ignoreExportsUsedInFile: true,
    ignoreBinaries: [
        // Optional for coverage:diff development script
        "diff-cover",
    ],
    compilers: {
        pcss: (text: string) =>
            [...text.matchAll(/@import\s+(?:url\()?["']([^"']+)["']\)?[^;]*;/g)]
                .map(([, specifier]) => `import "${specifier}";`)
                .join("\n"),
    },
    nx: {
        config: ["{nx,package,project}.json", "{apps,packages,modules}/**/{package,project}.json"],
    },
    playwright: {
        config: ["playwright.config.ts", "playwright-merge.config.ts"],
    },
    tags: ["-knipignore"],
    treatConfigHintsAsErrors: true,
    treatTagHintsAsErrors: true,
} satisfies KnipConfig;
