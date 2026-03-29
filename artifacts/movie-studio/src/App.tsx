import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AnimatePresence } from "framer-motion";

import Home from "./pages/Home";
import Search from "./pages/Search";
import Chat from "./pages/Chat";
import Upload from "./pages/Upload";
import Compare from "./pages/Compare";
import Admin from "./pages/Admin";
import Eval from "./pages/Eval";
import NotFound from "@/pages/not-found";

import { AppLayout } from "./components/AppLayout";
import { BackendStartupScreen } from "./components/BackendStartupScreen";
import { BackendStatusPill } from "./components/BackendStatusPill";
import { useBackendReadiness } from "./hooks/useBackendReadiness";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AppRoutes() {
  const { status } = useBackendReadiness();
  const showStartup = status === "checking" || status === "starting";

  return (
    <>
      <AnimatePresence>
        {showStartup && <BackendStartupScreen />}
      </AnimatePresence>
      <BackendStatusPill />
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
    </>
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
