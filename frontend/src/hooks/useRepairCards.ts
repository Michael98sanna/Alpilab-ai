import { useCallback, useEffect, useState } from "react";
import {
  fetchActiveDiagnosticCards,
  fetchDiagnosticCard,
  type DiagnosticCard,
} from "../api/diagnosticCards";
import type { ChatMessage, MessageRole } from "../types";

function mapConversationToChatMessages(
  cardId: string,
  conversation: Array<{ role: string; content: string; timestamp: string }>,
): ChatMessage[] {
  return conversation.map((message, index) => ({
    id: `${cardId}-${index}-${message.timestamp}`,
    role: message.role as MessageRole,
    content: message.content,
    timestamp: new Date(message.timestamp).toLocaleTimeString("it-IT", {
      hour: "2-digit",
      minute: "2-digit",
    }),
  }));
}

export function useRepairCards(sessionId: string, activeCardId: string | null) {
  const [cards, setCards] = useState<DiagnosticCard[]>([]);
  const [cardMessages, setCardMessages] = useState<ChatMessage[]>([]);
  const [loadingCards, setLoadingCards] = useState(false);

  const loadCards = useCallback(async () => {
    setLoadingCards(true);
    try {
      const nextCards = await fetchActiveDiagnosticCards(sessionId);
      setCards(nextCards);
      return nextCards;
    } catch (error) {
      console.error("Failed to load repair cards:", error);
      return [];
    } finally {
      setLoadingCards(false);
    }
  }, [sessionId]);

  const loadCardMessages = useCallback(async (cardId: string) => {
    try {
      const data = await fetchDiagnosticCard(cardId);
      setCardMessages(mapConversationToChatMessages(cardId, data.conversation));
    } catch (error) {
      console.error("Failed to load card conversation:", error);
      setCardMessages([]);
    }
  }, []);

  useEffect(() => {
    void loadCards();
    const timer = window.setInterval(() => {
      void loadCards();
    }, 15000);
    return () => window.clearInterval(timer);
  }, [loadCards]);

  useEffect(() => {
    if (!activeCardId) {
      setCardMessages([]);
      return;
    }
    void loadCardMessages(activeCardId);
  }, [activeCardId, loadCardMessages]);

  return {
    cards,
    cardMessages,
    loadingCards,
    loadCards,
    loadCardMessages,
    refreshCardMessages: () => {
      if (activeCardId) {
        void loadCardMessages(activeCardId);
      }
    },
  };
}
