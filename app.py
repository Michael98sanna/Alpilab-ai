"""Start the Alpilab AI web API.

This project is cloud-first: the entry point serves a web backend (and a
minimal frontend) rather than a desktop-only loop.
"""

from __future__ import annotations

import argparse

import uvicorn

from app.core.config import get_settings


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Alpilab AI API server")
    parser.add_argument("--host", default=settings.host)
    parser.add_argument("--port", type=int, default=settings.port)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
