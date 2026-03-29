import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Film, Sparkles } from "lucide-react";

const warmupMessages = [
  "Waking up the movie intelligence engine...",
  "Loading retrieval and analysis services...",
  "Initializing AI-powered search...",
  "Preparing the cinematic knowledge base...",
  "Connecting to movie databases...",
  "Almost there — warming up neural pathways...",
  "This can take a minute on first launch...",
  "Thanks for waiting — we'll continue automatically",
];

const sampleQuestions = [
  "What themes connect Nolan's films?",
  "Compare Dune and Blade Runner 2049",
  "Tell me about Tom Cruise's career evolution",
  "What awards did Oppenheimer win?",
  "Analyze Denis Villeneuve's directing style",
];

export function BackendStartupScreen() {
  const [msgIndex, setMsgIndex] = useState(0);
  const [dots, setDots] = useState("");

  useEffect(() => {
    const msgTimer = setInterval(() => {
      setMsgIndex((i) => (i + 1) % warmupMessages.length);
    }, 4000);
    return () => clearInterval(msgTimer);
  }, []);

  useEffect(() => {
    const dotTimer = setInterval(() => {
      setDots((d) => (d.length >= 3 ? "" : d + "."));
    }, 500);
    return () => clearInterval(dotTimer);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
      className="fixed inset-0 z-[100] bg-background flex items-center justify-center overflow-hidden"
    >
      <div
        className="absolute inset-0 opacity-30 pointer-events-none"
        style={{
          backgroundImage: `url(${import.meta.env.BASE_URL}images/hero-bg.png)`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          mixBlendMode: "screen",
        }}
      />

      <div className="relative z-10 flex flex-col items-center max-w-lg mx-auto px-6 text-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="mb-8"
        >
          <div className="relative">
            <div className="bg-primary/20 p-5 rounded-2xl border border-primary/30">
              <Film className="w-12 h-12 text-primary" />
            </div>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              className="absolute -top-2 -right-2"
            >
              <Sparkles className="w-5 h-5 text-amber-400" />
            </motion.div>
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-3xl font-display font-bold text-white mb-2"
        >
          Asif Movie Intel Studio
        </motion.h1>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mb-8"
        >
          <div className="flex items-center gap-2 mb-4">
            <div className="h-1 w-16 bg-primary/30 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary rounded-full"
                animate={{ x: ["-100%", "100%"] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                style={{ width: "50%" }}
              />
            </div>
          </div>

          <AnimatePresence mode="wait">
            <motion.p
              key={msgIndex}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.3 }}
              className="text-muted-foreground text-base"
            >
              {warmupMessages[msgIndex]}{dots}
            </motion.p>
          </AnimatePresence>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="w-full"
        >
          <p className="text-xs text-muted-foreground/60 uppercase tracking-wider mb-3">
            Questions you can ask once ready
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            {sampleQuestions.map((q, i) => (
              <motion.span
                key={q}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1 + i * 0.1 }}
                className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-full text-xs text-white/60"
              >
                {q}
              </motion.span>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
