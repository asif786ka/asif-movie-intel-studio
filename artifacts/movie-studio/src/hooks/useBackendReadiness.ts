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
const FAST_POLL = 4000;
const SLOW_POLL = 10000;
const FAST_PHASE_CHECKS = 45;

export function useBackendReadiness() {
  const store = useReadinessStore();
  const checkCount = useRef(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (store.status === "ready") return;

    async function check() {
      try {
        const healthRes = await fetch(`${BASE}/health`, { signal: AbortSignal.timeout(5000) });
        if (!healthRes.ok) {
          if (healthRes.status === 503) {
            store.setStatus("starting", "AI engine is loading...");
          } else {
            store.setStatus("starting", "Waiting for backend services...");
          }
          checkCount.current++;
          return;
        }

        try {
          const readyRes = await fetch(`${BASE}/ready`, { signal: AbortSignal.timeout(5000) });
          if (readyRes.ok) {
            const data = await readyRes.json();
            store.setReady(data.data?.vector_store_chunks || 0);
            if (intervalRef.current) clearInterval(intervalRef.current);
            return;
          }
          store.setStatus("starting", "Backend is loading AI models...");
        } catch {
          store.setStatus("starting", "Backend is initializing...");
        }
      } catch {
        if (checkCount.current < 5) {
          store.setStatus("checking", "Connecting to services...");
        } else {
          store.setStatus("starting", "AI services are warming up...");
        }
      }

      checkCount.current++;

      if (checkCount.current === FAST_PHASE_CHECKS && intervalRef.current) {
        clearInterval(intervalRef.current);
        store.setStatus("unavailable", "Taking longer than expected — still trying...");
        intervalRef.current = setInterval(check, SLOW_POLL);
      }
    }

    check();
    intervalRef.current = setInterval(check, FAST_POLL);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return store;
}
