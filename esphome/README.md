# ESPHome config for Cheeko Gotchi

Runs the Cheeko Gotchi board under ESPHome so it shows up in Home Assistant (HA):
an animated face, clock, messages, live web pages and a voice assistant on the
240x296 touch display. This **replaces** the Cheeko app firmware; you can't run both.

Device name: `cgotchi`. Config: [cgotchi.yaml](cgotchi.yaml).

## Quick install

You need Home Assistant with the **ESPHome Device Builder** add-on.

1. In the builder, click **Secrets** and add the eight keys from
   [secrets.example.yaml](secrets.example.yaml) (Wi-Fi, API key, and the server
   addresses). Details: [docs/install.md](docs/install.md).
2. **New Device**, **Skip** the wizard, then **Edit** it.
3. Replace the contents with:
   ```yaml
   packages:
     cgotchi: github://ShanuDey/cheeko-gotchi/esphome/cgotchi.yaml@esphome
   ```
4. **Install**. The first install is over USB ([docs/flash.md](docs/flash.md)),
   later ones are wireless.

## What it does

- **Pages:** Face, Clock, Message, Display Frame (JPEG snapshots), WebView (live web page).
- **Voice assistant:** hold Volume Up to talk, or turn on Wake Word Mode.
- **Speaker and mic** as HA entities, volume buttons, dimmable backlight.
- **Wireless, encrypted OTA** with an on-screen progress bar.

## Docs

Everything else is in [docs/](docs/README.md): voice, display pages, Display
Frame, WebView, HA entities, validating, flashing, troubleshooting, hardware
notes and development.
