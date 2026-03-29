import { useRef, useEffect, useCallback } from "react";
import { useChatStore } from "../stores/appStore";
import { chatApi } from "../lib/api";
import type { ChatMessage } from "../lib/types";

const MAX_RETRIES = 5;
const RETRY_DELAY_MS = 8000;

export function useChatStream() {
  const { messages, isStreaming, sessionId, addMessage, updateMessage, setSessionId, setStreaming } = useChatStore();
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const sendMessage = useCallback(async (query: string) => {
    if (isStreaming || !query.trim()) return;

    abortControllerRef.current = new AbortController();
    setStreaming(true);

    const userMsg: ChatMessage = { id: Date.now().toString(), role: "user", content: query };
    const assistantId = (Date.now() + 1).toString();

    addMessage(userMsg);
    addMessage({ id: assistantId, role: "assistant", content: "" });

    let fullContent = "";
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
      if (abortControllerRef.current?.signal.aborted) break;

      if (attempt > 0) {
        updateMessage(assistantId, {
          content: `Backend is starting up... retrying in a few seconds (attempt ${attempt}/${MAX_RETRIES})`,
        });
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
        if (abortControllerRef.current?.signal.aborted) break;
        fullContent = "";
      }

      try {
        await chatApi.streamChat(query, sessionId, abortControllerRef.current!.signal, {
          onStart: (data) => {
            if (data.session_id) setSessionId(data.session_id);
          },
          onContent: (content) => {
            fullContent += content;
            updateMessage(assistantId, { content: fullContent });
          },
          onMetadata: (data) => {
            updateMessage(assistantId, {
              citations: data.citations,
              queryType: data.query_type,
              routeType: data.route_type,
              traceId: data.trace_id,
              latency: data.latency_ms,
            });
          },
        });
        lastError = null;
        break;
      } catch (err: unknown) {
        if (err instanceof Error && err.name === "AbortError") break;
        lastError = err instanceof Error ? err : new Error(String(err));
        const isStartingUp =
          lastError.message.includes("503") ||
          lastError.message.includes("starting up") ||
          lastError.message.includes("Failed to fetch");
        if (!isStartingUp || attempt >= MAX_RETRIES) break;
      }
    }

    if (lastError && lastError.name !== "AbortError") {
      updateMessage(assistantId, {
        content:
          fullContent +
          "\n\n**Error:** The server may still be starting up. Please wait a moment and try again.",
      });
    }

    setStreaming(false);
  }, [isStreaming, sessionId, addMessage, updateMessage, setSessionId, setStreaming]);

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    setStreaming(false);
  }, [setStreaming]);

  return { messages, isStreaming, sendMessage, stopGeneration };
}
