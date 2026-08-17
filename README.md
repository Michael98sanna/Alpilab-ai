# Alpilab AI

Assistente tecnico AI cloud/web per laboratori di riparazione smartphone.

Alpilab AI è un progetto **separato** da [Alpilab Check](https://github.com/Michael98sanna/Alpilab-ai): non importa il codice interno di Alpilab Check e in futuro comunicherà con esso solo tramite un contratto dati/API stabile.

## Alpilab AI vs Alpilab Check

| | Alpilab Check | Alpilab AI |
|---|---------------|------------|
| Tipo | Applicazione Windows al banco | Web app cloud-first (futura PWA) |
| Uso principale | Identificazione e diagnostica al banco | Assistente tecnico AI multi-dispositivo |
| Accesso | PC Windows | PC, tablet, smartphone (iOS/Android) |
| Relazione | Progetto autonomo esistente | Nuovo progetto; bridge futuro via API |

## Obiettivo

Alpilab AI supporta i tecnici con:

- ragionamento su problemi tecnici
- knowledge base e RAG (futuro)
- più motori AI tramite router comune
- modelli locali e cloud intercambiabili
- storico riparazioni e memoria del laboratorio (futuro)
- integrazione con Alpilab Check, Hub e strumenti del banco (futuro)

## Architettura (overview)

```text
                    ALPILAB AI
                        |
                  AI Router
          _____________|_____________
         |             |             |
      Local AI      Online AI      Fallback
         |             |             |
         +_____________+_____________+
                       |
                Knowledge Base
                       |
             Repair History / RAG
                       |
              Alpilab Check Bridge
```

Dettagli completi: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Struttura repository

```text
alpilab-ai/
├── app/                    # Backend application
│   ├── api/                # Futuri endpoint HTTP
│   ├── core/               # Configurazione
│   ├── models/             # Futuro layer persistenza
│   ├── schemas/            # Modelli dati (contratto condiviso)
│   ├── services/           # Logica di business
│   └── integrations/       # Alpilab Check bridge
├── ai/                     # AI layer
│   ├── providers/          # MockProvider (+ futuri provider)
│   ├── router.py           # AI Router
│   ├── prompts/            # Template di sistema
│   └── schemas.py          # AIRequest / AIResponse
├── knowledge/              # Futura knowledge base / RAG
├── frontend/               # Futura web app / PWA
├── hub/                    # Interfacce Alpilab Hub (mock)
├── tests/                  # Test pytest
├── docs/                   # Documentazione
├── app.py                  # Entry point CLI
├── requirements.txt
├── .env.example
└── README.md
```

## Requisiti

- Python 3.10+
- pip

## Avvio

```bash
# Installazione dipendenze
pip install -r requirements.txt

# Configurazione locale (opzionale)
cp .env.example .env

# CLI interattiva con MockProvider
python app.py
```

## Test

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Cosa è implementato

- Interfaccia astratta `AIProvider` (`generate`, `generate_with_image`, `generate_stream`, `is_available`)
- `MockProvider` per sviluppo e test senza API esterne
- `AIRouter` con selezione base del provider (testo vs immagini)
- Schemi Pydantic per entità di riparazione (`Device`, `RepairSession`, `DiagnosticTest`, `Measurement`, ecc.)
- `AlpilabCheckConnector` (interfaccia + mock)
- `AlpilabHub` (interfaccia + mock per hardware/software del PC)
- Configurazione via `.env` (senza segreti nel repo)
- Test pytest per i componenti sopra
- Documentazione architetturale

## Cosa è pianificato (non in questa fase)

- Autenticazione e gestione utenti
- Deploy cloud e database PostgreSQL
- Provider AI reali (OpenAI, Gemini, Anthropic, modelli locali)
- API REST per frontend web/mobile
- Knowledge base, RAG e storico riparazioni
- Integrazione reale con Alpilab Check e Alpilab Hub
- Controllo hardware (microscopio, termocamera, multimetro, alimentatore)
- Integrazione 3uTools, Borneo, ZXW
- Assistente vocale e PWA installabile

## Regole del progetto

1. Nessuna API key nel repository.
2. I provider AI devono essere intercambiabili.
3. La logica tecnica non deve dipendere dal provider scelto.
4. Alpilab Check: solo tramite interfaccia dati separata.
5. Risposte tecniche: distinguere fatti, dati rilevati, ipotesi e confidenza.
6. Prima di automatizzare una diagnosi: proporre controlli verificabili.
7. Nessuna esecuzione arbitraria di comandi o remote shell dall'Hub.

## Licenza

Da definire.
