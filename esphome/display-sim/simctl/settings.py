"""The settings model and the settings.txt file the simulator polls.

The file is the whole state: the simulator resets whatever it does not mention. This module reads
hand-edited files leniently (bad lines are skipped, option names are case insensitive) and writes
atomically so the simulator never sees half a file.
"""
import os
import shutil
import time
from pathlib import Path

from pydantic import BaseModel, Field

from . import SETTINGS_EXAMPLE_PATH, SETTINGS_PATH
from .meta import FPS_DEFAULT, FPS_MAX, FPS_MIN, FPS_STEP, Meta

HEADER = "# Written by control.py. Edit freely: the simulator applies saved changes.\n"
ON = {"on", "true", "1"}
OFF = {"off", "false", "0"}


class Settings(BaseModel):
    expression: str
    voice: str = "Idle"
    speaking: bool = False
    color: str = "Blue"
    fps: int = FPS_DEFAULT
    idle_motion: bool = True
    shape: dict[str, float] = Field(default_factory=dict)   # field name -> overridden value (px)

    def problems(self, meta: Meta) -> list[str]:
        """What is wrong with these values; empty when they are fine."""
        found = []
        if self.expression not in {e.name for e in meta.expressions}:
            found.append(f"unknown expression '{self.expression}'")
        if self.voice not in meta.voices:
            found.append(f"unknown voice '{self.voice}'")
        if self.color not in {c.name for c in meta.colors}:
            found.append(f"unknown color '{self.color}'")
        if not FPS_MIN <= self.fps <= FPS_MAX or (self.fps - FPS_MIN) % FPS_STEP:
            found.append(f"fps must be {FPS_MIN} to {FPS_MAX} in steps of {FPS_STEP}")
        known = {f.name for f in meta.fields}
        found += [f"unknown shape field '{name}'" for name in self.shape if name not in known]
        return found

    def render(self) -> str:
        lines = [
            f"expression = {self.expression}",
            f"voice = {self.voice}",
            f"speaking = {'on' if self.speaking else 'off'}",
            f"color = {self.color}",
            f"fps = {self.fps}",
            f"idle_motion = {'on' if self.idle_motion else 'off'}",
            *(f"shape.{name} = {value:g}" for name, value in self.shape.items()),
        ]
        return HEADER + "\n".join(lines) + "\n"


def parse(text: str, meta: Meta) -> Settings:
    """Reads settings.txt text. Anything unusable keeps its default."""
    settings = Settings(expression=meta.expressions[0].name)
    options = {
        "expression": [e.name for e in meta.expressions],
        "voice": meta.voices,
        "color": [c.name for c in meta.colors],
    }
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        key, sep, value = (part.strip() for part in line.partition("="))
        if not sep:
            continue
        key, low = key.lower(), value.lower()
        try:
            if key in options:
                match = next((o for o in options[key] if o.lower() == low), None)
                if match:
                    setattr(settings, key, match)
            elif key in ("speaking", "idle_motion"):
                if low in ON | OFF:
                    setattr(settings, key, low in ON)
            elif key == "fps":
                settings.fps = int(float(value))
            elif key.startswith("shape."):
                settings.shape[key.removeprefix("shape.")] = float(value)
        except ValueError:
            continue
    return settings


class SettingsFile:
    def __init__(self, meta: Meta, path: Path = SETTINGS_PATH):
        self.meta = meta
        self.path = path

    def read(self) -> Settings:
        if not self.path.exists():
            shutil.copy(SETTINGS_EXAMPLE_PATH, self.path)
        return parse(self.path.read_text(encoding="utf-8"), self.meta)

    def write(self, settings: Settings) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(settings.render(), encoding="utf-8", newline="\n")
        for attempt in range(5):   # the simulator (in WSL) may have the file open for a moment
            try:
                os.replace(tmp, self.path)
                return
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.05)
