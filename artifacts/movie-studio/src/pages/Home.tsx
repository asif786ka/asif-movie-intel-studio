import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { MessageSquare, Upload, GitCompare, Search, ArrowRight } from "lucide-react";
import { Card, Button } from "../components/UI";

export default function Home() {
  return (
    <div className="min-h-full p-6 md:p-12 lg:px-24 w-full max-w-7xl mx-auto flex flex-col">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="mt-12 md:mt-24">
        <h1 className="text-5xl md:text-7xl font-display font-bold text-white mb-6">
          Intelligence for <br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-amber-200">Cinematic Lore</span>
        </h1>
        <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mb-10 leading-relaxed">
          A production-grade AI research studio combining structured TMDB data with deep RAG analysis over screenplays, reviews, and cinematic timelines.
        </p>
        
        <div className="flex flex-wrap gap-4 mb-20">
          <Link to="/chat">
            <Button className="px-8 py-6 text-lg gap-3 rounded-2xl">
              <MessageSquare className="w-5 h-5" />
              Start Research
            </Button>
          </Link>
          <Link to="/search">
            <Button variant="outline" className="px-8 py-6 text-lg gap-3 rounded-2xl">
              <Search className="w-5 h-5" />
              Movie Database
            </Button>
          </Link>
          <Link to="/compare">
            <Button variant="outline" className="px-8 py-6 text-lg gap-3 rounded-2xl">
              <GitCompare className="w-5 h-5" />
              Compare Films
            </Button>
          </Link>
          <Link to="/upload">
            <Button variant="outline" className="px-8 py-6 text-lg gap-3 rounded-2xl">
              <Upload className="w-5 h-5" />
              Ingest Documents
            </Button>
          </Link>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mt-auto pb-12">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
          <h3 className="text-sm font-semibold text-primary uppercase tracking-wider mb-6">System Architecture</h3>
          <Card className="p-1 group overflow-hidden relative">
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent z-10" />
            <img 
              src={`${import.meta.env.BASE_URL}images/arch-diagram.png`} 
              alt="LangGraph Architecture Diagram" 
              className="w-full h-64 object-cover opacity-80 group-hover:scale-105 transition-transform duration-700"
            />
            <div className="absolute bottom-6 left-6 z-20">
              <p className="text-white font-medium">LangGraph Orchestration</p>
              <p className="text-sm text-white/60">Hybrid TMDB + ChromaDB Pipeline</p>
            </div>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
          <h3 className="text-sm font-semibold text-primary uppercase tracking-wider mb-6">Sample Queries</h3>
          <div className="space-y-4">
            {[
              "Compare the themes of Dune and Blade Runner 2049.",
              "What awards did Oppenheimer win?",
              "Summarize the critical reception of Interstellar."
            ].map((q, i) => (
              <Link key={i} to={`/chat?q=${encodeURIComponent(q)}`}>
                <Card className="p-5 hover:bg-white/10 transition-colors cursor-pointer flex items-center justify-between group">
                  <p className="text-white/80 font-medium group-hover:text-white transition-colors">{q}</p>
                  <ArrowRight className="w-5 h-5 text-primary opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                </Card>
              </Link>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
