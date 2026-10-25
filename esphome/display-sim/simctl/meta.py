"""What the simulator can show, read from components/face/looks.h and colors.h.

Reading the headers keeps one source of truth: add an expression there and it appears here. The
parsing relies on the plain style looks.h is written in (see the note at the top of that file).
"""
import re
from dataclasses import dataclass
from functools import lru_cache

from . import FACE_DIR

# Must match the "Face Frame Rate" number in display-sim.yaml.
FPS_MIN, FPS_MAX, FPS_STEP, FPS_DEFAULT = 5, 25, 5, 20

# Slider ranges in pixels for each Shape field, keyed by field name. A field not listed here gets
# a generic range, so a new field still shows up (and tells you to add it, see load_meta).
RANGES = {
    "eye_w": (10, 90), "eye_h": (2, 100), "eye_r": (0, 45), "eye_gap": (50, 140), "eye_y": (60, 160),
    "lid_top": (0, 60), "lid_tilt": (-40, 40), "lid_asym": (-30, 30), "lid_bot": (0, 60), "wink": (0, 100),
    "look_x": (-30, 30), "look_y": (-30, 30),
    "mouth_y": (150, 240), "mouth_w": (0, 140), "mouth_curve": (-50, 50), "mouth_open": (0, 60),
}
GENERIC_RANGE = (-100, 300)

NUMBER = r"-?\d+(?:\.\d+)?"


@dataclass(frozen=True)
class Field:
    name: str
    default: float
    group: str
    min: float
    max: float


@dataclass(frozen=True)
class Expression:
    name: str                     # as shown in the select, e.g. "Happy"
    func: str                     # its function in looks.h, e.g. "happy"
    base: str | None              # function it starts from (`Shape s = happy();`), if any
    values: dict[str, float]      # every field's final value


@dataclass(frozen=True)
class Color:
    name: str
    rgb: tuple[int, int, int]


@dataclass(frozen=True)
class Meta:
    fields: list[Field]
    expressions: list[Expression]
    voices: list[str]
    colors: list[Color]

    def expression(self, name: str) -> Expression:
        return next(e for e in self.expressions if e.name == name)

    def expression_by_func(self, func: str) -> Expression:
        return next(e for e in self.expressions if e.func == func)

    @property
    def defaults(self) -> dict[str, float]:
        return {f.name: f.default for f in self.fields}

    def to_json(self) -> dict:
        return {
            "fields": [vars(f) for f in self.fields],
            "expressions": [{"name": e.name, "base": e.base, "values": e.values} for e in self.expressions],
            "voices": self.voices,
            "colors": [{"name": c.name, "rgb": c.rgb} for c in self.colors],
            "fps": {"min": FPS_MIN, "max": FPS_MAX, "step": FPS_STEP, "default": FPS_DEFAULT},
        }


def _group(field: str) -> str:
    for prefix, group in (("eye_", "Eyes"), ("lid_", "Lids"), ("wink", "Lids"), ("look_", "Gaze"), ("mouth_", "Mouth")):
        if field.startswith(prefix):
            return group
    return "Other"


def _strip_comments(text: str) -> str:
    return re.sub(r"//.*", "", text)


def _parse_fields(looks: str) -> list[Field]:
    block = re.search(r"struct Shape \{(.*?)\n\};", looks, re.S)
    if not block:
        raise RuntimeError("looks.h: struct Shape not found")
    pairs = re.findall(rf"(\w+)\s*=\s*({NUMBER})", _strip_comments(block.group(1)))
    return [
        Field(name, float(value), _group(name), *RANGES.get(name, GENERIC_RANGE))
        for name, value in pairs
    ]


def _parse_enum(text: str, name: str) -> list[str]:
    block = re.search(rf"enum class {name}[^{{]*\{{([^}}]*)\}}", text)
    if not block:
        raise RuntimeError(f"looks.h: enum {name} not found")
    return [n.strip() for n in block.group(1).split(",") if n.strip() and n.strip() != "Count"]


def _parse_expressions(looks: str, names: list[str], defaults: dict[str, float]) -> list[Expression]:
    funcs = {}
    for func, body in re.findall(r"inline Shape (\w+)\(\) \{\n(.*?)\n\}", looks, re.S):
        base = re.search(r"Shape s = (\w+)\(\);", body)
        assigns = {k: float(v) for k, v in re.findall(rf"\bs\.(\w+)\s*=\s*({NUMBER})f?;", body)}
        funcs[func] = (base.group(1) if base else None, assigns)

    def resolve(func: str) -> dict[str, float]:
        base, assigns = funcs[func]
        return {**(resolve(base) if base else defaults), **assigns}

    expressions = []
    for name in names:
        func = name.lower()
        if func not in funcs:
            raise RuntimeError(f"looks.h: no function {func}() for expression {name}")
        expressions.append(Expression(name, func, funcs[func][0], resolve(func)))
    return expressions


def _parse_colors(colors: str) -> list[Color]:
    return [
        Color(name, (round(float(r) * 255), round(float(g) * 255), round(float(b) * 255)))
        for name, r, g, b in re.findall(rf'\{{"(\w+)",\s*({NUMBER})f,\s*({NUMBER})f,\s*({NUMBER})f\}}', colors)
    ]


@lru_cache
def load_meta() -> Meta:
    looks = (FACE_DIR / "looks.h").read_text(encoding="utf-8")
    fields = _parse_fields(looks)
    defaults = {f.name: f.default for f in fields}
    unknown = [f.name for f in fields if f.name not in RANGES]
    if unknown:
        print(f"note: no slider range for {unknown}; add them to RANGES in simctl/meta.py")
    return Meta(
        fields=fields,
        expressions=_parse_expressions(looks, _parse_enum(looks, "Expression"), defaults),
        voices=_parse_enum(looks, "Voice"),
        colors=_parse_colors((FACE_DIR / "colors.h").read_text(encoding="utf-8")),
    )
