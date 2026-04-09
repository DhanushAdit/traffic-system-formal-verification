"""
Web visualizer for the traffic infrastructure simulator.

- Pure HTTP: `POST /api/reset`, `POST /api/step` return JSON snapshots from your Python code.
- Open http://127.0.0.1:8765/ after:  python -m traffic_infra.web_app

Requires: pip install -e ".[web]"
"""

from __future__ import annotations

import argparse
import os
import socket
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from .viz_session import VizSimulationSession

STATIC_DIR = Path(__file__).resolve().parent / "static"

_FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<rect fill="#0d9488" width="32" height="32" rx="6"/>'
    '<path stroke="#ccfbf1" stroke-width="2" fill="none" d="M10 22L22 10M10 10l12 12"/></svg>'
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
SESSION_COOKIE = "traffic_viz_session"
_sessions: dict[str, VizSimulationSession] = {}


def create_app() -> FastAPI:
    app = FastAPI(title="Traffic visualizer", version="2")

    @app.middleware("http")
    async def no_cache_static(request: Request, call_next):
        resp = await call_next(request)
        if request.url.path.startswith("/assets"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        return Response(_FAVICON_SVG, media_type="image/svg+xml")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})

    def _get_session(request: Request, response: Response) -> VizSimulationSession:
        sid = request.cookies.get(SESSION_COOKIE)
        if not sid or sid not in _sessions:
            sid = str(uuid.uuid4())
            _sessions[sid] = VizSimulationSession()
            response.set_cookie(
                SESSION_COOKIE,
                sid,
                httponly=True,
                samesite="lax",
                path="/",
                max_age=86400 * 7,
            )
        return _sessions[sid]

    @app.post("/api/reset")
    async def api_reset(request: Request, response: Response) -> dict:
        sid = request.cookies.get(SESSION_COOKIE)
        if sid and sid in _sessions:
            del _sessions[sid]
        session = _get_session(request, response)
        return session.reset()

    @app.post("/api/step")
    async def api_step(request: Request, response: Response) -> dict:
        session = _get_session(request, response)
        return session.step()

    app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")
    return app


app = create_app()


def _first_free_port(host: str, preferred: int, *, attempts: int = 40) -> int:
    for p in range(preferred, preferred + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, p))
            except OSError:
                continue
            return p
    raise SystemExit(f"No free port on {host!r} in range {preferred}–{preferred + attempts - 1}")


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="Traffic visualizer (HTTP API + canvas UI).")
    parser.add_argument("--host", default=os.environ.get("TRAFFIC_INFRA_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("TRAFFIC_INFRA_PORT", str(DEFAULT_PORT))))
    parser.add_argument("--strict-port", action="store_true")
    args = parser.parse_args()

    if args.strict_port:
        port = args.port
        _first_free_port(args.host, port, attempts=1)
    else:
        port = _first_free_port(args.host, args.port)
        if port != args.port:
            print(f"Port {args.port} busy → using {port}\n")

    print(f"Visualizer:  http://127.0.0.1:{port}/\n")

    uvicorn.run("traffic_infra.web_app:app", host=args.host, port=port, reload=False)


if __name__ == "__main__":
    main()
