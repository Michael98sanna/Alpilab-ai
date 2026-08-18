import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, within, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HomePage } from "../pages/HomePage";
import { RealtimeProvider } from "../realtime/RealtimeProvider";

vi.mock("../config/env", () => ({
  getAppMode: () => "mock",
  getSessionIdFromUrl: () => null,
  getApiBaseUrl: () => "http://127.0.0.1:8000",
  getWsBaseUrl: () => "ws://127.0.0.1:8000",
  isLoopbackHost: () => true,
}));

function renderHome() {
  return render(
    <RealtimeProvider>
      <HomePage />
    </RealtimeProvider>,
  );
}

function swipe(
  element: Element,
  start: { x: number; y: number },
  end: { x: number; y: number },
) {
  fireEvent.touchStart(element, {
    touches: [{ clientX: start.x, clientY: start.y }],
  });
  fireEvent.touchMove(element, {
    touches: [{ clientX: end.x, clientY: end.y }],
  });
  fireEvent.touchEnd(element, {
    changedTouches: [{ clientX: end.x, clientY: end.y }],
  });
}

function dragSheetDown(sheetTestId: string, deltaY: number) {
  const dragZone = screen.getByTestId(`${sheetTestId}-drag-zone`);
  const startY = 100;
  const endY = startY + deltaY;
  fireEvent.touchStart(dragZone, {
    touches: [{ clientY: startY, clientX: 200 }],
  });
  fireEvent.touchMove(dragZone, {
    touches: [{ clientY: endY, clientX: 200 }],
  });
  fireEvent.touchEnd(dragZone, {
    changedTouches: [{ clientY: endY, clientX: 200 }],
  });
}

describe("HomePage V0.3.1 layout", () => {
  it("renders header and chat timeline", () => {
    renderHome();
    expect(screen.getByRole("banner")).toHaveTextContent("ALPILAB AI");
    expect(screen.getByTestId("chat-timeline")).toBeInTheDocument();
  });

  it("shows centered sticky core above input, not in timeline", () => {
    renderHome();
    const statusBar = screen.getByTestId("alpilab-status-bar");
    expect(statusBar).toBeInTheDocument();
    expect(screen.getByTestId("core-status-center")).toBeInTheDocument();
    expect(screen.getByTestId("core-status-label")).toHaveTextContent("ALPILAB AI");

    const timeline = screen.getByTestId("chat-timeline");
    expect(within(timeline).queryByTestId("assistant-status")).not.toBeInTheDocument();
  });

  it("shows compact repair context banner", () => {
    renderHome();
    const ctx = screen.getByTestId("repair-context");
    expect(within(ctx).getByText("iPhone 13 Pro")).toBeInTheDocument();
    expect(within(ctx).getByText("No Power")).toBeInTheDocument();
  });

  it("keeps diagnostics closed by default", () => {
    renderHome();
    expect(screen.queryByTestId("diagnostics-expanded")).not.toBeInTheDocument();
    expect(screen.queryByTestId("diagnostics-sheet")).not.toBeInTheDocument();
  });

  it("shows session devices compact chip in header", () => {
    renderHome();
    expect(screen.getByTestId("session-devices-chip")).toBeInTheDocument();
  });
});

describe("HomePage V0.3.1 core states", () => {
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

  it("shows STO ASCOLTANDO... during voice simulation", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByLabelText("Microfono"));
    expect(screen.getByTestId("core-status-label")).toHaveTextContent("STO ASCOLTANDO...");
  });
});

describe("HomePage V0.3.1 interactions", () => {
  it("allows sending a chat message", async () => {
    const user = userEvent.setup();
    renderHome();
    const input = screen.getByLabelText("Messaggio");
    await user.type(input, "Test messaggio mock");
    await user.click(screen.getByLabelText("Invia messaggio"));
    expect(screen.getByText("Test messaggio mock")).toBeInTheDocument();
  });

  it("opens and closes diagnostics via buttons", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByLabelText("Apri diagnosi"));
    expect(screen.getByTestId("diagnostics-sheet")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Chiudi" }));
    expect(screen.queryByTestId("diagnostics-sheet")).not.toBeInTheDocument();
  });

  it("opens tools bottom sheet via tap", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByLabelText("Apri strumenti"));
    expect(screen.getByTestId("tools-sheet")).toBeInTheDocument();
    expect(screen.getByLabelText("Microscope")).toBeInTheDocument();
  });
});

describe("HomePage V0.3.1 gestures", () => {
  const originalMatchMedia = window.matchMedia;
  const originalInnerWidth = window.innerWidth;

  beforeEach(() => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 390,
    });
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: !query.includes("1024px"),
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
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  it("swipe left-to-right opens diagnostics", () => {
    renderHome();
    swipe(screen.getByTestId("chat-swipe-zone"), { x: 10, y: 200 }, { x: 120, y: 205 });
    expect(screen.getByTestId("diagnostics-sheet")).toBeInTheDocument();
  });

  it("swipe right-to-left opens tools", () => {
    renderHome();
    swipe(screen.getByTestId("chat-swipe-zone"), { x: 380, y: 200 }, { x: 260, y: 205 });
    expect(screen.getByTestId("tools-sheet")).toBeInTheDocument();
  });

  it("vertical scroll does not open panels", () => {
    renderHome();
    swipe(screen.getByTestId("chat-swipe-zone"), { x: 200, y: 100 }, { x: 205, y: 280 });
    expect(screen.queryByTestId("diagnostics-sheet")).not.toBeInTheDocument();
    expect(screen.queryByTestId("tools-sheet")).not.toBeInTheDocument();
  });

  it("closes diagnostics with swipe left when open", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByLabelText("Apri diagnosi"));
    swipe(screen.getByTestId("diagnostics-sheet"), { x: 300, y: 400 }, { x: 180, y: 405 });
    expect(screen.queryByTestId("diagnostics-sheet")).not.toBeInTheDocument();
  });

  it("closes diagnostics with swipe down when open", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByLabelText("Apri diagnosi"));
    swipe(screen.getByTestId("diagnostics-sheet"), { x: 200, y: 300 }, { x: 200, y: 420 });
    expect(screen.queryByTestId("diagnostics-sheet")).not.toBeInTheDocument();
  });

  it("closes tools with swipe right when open", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByLabelText("Apri strumenti"));
    swipe(screen.getByTestId("tools-sheet"), { x: 100, y: 400 }, { x: 220, y: 405 });
    expect(screen.queryByTestId("tools-sheet")).not.toBeInTheDocument();
  });

  it("closes tools with swipe down when open", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByLabelText("Apri strumenti"));
    swipe(screen.getByTestId("tools-sheet"), { x: 200, y: 300 }, { x: 200, y: 420 });
    expect(screen.queryByTestId("tools-sheet")).not.toBeInTheDocument();
  });
});

describe("HomePage V0.3.1 sheet drag", () => {
  const originalMatchMedia = window.matchMedia;

  beforeEach(() => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: !query.includes("1024px"),
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

  it("dismisses sheet when drag exceeds threshold", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByLabelText("Apri diagnosi"));
    dragSheetDown("diagnostics-sheet", 120);
    expect(screen.queryByTestId("diagnostics-sheet")).not.toBeInTheDocument();
  });

  it("snaps back when drag is below threshold", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByLabelText("Apri diagnosi"));
    dragSheetDown("diagnostics-sheet", 30);
    expect(screen.getByTestId("diagnostics-sheet")).toBeInTheDocument();
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

  it("shows diagnostic side panel when opened", async () => {
    const user = userEvent.setup();
    renderHome();
    await user.click(screen.getByLabelText("Apri diagnosi"));
    expect(screen.getByTestId("diagnostics-expanded")).toBeInTheDocument();
  });
});
