"""The FastAPI app: a thin layer over meta, settings and the simulator, plus the static page."""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from . import WEB_DIR
from .launcher import Simulator
from .meta import Meta
from .settings import Settings, SettingsFile


def create_app(meta: Meta, settings_file: SettingsFile, simulator: Simulator) -> FastAPI:
    app = FastAPI(title="Display simulator control", docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")

    @app.get("/api/meta")
    def get_meta() -> dict:
        """What can be set: expressions, voice states, colors and the frame rate range."""
        return meta.to_json()

    @app.get("/api/state")
    def get_state() -> Settings:
        """The current settings.txt, including hand edits."""
        return settings_file.read()

    @app.put("/api/state")
    def put_state(settings: Settings) -> Settings:
        """Replaces settings.txt. The simulator applies it within a fraction of a second."""
        problems = settings.problems(meta)
        if problems:
            raise HTTPException(status_code=422, detail=problems)
        settings_file.write(settings)
        return settings

    @app.post("/api/restart")
    def restart() -> dict:
        """Restarts the simulator, to pick up edits to the face component (looks.h and friends)."""
        if not simulator.managed:
            raise HTTPException(status_code=409, detail="The simulator was not started by control.py (--no-sim)")
        simulator.restart()
        return {"status": "restarting"}

    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app
