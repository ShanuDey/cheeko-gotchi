# ESPHome config for Cheeko Gotchi

Runs the board under ESPHome so it shows up in Home Assistant (HA). Pins come
from [SKILL.md](../SKILL.md). This **replaces** the Cheeko app firmware; you
can't run both.

Device name: `cgotchi`. Config: [cheeko-gotchi.yaml](cheeko-gotchi.yaml).

## Status

| Part | State |
|---|---|
| Wi-Fi, HA API, wireless OTA | works |
| Backlight (dimmable light) | works |
| Volume up/down buttons | works: each short press steps the speaker volume by 5%; 0 to 100% is rescaled onto the audible, undistorted DAC range (0.3 to 0.8) |
| Voice assistant | added: hold Volume Up (about 1 s) to talk, or turn on Wake Word Mode for an on-device wake word. Listening, thinking and speaking each have their own face. See Voice assistant below. |
| Boot animation | works: eyes open and "Hello!" for the first ~2.6 s after power on |
| On-screen OTA progress | works: "Updating" with a percentage, or "Update failed" |
| Charging detect (GPIO 37) | not possible, see Notes |
| Middle button (GPIO 3) | not working, see Troubleshooting |
| Display: Face, Clock and Message pages, talking mouth while audio plays | works |
| Display Frame page (JPEG snapshots from a URL) | works: tested with the display-frame clock; see Display Frame below |
| Clock format (12/24 hour) | works: **Clock Format** select; the choice is stored in flash and survives power-off and OTA |
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

## Voice assistant

The device is a push-to-talk microphone and speaker for HA's Assist pipeline
(speech to text, conversation agent, text to speech). By default it is push-to-talk.
Turn on the **Wake Word Mode** switch in HA to use a wake word as well: the device
runs ESPHome's on-device `micro_wake_word` (models `okay_nabu` and `hey_jarvis`) and
only talks to HA once it hears one. Pick the active model in the device's **Wake word**
select in HA. Holding Volume Up still works in both modes. The switch survives reboots.
A green dot at the top center of the screen shows whenever the mic is open (wake word
listening or recording a request). It is not drawn on the WebView page.
HA's openWakeWord add-on is not used: HA only offers a wake word for an ESPHome device
from the models the device itself reports.

1. In HA, open the device page and set its **Assist pipeline** to the one you
   want (an LLM conversation agent gives open-ended chat).
2. Hold **Volume Up** for about 1 second. A short press still raises the volume.
   Hold again while it is running to cancel.
3. The face shows the state: wide eyes with pulsing rings (listening), eyes
   glancing aside with three dots (thinking), then the talking mouth while the
   reply plays. A red `voice error` caption appears for 3 s if the pipeline fails.

Replies play through the **Speaker** media player, so the volume buttons control
them. Tune `mic_gain` (under `audio_adc`) and `noise_suppression_level`,
`auto_gain` and `volume_multiplier` (under `voice_assistant`) if speech is
quiet or misheard. The mic also hears the speaker, so interrupting a reply is
unreliable.

## Screen shape: rounded corners

The panel is a 240x296 rectangle, but the bezel and glass have rounded corners
that hide the pixels in all four corners (the radius is not measured; about
25 to 30 px is a guess). Keep text, icons and anything important about 16 to
20 px away from the corners, in display lambdas, display frames and website
screenshots alike. The Face, Clock and Message pages are centred and already
fit. Content in the middle of each edge stays visible.

## Display Frame (JPEG snapshots)

ESPHome has no video player, so the **Display Frame** page shows JPEG snapshots fetched
one after another over HTTP (a few frames per second, no audio).

1. Serve JPEG frames already scaled to 240x296. The device only decodes; it
   does not resize. Leave a safe margin for the rounded corners (see above).
   [display-frame/](display-frame/README.md) does this: it renders a
   page (a built-in clock by default) in headless Chromium and serves it at
   `http://<docker-host-ip>:28240/frame.jpg`.
2. Put the service address in `secrets.yaml` as `display_frame_server`
   (`http://<docker-host-ip>:28240`, use the IP) and the default page as
   `display_frame_url`. In HA, **Display Frame Source** picks a page bundled with the service
   (the list comes from the service a few seconds after boot) or `Custom`,
   which renders whatever **Display Frame URL** holds (sent as `?url=`). No reflash needed.
3. Long press Volume Down until the Display Frame page shows (the order is Face,
   Clock, Message, Display Frame, WebView), or set **Display Page** to Display Frame
   in HA. Fetching runs only while that page is showing, so choosing another page
   stops it.

The page shows "Loading..." until the first frame decodes. After 3 failed
fetches in a row (server down, wrong port, malformed or empty URL) it shows
"No frame" with "check Frame URL" (or `display_frame_server`). The device keeps retrying every second and the
picture returns once the server answers. Touch does nothing on this page; change
page with Volume Down (long press) or **Display Page** in HA.

The server must not send `Last-Modified` or allow caching (send
`Cache-Control: no-store`). Otherwise the device sends `If-Modified-Since`,
gets `304 Not Modified`, and the log fills with `HTTP Request failed; Code: 304`.
The page select is not restored on boot, so a reboot lands on Face.

The next download is started by the `fetch_next` script, never from inside
`on_download_finished` or `on_error`. ESPHome tears down the connection right
after those callbacks, so a download started inside them is aborted and the
image is released (frozen frame, then a black screen).

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
  (time such as `9:05`, or `09:05` in 24-hour mode, with the date below) or
  Message and check the text reads left to right; mirrored text means the
  `mirror_x` transform is wrong. While audio plays the face talks whatever page
  is selected (the **Display Page** select does not change).
- Boot: power-cycle the board. The eyes grow from dots, then a smile and
  "Hello!" appear before the normal Face page. During a later OTA the screen
  shows "Updating" with a progress bar instead (it only appears if the firmware
  already running has it, so it shows from the second flash after adding it).
- Voice: hold Volume Up, speak, and check the face changes from listening to
  thinking to talking, and the reply is audible. The log shows
  `Assist Pipeline ended` when it finishes.
- HA: the device page has **Backlight**, the **Speaker** media player,
  **Display Page**, **Clock Format** (12 or 24 hour), **Face Expression**,
  **Face Color** (colour picker for the face only) with **Face Color Preset**
  (Blue, Green, Pink, ... or Custom), **Message Title/Body**, **Mic Level**
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
- **Face does not show while the assistant talks:** voice replies play as
  announcements, so the media player state is `ANNOUNCING`, not `PLAYING`. The
  display and the redraw interval check both.
- **Voice assistant does nothing or sits at listening:** check the device has an
  Assist pipeline selected in HA, and look for `voice_assistant` lines in the log.
  `sound_level ... Microphone isn't running` is normal (Mic Level is passive).
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
- Saved settings: **Clock Format**, **Face Expression**, **Face Color Preset**, **Message Title/Body**
  and **Display Frame URL** use `restore_value: true`, so they live in flash and
  survive power-off, reboots and OTA. Renaming one or changing its options in
  the YAML resets it to the default once; a full flash erase clears them all.
- There is no battery-backed clock. After power-off the Clock page shows
  "waiting for time" until the board reconnects to HA and syncs.
- `transform:` needs all three keys (`swap_xy`, `mirror_x`, `mirror_y`).
- The `gpio3` debug log is temporary; remove it once the middle button is sorted.
