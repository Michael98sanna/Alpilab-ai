import { useCallback, useRef, useState } from "react";

export type PanelMode = "none" | "diagnostics" | "tools";

export type SwipeFeedback =
  | "open-diagnostics"
  | "open-tools"
  | "close-diagnostics"
  | "close-tools"
  | null;

const SWIPE_THRESHOLD = 70;
const EDGE_MARGIN = 48;

function isInteractiveTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName.toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "button" || tag === "a") {
    return true;
  }
  return Boolean(
    target.closest("button, a, input, textarea, [data-sheet-drag='true']"),
  );
}

interface UseSwipeGestureOptions {
  enabled: boolean;
  panelMode: PanelMode;
  onOpenDiagnostics: () => void;
  onOpenTools: () => void;
  onCloseDiagnostics: () => void;
  onCloseTools: () => void;
}

function resolveAction(
  deltaX: number,
  deltaY: number,
  panelMode: PanelMode,
  startX: number,
): SwipeFeedback {
  const absX = Math.abs(deltaX);
  const absY = Math.abs(deltaY);

  if (panelMode === "diagnostics") {
    if (absY > absX && deltaY > SWIPE_THRESHOLD) return "close-diagnostics";
    if (absX > absY && deltaX < -SWIPE_THRESHOLD) return "close-diagnostics";
    return null;
  }

  if (panelMode === "tools") {
    if (absY > absX && deltaY > SWIPE_THRESHOLD) return "close-tools";
    if (absX > absY && deltaX > SWIPE_THRESHOLD) return "close-tools";
    return null;
  }

  if (absY >= absX) return null;
  if (absX < SWIPE_THRESHOLD) return null;

  if (deltaX > 0) {
    if (startX <= EDGE_MARGIN || absX > SWIPE_THRESHOLD) return "open-diagnostics";
  }
  if (deltaX < 0) {
    if (startX >= window.innerWidth - EDGE_MARGIN || absX > SWIPE_THRESHOLD) {
      return "open-tools";
    }
  }

  return null;
}

export function useSwipeGesture({
  enabled,
  panelMode,
  onOpenDiagnostics,
  onOpenTools,
  onCloseDiagnostics,
  onCloseTools,
}: UseSwipeGestureOptions) {
  const startRef = useRef<{ x: number; y: number } | null>(null);
  const [feedback, setFeedback] = useState<SwipeFeedback>(null);

  const dispatchAction = useCallback(
    (action: SwipeFeedback) => {
      switch (action) {
        case "open-diagnostics":
          onOpenDiagnostics();
          break;
        case "open-tools":
          onOpenTools();
          break;
        case "close-diagnostics":
          onCloseDiagnostics();
          break;
        case "close-tools":
          onCloseTools();
          break;
      }
    },
    [onOpenDiagnostics, onOpenTools, onCloseDiagnostics, onCloseTools],
  );

  const onTouchStart = useCallback(
    (e: React.TouchEvent) => {
      if (!enabled || isInteractiveTarget(e.target)) return;
      const touch = e.touches[0];
      if (!touch) return;
      startRef.current = { x: touch.clientX, y: touch.clientY };
      setFeedback(null);
    },
    [enabled],
  );

  const onTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (!enabled || !startRef.current) return;
      const touch = e.touches[0];
      if (!touch) return;

      const deltaX = touch.clientX - startRef.current.x;
      const deltaY = touch.clientY - startRef.current.y;
      const action = resolveAction(deltaX, deltaY, panelMode, startRef.current.x);

      if (action && Math.abs(deltaX) > SWIPE_THRESHOLD * 0.35) {
        setFeedback(action);
      } else if (action && Math.abs(deltaY) > SWIPE_THRESHOLD * 0.35) {
        setFeedback(action);
      } else {
        setFeedback(null);
      }
    },
    [enabled, panelMode],
  );

  const onTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      if (!enabled || !startRef.current) {
        startRef.current = null;
        setFeedback(null);
        return;
      }

      const touch = e.changedTouches[0];
      if (!touch) {
        startRef.current = null;
        setFeedback(null);
        return;
      }

      const deltaX = touch.clientX - startRef.current.x;
      const deltaY = touch.clientY - startRef.current.y;
      const startX = startRef.current.x;

      startRef.current = null;
      setFeedback(null);

      const action = resolveAction(deltaX, deltaY, panelMode, startX);
      if (action) dispatchAction(action);
    },
    [enabled, panelMode, dispatchAction],
  );

  return {
    feedback,
    handlers: {
      onTouchStart,
      onTouchMove,
      onTouchEnd,
    },
  };
}
