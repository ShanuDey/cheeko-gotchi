# Hardware notes and status

Pins and quirks come from [SKILL.md](../../SKILL.md).

## Status

| Part | State |
|---|---|
| Wi-Fi, HA API, wireless OTA | works |
| Backlight (dimmable light) | works |
| Volume up/down buttons | works: each short press steps the speaker volume by 5%; 0 to 100% is rescaled onto the audible, undistorted DAC range (0.3 to 0.8) |
| Voice assistant | works: hold Volume Up to talk, or turn on Wake Word Mode. See [voice-assistant.md](voice-assistant.md). |
| Boot animation, on-screen OTA progress | works |
| Display: Face, Clock, Message, Display Frame, WebView | works, see [display-pages.md](display-pages.md) |
| Speaker (HA media player), mic level | works |
| Charging detect (GPIO 37) | not possible, see below |
| Middle button (GPIO 3) | not working, see [troubleshooting.md](troubleshooting.md) |
| Touch (CST810) | used by the WebView page only |
| Accelerometer (LIS2DH12) | not added yet |

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
- Octal PSRAM is mandatory on this board.
- This config **replaces** the Cheeko app firmware; you can't run both.
