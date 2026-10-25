"""Turns tuned values into a looks.h expression function, ready to paste."""
from .meta import Meta
from .settings import Settings


def _number(value: float) -> str:
    return f"{value:g}" if value == int(value) else f"{value:g}f"


def expression_to_cpp(meta: Meta, settings: Settings) -> str:
    """The current expression with the shape overrides applied, in the style of looks.h."""
    expression = meta.expression(settings.expression)
    # Only write what differs from where the function starts: the neutral Shape, or its base.
    start = meta.expression_by_func(expression.base).values if expression.base else meta.defaults
    final = {**expression.values, **settings.shape}

    init = f" = {expression.base}()" if expression.base else ""
    lines = [f"inline Shape {expression.func}() {{", f"  Shape s{init};"]
    lines += [f"  s.{f.name} = {_number(final[f.name])};" for f in meta.fields if final[f.name] != start[f.name]]
    lines += ["  return s;", "}"]
    return "\n".join(lines) + "\n"
