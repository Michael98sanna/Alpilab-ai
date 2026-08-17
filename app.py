"""Alpilab AI - application entry points."""

from __future__ import annotations

import argparse

from ai.router import AIRouter


def run_cli() -> None:
    router = AIRouter()
    print("Alpilab AI - base architecture")
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


def run_api() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Alpilab AI")
    parser.add_argument(
        "--api",
        action="store_true",
        help="Avvia il server HTTP FastAPI invece della CLI.",
    )
    args = parser.parse_args()
    if args.api:
        run_api()
    else:
        run_cli()


if __name__ == "__main__":
    main()
