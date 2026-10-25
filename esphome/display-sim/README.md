# Display simulator

Runs the real `face` component on your PC, with no device. It opens a 240x296 window
using ESPHome's [host platform and SDL display](https://esphome.io/components/display/sdl/),
so the same C++ that runs on the board draws what you see. Use it to tune faces and check
animation before flashing.

Only the face is simulated: not the other pages, audio, touch or Home Assistant.

## One-time setup (Windows 11)

The host platform needs Linux, so it runs in WSL. Everything else stays on Windows.

1. WSL with Ubuntu: `wsl --install -d Ubuntu` (skip if `wsl -l -v` already lists it).
2. In Ubuntu, install the compiler and SDL2:

   ```bash
   sudo apt update && sudo apt install -y build-essential libsdl2-dev pkg-config
   ```

3. In Ubuntu, install `uv`:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

The simulator keeps its own Linux Python environment and build output in your WSL home
(`~/.venvs/cgotchi`, `~/.esphome-sim`), so the repo's Windows `.venv` and `.esphome` are
not touched. The window appears through WSLg, which ships with Windows 11.

## Run with the control page (recommended)

From the repo root in PowerShell (or any shell on Linux or macOS):

```powershell
uv run --group sim esphome/display-sim/control.py
```

This starts the simulator in WSL, opens the control page at <http://localhost:8081>, and
stops the simulator when you press Ctrl+C. The first build is slow. Options:
`--no-sim` (only the page, start the simulator yourself), `--no-browser`, `--port`,
`--distro` (the WSL distribution, default Ubuntu).

The page changes the expression, voice state, speaking, color and frame rate, and has a
slider for every shape field (eye size, lids, gaze, mouth) to tune an expression live.
**Copy as C++** prints the tuned expression as a `looks.h` function to paste in. The
preview is the simulator window itself, so it is exactly what the device draws.

Tweaks belong to the current expression and are dropped when you pick another one.
**Idle motion** off freezes blinking and glancing, which helps while tuning. The face engine
reads its numbers from `components/face/looks.h`, and so does the page, so a new
expression there shows up in both after a restart.

## Run the simulator alone

```powershell
wsl -d Ubuntu -- bash <localrepo_path>/esphome/display-sim/run.sh
```

or from an Ubuntu shell, `./esphome/display-sim/run.sh`. Arguments: `config` (validate only),
`compile`, or `run` (the default: build and open the window).

## Settings file

The simulator polls `settings.txt` (created from `settings.example.txt` on the first run,
git-ignored) and applies it whenever it changes. The control page writes it, and you can edit
it by hand in any editor: saving applies the change within a fraction of a second. The file is
the whole state, so a line you delete goes back to its default. Bad lines are logged and
skipped. See the comments in [settings.example.txt](settings.example.txt) for every key,
including `shape.<field>` overrides.

## Keys

Click the window first so it has focus.

| Key | Action |
|---|---|
| Left / Right | previous / next expression |
| V | next voice state (Idle, Listening, Thinking, Replying, Error) |
| S | toggle speaking |
| C | next color preset |
| Up / Down | frame rate +5 / -5 fps |

Keys change the running simulator only, not `settings.txt`, so the next edit of the file or
the page puts everything back to what it says.

## Layout

| Path | Role |
|---|---|
| `display-sim.yaml` | the simulator's ESPHome config (SDL window, settings polling, key bindings) |
| `run.sh` | runs it in WSL |
| `control.py`, `simctl/` | the control page's FastAPI server (`meta`, `settings`, `exporter`, `api`, `launcher`) |
| `web/` | the page: plain HTML, CSS and JavaScript, no build step |
| `settings.example.txt` | documented template for `settings.txt` |

## Keeping it in step with the device

`display-sim.yaml` holds a small copy of the face part of the display lambda in
`cgotchi.yaml`, and the same option lists. If you change the face page in
`cgotchi.yaml`, mirror it here. The engine itself (`components/face/`) is shared, so
edits to expressions and drawing show up in both with no copying.
