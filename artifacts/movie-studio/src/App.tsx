/**
 * App.tsx — Root component for the Asif Movie Intel Studio frontend.
 *
 * Architecture Note (Senior AI Architect):
 *   This is the top-level React component that assembles the full application:
 *
 *   Provider Stack (outside → inside):
 *     1. QueryClientProvider — TanStack React Query for server state caching
 *     2. TooltipProvider — Shared tooltip context for UI components
 *     3. BrowserRouter — React Router with artifact-aware basename
 *     4. AppLayout — Shared navigation sidebar + content area
 *
 *   Routing Architecture:
 *     - basename is derived from import.meta.env.BASE_URL (set by Vite)
 *     - This enables deployment at any path prefix (/, /studio, etc.)
 *     - 7 routes covering the full application surface area
 *     - Catch-all (*) route for 404 handling
 *
 *   Query Client Configuration:
 *     - retry: 1 — single retry on failed queries (fail fast for UX)
 *     - refetchOnWindowFocus: false — prevent unnecessary API calls
 */

import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";

import Home from "./pages/Home";
import Search from "./pages/Search";
import Chat from "./pages/Chat";
import Upload from "./pages/Upload";
import Compare from "./pages/Compare";
import Admin from "./pages/Admin";
import Eval from "./pages/Eval";
import NotFound from "@/pages/not-found";

import { AppLayout } from "./components/AppLayout";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AppRoutes() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/eval" element={<Eval />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppLayout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <AppRoutes />
        </BrowserRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
