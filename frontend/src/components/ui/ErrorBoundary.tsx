import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Alpilab UI error", error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div
          style={{
            minHeight: "100dvh",
            padding: "1.5rem",
            background: "#0a0e17",
            color: "#e8edf5",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <h1 style={{ fontSize: "1.1rem" }}>Alpilab AI — errore interfaccia</h1>
          <p style={{ color: "#94a3b8" }}>{this.state.error.message}</p>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.8rem" }}>
            {this.state.error.stack}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}
