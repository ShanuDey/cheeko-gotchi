# Display pages and settings

The display has five pages. Change page with a long press of Volume Down or the
**Display Page** select in HA. The select is not restored on boot, so a reboot
lands on Face.

| Page | Shows |
|---|---|
| Face | Animated face. The color, expression and mouth react to voice and audio. |
| Clock | Time and date from HA. |
| Message | **Message Title** and **Message Body**, set from HA. |
| Display Frame | JPEG snapshots from a URL: [display-frame.md](display-frame.md). |
| WebView | A live web page: [webview.md](webview.md). |

While audio plays, or the voice assistant is running, the face talks whatever page
is selected (the **Display Page** select does not change).

## Face

**Face Expression** (Happy, Sad, Sleepy, Surprised, Angry, Laughing, Confused,
Love, Wink) and **Face Color** (a color picker for the face only) with **Face
Color Preset** (Blue, Green, Pink, Orange, Purple, Red, Yellow, White, or Custom).

The face is drawn by the header-only `face` component, split by concern:

| File | Role |
|---|---|
| [looks.h](../components/face/looks.h) | The `Shape` model (eye size, lids, gaze, mouth) and one function per expression. |
| [draw.h](../components/face/draw.h) | Draws one frame from a `Shape`. No state, no timing. |
| [face.h](../components/face/face.h) | Eases between expressions, blinks, glances around, reacts to voice and audio. |
| [colors.h](../components/face/colors.h) | The color presets. |

Between expressions the face morphs rather than snapping. While nothing moves, it
redraws only for the occasional blink or glance, which keeps battery use low.
**Face Frame Rate** (5 to 25 fps) caps how often it may redraw while animating:
lower saves battery and leaves more time for audio, higher is smoother.

To add an expression: write a function in `looks.h`, add it to the `Expression`
enum and to `looks()`, and add its name to the **Face Expression** select in
`cgotchi.yaml` in the same order. Keep the color preset names in `colors.h` in
sync with the **Face Color Preset** select the same way.

## Clock

**Clock Format** selects 12 or 24 hour (no AM/PM). There is no battery-backed
clock: after power-off the Clock page shows "waiting for time" until the board
reconnects to HA and syncs.

## Boot and updates

- **Boot animation:** eyes open and "Hello!" appears for the first ~2.6 s after power on.
- **OTA progress:** "Updating" with a percentage, or "Update failed". It only
  appears if the firmware already running has it, so it shows from the second flash
  after adding it.

## Rounded corners

The panel is a 240x296 rectangle, but the bezel and glass have rounded corners
that hide the pixels in all four corners (the radius is not measured; about
25 to 30 px is a guess). Keep text, icons and anything important about 16 to
20 px away from the corners, in display lambdas, display frames and website
screenshots alike. The Face, Clock and Message pages are centred and already
fit. Content in the middle of each edge stays visible.

## Saved settings

**Clock Format**, **Face Expression**, **Face Color Preset**, **Message Title/Body**
and **Display Frame URL** use `restore_value: true`, so they live in flash and
survive power-off, reboots and OTA. Renaming one or changing its options in
the YAML resets it to the default once; a full flash erase clears them all.

## Display notes

- `transform:` needs all three keys (`swap_xy`, `mirror_x`, `mirror_y`).
- The display redraws on any display-entity change, once a minute, and while audio
  plays (`update_interval: never`).
