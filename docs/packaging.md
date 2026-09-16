## Packaging builds

Seventwos Workspace for Desktop artifacts are built by the
[`build_desktop_and_deploy.yaml`](https://github.com/seventwos-app/usr-workspace-desktop/blob/develop/.github/workflows/build_desktop_and_deploy.yaml)
GitHub Actions workflow.

This workflow is currently triggered manually (`workflow_dispatch`) rather than on a schedule. It takes
the pinned upstream web bundle URL and SHA-256 digest as inputs (see the repository README for details
on how the desktop app packages a pre-built web UI bundle rather than compiling one in this repository),
and builds unsigned macOS, Windows, and Linux artifacts as selected via the workflow's inputs.

### Triggering a manual build

Go to the
[`build_desktop_and_deploy.yaml`](https://github.com/seventwos-app/usr-workspace-desktop/actions/workflows/build_desktop_and_deploy.yaml)
workflow page in this repository:

1. Click `Run workflow`
1. Provide the pinned upstream web bundle URL and SHA-256 digest, and the desired variant/platform inputs
1. Click the green `Run workflow`

### Signing and distribution

This repository's build workflow currently produces unsigned artifacts only; it does not sign, notarise,
or publish artifacts to any package repository or distribution endpoint. Setting up code signing (macOS
notarisation, Windows signing, Linux repository distribution) and an automated release/deployment
pipeline remains future work for this fork.
