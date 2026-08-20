"""User-facing messages for natural language command outcomes."""

from __future__ import annotations

ERROR_MESSAGES: dict[str, str] = {
    "AMBIGUOUS_COMMAND": "Quale programma vuoi aprire?",
    "COMMAND_NOT_SUPPORTED": "Questo comando non è ancora supportato.",
    "UNKNOWN_APPLICATION": "Non riconosco quell'applicazione.",
    "INVALID_COMMAND": "Non posso eseguire comandi di sistema o percorsi arbitrari.",
    "AUTHORIZATION_DENIED": "Non sono autorizzato ad eseguire questa azione.",
    "TOOL_NOT_FOUND": "Lo strumento richiesto non è registrato.",
    "TOOL_DISABLED": "Lo strumento richiesto è disabilitato.",
    "CAPABILITY_MISSING": "Il PC Agent non ha la capability necessaria.",
    "AGENT_NOT_FOUND": "Non riesco ad aprire 3uTools: il PC Agent non è online.",
    "EXECUTABLE_NOT_FOUND": "Non riesco ad aprire 3uTools: l'applicazione non è disponibile sul PC.",
    "PROCESS_START_FAILED": "Non riesco ad aprire 3uTools: avvio dell'applicazione fallito.",
    "TOOL_EXECUTION_FAILED": "Non riesco ad aprire 3uTools: esecuzione fallita.",
    "TOOL_EXECUTION_TIMEOUT": "Non riesco ad aprire 3uTools: il PC Agent non ha risposto in tempo.",
    "ALPILAB_CHECK_UNAVAILABLE": "Alpilab Check non è disponibile sul PC in questo momento.",
    "ALPILAB_CHECK_TIMEOUT": "Alpilab Check non ha risposto in tempo.",
    "ALPILAB_CHECK_PROTOCOL_MISMATCH": "Versione bridge Alpilab Check non compatibile.",
    "ALPILAB_CHECK_UNAUTHORIZED": "Non sono autorizzato a leggere i dati da Alpilab Check.",
    "ALPILAB_CHECK_INVALID_RESPONSE": "Alpilab Check ha restituito una risposta non valida.",
    "ALPILAB_CHECK_UPSTREAM_ERROR": "Alpilab Check ha restituito un errore.",
}


def success_message(*, dry_run: bool) -> str:
    if dry_run:
        return "3uTools è configurato correttamente e verrebbe avviato."
    return "Ho aperto 3uTools."


def error_message(code: str) -> str:
    return ERROR_MESSAGES.get(code, "Non riesco a completare la richiesta.")
