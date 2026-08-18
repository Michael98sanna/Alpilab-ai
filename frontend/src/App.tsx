import { ErrorBoundary } from "./components/ui/ErrorBoundary";
import { RealtimeProvider } from "./realtime/RealtimeProvider";
import { HomePage } from "./pages/HomePage";

export function App() {
  return (
    <ErrorBoundary>
      <RealtimeProvider>
        <HomePage />
      </RealtimeProvider>
    </ErrorBoundary>
  );
}
