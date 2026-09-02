#!/usr/bin/env python3
"""Read-only diagnostics for ALPILAB Brain API keys and Ollama."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai.providers.diagnostics import ACTIONS_IT, build_provider_status
from app.ai.providers.key_validation import assert_no_secrets_in_text
from app.config.env_loader import get_env_load_state, load_environment


def main() -> int:
    import logging

    logging.basicConfig(level=logging.ERROR)
    parser = argparse.ArgumentParser(description="Verifica chiavi API ALPILAB Brain")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Non effettua chiamate reali ai provider",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Percorso esplicito del file .env da verificare",
    )
    args = parser.parse_args()

    try:
        loaded = load_environment(force=True, env_file=args.env_file)
    except FileNotFoundError as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        return 2

    status = build_provider_status(live=not args.offline)
    config = get_env_load_state()

    print("=== ALPILAB Brain — verifica configurazione ===")
    print(f"File .env caricato: {config.get('env_file_loaded') or 'nessuno'}")
    print(f"Sorgente selezionata: {config.get('env_file_loaded_from') or 'nessuna'}")
    print("Candidati .env (in ordine):")
    for entry in config.get("env_file_searched", []):
        path = entry.get("path") or "-"
        outcome = entry.get("outcome")
        selected = (
            loaded is not None
            and entry.get("path")
            and str(loaded) == str(entry.get("path"))
            and outcome == "found"
        )
        marker = ">" if selected else " "
        print(f"  {marker} [{entry.get('origin')} | {outcome}] {path}")

    print("\nProvider:")
    for row in status["providers"]:
        name = row["name"]
        present = "sì" if row["key_present"] else "no"
        shape = "sì" if row["key_shape_valid"] else "no"
        available = "sì" if row["available"] else "no"
        error_kind = row.get("error_kind", "none")
        latency = row.get("latency_ms")
        latency_text = f"{latency} ms" if latency is not None else "n/d"
        print(f"- {name}: chiave={present}, forma={shape}, operativo={available}, latenza={latency_text}")
        if error_kind != "none":
            print(f"    errore: {error_kind}")
            print(f"    azione: {ACTIONS_IT.get(error_kind, ACTIONS_IT['none'])}")

    mode = status["brain_mode"]
    if mode == "cloud":
        summary = "Brain operativo con provider cloud."
    elif mode == "local_only":
        summary = "Brain operativo solo con modello locale Ollama."
    else:
        summary = "Brain non operativo: configura chiavi API o Ollama."

    print(f"\nConclusione: {summary}")
    if loaded is None:
        print(f"Crea il file .env qui: {config.get('env_file_recommended')}")

    payload = json.dumps(status, ensure_ascii=False)
    assert_no_secrets_in_text(payload)
    return 0 if mode != "unavailable" else 1


if __name__ == "__main__":
    raise SystemExit(main())
