import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search as SearchIcon, Star, Calendar, Loader2 } from "lucide-react";
import { useMovieSearch, useMovieDetails } from "../hooks/use-movies";
import { Input, Card, Badge, Button } from "../components/UI";
import { useReadinessStore } from "../hooks/useBackendReadiness";
import type { MovieSearchResult } from "../lib/types";

export default function Search() {
  const { query, setQuery, data: movies, isLoading } = useMovieSearch("", 500);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { data: details, isLoading: detailsLoading } = useMovieDetails(selectedId);
  const backendStatus = useReadinessStore((s) => s.status);
  const isReady = backendStatus === "ready";

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto h-full flex flex-col">
      <div className="mb-8">
        <h2 className="text-3xl font-display font-bold text-white mb-2">Movie Database</h2>
        <p className="text-muted-foreground">Search TMDB with real-time intelligence.</p>
      </div>

      <div className="relative mb-10 max-w-2xl">
        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input 
          className="pl-12 py-6 text-lg rounded-2xl bg-black/40 border-white/10"
          placeholder={isReady ? "Search for movies..." : "Search will be available once the engine is ready..."}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={!isReady}
        />
        {isLoading && <div className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />}
        {!isReady && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-1.5 text-amber-400 text-xs">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Warming up</span>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto pb-20">
        {!query && (
          <div className="h-64 flex flex-col items-center justify-center opacity-50">
            <img src={`${import.meta.env.BASE_URL}images/film-reel-3d.png`} className="w-32 h-32 mb-4 drop-shadow-2xl" alt="Empty state" />
            <p className="text-xl font-medium">Search the archives</p>
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
          {movies?.map((movie: MovieSearchResult, i: number) => (
            <motion.div
              key={movie.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => setSelectedId(movie.id)}
            >
              <Card className="cursor-pointer group h-full flex flex-col hover:border-primary/50 transition-all duration-300 hover:-translate-y-2">
                <div className="aspect-[2/3] relative overflow-hidden bg-muted">
                  {movie.poster_path ? (
                    <img 
                      src={`https://image.tmdb.org/t/p/w500${movie.poster_path}`} 
                      alt={movie.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-black/50 text-white/30">No Poster</div>
                  )}
                  <div className="absolute top-2 right-2 bg-black/70 backdrop-blur-md px-2 py-1 rounded-lg flex items-center gap-1 text-sm font-medium text-amber-400">
                    <Star className="w-3.5 h-3.5 fill-current" />
                    {movie.vote_average.toFixed(1)}
                  </div>
                </div>
                <div className="p-4">
                  <h3 className="font-semibold text-white line-clamp-1">{movie.title}</h3>
                  <p className="text-sm text-muted-foreground mt-1 flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    {movie.release_date?.split('-')[0] || "TBA"}
                  </p>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>

      <AnimatePresence>
        {selectedId && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
            onClick={() => setSelectedId(null)}
          >
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-3xl bg-card border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row max-h-[80vh]"
              onClick={(e) => e.stopPropagation()}
            >
              {detailsLoading || !details ? (
                <div className="p-12 w-full flex justify-center"><div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" /></div>
              ) : (
                <>
                  <div className="md:w-1/3 bg-muted">
                    {details.poster_path && (
                      <img src={`https://image.tmdb.org/t/p/w500${details.poster_path}`} className="w-full h-full object-cover" alt="Poster" />
                    )}
                  </div>
                  <div className="md:w-2/3 p-6 overflow-y-auto">
                    <div className="flex justify-between items-start mb-4">
                      <h2 className="text-2xl font-bold text-white">{details.title}</h2>
                      <Badge variant="warning" className="text-sm"><Star className="w-4 h-4 mr-1 fill-current" /> {details.vote_average.toFixed(1)}</Badge>
                    </div>
                    <div className="flex flex-wrap gap-2 mb-6">
                      {details.genres.map(g => <Badge key={g.id} variant="outline">{g.name}</Badge>)}
                      <Badge variant="outline">{details.runtime} min</Badge>
                      <Badge variant="outline">{details.release_date.split('-')[0]}</Badge>
                    </div>
                    <p className="text-primary italic mb-4">"{details.tagline}"</p>
                    <p className="text-white/80 leading-relaxed mb-6">{details.overview}</p>
                    
                    <Button onClick={() => setSelectedId(null)} variant="secondary" className="w-full mt-auto">Close</Button>
                  </div>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
