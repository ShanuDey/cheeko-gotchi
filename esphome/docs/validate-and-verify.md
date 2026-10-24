# Validate and verify

## Validate before installing

Catches YAML errors in one pass instead of one at a time in the editor. Run
from **PowerShell** in `esphome/`. Don't use Git Bash: ESP-IDF fails there with
`MSys/Mingw is not supported`.
```powershell
uv run esphome config cgotchi.yaml
```
This checks the YAML only. C++ lambdas are checked by
`uv run esphome compile cgotchi.yaml`, which is slow the first time. Run both
before every flash, especially after editing a `lambda:`. Keep the pinned ESPHome
version equal to the dashboard's (shown at its bottom):
`uv add --dev esphome==<version>`.

`config` and `compile` need `secrets.yaml`. For validation only you can use a
copy of `secrets.example.yaml`, but never flash with it. See [flash.md](flash.md).

## Check it works

- Log: I2C scan finds `0x15 0x18 0x19 0x40`.
- Screen: the Face page shows a smiling face. Switch **Display Page** to Clock
  (time such as `9:05`, or `09:05` in 24-hour mode, with the date below) or
  Message and check the text reads left to right; mirrored text means the
  `mirror_x` transform is wrong.
- Boot: power-cycle the board. The eyes grow from dots, then a smile and
  "Hello!" appear before the normal Face page.
- Voice: hold Volume Up, speak, and check the face changes from listening to
  thinking to talking, and the reply is audible. The log shows
  `Assist Pipeline ended` when it finishes.
- HA: the device page has the entities listed in [ha-entities.md](ha-entities.md).
