import { motion } from "framer-motion";
import { useReadinessStore } from "../hooks/useBackendReadiness";

const statusConfig = {
  checking: { color: "bg-amber-500", ring: "ring-amber-500/30", label: "Connecting" },
  starting: { color: "bg-amber-500", ring: "ring-amber-500/30", label: "Warming up" },
  ready: { color: "bg-green-500", ring: "ring-green-500/30", label: "Ready" },
  unavailable: { color: "bg-red-500", ring: "ring-red-500/30", label: "Unavailable" },
};

export function BackendStatusPill() {
  const { status } = useReadinessStore();
  const config = statusConfig[status];

  if (status === "ready") return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="fixed top-3 right-3 z-50 flex items-center gap-2 px-3 py-1.5 bg-card/90 backdrop-blur-xl border border-white/10 rounded-full shadow-lg"
    >
      <span className={`relative flex h-2.5 w-2.5`}>
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.color} opacity-75`} />
        <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${config.color}`} />
      </span>
      <span className="text-xs font-medium text-white/80">{config.label}</span>
    </motion.div>
  );
}
