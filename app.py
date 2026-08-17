"""Alpilab AI — dual entrypoint: CLI (default) or API server.

Usage:
  python app.py              # interactive CLI with MockProvider
  python app.py --serve      # FastAPI via uvicorn (http://127.0.0.1:8000)
"""

from __future__ import annotations

import argparse

from ai.router import AIRouter


def run_cli() -> None:
    router = AIRouter()
    print("Alpilab AI - foundation (MockProvider)")
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

    uvicorn.run("app.api.main:app", host=host, port=port, reload=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Alpilab AI")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Avvia il server FastAPI invece della CLI.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.serve:
        run_server(args.host, args.port)
    else:
        run_cli()


if __name__ == "__main__":
    main()
