# Install

Two ways to build: the HA ESPHome Device Builder (quick), or a local build with
`uv`. Both need the secrets below.

## Quick install (HA ESPHome Device Builder)

Nothing to download or copy. The config and its two custom components
(`remote_webview`, `face_colors`) are fetched from this repo when you build.

1. In HA, open **ESPHome Device Builder**, click **Secrets**, and add the keys
   from [secrets.example.yaml](../secrets.example.yaml) with your own values (see
   Secrets below). All eight are required.
2. Click **New Device**, then **Skip** the wizard, and **Edit** the new device.
3. Replace its contents with just this:
   ```yaml
   packages:
     cgotchi: github://ShanuDey/cheeko-gotchi/esphome/cgotchi.yaml@esphome
   ```
   The device is named `cgotchi`; to use another name, add
   `esphome: {name: mydevice}` above `packages:`.
4. **Install**. The first install is over USB, later ones are wireless (see
   [flash.md](flash.md)).

`@esphome` is the branch. For a stable setup pin a release tag instead (for
example `@v0.1.0`) so later changes to this repo don't alter your build. The first
build downloads the repo and the toolchain, so it is slow.

## Secrets

| Key | Value |
|---|---|
| `wifi_ssid`, `wifi_password` | Your Wi-Fi. 2.4 GHz only, the ESP32-S3 has no 5 GHz. |
| `ap_password` | Password of the fallback hotspot the device opens if Wi-Fi fails. |
| `api_key` | 32 byte base64 key (below). Also used for encrypted OTA. |
| `webview_server` | `host:port` of the Remote WebView server, no `http://`. Use the IP. |
| `webview_url` | Page the WebView shows, for example `http://<ha-ip>:8123/lovelace/default_view`. |
| `display_frame_server` | Address of the display-frame service, for example `http://<docker-host-ip>:28240`. Use the IP. |
| `display_frame_url` | Default page the Display Frame renders. |

Generate `api_key` with:
```bash
python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())"
```

All eight are required even if you don't use the WebView or Display Frame pages,
because the YAML reads them. If the device is already paired in HA, reuse its
existing `api_key` or HA will reject the new one.

The builder keeps its own secrets file (the **Secrets** button), separate from
any `secrets.yaml` in this repo.

The two servers behind the WebView and Display Frame pages run as Docker
containers: see [remote-webview/](../remote-webview/) and
[display-frame/](../display-frame/README.md).

## Local build

`uv sync` (esphome is a dev dependency, pinned in `uv.lock`), then
`cp secrets.example.yaml secrets.yaml` (git-ignored, never commit it) and fill in
the same secrets as above. Run `uv run esphome ...` from the `esphome/` folder in
**PowerShell**, not Git Bash (ESP-IDF fails there with `MSys/Mingw is not
supported`).

See [validate-and-verify.md](validate-and-verify.md) before the first flash, and
[development.md](development.md) for how the components are sourced.
