type ErrorClassification = "startup" | "transient" | "fatal";

export function classifyError(status: number, message?: string): ErrorClassification {
  if (status === 503) return "startup";
  if (status === 429 || status === 502 || status === 504) return "transient";
  if (status === 0 || message?.includes("Failed to fetch") || message?.includes("NetworkError")) return "startup";
  return "fatal";
}

interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  onRetry?: (attempt: number, delay: number) => void;
  signal?: AbortSignal;
}

export async function fetchWithBackoff(
  url: string,
  init?: RequestInit,
  options: RetryOptions = {}
): Promise<Response> {
  const { maxRetries = 5, baseDelay = 3000, maxDelay = 15000, onRetry, signal } = options;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");

    try {
      const res = await fetch(url, { ...init, signal });

      if (res.ok || attempt >= maxRetries) return res;

      const classification = classifyError(res.status);
      if (classification === "fatal") return res;

      const jitter = Math.random() * 1000;
      const delay = Math.min(baseDelay * Math.pow(1.5, attempt) + jitter, maxDelay);
      onRetry?.(attempt + 1, delay);
      await new Promise((r) => setTimeout(r, delay));
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") throw err;

      if (attempt >= maxRetries) throw err;

      const jitter = Math.random() * 1000;
      const delay = Math.min(baseDelay * Math.pow(1.5, attempt) + jitter, maxDelay);
      onRetry?.(attempt + 1, delay);
      await new Promise((r) => setTimeout(r, delay));
    }
  }

  return fetch(url, { ...init, signal });
}
