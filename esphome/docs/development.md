# Development

## How the components are sourced

`cgotchi.yaml` loads its two custom components from GitHub:

```yaml
external_components:
  - source:
      type: git
      url: https://github.com/ShanuDey/cheeko-gotchi
      ref: esphome
      path: esphome/components
    components: [remote_webview, face_colors]
```

- `remote_webview`: the WebView client, a patched copy of strange-v's
  RemoteWebViewClient.
- `face_colors`: header-only; makes `FACE_PRESETS` available to the lambdas.

This is what lets the config work standalone in the HA builder with no local
files. The catch: edits to `components/` have no effect on a build until you push
them. To iterate on a component locally, temporarily change the source to:

```yaml
  - source:
      type: local
      path: components
    components: [remote_webview, face_colors]
```

and change it back before you commit. ESPHome caches the git clone; use
`esphome config --clean` (or delete the cached clone under `.esphome/`) after
pushing a change.

## Releasing

1. Merge to `main` and tag a release (for example `v0.1.0`).
2. Point `ref:` in `cgotchi.yaml` and the `packages:` line in
   [install.md](install.md) at the tag, so users don't break when the branch moves.

## Other folders

- [display-frame/](../display-frame/README.md): the display-frame service.
- [remote-webview/](../remote-webview/): Docker Compose for the Remote WebView server.
- `wyoming-voice/`: Docker Compose for local Wyoming speech services (Piper and Whisper) for the Assist pipeline.
