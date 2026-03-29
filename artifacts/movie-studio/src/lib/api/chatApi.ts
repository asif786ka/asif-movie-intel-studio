const BASE = import.meta.env.BASE_URL + "api";

export interface StreamCallbacks {
  onStart?: (data: { trace_id: string; session_id: string }) => void;
  onContent?: (content: string) => void;
  onMetadata?: (data: {
    citations: Array<{ chunk_text: string; metadata: Record<string, string | number | boolean | null>; score?: number }>;
    query_type: string;
    route_type: string;
    trace_id: string;
    latency_ms: number;
  }) => void;
  onDone?: () => void;
  onError?: (error: Error) => void;
}

export async function streamChat(
  query: string,
  sessionId?: string,
  signal?: AbortSignal,
  callbacks?: StreamCallbacks
): Promise<void> {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, session_id: sessionId, include_sources: true }),
    signal,
  });

  if (!res.ok) throw new Error(`Stream failed: ${res.status}`);
  if (!res.body) throw new Error("No body in response");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const part of parts) {
      if (!part.startsWith("data: ")) continue;
      try {
        const data = JSON.parse(part.slice(6));
        switch (data.type) {
          case "start":
            callbacks?.onStart?.(data);
            break;
          case "content":
            callbacks?.onContent?.(data.content);
            break;
          case "metadata":
            callbacks?.onMetadata?.(data);
            break;
          case "done":
            callbacks?.onDone?.();
            break;
        }
      } catch {
        // skip malformed SSE events
      }
    }
  }
}

interface ChatHistoryResponse {
  messages: Array<{ role: string; content: string }>;
  session_id: string;
}

export async function getChatHistory(sessionId: string): Promise<ChatHistoryResponse> {
  const res = await fetch(`${BASE}/chat/history/${sessionId}`);
  if (!res.ok) throw new Error("Failed to fetch chat history");
  const json = await res.json();
  return json.data ?? json;
}
