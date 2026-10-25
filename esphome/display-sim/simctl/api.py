"""The FastAPI app: a thin layer over meta, settings and the exporter, plus the static page."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import WEB_DIR
from .exporter import expression_to_cpp
from .meta import Meta
from .settings import Settings, SettingsFile


def create_app(meta: Meta, settings_file: SettingsFile) -> FastAPI:
    app = FastAPI(title="Display simulator control", docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")

    @app.get("/api/meta")
    def get_meta() -> dict:
        """What can be set: fields with ranges, expressions with their values, voices, colors."""
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

    @app.get("/api/export", response_class=PlainTextResponse)
    def export() -> str:
        """The current expression with its shape tweaks as a looks.h function."""
        return expression_to_cpp(meta, settings_file.read())

    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app
