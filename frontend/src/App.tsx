import { RealtimeProvider } from "./realtime/RealtimeProvider";
import { HomePage } from "./pages/HomePage";

export function App() {
  return (
    <RealtimeProvider>
      <HomePage />
    </RealtimeProvider>
  );
}
