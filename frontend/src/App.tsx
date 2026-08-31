import { ErrorBoundary } from "./components/ui/ErrorBoundary";
import { OfflineIndicator } from "./components/OfflineIndicator";
import { OfflineQueueProvider } from "./hooks/useOfflineQueue";
import { RealtimeProvider } from "./realtime/RealtimeProvider";
import { HomePage } from "./pages/HomePage";

export function App() {
  return (
    <ErrorBoundary>
      <OfflineQueueProvider>
        <RealtimeProvider>
          <HomePage />
          <OfflineIndicator />
        </RealtimeProvider>
      </OfflineQueueProvider>
    </ErrorBoundary>
  );
}
