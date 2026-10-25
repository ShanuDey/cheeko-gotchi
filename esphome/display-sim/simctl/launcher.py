"""Starts and stops the simulator itself. It needs Linux, so on Windows it runs inside WSL."""
import subprocess
import sys
from pathlib import Path

from . import SIM_DIR

RUN_SH = SIM_DIR / "run.sh"
# Matches the host program and the esphome process that started it, nothing else.
STOP_PATTERNS = ("pioenvs/cgotchi-sim", "esphome run display-sim.yaml")


def _wsl_path(path: Path) -> str:
    """C:\\Users\\me\\x -> /mnt/c/Users/me/x"""
    drive, rest = path.drive.rstrip(":").lower(), path.as_posix()[len(path.drive):]
    return f"/mnt/{drive}{rest}"


class Simulator:
    def __init__(self, distro: str = "Ubuntu", managed: bool = True):
        self.distro = distro
        self.managed = managed   # False: the user runs the simulator, so there is nothing to restart
        self.process: subprocess.Popen | None = None

    @property
    def _on_windows(self) -> bool:
        return sys.platform == "win32"

    def start(self) -> None:
        if self._on_windows:
            command = ["wsl", "-d", self.distro, "--", "bash", _wsl_path(RUN_SH)]
        else:
            command = ["bash", str(RUN_SH)]
        print(f"starting the simulator: {' '.join(command)}")
        self.process = subprocess.Popen(command)

    def restart(self) -> None:
        self.stop()
        self.start()

    def stop(self) -> None:
        if self.process is None:
            return
        self.process.terminate()
        # Ending wsl.exe does not end what it started inside Linux.
        prefix = ["wsl", "-d", self.distro, "--"] if self._on_windows else []
        for pattern in STOP_PATTERNS:
            subprocess.run([*prefix, "pkill", "-f", pattern], check=False)
        self.process = None
