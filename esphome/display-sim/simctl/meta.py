"""What the simulator can show, read from components/face/looks.h and colors.h.

Reading the headers keeps one source of truth: add an expression or a color there and it appears
on the page after a restart. The parsing relies on the plain style those headers are written in.
"""
import re
from dataclasses import dataclass
from functools import lru_cache

from . import FACE_DIR

# Must match the "Face Frame Rate" number in display-sim.yaml.
FPS_MIN, FPS_MAX, FPS_STEP, FPS_DEFAULT = 5, 25, 5, 20

NUMBER = r"-?\d+(?:\.\d+)?"


@dataclass(frozen=True)
class Color:
    name: str
    rgb: tuple[int, int, int]


@dataclass(frozen=True)
class Meta:
    expressions: list[str]
    voices: list[str]
    colors: list[Color]

    def to_json(self) -> dict:
        return {
            "expressions": self.expressions,
            "voices": self.voices,
            "colors": [{"name": c.name, "rgb": c.rgb} for c in self.colors],
            "fps": {"min": FPS_MIN, "max": FPS_MAX, "step": FPS_STEP, "default": FPS_DEFAULT},
        }


def _parse_enum(text: str, name: str) -> list[str]:
    block = re.search(rf"enum class {name}[^{{]*\{{([^}}]*)\}}", text)
    if not block:
        raise RuntimeError(f"looks.h: enum {name} not found")
    return [n.strip() for n in block.group(1).split(",") if n.strip() and n.strip() != "Count"]


def _parse_colors(text: str) -> list[Color]:
    colors = [
        Color(name, (round(float(r) * 255), round(float(g) * 255), round(float(b) * 255)))
        for name, r, g, b in re.findall(rf'\{{"(\w+)",\s*({NUMBER})f,\s*({NUMBER})f,\s*({NUMBER})f\}}', text)
    ]
    if not colors:
        raise RuntimeError("colors.h: no color presets found")
    return colors


@lru_cache
def load_meta() -> Meta:
    looks = (FACE_DIR / "looks.h").read_text(encoding="utf-8")
    return Meta(
        expressions=_parse_enum(looks, "Expression"),
        voices=_parse_enum(looks, "Voice"),
        colors=_parse_colors((FACE_DIR / "colors.h").read_text(encoding="utf-8")),
    )
