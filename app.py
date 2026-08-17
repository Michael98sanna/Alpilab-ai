"""Alpilab AI - minimal CLI entry point for the foundation phase."""

from __future__ import annotations

from ai.router import AIRouter
from app.api.health import health_payload
from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    router = AIRouter()
    health = health_payload()

    print(f"{settings.app_name} — foundation phase")
    print(f"Environment: {settings.environment}")
    print(f"Provider attivo: {router.provider_name}")
    print(f"Health: {health['status']} (phase={health['phase']})")
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


if __name__ == "__main__":
    main()
