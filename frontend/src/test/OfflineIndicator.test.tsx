import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { OfflineIndicator } from "../components/OfflineIndicator";
import { OfflineQueueProvider } from "../hooks/useOfflineQueue";

describe("OfflineIndicator", () => {
  beforeEach(() => {
    Object.defineProperty(window.navigator, "onLine", {
      configurable: true,
      value: true,
    });
  });

  it("is hidden when online and queue is empty", () => {
    render(
      <OfflineQueueProvider>
        <OfflineIndicator />
      </OfflineQueueProvider>,
    );

    expect(screen.queryByTestId("offline-indicator")).toBeNull();
  });

  it("shows offline banner when navigator is offline", () => {
    Object.defineProperty(window.navigator, "onLine", {
      configurable: true,
      value: false,
    });

    render(
      <OfflineQueueProvider>
        <OfflineIndicator />
      </OfflineQueueProvider>,
    );

    expect(screen.getByTestId("offline-indicator")).toHaveTextContent(
      "Offline — Sincronizzazione locale",
    );
  });
});
