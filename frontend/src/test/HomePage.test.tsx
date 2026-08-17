import { describe, it, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HomePage } from "../pages/HomePage";

describe("HomePage", () => {
  it("renders home with brand and core", () => {
    render(<HomePage />);
    expect(screen.getByText("ALPILAB AI")).toBeInTheDocument();
    expect(screen.getByText("Alpilab")).toBeInTheDocument();
    expect(screen.getByText("Nuova riparazione")).toBeInTheDocument();
  });

  it("shows mock scenario repair info", () => {
    render(<HomePage />);
    const banner = screen.getByLabelText("Riparazione attiva");
    expect(within(banner).getByText("iPhone 13 Pro")).toBeInTheDocument();
    expect(within(banner).getByText("No Power")).toBeInTheDocument();
  });

  it("shows diagnostic tests from mock", () => {
    render(<HomePage />);
    expect(screen.getByText("Battery voltage")).toBeInTheDocument();
    expect(screen.getByText("PP_VDD_MAIN")).toBeInTheDocument();
  });
});

describe("HomePage interactions", () => {
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
    render(<HomePage />);
    await user.click(screen.getByText("Nuova riparazione"));
    expect(screen.getAllByText(/Che dispositivo/).length).toBeGreaterThan(0);
  });

  it("updates diagnostic test on measurement submit", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    const measureInput = screen.getByLabelText("Valore misura");
    await user.clear(measureInput);
    await user.type(measureInput, "0.00");
    await user.click(screen.getByText("Inserisci"));
    const panel = screen.getByLabelText("Diagnostica");
    expect(within(panel).getByText(/0\.00/)).toBeInTheDocument();
  });

  it("pauses and resumes diagnosis", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    await user.click(screen.getByText("Pausa diagnosi"));
    const banner = screen.getByLabelText("Riparazione attiva");
    expect(within(banner).getByText("Diagnosis paused")).toBeInTheDocument();
    await user.click(screen.getByText("Continua diagnosi"));
    expect(within(banner).getByText("Diagnosis in progress")).toBeInTheDocument();
  });

  it("opens contextual tools panel", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    const toggle = screen.getByText(/Strumenti|strumenti contestuali/i);
    await user.click(toggle);
    expect(screen.getByLabelText("Microscope")).toBeInTheDocument();
  });
});
