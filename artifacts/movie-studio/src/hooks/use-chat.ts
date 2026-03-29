import { useRef, useEffect, useCallback } from "react";
import { useChatStore } from "../stores/appStore";
import { chatApi } from "../lib/api";
import { useReadinessStore } from "./useBackendReadiness";
import type { ChatMessage } from "../lib/types";

const MAX_RETRIES = 8;
const BASE_DELAY = 4000;
const MAX_DELAY = 15000;

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

    const readiness = useReadinessStore.getState();
    if (readiness.status !== "ready") {
      const userMsg: ChatMessage = { id: Date.now().toString(), role: "user", content: query };
      const infoId = (Date.now() + 1).toString();
      addMessage(userMsg);
      addMessage({ id: infoId, role: "assistant", content: "The AI engine is still warming up. Your question will be sent automatically once it's ready — hang tight!" });
      
      const waitForReady = () => new Promise<void>((resolve) => {
        const unsub = useReadinessStore.subscribe((state) => {
          if (state.status === "ready") {
            unsub();
            resolve();
          }
        });
        if (useReadinessStore.getState().status === "ready") {
          unsub();
          resolve();
        }
      });
      
      await waitForReady();
      updateMessage(infoId, { content: "" });
    }

    abortControllerRef.current = new AbortController();
    setStreaming(true);

    const hasUserMsg = messages.some(m => m.role === "user" && m.content === query);
    if (!hasUserMsg) {
      const userMsg: ChatMessage = { id: Date.now().toString(), role: "user", content: query };
      addMessage(userMsg);
    }
    const assistantId = (Date.now() + 1).toString();
    addMessage({ id: assistantId, role: "assistant", content: "" });

    let fullContent = "";
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
      if (abortControllerRef.current?.signal.aborted) break;

      if (attempt > 0) {
        const jitter = Math.random() * 1000;
        const delay = Math.min(BASE_DELAY * Math.pow(1.5, attempt - 1) + jitter, MAX_DELAY);
        updateMessage(assistantId, {
          content: `AI engine is warming up — retrying automatically... (attempt ${attempt}/${MAX_RETRIES})`,
        });
        await new Promise((r) => setTimeout(r, delay));
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
          lastError.message.includes("warming") ||
          lastError.message.includes("Failed to fetch");
        if (!isStartingUp || attempt >= MAX_RETRIES) break;
      }
    }

    if (lastError && lastError.name !== "AbortError") {
      updateMessage(assistantId, {
        content:
          fullContent +
          "\n\nThe AI engine is taking longer than expected to start. Please wait a moment and try again.",
      });
    }

    setStreaming(false);
  }, [isStreaming, sessionId, messages, addMessage, updateMessage, setSessionId, setStreaming]);

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    setStreaming(false);
  }, [setStreaming]);

  return { messages, isStreaming, sendMessage, stopGeneration };
}
