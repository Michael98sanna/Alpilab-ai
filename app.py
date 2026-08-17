"""Alpilab AI — application entry point.

Modes:
- CLI interactive (default): ``python app.py``
- HTTP API: ``python app.py --api``  (uvicorn + FastAPI, mock provider)
"""

from __future__ import annotations

import argparse
import sys

from app.core import get_settings
from app.services import AssistantService, build_router


def run_cli() -> None:
    settings = get_settings()
    try:
        router = build_router(settings)
    except ValueError as exc:
        print(f"Errore configurazione: {exc}", file=sys.stderr)
        sys.exit(1)

    assistant = AssistantService(router)
    print(f"{settings.app_name} — fondazione modulare")
    print(f"Ambiente: {settings.environment}")
    print(f"Provider attivo: {assistant.provider_name}")
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

        response = assistant.ask(question)
        print(f"\nAlpilab AI [{response.provider}] >")
        print(response.content)


def run_api() -> None:
    settings = get_settings()
    try:
        import uvicorn
    except ImportError:
        print(
            "uvicorn non installato. Esegui: pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"Avvio API {settings.app_name} su "
        f"http://{settings.api_host}:{settings.api_port} "
        f"(provider={settings.ai_provider})"
    )
    uvicorn.run(
        "app.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Alpilab AI")
    parser.add_argument(
        "--api",
        action="store_true",
        help="Avvia l'API HTTP FastAPI invece della CLI",
    )
    args = parser.parse_args(argv)
    if args.api:
        run_api()
    else:
        run_cli()


if __name__ == "__main__":
    main()
