import { create } from "zustand";
import { useEffect, useRef } from "react";

type BackendStatus = "checking" | "starting" | "ready" | "unavailable";

interface ReadinessState {
  status: BackendStatus;
  message: string;
  vectorChunks: number;
  setStatus: (status: BackendStatus, message?: string) => void;
  setReady: (chunks: number) => void;
}

export const useReadinessStore = create<ReadinessState>((set) => ({
  status: "checking",
  message: "Connecting to services...",
  vectorChunks: 0,
  setStatus: (status, message) =>
    set({ status, message: message || statusMessages[status] }),
  setReady: (chunks) =>
    set({ status: "ready", message: "All systems operational", vectorChunks: chunks }),
}));

const statusMessages: Record<BackendStatus, string> = {
  checking: "Connecting to services...",
  starting: "AI services are warming up...",
  ready: "All systems operational",
  unavailable: "Services temporarily unavailable",
};

const BASE = import.meta.env.BASE_URL + "api";
const POLL_INTERVAL = 4000;
const MAX_CHECKS = 60;

export function useBackendReadiness() {
  const store = useReadinessStore();
  const checkCount = useRef(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (store.status === "ready") return;

    async function check() {
      try {
        const res = await fetch(`${BASE}/health`, { signal: AbortSignal.timeout(5000) });
        if (res.ok) {
          try {
            const readyRes = await fetch(`${BASE}/ready`, { signal: AbortSignal.timeout(5000) });
            if (readyRes.ok) {
              const data = await readyRes.json();
              store.setReady(data.data?.vector_store_chunks || 0);
              if (intervalRef.current) clearInterval(intervalRef.current);
              return;
            }
          } catch {}
          store.setReady(0);
          if (intervalRef.current) clearInterval(intervalRef.current);
          return;
        }
        if (res.status === 503) {
          store.setStatus("starting", "AI engine is loading...");
        }
      } catch {
        if (checkCount.current < 5) {
          store.setStatus("checking", "Connecting to services...");
        } else {
          store.setStatus("starting", "AI services are warming up...");
        }
      }

      checkCount.current++;
      if (checkCount.current >= MAX_CHECKS) {
        store.setStatus("unavailable", "Services are taking longer than expected. Please refresh.");
        if (intervalRef.current) clearInterval(intervalRef.current);
      }
    }

    check();
    intervalRef.current = setInterval(check, POLL_INTERVAL);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return store;
}
