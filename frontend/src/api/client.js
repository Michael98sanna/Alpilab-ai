/**
 * API client stub for future Alpilab AI backend.
 * Designed for web, tablet, and mobile clients (future PWA).
 */

const DEFAULT_BASE_URL = "";

export class AlpilabApiClient {
  constructor(baseUrl = DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async getHealth() {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return response.json();
  }

  async generateText(prompt) {
    const response = await fetch(`${this.baseUrl}/api/v1/ai/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    if (!response.ok) {
      throw new Error(`AI generate failed: ${response.status}`);
    }
    return response.json();
  }
}
