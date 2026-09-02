# Configurazione API — ALPILAB Brain

Guida per chi usa **ALPILAB AI.exe** o lo sviluppo locale, senza conoscere il codice.

## Dove mettere il file `.env`

ALPILAB legge un file chiamato **`.env`** (punto env, senza `.txt`).

### Build EXE (consigliato in laboratorio)

Metti il file **nella stessa cartella dell'eseguibile**:

```
C:\Users\MichaelLab\Desktop\Alpilab-ai\build\release\.env
C:\Users\MichaelLab\Desktop\Alpilab-ai\build\release\ALPILAB AI.exe
```

### Sviluppo (codice sorgente)

Metti il file nella **root del repository**:

```
C:\Users\MichaelLab\Desktop\Alpilab-ai\.env
```

### Ordine di ricerca

1. Path in `ALPILAB_ENV_FILE` (se impostata)
2. Cartella dell'eseguibile (solo EXE)
3. Cartella di lavoro corrente
4. Root del progetto (solo in dev)

**Il `.env` non è incluso nell'EXE** per sicurezza: resta un file esterno che puoi modificare senza ricompilare.

---

## Creare `.env` su Windows (senza `.env.txt`)

1. Copia `.env.example` nella cartella corretta e rinominalo in `.env`
2. Oppure in PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

3. In Blocco Note: **Salva con nome** → nome file `.env` → Tipo: **Tutti i file (*.*)**  
   Se salvi come "Documento di testo", otterrai `.env.txt` che **non funziona**.

---

## Chiavi supportate

| Variabile | Provider | Obbligatoria? | Note |
|-----------|----------|---------------|------|
| `OPENAI_API_KEY` | OpenAI (GPT) | No* | Prefisso `sk-`. Serve **credito API** separato da ChatGPT Plus |
| `ANTHROPIC_API_KEY` | Claude | No* | Prefisso `sk-ant-` |
| `GOOGLE_API_KEY` | Gemini | No | Prefisso `AIza` |
| `PERPLEXITY_API_KEY` | Perplexity | No | Prefisso `pplx-` |
| `ALPILAB_OLLAMA_URL` | Ollama locale | No | Default `http://127.0.0.1:11434` |

\* Serve **almeno una** tra chiave cloud **oppure** Ollama con modello scaricato.

### Dove ottenere le chiavi

- **OpenAI:** https://platform.openai.com/api-keys  
- **Anthropic:** https://console.anthropic.com/  
- **Google AI:** https://aistudio.google.com/apikey  
- **Perplexity:** https://www.perplexity.ai/settings/api  

> **ChatGPT Plus ≠ API OpenAI.** L'abbonamento ChatGPT non abilita automaticamente le chiamate API: serve un account con fatturazione/credito API.

---

## Ollama (AI locale gratuita)

1. Installa Ollama da https://ollama.com  
2. Scarica il modello usato da ALPILAB:

```powershell
ollama pull llama3.2
```

3. Verifica:

```powershell
ollama list
```

Deve comparire `llama3.2`. Ollama di solito resta in background (icona nella system tray).

---

## Verificare la configurazione

### Script da terminale (sola lettura)

```powershell
cd C:\Users\MichaelLab\Desktop\Alpilab-ai
python scripts\check_api_keys.py
```

Solo presenza/forma chiavi, senza chiamate:

```powershell
python scripts\check_api_keys.py --offline
```

### API (con ALPILAB avviato)

Apri nel browser o con curl:

```
http://127.0.0.1:8000/api/v1/ai/providers/status
```

Controlla il blocco `config` (`env_file_loaded`, `env_file_searched`) e per ogni provider: `key_present`, `key_shape_valid`, `available`, `error_kind`.

---

## Errori frequenti

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| Brain usa solo Ollama | Nessuna chiave cloud nel `.env` letto | Metti `.env` accanto all'EXE e riavvia |
| `.env` ignorato | File salvato come `.env.txt` | Rinomina e usa "Tutti i file" in Salva con nome |
| Chiave "presente" ma rifiutata | Virgolette, spazi, chiave troncata | `OPENAI_API_KEY=sk-...` senza `"` intorno |
| Riga vuota `KEY=` | Equivalente a chiave assente | Rimuovi la riga o inserisci il valore |
| Ollama non risponde | Servizio spento | Avvia Ollama |
| `model_missing` | Modello non scaricato | `ollama pull llama3.2` |
| `no_credit` | Quota/credito esaurito | Ricarica billing del provider |

---

## Dopo ogni modifica al `.env`

**Riavvia ALPILAB AI.exe** (o il Local Hub in dev) per ricaricare le variabili.
