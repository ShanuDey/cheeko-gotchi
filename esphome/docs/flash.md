# Flash

First flash is over USB. Local: `uv run esphome run cgotchi.yaml --device COMx`
(find the port with `../../tools/cheeko ports`). Or download the factory image
from the dashboard and flash it with https://web.esphome.io in Chrome/Edge.
After flashing, unplug and replug USB; the board stays in download mode.

After that, use **Install → Wirelessly**, or locally
`uv run esphome run cgotchi.yaml --device <ip> --no-logs`. Use the device
IP (HA device page), not `cgotchi.local`; mDNS is unreliable on Windows. OTA is
encrypted: it reuses `api_key`.
If a first encrypted install is refused, add `allow_plaintext_upload: true`
under `ota` for that one install, then remove it.

Flashing ESPHome overwrites the factory firmware and its TinyUF2 recovery
bootloader at `0x410000`. To keep a backup first:
`esptool --chip esp32s3 -p COMx read_flash 0 0x1000000 backup.bin`

Never flash with the dummy values from `secrets.example.yaml`: the device would
get the wrong Wi-Fi credentials. Flash only with your real secrets.

A failed OTA that resets before boot completes rolls back to the previous
build. Check `compiled on` in the log to see which build is running. See
[troubleshooting.md](troubleshooting.md) if an OTA seems to succeed but nothing changes.
