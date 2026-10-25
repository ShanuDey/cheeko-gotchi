"""Runs ESPHome on cgotchi.yaml with the custom components taken from this checkout (components/)
instead of the GitHub branch, so edits there apply without pushing.

    uv run dev.py config
    uv run dev.py compile
    uv run dev.py run --device <ip|COMx> --no-logs
    uv run dev.py logs --device <ip>

Run it from esphome/. It writes cgotchi-dev.yaml (git-ignored): a copy of cgotchi.yaml with only
the external_components source switched to local, then passes everything on to ESPHome. cgotchi.yaml
stays the one real config, so nothing drifts. Releases and the HA builder use cgotchi.yaml directly.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GIT_SOURCE = re.compile(r"type: git\s+url: [^\r\n]+\s+ref: [^\r\n]+\s+path: esphome/components")
LOCAL_SOURCE = "type: local\n      path: components"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    config = (HERE / "cgotchi.yaml").read_text(encoding="utf-8")
    dev, replaced = GIT_SOURCE.subn(LOCAL_SOURCE, config)
    if replaced != 1:
        print("Expected one git external_components source in cgotchi.yaml.", file=sys.stderr)
        return 1
    (HERE / "cgotchi-dev.yaml").write_text(dev, encoding="utf-8", newline="\n")

    command, *rest = sys.argv[1:]
    return subprocess.call([sys.executable, "-m", "esphome", command, "cgotchi-dev.yaml", *rest], cwd=HERE)


if __name__ == "__main__":
    sys.exit(main())
