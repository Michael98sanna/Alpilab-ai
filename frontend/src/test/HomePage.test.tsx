import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { UserEvent } from "@testing-library/user-event";
import { HomePage } from "../pages/HomePage";
import { OfflineQueueProvider } from "../hooks/useOfflineQueue";
import { RealtimeProvider } from "../realtime/RealtimeProvider";
import * as toolsApi from "../api/tools";

vi.mock("../config/env", () => ({
  getAppMode: () => "mock",
  getSessionIdFromUrl: () => null,
  getApiBaseUrl: () => "http://127.0.0.1:8000",
  getWsBaseUrl: () => "ws://127.0.0.1:8000",
  isLoopbackHost: () => true,
}));

function renderHome() {
  return render(
    <OfflineQueueProvider>
      <RealtimeProvider>
        <HomePage />
      </RealtimeProvider>
    </OfflineQueueProvider>,
  );
}

async function loadDemoScenario(user: UserEvent) {
  await user.click(screen.getByRole("button", { name: /Demo scenario/i }));
}

async function startRepairFromChat(user: UserEvent) {
  const input = screen.getByLabelText("Messaggio");
  await user.type(input, "iPhone 14 Pro");
  await user.click(screen.getByLabelText("Invia messaggio"));
}

describe("HomePage V0.7 layout", () => {
  it("renders header, section nav, sidebar and empty workspace at startup", () => {
    renderHome();
    expect(screen.getByRole("banner")).toHaveTextContent("ALPILAB AI");
    expect(screen.getByTestId("main-section-nav")).toBeInTheDocument();
    expect(screen.getByTestId("section-chat")).toBeInTheDocument();
    expect(screen.getByTestId("section-diagnostics")).toBeInTheDocument();
    expect(screen.getByTestId("section-programs")).toBeInTheDocument();
    expect(screen.getByTestId("repair-cards-sidebar")).toBeInTheDocument();
    expect(screen.getByTestId("add-device-btn")).toBeInTheDocument();
    expect(screen.getByTestId("empty-workspace")).toBeInTheDocument();
    expect(screen.queryByTestId("chat-timeline")).not.toBeInTheDocument();
  });

  it("shows centered sticky core above input after repair starts", async () => {
    const user = userEvent.setup();
    renderHome();
    await startRepairFromChat(user);
    expect(screen.getByTestId("alpilab-status-bar")).toBeInTheDocument();
    await waitFor(
      () => {
        expect(screen.getByTestId("core-status-label")).toHaveTextContent("ALPILAB AI");
      },
      { timeout: 2000 },
    );
  });

  it("keeps section nav above composer in bottom chrome", async () => {
    const user = userEvent.setup();
    renderHome();
    await startRepairFromChat(user);
    const chrome = screen.getByTestId("bottom-chrome");
    const chromeKids = Array.from(chrome.children);
    const navIdx = chromeKids.findIndex(
      (el) => el.getAttribute("data-testid") === "main-section-nav",
    );
    const inputIdx = chromeKids.findIndex((el) =>
      el.querySelector?.('[data-testid="chat-composer"]'),
    );
    expect(navIdx).toBe(0);
    expect(inputIdx).toBeGreaterThan(navIdx);

    const chatColumn = screen.getByTestId("chat-section")
      .firstElementChild as HTMLElement;
    expect(
      chatColumn.querySelector('[data-testid="alpilab-status-bar"]'),
    ).toBeTruthy();
    expect(
      chatColumn.querySelector('[data-testid="chat-composer"]'),
    ).toBeNull();
  });

  it("opens pairing dialog from Collega dispositivo", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByTestId("pair-device"));
    expect(screen.getByTestId("pairing-dialog")).toBeInTheDocument();
  });
});

describe("HomePage V0.7 sections", () => {
  it("opens Diagnosi section with diagnostic panel", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByTestId("section-diagnostics"));
    expect(screen.getByTestId("diagnostics-section")).toBeInTheDocument();
    expect(screen.getByTestId("diagnostics-expanded")).toBeInTheDocument();
  });

  it("opens Programmi with operational and future entries", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByTestId("section-programs"));
    expect(screen.getByTestId("programs-panel")).toBeInTheDocument();
    expect(screen.getByTestId("program-3utools")).toHaveAttribute(
      "data-status",
      "operational",
    );
    expect(screen.getByTestId("program-alpilab_check")).toHaveAttribute(
      "data-status",
      "operational",
    );
    expect(screen.getByTestId("program-action-alpilab_check")).toHaveTextContent(
      "Apri",
    );
    expect(screen.getByTestId("program-thermal_camera")).toHaveAttribute(
      "data-status",
      "operational",
    );
    expect(screen.getByTestId("program-microscope")).toHaveAttribute(
      "data-status",
      "operational",
    );
    expect(screen.getByTestId("program-borneo")).toHaveAttribute(
      "data-status",
      "operational",
    );
    expect(screen.getByTestId("program-zxw")).toHaveAttribute("data-status", "future");
  });

  it("does not execute the termocamera in mock mode", async () => {
    const user = userEvent.setup();
    const spy = vi.spyOn(toolsApi, "executeRegisteredTool");
    renderHome();
    await user.click(screen.getByTestId("section-programs"));
    await user.click(screen.getByTestId("program-action-thermal_camera"));
    expect(screen.getByTestId("program-feedback-thermal_camera")).toHaveTextContent(
      /realtime|PC Agent/i,
    );
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it("Alpilab Check Apri does not navigate to chat in mock mode", async () => {
    const user = userEvent.setup();
    const spy = vi.spyOn(toolsApi, "executeRegisteredTool");
    renderHome();
    await user.click(screen.getByTestId("section-programs"));
    expect(screen.getByTestId("program-action-alpilab_check")).toHaveTextContent(
      "Apri",
    );
    await user.click(screen.getByTestId("program-action-alpilab_check"));
    expect(screen.getByTestId("programs-section")).toBeInTheDocument();
    expect(screen.queryByTestId("chat-section")).not.toBeInTheDocument();
    expect(await screen.findByTestId("program-feedback-alpilab_check")).toHaveTextContent(
      /realtime|PC Agent/i,
    );
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it("does not execute 3uTools in mock mode (no false success)", async () => {
    const user = userEvent.setup();
    const spy = vi.spyOn(toolsApi, "executeRegisteredTool");
    renderHome();
    await user.click(screen.getByTestId("section-programs"));
    await user.click(screen.getByTestId("program-action-3utools"));
    expect(await screen.findByTestId("program-feedback-3utools")).toHaveTextContent(
      /realtime|PC Agent/i,
    );
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });
});

describe("HomePage V0.7 core states", () => {
  it("shows STO PENSANDO... while processing a message", async () => {
    const user = userEvent.setup();
    renderHome();
    await loadDemoScenario(user);
    const input = screen.getByLabelText("Messaggio");
    await user.type(input, "Test stato");
    await user.click(screen.getByLabelText("Invia messaggio"));
    expect(screen.getByTestId("core-status-label")).toHaveTextContent("STO PENSANDO...");
  });

  it("returns to ALPILAB AI after response", async () => {
    const user = userEvent.setup();
    renderHome();
    await loadDemoScenario(user);
    const input = screen.getByLabelText("Messaggio");
    await user.type(input, "Test stato");
    await user.click(screen.getByLabelText("Invia messaggio"));
    await waitFor(
      () => {
        expect(screen.getByTestId("core-status-label")).toHaveTextContent("ALPILAB AI");
      },
      { timeout: 2000 },
    );
  });
});

describe("HomePage V0.7 interactions", () => {
  it("allows sending a chat message", async () => {
    const user = userEvent.setup();
    renderHome();
    await loadDemoScenario(user);
    const input = screen.getByLabelText("Messaggio");
    await user.type(input, "Test messaggio mock");
    await user.click(screen.getByLabelText("Invia messaggio"));
    expect(screen.getByText("Test messaggio mock")).toBeInTheDocument();
  });
});

describe("HomePage desktop layout", () => {
  const originalMatchMedia = window.matchMedia;

  beforeEach(() => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes("1024px"),
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
  });

  it("keeps core centered in chat column", async () => {
    const user = userEvent.setup();
    renderHome();
    await startRepairFromChat(user);
    expect(screen.getByTestId("core-status-center")).toBeInTheDocument();
  });

  it("shows diagnostic panel via section nav after demo load", async () => {
    const user = userEvent.setup();
    renderHome();
    await loadDemoScenario(user);
    await user.click(screen.getByTestId("section-diagnostics"));
    expect(screen.getByTestId("diagnostics-expanded")).toBeInTheDocument();
  });
});
