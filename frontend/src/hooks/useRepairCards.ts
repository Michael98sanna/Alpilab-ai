import { useCallback, useEffect, useState } from "react";
import { brainChat } from "../api/aiBrain";
import {
  fetchActiveDiagnosticCards,
  fetchDiagnosticCard,
  type DiagnosticCard,
} from "../api/diagnosticCards";
import type { ChatMessage, MessageRole } from "../types";

function createMessageId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function formatMessageTime(value: Date = new Date()): string {
  return value.toLocaleTimeString("it-IT", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

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
      setCards(nextCards ?? []);
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
      return data.conversation;
    } catch (error) {
      console.error("Failed to load card conversation:", error);
      return null;
    }
  }, []);

  const sendCardMessage = useCallback(
    async (cardId: string, text: string) => {
      const trimmed = text.trim();
      if (!trimmed) {
        return { ok: false as const, error: "Messaggio vuoto" };
      }

      const optimisticUser: ChatMessage = {
        id: createMessageId(),
        role: "user",
        content: trimmed,
        timestamp: formatMessageTime(),
      };
      setCardMessages((current) => [...current, optimisticUser]);

      try {
        const response = await brainChat(cardId, trimmed);
        const conversation = await loadCardMessages(cardId);
        if (!conversation || conversation.length === 0) {
          setCardMessages((current) => {
            const withoutPending = current.filter((message) => message.id !== optimisticUser.id);
            return [
              ...withoutPending,
              optimisticUser,
              {
                id: createMessageId(),
                role: "assistant",
                content: response.content,
                timestamp: formatMessageTime(),
              },
            ];
          });
        }
        return { ok: true as const };
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Invio messaggio non riuscito";
        setCardMessages((current) => [
          ...current,
          {
            id: createMessageId(),
            role: "assistant",
            content: `Non sono riuscito a elaborare il messaggio (${message}). Verifica che ALPILAB Brain sia disponibile e riprova.`,
            timestamp: formatMessageTime(),
          },
        ]);
        return { ok: false as const, error: message };
      }
    },
    [loadCardMessages],
  );

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
    sendCardMessage,
    refreshCardMessages: () => {
      if (activeCardId) {
        void loadCardMessages(activeCardId);
      }
    },
  };
}
