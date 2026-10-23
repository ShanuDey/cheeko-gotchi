# ESPHome config for Cheeko Gotchi

Runs the board under ESPHome so it shows up in Home Assistant (HA). Pins come
from [SKILL.md](../SKILL.md). This **replaces** the Cheeko app firmware; you
can't run both.

Device name: `cgotchi`. Config: [cheeko-gotchi.yaml](cheeko-gotchi.yaml).

## Status

| Part | State |
|---|---|
| Wi-Fi, HA API, wireless OTA | works |
| Backlight switch | works |
| Volume up/down buttons | works: each press steps the speaker volume by 10% (min 10%) |
| Boot animation | works: eyes open and "Hello!" for the first ~2.6 s after power on |
| On-screen OTA progress | works: "Updating" with a percentage, or "Update failed" |
| Charging detect (GPIO 37) | not possible, see Notes |
| Middle button (GPIO 3) | not working, see Troubleshooting |
| Display: Face, Clock and Message pages, talking mouth while audio plays | works |
| Speaker (HA media player), mic level | works |
| Touch (CST810), accelerometer (LIS2DH12) | not added yet |

## Setup

Two ways to build. Both need the secrets below.

**HA add-on (what we use):** open ESPHome Device Builder, edit `cgotchi`, paste
the contents of `cheeko-gotchi.yaml`, then **Install**. Secrets go in the
dashboard's **Secrets** page.

**Local:** `uv sync` (esphome is a dev dependency, pinned in `uv.lock`), then
`cp secrets.example.yaml secrets.yaml` (git-ignored, never commit it).

Secrets: `wifi_ssid` and `wifi_password` (2.4 GHz only), `ap_password`, and
`api_key`:
```bash
python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())"
```

## Validate before installing

Catches YAML errors in one pass instead of one at a time in the editor. Run
from **PowerShell** in `esphome/`. Don't use Git Bash: ESP-IDF fails there with
`MSys/Mingw is not supported`.
```powershell
uv run esphome config cheeko-gotchi.yaml
```
This checks the YAML only. C++ lambdas (tone generator, GPIO 3 debug log) are
checked by `uv run esphome compile cheeko-gotchi.yaml`, which is slow the first
time. Run both before every flash, especially after editing a `lambda:`. Keep
the pinned ESPHome version equal to the dashboard's (shown at its bottom):
`uv add --dev esphome==<version>`.

`config` and `compile` need `secrets.yaml`. For validation only you can use a
copy of `secrets.example.yaml`, but never flash with it: the device would get
the wrong Wi-Fi credentials. Flash only with your real file.

## Flash

First flash is over USB. Local: `uv run esphome run cheeko-gotchi.yaml --device COMx`
(find the port with `../tools/cheeko ports`). Or download the factory image
from the dashboard and flash it with https://web.esphome.io in Chrome/Edge.
After flashing, unplug and replug USB; the board stays in download mode.

After that, use **Install → Wirelessly**, or locally
`uv run esphome run cheeko-gotchi.yaml --device <ip> --no-logs`. Use the device
IP (HA device page), not `cgotchi.local`; mDNS is unreliable on Windows. OTA is
encrypted: it reuses `api_key`.
If a first encrypted install is refused, add `allow_plaintext_upload: true`
under `ota` for that one install, then remove it.

Flashing ESPHome overwrites the factory firmware and its TinyUF2 recovery
bootloader at `0x410000`. To keep a backup first:
`esptool --chip esp32s3 -p COMx read_flash 0 0x1000000 backup.bin`

## Check it works

- Log: I2C scan finds `0x15 0x18 0x19 0x40`.
- Screen: the Face page shows a smiling face. Switch **Display Page** to Clock
  (12-hour time such as `9:05` with AM/PM above it, and the date below) or
  Message and check the text reads left to right; mirrored text means the
  `mirror_x` transform is wrong. While audio plays the face talks whatever page
  is selected (the **Display Page** select does not change).
- Boot: power-cycle the board. The eyes grow from dots, then a smile and
  "Hello!" appear before the normal Face page. During a later OTA the screen
  shows "Updating" with a progress bar instead (it only appears if the firmware
  already running has it, so it shows from the second flash after adding it).
- HA: the device page has **Backlight**, the **Speaker** media player,
  **Display Page**, **Face Expression**, **Message Title/Body**, **Mic Level**
  and three button sensors. Mic Level only updates while something else is
  capturing audio (it is passive).

## Troubleshooting

- **Black screen after flashing:** expected until the YAML has a `display:`
  section; ESPHome only does what the YAML says.
- **Display stays black though flashed:** the display redraws on any
  display-entity change, once a minute, and while audio plays, so check the
  backlight switch and the log.
- **OTA says successful but the old build is still running:** the new image
  reset before it was marked good and the bootloader rolled back. Check the log
  for `OTA rollback detected` and compare `compiled on` with your build time.
  Usually a newly added pin or component; remove it and reflash.
- **OTA upload times out:** retry `esphome upload`; the connection is flaky
  right after a reboot.
- **Colours swapped or picture offset:** `color_order`, `invert_colors`, or
  `offset_width`/`offset_height` under `dimensions`. SKILL.md has the panel's
  known quirks (GRAM wider than the visible area, edge colour corruption).
- **Middle button silent:** the YAML logs `gpio3 raw level = N` on every change.
  No log line means the signal never reaches GPIO 3 (the one-key power circuit
  may handle it). Don't hold it about 3 s; that's the deliberate power-off.
- **Editor shows a red marker:** run `esphome config` locally for the full list.
- **`sound_level` rejects `update_interval`/`dbfs`:** it needs `passive:` and an
  `rms:` or `peak:` sensor.
- **Upload drops with `connection forcibly closed` but the device is up:** retry
  with `esphome upload`.
- **Speaker log `Parent bus is busy`:** a non-passive `sound_level` holds the
  shared I2S bus. Keep it `passive: true`.
- **Speaker clicks but is silent:** the amp works but the codec isn't producing
  sound; compare against the reference init in SKILL.md section 6.

## Notes

- GPIO 2 is forced low at boot. Driving it high cuts the board's power.
- The ES8311 can't record. All mic capture goes through the ES7210.
- Volume Up/Down are wired to the **Speaker** media player (`volume_increment`,
  `volume_min` and `volume_max` in the YAML). They also stay visible in HA as
  button sensors.
- Charging detect is GPIO 37, which octal PSRAM uses. A `gpio` sensor there made
  the new build reset at boot and ESP-IDF rolled back to the old firmware
  (`OTA rollback detected`). Don't add one. There is no battery level sensor:
  the board has no fuel gauge on I2C and no known battery-voltage ADC pin.
- A failed OTA that resets before boot completes rolls back to the previous
  build. Check `compiled on` in the log to see which build is running.
- `transform:` needs all three keys (`swap_xy`, `mirror_x`, `mirror_y`).
- The `gpio3` debug log is temporary; remove it once the middle button is sorted.
