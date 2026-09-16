# Feature flags

Feature flags (a.k.a. labs flags) are controlled entirely at runtime through the `features` key in
`config.json` — see [Labs flags](./config.md#labs-flags) in the config documentation. This
repository does not contain the source of the bundled web app (`apps/web`), so new feature flags
cannot be defined here; they are defined in the upstream
[element-hq/element-web](https://github.com/element-hq/element-web) source that produces the web
bundle this app fetches and packages (see the [repository README](../README.md) for how the bundle
is fetched and verified).

What this repository _does_ control is which flags are forced on or off for the Seventwos Workspace
builds, via the checked-in configs:

- [`apps/desktop/seventwos.org/release/config.json`](../apps/desktop/seventwos.org/release/config.json)
- [`apps/desktop/seventwos.org/preview/config.json`](../apps/desktop/seventwos.org/preview/config.json)

For example, the release config currently forces the following off:

```json
{
    "features": {
        "feature_video_rooms": false,
        "feature_element_call_video_rooms": false
    }
}
```

## Enabling or disabling a flag for this product

1. Confirm the flag exists in whichever pinned upstream web bundle version this fork fetches (see
   [labs.md](./labs.md) for the non-exhaustive list of upstream flags and their status).
2. Add or update the entry under `"features"` in the relevant `config.json` variant(s) above.
3. If you'd like end users to be able to toggle a flag themselves, also set `"show_labs_settings": true`
   in that config so the Labs tab in user settings is shown.

## Adding a brand-new flag

Defining a new feature flag (i.e. a new `feature_*` setting recognised by the app) requires a code
change in the upstream `element-hq/element-web` project, not this repository. See that project's own
contribution docs for its process. Once a corresponding upstream release is fetched and pinned by this
repository, the flag can be forced on/off here using the steps above.
