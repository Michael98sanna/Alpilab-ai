"""Interactive CLI for local checks. The primary interface is the HTTP API."""

from ai.router import build_router
from app.core.config import settings


def main() -> None:
    router = build_router(settings.ai_provider)
    print("Alpilab AI — CLI di sviluppo")
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


if __name__ == "__main__":
    main()
