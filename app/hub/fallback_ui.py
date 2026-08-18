"""Minimal Hub UI when frontend/dist is not built."""

HUB_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>ALPILAB AI — Local Hub</title>
  <style>
    body { font-family: system-ui, sans-serif; background:#0a0e17; color:#e8edf5;
           margin:0; padding:1.25rem; }
    h1 { font-size:1.2rem; }
    button, input { font: inherit; padding:.5rem .75rem; border-radius:8px; border:0; }
    button { background:#22d3ee; color:#042027; font-weight:600; cursor:pointer; }
    input { width:min(100%, 28rem); background:#151c2c; color:#e8edf5; }
    #log { white-space:pre-wrap; background:#111827; padding:1rem; border-radius:8px;
           min-height:8rem; margin-top:1rem; }
    .muted { color:#94a3b8; }
  </style>
</head>
<body>
  <h1>ALPILAB AI — Local Hub</h1>
  <p class="muted" id="info">Avvio…</p>
  <p>
    <button id="pair">Collega dispositivo</button>
    <span id="code"></span>
  </p>
  <p>
    <input id="msg" placeholder="Scrivi un messaggio…"/>
    <button id="send">Invia</button>
  </p>
  <div id="log"></div>
  <script>
    const session = "repair-001";
    const deviceId = "hub-ui-" + Math.random().toString(16).slice(2, 8);
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = proto + "//" + location.host + "/ws/sessions/" + session
      + "?device_id=" + deviceId + "&device_type=pc&device_name=HubUI";
    const log = (t) => { document.getElementById("log").textContent += t + "\\n"; };
    fetch("/api/v1/hub/info").then(r => r.json()).then(info => {
      document.getElementById("info").textContent =
        info.name + " · " + info.lan_url + " · sessione " + info.default_session_id;
    });
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => log("Connesso al Local Hub");
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === "event" && msg.event && msg.event.event_type === "CHAT_MESSAGE") {
        const p = msg.event.payload || {};
        log((p.role || "") + ": " + (p.content || ""));
      }
    };
    document.getElementById("pair").onclick = async () => {
      const res = await fetch("/api/v1/pairing/start", { method: "POST" });
      const data = await res.json();
      document.getElementById("code").textContent = " Codice: " + data.code;
      log("Pairing avviato. Codice " + data.code);
    };
    document.getElementById("send").onclick = () => {
      const content = document.getElementById("msg").value.trim();
      if (!content || ws.readyState !== 1) return;
      ws.send(JSON.stringify({ type: "chat_message", content, role: "user" }));
      document.getElementById("msg").value = "";
    };
  </script>
</body>
</html>
"""
