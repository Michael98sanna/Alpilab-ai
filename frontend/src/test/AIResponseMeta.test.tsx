import { render, screen } from "@testing-library/react";

import { describe, expect, it } from "vitest";

import { AIResponseMeta } from "../components/ai/AIResponseMeta";



describe("AIResponseMeta", () => {

  it("does not show local badge in hash kb mode", () => {

    render(

      <AIResponseMeta

        source="local_kb"

        provider="local_kb"

        confidence={0.9}

        kbMode="hash"

      />,

    );

    expect(screen.queryByText(/da conoscenza locale/i)).not.toBeInTheDocument();

    expect(screen.getByText(/online/i)).toBeInTheDocument();

  });



  it("shows local badge only in semantic kb mode", () => {

    render(

      <AIResponseMeta

        source="local_kb"

        provider="local_kb"

        confidence={0.9}

        kbMode="semantic"

      />,

    );

    expect(screen.getByText(/da conoscenza locale/i)).toBeInTheDocument();

  });



  it("shows local model badge for Ollama responses", () => {
    render(
      <AIResponseMeta
        source="online"
        provider="ollama"
        confidence={0.45}
        localModel
      />,
    );
    expect(screen.getByTestId("local-model-badge")).toHaveTextContent(
      /modello locale/i,
    );
  });

  it("shows override badge when validation overridden", () => {
    render(
      <AIResponseMeta
        source="online"
        provider="gpt4"
        confidence={0.8}
        kbMode="semantic"
        validation={{ performed: true, agreed: false, overridden: true }}
      />,
    );
    expect(screen.getByTestId("validation-override-badge")).toHaveTextContent(
      /caso locale corretto online/i,
    );
  });
});

