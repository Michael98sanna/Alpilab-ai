"""Alpilab AI — application entry point.

Modes:
  python app.py              interactive CLI (MockProvider)
  python app.py --serve      start local FastAPI server
"""

from __future__ import annotations

import argparse
import sys

from ai.router import build_default_router
from app.core.config import get_settings


def run_cli() -> None:
    settings = get_settings()
    router = build_default_router(settings)
    print(f"{settings.app_name} — foundation")
    print("Provider attivo:", router.provider_name)
    print("Scrivi una domanda tecnica (exit per uscire).")

    while True:
        try:
            question = input("\nTu > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if question.lower() in {"exit", "quit", "esci"}:
            break
        if not question:
            continue

        response = router.ask(question)
        print("\nAlpilab AI >", response)


def run_server(host: str, port: int) -> None:
    import uvicorn

    uvicorn.run("app.main:app", host=host, port=port, reload=False)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Alpilab AI")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the local FastAPI HTTP server",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.serve:
        run_server(args.host, args.port)
    else:
        run_cli()


if __name__ == "__main__":
    main(sys.argv[1:])
