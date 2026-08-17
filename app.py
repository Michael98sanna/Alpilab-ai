"""Alpilab AI — CLI entry point for local smoke testing.

For the HTTP API, prefer:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import argparse
import sys

from ai.router import AIRouter


def run_cli() -> int:
    router = AIRouter()
    print("Alpilab AI — foundation (CLI)")
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

    return 0


def run_api(host: str, port: int) -> int:
    try:
        import uvicorn
    except ImportError:
        print(
            "uvicorn non installato. Esegui: pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    uvicorn.run("app.main:app", host=host, port=port, reload=False)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Alpilab AI entry point")
    parser.add_argument(
        "--api",
        action="store_true",
        help="Avvia l'API HTTP FastAPI invece della CLI",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.api:
        return run_api(args.host, args.port)
    return run_cli()


if __name__ == "__main__":
    raise SystemExit(main())
