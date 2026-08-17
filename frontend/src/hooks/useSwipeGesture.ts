import { useCallback, useRef, useState } from "react";

export type SwipeDirection = "diagnostics" | "tools" | null;

const SWIPE_THRESHOLD = 70;
const EDGE_MARGIN = 48;

function isInteractiveTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName.toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "button" || tag === "a") {
    return true;
  }
  return Boolean(target.closest("button, a, input, textarea, [role='dialog']"));
}

interface UseSwipeGestureOptions {
  enabled: boolean;
  blocked: boolean;
  onSwipeDiagnostics: () => void;
  onSwipeTools: () => void;
}

export function useSwipeGesture({
  enabled,
  blocked,
  onSwipeDiagnostics,
  onSwipeTools,
}: UseSwipeGestureOptions) {
  const startRef = useRef<{ x: number; y: number } | null>(null);
  const [feedback, setFeedback] = useState<SwipeDirection>(null);

  const onTouchStart = useCallback(
    (e: React.TouchEvent) => {
      if (!enabled || blocked || isInteractiveTarget(e.target)) return;
      const touch = e.touches[0];
      if (!touch) return;
      startRef.current = { x: touch.clientX, y: touch.clientY };
      setFeedback(null);
    },
    [enabled, blocked],
  );

  const onTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (!enabled || blocked || !startRef.current) return;
      const touch = e.touches[0];
      if (!touch) return;

      const deltaX = touch.clientX - startRef.current.x;
      const deltaY = touch.clientY - startRef.current.y;

      if (Math.abs(deltaY) >= Math.abs(deltaX)) {
        setFeedback(null);
        return;
      }

      if (Math.abs(deltaX) < SWIPE_THRESHOLD * 0.4) {
        setFeedback(null);
        return;
      }

      if (deltaX > 0 && startRef.current.x <= EDGE_MARGIN) {
        setFeedback("diagnostics");
      } else if (deltaX < 0 && startRef.current.x >= window.innerWidth - EDGE_MARGIN) {
        setFeedback("tools");
      } else if (Math.abs(deltaX) > SWIPE_THRESHOLD * 0.6) {
        setFeedback(deltaX > 0 ? "diagnostics" : "tools");
      }
    },
    [enabled, blocked],
  );

  const onTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      if (!enabled || blocked || !startRef.current) {
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

      startRef.current = null;
      setFeedback(null);

      if (Math.abs(deltaY) >= Math.abs(deltaX)) return;
      if (Math.abs(deltaX) < SWIPE_THRESHOLD) return;

      if (deltaX > 0) {
        onSwipeDiagnostics();
      } else {
        onSwipeTools();
      }
    },
    [enabled, blocked, onSwipeDiagnostics, onSwipeTools],
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
