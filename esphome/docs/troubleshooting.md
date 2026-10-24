# Troubleshooting

## Install and build

- **Builder shows red errors on `!secret` lines:** the builder's own secrets file
  is missing keys. Add all eight in **Secrets**, see [install.md](install.md).
- **Editor shows a red marker:** run `esphome config` locally for the full list.
- **Upload drops with `connection forcibly closed` but the device is up:** retry
  with `esphome upload`.
- **OTA upload times out:** retry `esphome upload`; the connection is flaky
  right after a reboot.
- **OTA says successful but the old build is still running:** the new image
  reset before it was marked good and the bootloader rolled back. Check the log
  for `OTA rollback detected` and compare `compiled on` with your build time.
  Usually a newly added pin or component; remove it and reflash.

## Display

- **Black screen after flashing:** expected until the YAML has a `display:`
  section; ESPHome only does what the YAML says.
- **Display stays black though flashed:** the display redraws on any
  display-entity change, once a minute, and while audio plays, so check the
  backlight switch and the log.
- **Colours swapped or picture offset:** `color_order`, `invert_colors`, or
  `offset_width`/`offset_height` under `dimensions`. [SKILL.md](../../SKILL.md) has
  the panel's known quirks (GRAM wider than the visible area, edge colour corruption).
- **Face does not show while the assistant talks:** voice replies play as
  announcements, so the media player state is `ANNOUNCING`, not `PLAYING`. The
  display and the redraw interval check both.
- **Display Frame shows "No frame":** see [display-frame.md](display-frame.md).
  Log full of `Code: 304` means the server allows caching.

## Audio and voice

- **Voice assistant does nothing or sits at listening:** check the device has an
  Assist pipeline selected in HA, and look for `voice_assistant` lines in the log.
  `sound_level ... Microphone isn't running` is normal (Mic Level is passive).
- **Speaker log `Parent bus is busy`:** a non-passive `sound_level` holds the
  shared I2S bus. Keep it `passive: true`.
- **`sound_level` rejects `update_interval`/`dbfs`:** it needs `passive:` and an
  `rms:` or `peak:` sensor.
- **Speaker clicks but is silent:** the amp works but the codec isn't producing
  sound; compare against the reference init in [SKILL.md](../../SKILL.md) section 6.

## Buttons

- **Middle button silent:** the YAML has no sensor for it. It feeds the power
  circuit and never reaches GPIO 3 on this unit. Don't hold it about 3 s; that's
  the deliberate power-off.
