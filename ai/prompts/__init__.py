"""Prompt templates for Alpilab AI.

Keep prompts versioned and provider-agnostic. Real prompt engineering will
evolve here; these are starter scaffolds only.
"""

from __future__ import annotations

SYSTEM_TECHNICAL_ASSISTANT = """\
Sei ALPILAB AI, un assistente tecnico per un laboratorio di riparazione smartphone.
Rispondi in italiano, in modo chiaro e operativo.
Distingui sempre: fatti verificati, dati rilevati, ipotesi, livello di confidenza.
Prima di suggerire interventi invasivi, proponi controlli verificabili.
"""

DIAGNOSIS_PROMPT = """\
Contesto riparazione:
{context}

Problema segnalato:
{issue}

Fornisci:
1. Possibili cause ordinate per probabilità
2. Controlli da eseguire al banco
3. Cosa NON fare (azioni rischiose)
4. Livello di confidenza (basso/medio/alto) con motivazione
"""


def build_diagnosis_prompt(*, context: str, issue: str) -> str:
    return DIAGNOSIS_PROMPT.format(context=context.strip(), issue=issue.strip())
