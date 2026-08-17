/**
 * Future API client — not used by UI V0.1 (mock data only).
 */

const DEFAULT_BASE_URL = "";

export class AlpilabApiClient {
  private baseUrl: string;

  constructor(baseUrl = DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async getHealth(): Promise<Record<string, unknown>> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return response.json();
  }

  async generateText(prompt: string): Promise<Record<string, unknown>> {
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
