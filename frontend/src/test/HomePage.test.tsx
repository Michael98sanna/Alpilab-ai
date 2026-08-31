import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

describe("HomePage V0.7 layout", () => {
  it("renders header, section nav and chat timeline", () => {
    renderHome();
    expect(screen.getByRole("banner")).toHaveTextContent("ALPILAB AI");
    expect(screen.getByTestId("main-section-nav")).toBeInTheDocument();
    expect(screen.getByTestId("section-chat")).toBeInTheDocument();
    expect(screen.getByTestId("section-diagnostics")).toBeInTheDocument();
    expect(screen.getByTestId("section-programs")).toBeInTheDocument();
    expect(screen.getByTestId("chat-timeline")).toBeInTheDocument();
  });

  it("shows centered sticky core above input", () => {
    renderHome();
    expect(screen.getByTestId("alpilab-status-bar")).toBeInTheDocument();
    expect(screen.getByTestId("core-status-label")).toHaveTextContent("ALPILAB AI");
  });

  it("keeps section nav above composer in bottom chrome", () => {
    renderHome();
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

  it("shows compact repair context banner when scenario loaded", () => {
    renderHome();
    const ctx = screen.getByTestId("repair-context");
    expect(within(ctx).getByText("iPhone 13 Pro")).toBeInTheDocument();
    expect(within(ctx).getByText("No Power")).toBeInTheDocument();
  });

  it("keeps diagnostics section closed by default (chat active)", () => {
    renderHome();
    expect(screen.queryByTestId("diagnostics-section")).not.toBeInTheDocument();
    expect(screen.getByTestId("chat-section")).toBeInTheDocument();
  });

  it("opens pairing dialog from Collega dispositivo", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByTestId("pair-device"));
    expect(screen.getByTestId("pairing-dialog")).toBeInTheDocument();
  });
});

describe("HomePage V0.7 sections", () => {
  it("opens Diagnosi when repair session is active", async () => {
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
      "configured",
    );
    expect(screen.getByTestId("program-microscope")).toHaveAttribute(
      "data-status",
      "configured",
    );
    expect(screen.getByTestId("program-zxw")).toHaveAttribute("data-status", "future");
    expect(screen.getByTestId("program-borneo")).toHaveAttribute(
      "data-status",
      "future",
    );
  });

  it("shows not configured for thermal without executing tools", async () => {
    const user = userEvent.setup();
    const spy = vi.spyOn(toolsApi, "executeRegisteredTool");
    renderHome();
    await user.click(screen.getByTestId("section-programs"));
    await user.click(screen.getByTestId("program-action-thermal_camera"));
    expect(screen.getByTestId("program-feedback-thermal_camera")).toHaveTextContent(
      "Non ancora configurato",
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
    const input = screen.getByLabelText("Messaggio");
    await user.type(input, "Test stato");
    await user.click(screen.getByLabelText("Invia messaggio"));
    expect(screen.getByTestId("core-status-label")).toHaveTextContent("STO PENSANDO...");
  });

  it("returns to ALPILAB AI after response", async () => {
    const user = userEvent.setup();
    renderHome();
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

  it("keeps core centered in chat column", () => {
    renderHome();
    expect(screen.getByTestId("core-status-center")).toBeInTheDocument();
  });

  it("shows diagnostic panel via section nav", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByTestId("section-diagnostics"));
    expect(screen.getByTestId("diagnostics-expanded")).toBeInTheDocument();
  });
});
