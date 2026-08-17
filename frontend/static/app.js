const statusEl = document.getElementById("status");
const questionEl = document.getElementById("question");
const answerEl = document.getElementById("answer");
const askBtn = document.getElementById("ask");

async function loadHealth() {
  try {
    const response = await fetch("/api/v1/health");
    if (!response.ok) {
      throw new Error("health " + response.status);
    }
    const data = await response.json();
    statusEl.dataset.state = "ok";
    statusEl.textContent = `${data.service} · ${data.phase} · ${data.provider}`;
  } catch (error) {
    statusEl.dataset.state = "error";
    statusEl.textContent = "API non raggiungibile";
  }
}

async function askAssistant() {
  const question = questionEl.value.trim();
  if (!question) {
    return;
  }

  askBtn.disabled = true;
  answerEl.hidden = false;
  answerEl.textContent = "Richiesta in corso…";

  try {
    const response = await fetch("/api/v1/assistant/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!response.ok) {
      throw new Error("ask " + response.status);
    }
    const data = await response.json();
    answerEl.textContent = data.text;
  } catch (error) {
    answerEl.textContent = "Errore di rete o API. Verifica che il server sia avviato.";
  } finally {
    askBtn.disabled = false;
  }
}

askBtn.addEventListener("click", askAssistant);
questionEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
    askAssistant();
  }
});

loadHealth();
