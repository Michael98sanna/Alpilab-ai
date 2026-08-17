import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HomePage } from "../pages/HomePage";

describe("HomePage V0.2", () => {
  it("renders header and chat timeline", () => {
    render(<HomePage />);
    expect(screen.getByRole("banner")).toHaveTextContent("ALPILAB AI");
    expect(screen.getByTestId("chat-timeline")).toBeInTheDocument();
  });

  it("shows assistant status in timeline not as sticky core", () => {
    render(<HomePage />);
    const timeline = screen.getByTestId("chat-timeline");
    const statuses = within(timeline).getAllByTestId("assistant-status");
    expect(statuses.length).toBeGreaterThan(0);
    expect(screen.queryByText("Alpilab")).not.toBeInTheDocument();
  });

  it("shows compact repair context banner", () => {
    render(<HomePage />);
    const ctx = screen.getByTestId("repair-context");
    expect(within(ctx).getByText("iPhone 13 Pro")).toBeInTheDocument();
    expect(within(ctx).getByText("No Power")).toBeInTheDocument();
  });

  it("shows collapsed diagnostics by default on mobile", () => {
    render(<HomePage />);
    expect(screen.getByTestId("diagnostics-collapsed")).toBeInTheDocument();
  });

  it("shows session devices compact chip in header", () => {
    render(<HomePage />);
    expect(screen.getByTestId("session-devices-chip")).toBeInTheDocument();
  });

  it("shows mock conversation messages", () => {
    render(<HomePage />);
    const timeline = screen.getByTestId("chat-timeline");
    expect(within(timeline).getByText(/Dimmi cosa dobbiamo riparare/)).toBeInTheDocument();
    expect(within(timeline).getByText("3.81 V")).toBeInTheDocument();
  });
});

describe("HomePage V0.2 interactions", () => {
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

  it("expands diagnostics panel on mobile", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    await user.click(screen.getByText("Apri diagnosi"));
    expect(screen.getByTestId("diagnostics-expanded")).toBeInTheDocument();
  });

  it("updates diagnostic test on measurement submit", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    await user.click(screen.getByText("Apri diagnosi"));
    const measureInput = screen.getByLabelText("Valore misura");
    await user.clear(measureInput);
    await user.type(measureInput, "0.00");
    await user.click(screen.getByText("Inserisci"));
    const panel = screen.getByTestId("diagnostics-expanded");
    expect(within(panel).getByText(/0\.00/)).toBeInTheDocument();
  });

  it("opens tools sheet on mobile", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    await user.click(screen.getByLabelText("Apri strumenti"));
    expect(screen.getByLabelText("Microscope")).toBeInTheDocument();
  });

  it("toggles session devices panel", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    const chip = screen.getByTestId("session-devices-chip");
    await user.click(chip);
    expect(screen.getAllByText(/online/).length).toBeGreaterThanOrEqual(2);
  });

  it("chat input is accessible", () => {
    render(<HomePage />);
    expect(screen.getByLabelText("Messaggio")).toBeInTheDocument();
    expect(screen.getByLabelText("Microfono")).toBeInTheDocument();
    expect(screen.getByLabelText("Invia messaggio")).toBeInTheDocument();
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

  it("shows context panel on wide viewport", () => {
    render(<HomePage />);
    expect(screen.getByLabelText("Pannello contesto")).toBeInTheDocument();
  });
});
