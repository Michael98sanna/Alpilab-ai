import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, within, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HomePage } from "../pages/HomePage";

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

describe("HomePage V0.3 layout", () => {
  it("renders header and chat timeline", () => {
    render(<HomePage />);
    expect(screen.getByRole("banner")).toHaveTextContent("ALPILAB AI");
    expect(screen.getByTestId("chat-timeline")).toBeInTheDocument();
  });

  it("shows sticky compact core above input, not in timeline", () => {
    render(<HomePage />);
    const statusBar = screen.getByTestId("alpilab-status-bar");
    expect(statusBar).toBeInTheDocument();
    expect(statusBar).toHaveTextContent(/ALPILAB AI/);
    expect(statusBar).toHaveTextContent(/Alpilab pronto/);

    const timeline = screen.getByTestId("chat-timeline");
    expect(within(timeline).queryByTestId("assistant-status")).not.toBeInTheDocument();
  });

  it("shows compact repair context banner", () => {
    render(<HomePage />);
    const ctx = screen.getByTestId("repair-context");
    expect(within(ctx).getByText("iPhone 13 Pro")).toBeInTheDocument();
    expect(within(ctx).getByText("No Power")).toBeInTheDocument();
  });

  it("keeps diagnostics closed by default", () => {
    render(<HomePage />);
    expect(screen.queryByTestId("diagnostics-expanded")).not.toBeInTheDocument();
    expect(screen.queryByTestId("diagnostics-sheet")).not.toBeInTheDocument();
  });

  it("shows session devices compact chip in header", () => {
    render(<HomePage />);
    expect(screen.getByTestId("session-devices-chip")).toBeInTheDocument();
  });

  it("shows mock conversation without status messages in timeline", () => {
    render(<HomePage />);
    const timeline = screen.getByTestId("chat-timeline");
    expect(within(timeline).getByText(/Dimmi cosa dobbiamo riparare/)).toBeInTheDocument();
    expect(within(timeline).getByText("3.81 V")).toBeInTheDocument();
    expect(within(timeline).queryByText(/Alpilab sta eseguendo/)).not.toBeInTheDocument();
  });
});

describe("HomePage V0.3 interactions", () => {
  it("allows sending a chat message", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    const input = screen.getByLabelText("Messaggio");
    await user.type(input, "Test messaggio mock");
    await user.click(screen.getByLabelText("Invia messaggio"));
    expect(screen.getByText("Test messaggio mock")).toBeInTheDocument();
  });

  it("starts new repair flow", async () => {
    const user = userEvent.setup();
    render(<HomePage loadScenarioOnInit={false} />);
    await user.click(screen.getByText("Nuova riparazione"));
    expect(screen.getAllByText(/Che dispositivo/).length).toBeGreaterThan(0);
  });

  it("opens diagnostics bottom sheet via tap", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    await user.click(screen.getByLabelText("Apri diagnosi"));
    expect(screen.getByTestId("diagnostics-sheet")).toBeInTheDocument();
    expect(screen.getByTestId("diagnostics-expanded")).toBeInTheDocument();
  });

  it("closes diagnostics sheet", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    await user.click(screen.getByLabelText("Apri diagnosi"));
    await user.click(screen.getByRole("button", { name: "Chiudi" }));
    expect(screen.queryByTestId("diagnostics-sheet")).not.toBeInTheDocument();
  });

  it("opens tools bottom sheet via tap", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    await user.click(screen.getByLabelText("Apri strumenti"));
    expect(screen.getByTestId("tools-sheet")).toBeInTheDocument();
    expect(screen.getByLabelText("Microscope")).toBeInTheDocument();
  });

  it("updates diagnostic test on measurement submit", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    await user.click(screen.getByLabelText("Apri diagnosi"));
    const measureInput = screen.getByLabelText("Valore misura");
    await user.clear(measureInput);
    await user.type(measureInput, "0.00");
    await user.click(screen.getByText("Inserisci"));
    const panel = screen.getByTestId("diagnostics-expanded");
    expect(within(panel).getByText(/0\.00/)).toBeInTheDocument();
  });

  it("toggles session devices panel", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    const chip = screen.getByTestId("session-devices-chip");
    await user.click(chip);
    expect(screen.getAllByText(/online/).length).toBeGreaterThanOrEqual(2);
  });

  it("chat input and status bar are accessible", () => {
    render(<HomePage />);
    expect(screen.getByLabelText("Messaggio")).toBeInTheDocument();
    expect(screen.getByLabelText("Microfono")).toBeInTheDocument();
    expect(screen.getByLabelText("Invia messaggio")).toBeInTheDocument();
    expect(screen.getByTestId("alpilab-status-bar")).toBeInTheDocument();
  });
});

describe("HomePage V0.3 gestures", () => {
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
    render(<HomePage />);
    const zone = screen.getByTestId("chat-swipe-zone");
    swipe(zone, { x: 10, y: 200 }, { x: 120, y: 205 });
    expect(screen.getByTestId("diagnostics-sheet")).toBeInTheDocument();
  });

  it("swipe right-to-left opens tools", () => {
    render(<HomePage />);
    const zone = screen.getByTestId("chat-swipe-zone");
    swipe(zone, { x: 380, y: 200 }, { x: 260, y: 205 });
    expect(screen.getByTestId("tools-sheet")).toBeInTheDocument();
  });

  it("vertical scroll does not open panels", () => {
    render(<HomePage />);
    const zone = screen.getByTestId("chat-swipe-zone");
    swipe(zone, { x: 200, y: 100 }, { x: 205, y: 280 });
    expect(screen.queryByTestId("diagnostics-sheet")).not.toBeInTheDocument();
    expect(screen.queryByTestId("tools-sheet")).not.toBeInTheDocument();
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

  it("shows diagnostic side panel when opened", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    expect(screen.queryByTestId("diagnostics-expanded")).not.toBeInTheDocument();
    await user.click(screen.getByLabelText("Apri diagnosi"));
    expect(screen.getByTestId("diagnostics-expanded")).toBeInTheDocument();
  });

  it("shows tools side panel when opened", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    await user.click(screen.getByLabelText("Apri strumenti"));
    expect(screen.getByTestId("tools-side-panel")).toBeInTheDocument();
  });
});
