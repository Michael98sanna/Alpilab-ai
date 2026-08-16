# Alpilab AI

Assistente tecnico AI indipendente da Alpilab Check.

## Obiettivo

Alpilab AI nasce come progetto separato da Alpilab Check. L'obiettivo è creare un assistente per il laboratorio di riparazione smartphone capace di:

- ragionare sui problemi tecnici;
- consultare una knowledge base tecnica;
- utilizzare più motori AI tramite un router comune;
- lavorare anche con modelli locali quando possibile;
- ricevere in futuro dati diagnostici da Alpilab Check senza dipendere dal suo codice;
- conservare uno storico delle riparazioni e usarlo come conoscenza del laboratorio.

## Principio architetturale

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

Alpilab Check rimane un progetto autonomo e operativo al banco. Alpilab AI non deve importare direttamente moduli interni di Alpilab Check: in futuro useremo un contratto dati/API stabile.

## Stato iniziale

Questa repository contiene solo la base architetturale. In questa fase non ci sono ancora API a pagamento, credenziali o dipendenze da un singolo provider.

## Regole del progetto

1. Nessuna API key nel repository.
2. I provider AI devono essere intercambiabili.
3. La logica tecnica non deve dipendere dal provider scelto.
4. Le informazioni provenienti da Alpilab Check devono arrivare tramite un'interfaccia dati separata.
5. Ogni risposta tecnica importante dovrà distinguere fatti, dati rilevati, ipotesi e livello di confidenza.
6. Prima di automatizzare una diagnosi, l'assistente deve proporre controlli verificabili.

## Avvio

```bash
python app.py
```

La prima versione usa un provider locale di test (`mock`) per verificare l'architettura senza configurare servizi esterni.

## Prossimi passi

- definire il modello dati per dispositivi e diagnosi;
- aggiungere il primo vero provider AI;
- introdurre configurazione tramite `.env` senza salvare segreti;
- costruire la knowledge base;
- aggiungere RAG;
- definire il bridge verso Alpilab Check;
- creare l'interfaccia grafica;
- aggiungere storico delle riparazioni;
- introdurre routing tra modelli locali e online.
