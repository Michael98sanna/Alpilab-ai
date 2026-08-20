import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DiagnosticPanel } from "../components/repair/DiagnosticPanel";

describe("DiagnosticPanel V0.7", () => {
  it("shows informative empty state instead of null", () => {
    render(
      <DiagnosticPanel
        tests={[]}
        onSubmitMeasurement={() => undefined}
        onPause={() => undefined}
        onResume={() => undefined}
        isPaused={false}
        showHeader
      />,
    );
    expect(screen.getByTestId("diagnostics-expanded")).toBeInTheDocument();
    expect(screen.getByTestId("diagnostics-empty")).toHaveTextContent(
      "Nessun test diagnostico disponibile",
    );
  });

  it("still lists existing tests", () => {
    render(
      <DiagnosticPanel
        tests={[
          { id: "t1", name: "Battery voltage", value: "3.81 V", status: "PASSED" },
        ]}
        onSubmitMeasurement={() => undefined}
        onPause={() => undefined}
        onResume={() => undefined}
        isPaused={false}
      />,
    );
    expect(screen.getByText(/Battery voltage/)).toBeInTheDocument();
    expect(screen.queryByTestId("diagnostics-empty")).not.toBeInTheDocument();
  });

  it("pause and resume remain available", async () => {
    const user = userEvent.setup();
    const onPause = vi.fn();
    const onResume = vi.fn();
    const { rerender } = render(
      <DiagnosticPanel
        tests={[{ id: "t1", name: "USB", status: "PENDING" }]}
        onSubmitMeasurement={() => undefined}
        onPause={onPause}
        onResume={onResume}
        isPaused={false}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Pausa diagnosi" }));
    expect(onPause).toHaveBeenCalled();
    rerender(
      <DiagnosticPanel
        tests={[{ id: "t1", name: "USB", status: "PENDING" }]}
        onSubmitMeasurement={() => undefined}
        onPause={onPause}
        onResume={onResume}
        isPaused
      />,
    );
    await user.click(screen.getByRole("button", { name: "Continua diagnosi" }));
    expect(onResume).toHaveBeenCalled();
  });
});
