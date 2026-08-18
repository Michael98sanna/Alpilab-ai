# V0.5.1 — test manuali (installabile, local-first)

Internet **OFF**, Wi-Fi/LAN **ON**. Nessun Cloudflare, ngrok, IP da digitare nel flusso normale.

---

## TEST A — Windows

1. Compila (su PC Windows): `.\scripts\build_windows_exe.ps1`
2. Doppio click `dist\ALPILAB AI.exe` (puoi copiarlo sul Desktop)
3. Si apre la **finestra ALPILAB AI** (non Chrome)
4. Local Hub attivo (log: `%USERPROFILE%\.alpilab\logs\hub.log`)
5. PC Agent **● ONLINE**
6. Sessione `repair-001` (nessun `?session=` da scrivere)
7. Scrivi **Ciao** → risposta locale

Config 3uTools: `%USERPROFILE%\.alpilab\windows_apps.json`  
(non ricompilare l'EXE se cambia il path)

---

## TEST B — Android

1. Su un PC con Flutter: `.\scripts\prepare_android_client.ps1` poi `flutter build apk --debug`
2. Installa `app-debug.apk` sul telefono
3. Stessa Wi-Fi del PC, ALPILAB AI.exe già aperto
4. Apri l'app → cerca **Alpilab Negozio**
5. Sul PC: **Collega dispositivo** → codice 6 cifre
6. Inserisci il codice sul telefono → RepairSession

---

## TEST C — Realtime

- Windows: messaggio **Ciao** → visibile su Android  
- Android: **Test realtime** → visibile su Windows  
Una sola chat, stessa RepairSession.

---

## TEST D — 3uTools

Dal telefono: **Aprimi 3uTools**  
Sul PC si apre 3uTools (o messaggio dry-run se `dry_run: true` nel json locale).  
Risultato visibile su telefono e Windows.

---

## TEST E — Offline

Disattiva Internet, tieni Wi-Fi. Ripeti C + D.

---

## Fallback discovery

Se l'app non trova l'Hub: "Apri ALPILAB AI sul PC e resta sulla stessa Wi-Fi."  
Niente tunnel. Niente IP nel flusso normale.
