/**
 * Frontend entry point (foundation only).
 * Full UI, routing, and PWA install flow will be added later.
 */

import { AlpilabApiClient } from "./api/client.js";

const statusCard = document.getElementById("status-card");

if (statusCard) {
  statusCard.innerHTML =
    "<p>Client API pronto. Collegamento al backend HTTP in fase successiva.</p>";
}

export { AlpilabApiClient };
