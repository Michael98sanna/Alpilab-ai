"""Alpilab AI - application entry point."""

from ai.router import AIRouter
from ai.schemas import AIRequest


def main() -> None:
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

        response = router.generate(AIRequest(prompt=question))
        print("\nAlpilab AI >", response.content)


if __name__ == "__main__":
    main()
