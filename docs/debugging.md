# Debugging Seventwos Workspace for Desktop

There are two parts of the desktop app that you might want to debug.

## The renderer process

This runs the bundled web UI (inherited from Element Web) and can be debugged by just selecting
'toggle developer tools' from the menu, even on packaged builds. This then works the same as Chrome
dev tools for a regular web app.

## The main process

This is debugged as a node app, so:

1.  Open any chrome dev tools window
1.  Start the app with the `--inspect-brk` flag
1.  Notice that you now have a little green icon in the top left of your chrome devtools window, click it.

You are now debugging the code of the desktop app itself.

## The main process of a package app

When the app is shipped, electron's "fuses" are flipped, editing the electron binary itself to prevent certain features from being usable, one of which is debugging using `--inspect-brk` as above. You can flip the fuse back on Linux as follows:

```
sudo npx @electron/fuses write --app "/opt/Seventwos Workspace/seventwos-workspace-desktop" EnableNodeCliInspectArguments=on
```

A similar command will work, in theory, on mac and windows, except that this will break code signing (which is the point of fuses) so you would have to re-sign the app or somesuch.
