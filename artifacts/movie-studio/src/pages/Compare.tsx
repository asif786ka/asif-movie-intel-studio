import { motion } from "framer-motion";
import { Search as SearchIcon, X, GitCompare, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Card, Button, Input, Badge } from "../components/UI";
import { useMovieSearch, useCompareMovies } from "../hooks/use-movies";
import { useCompareStore } from "../stores/appStore";
import type { MovieSearchResult } from "../lib/types";

export default function Compare() {
  const { query, setQuery, data: searchResults } = useMovieSearch("", 300);
  const { selectedMovies, addMovie, removeMovie } = useCompareStore();
  const compareMutation = useCompareMovies();

  const handleAdd = (movie: MovieSearchResult) => {
    addMovie(movie);
    setQuery("");
  };

  const handleCompare = () => {
    if (selectedMovies.length >= 2) {
      compareMutation.mutate(selectedMovies.map(m => m.id));
    }
  };

  const res = compareMutation.data?.data;

  const sections = [
    { id: "themes", label: "Thematic Analysis", data: res?.themes },
    { id: "critic_reception", label: "Critical Reception", data: res?.critic_reception },
    { id: "audience_reception", label: "Audience Reception", data: res?.audience_reception },
    { id: "awards", label: "Awards & Accolades", data: res?.awards },
    { id: "cast_and_director", label: "Direction & Performances", data: res?.cast_and_director },
    { id: "timeline", label: "Production Timeline", data: res?.timeline },
  ];

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto h-full overflow-y-auto">
      <div className="mb-10 text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center justify-center p-3 bg-primary/10 text-primary rounded-full mb-4">
          <GitCompare className="w-8 h-8" />
        </div>
        <h2 className="text-4xl font-display font-bold text-white mb-4">Compare Cinematic Worlds</h2>
        <p className="text-muted-foreground text-lg">Select up to 5 movies to generate a deep-dive comparative analysis across themes, reception, and production.</p>
      </div>

      <div className="max-w-3xl mx-auto mb-12">
        <div className="relative mb-4">
          <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input 
            value={query} onChange={e => setQuery(e.target.value)}
            placeholder="Search to add movies (e.g. Dune, Blade Runner)..."
            className="pl-12 py-6 text-lg bg-card/80 border-primary/30 shadow-lg"
          />
          {query && searchResults && searchResults.length > 0 && (
            <Card className="absolute top-full left-0 right-0 mt-2 p-2 z-50 max-h-64 overflow-y-auto bg-black/90 backdrop-blur-xl border-white/10">
              {searchResults.slice(0, 5).map(m => (
                <div key={m.id} onClick={() => handleAdd(m)} className="p-3 hover:bg-white/10 rounded-lg cursor-pointer flex items-center gap-3 transition-colors">
                  {m.poster_path ? <img src={`https://image.tmdb.org/t/p/w200${m.poster_path}`} className="w-8 h-12 object-cover rounded" alt={m.title} /> : <div className="w-8 h-12 bg-white/10 rounded" />}
                  <div>
                    <p className="text-white font-medium">{m.title}</p>
                    <p className="text-xs text-muted-foreground">{m.release_date?.split('-')[0]}</p>
                  </div>
                </div>
              ))}
            </Card>
          )}
        </div>

        {selectedMovies.length > 0 && (
          <div className="flex flex-wrap gap-3 mb-6">
            {selectedMovies.map(m => (
              <Badge key={m.id} variant="default" className="py-1.5 px-3 text-sm flex items-center gap-2 bg-card border-primary/40 text-white">
                {m.title}
                <button onClick={() => removeMovie(m.id)} className="hover:text-primary"><X className="w-4 h-4" /></button>
              </Badge>
            ))}
          </div>
        )}

        <Button onClick={handleCompare} disabled={selectedMovies.length < 2 || compareMutation.isPending} className="w-full py-6 text-lg shadow-primary/30">
          {compareMutation.isPending ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Analyzing Knowledge Base...</> : "Generate Comparison"}
        </Button>
      </div>

      {res && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8 pb-20">
          <Card className="p-8 bg-gradient-to-br from-card to-black border-primary/20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-2xl font-display font-semibold text-primary">Executive Summary</h3>
              <Badge variant="outline" className="text-xs">Confidence: {Math.round((res.confidence || 0) * 100)}%</Badge>
            </div>
            <p className="text-lg text-white/90 leading-relaxed font-serif">{res.summary}</p>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {sections.map(section => section.data && (
              <Card key={section.id} className="p-6">
                <h4 className="text-xl font-display font-medium text-white mb-4 flex items-center justify-between">
                  {section.label}
                  {section.data.citations && section.data.citations.length > 0 && (
                    <Badge variant="outline" className="text-xs">{section.data.citations.length} Sources</Badge>
                  )}
                </h4>
                <div className="prose prose-invert prose-sm">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{section.data.content}</ReactMarkdown>
                </div>
              </Card>
            ))}
          </div>

          {res.sections && res.sections.length > 0 && (
            <div className="grid grid-cols-1 gap-6">
              {res.sections.map((section, i) => (
                <Card key={i} className="p-6">
                  <h4 className="text-xl font-display font-medium text-white mb-4 flex items-center justify-between">
                    {section.dimension}
                    {section.citations && section.citations.length > 0 && (
                      <Badge variant="outline" className="text-xs">{section.citations.length} Sources</Badge>
                    )}
                  </h4>
                  <div className="prose prose-invert prose-sm">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{section.content}</ReactMarkdown>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
