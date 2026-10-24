# Home Assistant dashboard

A ready-made control dashboard for the device: speaker, display, clock, face,
voice assistant, message screen, WebView and Display Frame, plus a mic level
graph. Config: [../dashboard/cgotchi-control.yaml](../dashboard/cgotchi-control.yaml).

It holds no secrets: only entity IDs and card settings. The WebView and Display
Frame addresses are entity values that stay in your own Home Assistant.

## Install

1. In HACS, install these Frontend cards: **Mushroom** (piitaya/lovelace-mushroom),
   **layout-card** (thomasloven/lovelace-layout-card) and **card-mod**
   (thomasloven/lovelace-card-mod).
2. **Settings > Dashboards > Add dashboard > New dashboard from scratch**.
   Name it, for example, "cgotchi control".
3. Open it, then the three dots, **Edit dashboard**, three dots again,
   **Raw configuration editor**.
4. Replace everything with the contents of `cgotchi-control.yaml` and save.

## Entity names

The file uses `cgotchi_` in every entity ID, which is what the device name
`cgotchi` gives (for example `select.cgotchi_display_page`).

Home Assistant adds your area name if the device is placed in one, so yours may
be `<area>_cheeko_`, for example. Check **Settings > Devices > Cheeko**, then in
the raw editor use **Find and replace** (Ctrl+H) to change `cgotchi_` to your
prefix. The full list of entities is in [ha-entities.md](ha-entities.md).

## Notes

- Text boxes (Message, WebView URL, Display Frame URL) are Mushroom cards: tap
  one to edit it in the pop-up.
- The Mic level graph is mostly empty: the sensor only measures while the voice
  assistant is capturing.
- If a card shows "Entity not available", the ID prefix is the usual cause.
