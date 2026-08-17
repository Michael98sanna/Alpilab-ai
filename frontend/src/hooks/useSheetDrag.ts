import { useCallback, useRef, useState } from "react";

const DISMISS_THRESHOLD = 80;

export function useSheetDrag(onClose: () => void) {
  const [dragY, setDragY] = useState(0);
  const [dragging, setDragging] = useState(false);
  const startYRef = useRef(0);
  const draggingRef = useRef(false);

  const beginDrag = useCallback((clientY: number) => {
    startYRef.current = clientY;
    draggingRef.current = true;
    setDragging(true);
  }, []);

  const updateDrag = useCallback((clientY: number) => {
    if (!draggingRef.current) return;
    const dy = Math.max(0, clientY - startYRef.current);
    setDragY(dy);
  }, []);

  const finishDrag = useCallback(
    (clientY: number) => {
      if (!draggingRef.current) return;
      const dy = Math.max(0, clientY - startYRef.current);
      draggingRef.current = false;
      setDragging(false);
      setDragY(0);
      if (dy >= DISMISS_THRESHOLD) {
        onClose();
      }
    },
    [onClose],
  );

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (typeof e.button === "number" && e.button !== 0) return;
      beginDrag(e.clientY);
      e.currentTarget.setPointerCapture?.(e.pointerId);
    },
    [beginDrag],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      updateDrag(e.clientY);
    },
    [updateDrag],
  );

  const onPointerUp = useCallback(
    (e: React.PointerEvent) => {
      finishDrag(e.clientY);
    },
    [finishDrag],
  );

  const onTouchStart = useCallback(
    (e: React.TouchEvent) => {
      e.stopPropagation();
      const touch = e.touches[0];
      if (!touch) return;
      beginDrag(touch.clientY);
    },
    [beginDrag],
  );

  const onTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (!draggingRef.current) return;
      e.stopPropagation();
      const touch = e.touches[0];
      if (!touch) return;
      updateDrag(touch.clientY);
    },
    [updateDrag],
  );

  const onTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      e.stopPropagation();
      const touch = e.changedTouches[0];
      if (!touch) return;
      finishDrag(touch.clientY);
    },
    [finishDrag],
  );

  return {
    dragY,
    dragging,
    dismissThreshold: DISMISS_THRESHOLD,
    handlers: {
      onPointerDown,
      onPointerMove,
      onPointerUp,
      onPointerCancel: onPointerUp,
      onTouchStart,
      onTouchMove,
      onTouchEnd,
    },
  };
}
