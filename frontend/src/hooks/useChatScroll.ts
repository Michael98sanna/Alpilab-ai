import { useCallback, useEffect, useRef, useState } from "react";

const BOTTOM_THRESHOLD = 80;

export function useChatScroll(itemCount: number) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [showNewMessages, setShowNewMessages] = useState(false);
  const userScrolledUpRef = useRef(false);

  const isNearBottom = useCallback(() => {
    const el = containerRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < BOTTOM_THRESHOLD;
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    const el = containerRef.current;
    if (!el) return;
    if (typeof el.scrollTo === "function") {
      el.scrollTo({ top: el.scrollHeight, behavior });
    } else {
      el.scrollTop = el.scrollHeight;
    }
    setShowNewMessages(false);
    userScrolledUpRef.current = false;
  }, []);

  useEffect(() => {
    if (isNearBottom() || !userScrolledUpRef.current) {
      scrollToBottom("auto");
    } else {
      setShowNewMessages(true);
    }
  }, [itemCount, isNearBottom, scrollToBottom]);

  const onScroll = useCallback(() => {
    if (isNearBottom()) {
      userScrolledUpRef.current = false;
      setShowNewMessages(false);
    } else {
      userScrolledUpRef.current = true;
    }
  }, [isNearBottom]);

  return {
    containerRef,
    showNewMessages,
    scrollToBottom,
    onScroll,
  };
}
