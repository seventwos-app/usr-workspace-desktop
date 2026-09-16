# AGENTS.md

Instructions for AI coding agents working in this repository. Humans should read
[CONTRIBUTING.md](./CONTRIBUTING.md) and [code_style.md](./code_style.md) instead — this file summarises those and
adds the things that are easy to get wrong here.

## Repository layout

A pnpm + nx monorepo forked from Element Web. Workspaces are `apps/*`, `packages/*`, and `modules/*`.

This fork carries only the desktop application; the upstream `apps/web` package has been removed here (see
[README.md](./README.md) for why). Do not reintroduce `apps/web` paths in scripts, docs, or config.

| Path                                                                                                  | Contents                                                                                 |
| ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `apps/desktop`                                                                                        | The Electron desktop app (Seventwos Workspace for Desktop). Source in `src/`, tests in `playwright/` and `vitest.config.ts`. |
| `packages/shared-components`                                                                          | Published UI component library, `@element-hq/web-shared-components`.                      |
| `packages/module-api`, `packages/shared-utils`, `packages/shared-types`, `packages/playwright-common` | Published support packages.                                                                |
| `modules/*`                                                                                           | Optional runtime modules (banner, widget toggles, …).                                     |
| `docs/`                                                                                               | VitePress docs site.                                                                       |

`apps/desktop` does not build a webapp from source. It fetches a prebuilt Element Web bundle via
`apps/desktop/scripts/fetch-package.ts` and packs it as `webapp.asar`. See
[apps/desktop/README.md](./apps/desktop/README.md) for the fetch/build flow.

## Commands

Run from the repo root unless stated otherwise.

| Task                                                   | Command                                           |
| ------------------------------------------------------ | ------------------------------------------------- |
| Full lint (types, format, js, styles, workflows, knip) | `pnpm lint`                                       |
| Format                                                 | `pnpm lint:fmt:fix`                               |
| Lint JS/TS                                             | `pnpm lint:js:fix`                                |
| Typecheck                                              | `pnpm -r --workspace-concurrency=1 lint:types`    |
| All unit tests                                         | `pnpm test:unit`                                  |
| Regenerate i18n strings                                | `pnpm i18n`                                       |
| Start the app                                          | `cd apps/desktop && pnpm start`                   |
| Fetch webapp bundle                                    | `cd apps/desktop && pnpm fetch`                   |
| Storybook                                              | `cd packages/shared-components && pnpm storybook` |

Formatting is **oxfmt** and linting is **oxlint**. This repo does not use prettier or eslint — running prettier here
reformats files against the project style and reports failures that do not exist.

Run `pnpm i18n` after adding or changing any translated string.

## Running unit tests

`apps/desktop` uses vitest. Run it from within the package:

```sh
cd apps/desktop && pnpm test:unit
```

For `packages/shared-components`, run `cd packages/shared-components && pnpm test:unit -- <path>`.

- Vitest runs with `globals: false`, so import `describe`, `it`, `expect` and friends explicitly.
- "No test files found" means you picked the wrong path. It is not a pass.
- Prefer extending an existing test over adding a new file when covering a close variant of existing behaviour.

## Running e2e tests

Specs live in `apps/desktop/playwright`. See [docs/playwright.md](./docs/playwright.md) for the general Playwright
setup this repo inherits.

```sh
cd apps/desktop && pnpm test:playwright -- <spec>.spec.ts --project=Chrome
```

- On macOS, add `--ignore-snapshots`. Screenshot baselines are only committed for Linux, so comparisons fail locally.
- Never run the screenshots-update script locally to "fix" a screenshot diff — it writes host-rendered baselines.
  Screenshots are updated in the Docker environment, which CI matches.
- Locate elements by role, label and accessible name, not CSS classes.
- Tag any test using `toMatchScreenshot` with `@screenshot`.

### Reviewing updated screenshots

Updated baselines are part of the diff and must be reviewed, not accepted blindly. Before committing any changed
`.png` under `apps/desktop/playwright` or `packages/shared-components/__vis__/`:

- Look at the image. Confirm every visible difference is one your change was meant to produce.
- Treat anything else as a regression until proven otherwise: shifted or clipped layout, changed spacing or font,
  missing or duplicated elements, a wrong theme, an untranslated or placeholder string, a loading or error state
  captured instead of the real content.
- Unrelated files changing baselines is a signal in itself — if a screenshot moved for a component you did not
  touch, find out why rather than committing it.
- Never regenerate baselines to make a failing test pass. A diff you cannot explain is a bug in the change.

## Writing UI code: MVVM

New shared UI follows MVVM. Full details in [docs/MVVM.md](./docs/MVVM.md); the shape for a feature `Foo`:

**View** — `packages/shared-components/src/<domain>/FooView/` containing `FooView.tsx`, `FooView.module.css`,
`FooView.test.tsx`, `FooView.stories.tsx` and `index.ts`. The view declares the contract:

```tsx
export interface FooViewSnapshot { title: string }
interface FooViewActions { setTitle: (title: string) => void }
export type FooViewModel = ViewModel<FooViewSnapshot, FooViewActions>;

export function FooView({ vm }: { vm: FooViewModel }): JSX.Element {
    const { title } = useViewModel(vm);
    ...
}
```

Views are dumb: they read the snapshot and call actions, nothing else. Develop them in Storybook.

Rules that are easy to miss:

- Define actions as arrow-function class properties (`public doThing = (): void => {}`) so `this` survives being
  passed as a callback.
- Use `this.snapshot.merge({ field })` for partial updates. `merge` already skips emitting when nothing changed, so
  do not add equality guards around it, and do not recompute the whole snapshot for one field.
- Track listeners and sub-view-models with `this.disposables.trackListener(...)` / `this.disposables.track(...)`.
- A non-MVVM function component owning a view model should create it with `useCreateAutoDisposedViewModel`; a class
  component creates it in `componentDidMount` and disposes it in `componentWillUnmount`.

## Code style

Read [code_style.md](./code_style.md). The points most often missed:

- **Every new file needs a copyright header**, enforced by oxlint (`element-call/copyright-header`). Lint fails
  without it. Substitute the actual current year — check it rather than copying a year from another file — and leave
  headers on existing files alone:

    ```
    /*
    Copyright <current year> <copyright holder>

    SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial
    Please see LICENSE in the repository root for full details.
    */
    ```

    The holder is `Element Creations Ltd.` **only for contributions made as part of the inherited Element code**. An
    external or Seventwos contributor puts their own name or their company's there instead. Note that `oxlint --fix`
    inserts the Element line unconditionally, so contributors should write the header by hand and check what the
    autofix added.

- TypeScript only, named exports only — avoid `export default`.
- 4-space indent, 120-column limit, double quotes, semicolons.
- Declare member visibility (`public`/`private`/`protected`) on class members.
- Avoid `any`; if unavoidable, comment why.
- Roughly one interface, class or enum per file, named after the file.
- Never mix cosmetic and functional changes.
- **Styles:** `apps/desktop` uses PostCSS (`res/css/**/_Component.pcss`, `mx_`-prefixed classes).
  `packages/shared-components` uses CSS modules (`Component.module.css`, semantic camelCase class names, no `mx_`
  prefix) imported as `styles`. Use Compound design tokens (`var(--cpd-color-…)`, `var(--cpd-space-…)`) for all values.
- Prefer Compound typography components over raw text elements, and `Flex`/`Box` from shared-components over raw
  flexbox markup.

## Comments

Keep comments short and relevant.

- Add TSDoc to exported types, functions, classes and components. Document a component's props.
- Inside a function, explain _why_, not line by line. Add a short overview before a non-obvious block.
- Use plain language matching the identifiers around the comment — no metaphors or CS jargon.
- When changing code, update the comments around it so they stay accurate.
- Any intentionally suppressed lint or type rule needs a nearby comment explaining why.

## Tests are required

- Every change needs unit tests, including features behind labs flags.
- New user-facing features need a "happy path" Playwright e2e test before leaving labs.
- Aim for ≥80% coverage on the diff; CI checks this. There is no `coverage` script at the root — generate the
  reports in the workspaces you touched, then compare from the root:

    ```sh
    pnpm test:unit --coverage                              # vitest, writes coverage/lcov.info
    cd apps/desktop && pnpm coverage                       # writes apps/desktop/coverage/lcov.info
    cd packages/shared-components && pnpm coverage
    pnpm coverage:diff                                     # from the root, needs diff_cover installed
    ```

## Commits

- Split the work into logically separate commits: one concern per commit. Keep refactors, formatting and behaviour
  changes in separate commits.
- Short imperative subject line, no conventional-commit prefix (`feat:`, `fix:`, …).
- Add a body only when it says something the diff does not; keep it to a line or two.

## Pull requests

- The PR title becomes the changelog entry. Write it from the user's point of view and descriptively —
  "Fix bug where cows had five legs", not "Update file.ts". No issue number in the title.
- Keep the description short and relevant: what changed and why, `Fixes #NNN` for the issue, and a brief testing
  strategy. Put explanations of _how_ the code works in code comments, not the description.
- **State in the description that the PR was generated with AI.**
- Add screenshots for visual changes.
- Apply the right type label: `T-Enhancement` (minor bump), `T-Defect` (bug fix), or `T-Task` for changes with no
  user-facing effect — a `T-Task` gets no changelog entry. Add `X-Breaking-Change` for a breaking change.
- Never force-push to a PR branch; the project squash-merges.
