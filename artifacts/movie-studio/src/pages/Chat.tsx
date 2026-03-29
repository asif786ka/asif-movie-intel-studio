import { useState, useEffect, useRef } from "react";

import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, Bot, User, FileText, X, Loader2 } from "lucide-react";
import { Input, Button, Card, Badge } from "../components/UI";
import { useChatStream } from "../hooks/use-chat";
import { useReadinessStore } from "../hooks/useBackendReadiness";
import { Citation } from "../lib/types";

export default function Chat() {
  const [query, setQuery] = useState("");
  const { messages, isStreaming, sendMessage, stopGeneration } = useChatStream();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const backendStatus = useReadinessStore((s) => s.status);
  const isReady = backendStatus === "ready";

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    if (q && messages.length === 0) {
      sendMessage(q);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isStreaming) return;
    sendMessage(query);
    setQuery("");
  };

  return (
    <div className="h-full flex overflow-hidden">
      <div className="flex-1 flex flex-col h-full relative">
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 pb-32">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center opacity-50 max-w-md mx-auto text-center">
              <Bot className="w-16 h-16 mb-6 text-primary" />
              <h2 className="text-2xl font-display font-semibold text-white mb-2">Movie Studio AI</h2>
              <p className="text-muted-foreground">Ask anything about movies, directors, themes, box office performance, or detailed lore.</p>
              {!isReady && (
                <div className="mt-6 flex items-center gap-2 text-amber-400 text-sm">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>AI engine is warming up — you can type your question now</span>
                </div>
              )}
            </div>
          )}

          {messages.map((msg) => (
            <motion.div 
              key={msg.id} 
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              className={`flex gap-4 max-w-4xl mx-auto ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-10 h-10 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center flex-shrink-0 text-primary">
                  <Bot className="w-5 h-5" />
                </div>
              )}
              
              <div className={`space-y-3 max-w-[85%] ${msg.role === "user" ? "order-1" : "order-2"}`}>
                <div className={`p-5 rounded-2xl ${
                  msg.role === "user" 
                    ? "bg-primary text-primary-foreground rounded-tr-sm shadow-lg shadow-primary/20" 
                    : "bg-card border border-white/5 shadow-xl rounded-tl-sm text-white/90"
                }`}>
                  {msg.role === "assistant" ? (
                    msg.content ? (
                      <div className="prose prose-invert max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Thinking...</span>
                      </div>
                    )
                  ) : (
                    <p className="text-[15px] leading-relaxed">{msg.content}</p>
                  )}
                </div>

                {msg.role === "assistant" && !isStreaming && msg.queryType && (
                  <div className="flex flex-wrap gap-2 px-2">
                    <Badge variant="outline" className="text-xs">Query: {msg.queryType}</Badge>
                    <Badge variant="outline" className="text-xs">Route: {msg.routeType}</Badge>
                    <Badge variant="outline" className="text-xs font-mono">{msg.traceId}</Badge>
                    <Badge variant="outline" className="text-xs">{msg.latency}ms</Badge>
                  </div>
                )}
              </div>

              {msg.role === "user" && (
                <div className="w-10 h-10 rounded-full bg-secondary border border-white/10 flex items-center justify-center flex-shrink-0 order-2 text-white">
                  <User className="w-5 h-5" />
                </div>
              )}
            </motion.div>
          ))}
          <div ref={bottomRef} />
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-4 md:p-8 bg-gradient-to-t from-background via-background to-transparent">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative group">
            <Input 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={isReady ? "Ask about movies, actors, or cinematic themes..." : "Type your question — it will send when the AI is ready..."}
              className="pl-6 pr-32 py-8 text-lg rounded-full bg-card/90 backdrop-blur-xl border-white/10 shadow-2xl focus:border-primary/50 focus:ring-primary/20 focus:bg-card"
              disabled={isStreaming}
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center">
              {isStreaming ? (
                <Button type="button" onClick={stopGeneration} variant="destructive" className="rounded-full px-4 py-2 h-10">Stop</Button>
              ) : (
                <Button type="submit" disabled={!query.trim()} className="rounded-full w-12 h-12 p-0 shadow-primary/30">
                  <Send className="w-5 h-5 ml-1" />
                </Button>
              )}
            </div>
          </form>
        </div>
      </div>

      <div className="hidden lg:flex w-80 flex-col border-l border-white/5 bg-card/20 backdrop-blur-sm z-10">
        <div className="p-6 border-b border-white/5">
          <h3 className="font-display font-semibold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary" /> Sources & Citations
          </h3>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length > 0 ? (
            messages[messages.length - 1].citations?.map((cit, idx) => (
              <Card 
                key={idx} 
                className={`p-4 cursor-pointer transition-all duration-200 ${activeCitation === cit ? "border-primary/50 bg-primary/5" : "hover:border-white/20"}`}
                onClick={() => setActiveCitation(cit)}
              >
                <div className="flex justify-between items-start mb-2">
                  <Badge className="px-1.5 py-0 min-w-5 justify-center">[{idx + 1}]</Badge>
                  <Badge variant="outline" className="text-[10px]">{cit.metadata.source_type || 'Doc'}</Badge>
                </div>
                <h4 className="text-sm font-medium text-white mb-1 line-clamp-1">{cit.metadata.movie_title || "Unknown Source"}</h4>
                <p className="text-xs text-muted-foreground line-clamp-3">{cit.chunk_text}</p>
              </Card>
            )) || <p className="text-sm text-muted-foreground text-center mt-10">No citations for current response.</p>
          ) : (
            <p className="text-sm text-muted-foreground text-center mt-10">Sources will appear here.</p>
          )}
        </div>
      </div>

      <AnimatePresence>
        {activeCitation && (
          <motion.div 
            initial={{ opacity: 0, x: 400 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 400 }}
            className="fixed top-0 right-0 bottom-0 w-full md:w-96 bg-background border-l border-white/10 shadow-2xl z-50 flex flex-col"
          >
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-card">
              <h3 className="font-semibold text-white flex items-center gap-2">Source Excerpt</h3>
              <button onClick={() => setActiveCitation(null)} className="p-2 hover:bg-white/10 rounded-lg text-muted-foreground"><X className="w-5 h-5" /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <div className="mb-6 space-y-2">
                {Object.entries(activeCitation.metadata).map(([k, v]) => (
                  <div key={k} className="flex gap-2 text-sm">
                    <span className="text-muted-foreground capitalize w-24">{k.replace('_', ' ')}:</span>
                    <span className="text-white font-medium">{v}</span>
                  </div>
                ))}
              </div>
              <div className="p-5 bg-card/50 rounded-xl border border-white/5 text-white/90 text-sm leading-relaxed whitespace-pre-wrap font-serif">
                {activeCitation.chunk_text}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
