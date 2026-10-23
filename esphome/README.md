# ESPHome config for Cheeko Gotchi

Runs the board under ESPHome so it shows up in Home Assistant (HA). Pins come
from [SKILL.md](../SKILL.md). This **replaces** the Cheeko app firmware; you
can't run both.

Device name: `cgotchi`. Config: [cheeko-gotchi.yaml](cheeko-gotchi.yaml).

## Status

| Part | State |
|---|---|
| Wi-Fi, HA API, wireless OTA | works |
| Backlight switch, volume up/down | works |
| Middle button (GPIO 3) | not working, see Troubleshooting |
| Display, speaker, mic | in the config, not yet confirmed on hardware |
| Touch (CST810), accelerometer (LIS2DH12) | not added yet |

## Setup

Two ways to build. Both need the secrets below.

**HA add-on (what we use):** open ESPHome Device Builder, edit `cgotchi`, paste
the contents of `cheeko-gotchi.yaml`, then **Install**. Secrets go in the
dashboard's **Secrets** page.

**Local:** `pip install esphome`, then `cp secrets.example.yaml secrets.yaml`
(git-ignored, never commit it).

Secrets: `wifi_ssid` and `wifi_password` (2.4 GHz only), `ap_password`, and
`api_key`:
```bash
python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())"
```

## Validate before installing

Catches YAML errors in one pass instead of one at a time in the editor:
```bash
cd esphome
esphome config cheeko-gotchi.yaml
```
This checks the YAML only. C++ lambdas (tone generator, GPIO 3 debug log) are
checked by `esphome compile cheeko-gotchi.yaml`, which is slow the first time.
Use the same ESPHome version as the dashboard (shown at its bottom).

## Flash

First flash is over USB. Local: `esphome run cheeko-gotchi.yaml --device COMx`
(find the port with `../tools/cheeko ports`). Or download the factory image
from the dashboard and flash it with https://web.esphome.io in Chrome/Edge.
After flashing, unplug and replug USB; the board stays in download mode.

After that, use **Install → Wirelessly**. OTA is encrypted: it reuses `api_key`.
If a first encrypted install is refused, add `allow_plaintext_upload: true`
under `ota` for that one install, then remove it.

Flashing ESPHome overwrites the factory firmware and its TinyUF2 recovery
bootloader at `0x410000`. To keep a backup first:
`esptool --chip esp32s3 -p COMx read_flash 0 0x1000000 backup.bin`

## Check it works

- Log: I2C scan finds `0x15 0x18 0x19 0x40`.
- Screen: "ABC" reads left to right, red/green/blue squares, "Hello". Mirrored
  text means the `mirror_x` transform is wrong.
- HA: the device page has **Backlight**, **Play Test Tone**, **Redraw Display**,
  **Mic Level** and three button sensors. Clap near the board and watch Mic
  Level change.

## Troubleshooting

- **Black screen after flashing:** expected until the YAML has a `display:`
  section; ESPHome only does what the YAML says.
- **Display stays black though flashed:** the display uses
  `update_interval: never`, so it only draws on boot and on **Redraw Display**.
- **Colours swapped or picture offset:** `color_order`, `invert_colors`, or
  `offset_width`/`offset_height` under `dimensions`. SKILL.md has the panel's
  known quirks (GRAM wider than the visible area, edge colour corruption).
- **Middle button silent:** the YAML logs `gpio3 raw level = N` on every change.
  No log line means the signal never reaches GPIO 3 (the one-key power circuit
  may handle it). Don't hold it about 3 s; that's the deliberate power-off.
- **Editor shows a red marker:** run `esphome config` locally for the full list.

## Notes

- GPIO 2 is forced low at boot. Driving it high cuts the board's power.
- The ES8311 can't record. All mic capture goes through the ES7210.
- `transform:` needs all three keys (`swap_xy`, `mirror_x`, `mirror_y`).
- The `gpio3` debug log is temporary; remove it once the middle button is sorted.
