# remote_webview (patched copy)

Copy of `components/remote_webview` from
[strange-v/RemoteWebViewClient](https://github.com/strange-v/RemoteWebViewClient) (MIT, see
`LICENSE`), taken from `main` on 2026-10-24. Used by `esphome/cgotchi.yaml` and
`esphome/webview-test.yaml`-style configs. The server side is `esphome/remote-webview/`.

## Why a copy

Upstream draws tiles straight to the panel from the moment it connects, so it cannot share the
display with lambda-drawn pages. The changes below are the only differences from upstream.

## Changes

- `active:` (default `true`): start drawing or start paused.
- `RemoteWebView::set_active(bool)`: while inactive, decoded tiles are dropped, touch is not sent
  and no full-frame repair is requested. A mutex makes `set_active(false)` wait for a tile that is
  already being drawn, so the caller can draw to the display right after it returns. Turning it
  back on requests a full frame so the page repaints.
- `flip_x:` (default `false`): mirror every drawn region left to right in software, also
  switchable at runtime with `set_flip_x()` and `refresh()`. Not needed on this board once the
  display has `mirror_x: true`; the main config keeps it as a "WebView Flip X" debug switch.

- `swap_rb:` (default `false`): swap the red and blue channels of every drawn region in
  software. Not needed on this board: red/blue and left/right are fixed on the display itself
  (`color_order: bgr`, `mirror_x: true`), which also fixes the lambda pages.

The WebSocket stays connected while paused (the decoder still runs, only the drawing is skipped).

## Updating

To pick up upstream changes, re-copy the files and re-apply the changes above. The edits are
small and marked with comments.
