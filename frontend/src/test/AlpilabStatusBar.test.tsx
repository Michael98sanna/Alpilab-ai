import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AlpilabStatusBar } from "../components/core/AlpilabStatusBar";
import type { CoreState } from "../types";

describe("AlpilabStatusBar", () => {
  it("shows ALPILAB AI when IDLE", () => {
    render(<AlpilabStatusBar state="IDLE" />);
    expect(screen.getByTestId("core-status-label")).toHaveTextContent("ALPILAB AI");
  });

  it.each<[CoreState, string]>([
    ["LISTENING", "STO ASCOLTANDO..."],
    ["THINKING", "STO PENSANDO..."],
    ["SPEAKING", "STO PARLANDO..."],
    ["WORKING", "STO LAVORANDO..."],
    ["WARNING", "ATTENZIONE"],
    ["ERROR", "SI È VERIFICATO UN ERRORE"],
  ])("shows %s label as %s", (state, label) => {
    render(<AlpilabStatusBar state={state} />);
    expect(screen.getByTestId("core-status-label")).toHaveTextContent(label);
  });

  it("is visually centered", () => {
    render(<AlpilabStatusBar state="IDLE" />);
    expect(screen.getByTestId("core-status-center")).toBeInTheDocument();
  });
});
