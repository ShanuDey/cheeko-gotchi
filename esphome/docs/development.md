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
    components: [remote_webview, face]
```

- `remote_webview`: the WebView client, a patched copy of strange-v's
  RemoteWebViewClient.
- `face`: header-only; the face expressions, animation and drawing, plus the color
  presets. See [display-pages.md](display-pages.md#face).

This is what lets the config work standalone in the HA builder with no local
files. The catch: edits to `components/` have no effect on a build until you push
them. To iterate on a component locally, run ESPHome through `dev.py` (from
`esphome/`) instead of `uv run esphome`:

```bash
uv run dev.py compile
uv run dev.py run --device <ip|COMx> --no-logs
uv run dev.py logs --device <ip>
```

It writes `cgotchi-dev.yaml` (git-ignored), a copy of `cgotchi.yaml` with only the
component source switched to `components/` in this checkout. `cgotchi.yaml` is never
edited, so there is nothing to change back. Use plain `uv run esphome ... cgotchi.yaml`
to build what the branch on GitHub will give users.

ESPHome caches the git clone; use `esphome config --clean` (or delete the cached
clone under `.esphome/`) after pushing a change.

## Releasing

1. Merge to `main` and tag a release (for example `v0.1.0`).
2. Point `ref:` in `cgotchi.yaml` and the `packages:` line in
   [install.md](install.md) at the tag, so users don't break when the branch moves.

## Other folders

- [display-frame/](../display-frame/README.md): the display-frame service.
- [remote-webview/](../remote-webview/): Docker Compose for the Remote WebView server.
- `wyoming-voice/`: Docker Compose for local Wyoming speech services (Piper and Whisper) for the Assist pipeline.
