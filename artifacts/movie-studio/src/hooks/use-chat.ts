import { useRef, useEffect, useCallback } from "react";
import { useChatStore } from "../stores/appStore";
import { chatApi } from "../lib/api";
import type { ChatMessage } from "../lib/types";

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

    try {
      await chatApi.streamChat(query, sessionId, abortControllerRef.current.signal, {
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
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") {
        updateMessage(assistantId, { content: fullContent + "\n\n**Error:** Communication failed." });
      }
    } finally {
      setStreaming(false);
    }
  }, [isStreaming, sessionId, addMessage, updateMessage, setSessionId, setStreaming]);

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    setStreaming(false);
  }, [setStreaming]);

  return { messages, isStreaming, sendMessage, stopGeneration };
}
