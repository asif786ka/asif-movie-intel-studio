import React from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "../lib/utils";
import { Film, Home, Search, MessageSquare, Upload, GitCompare, Activity, ShieldAlert, Menu, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/chat", label: "Studio Chat", icon: MessageSquare },
  { href: "/search", label: "Movie Database", icon: Search },
  { href: "/compare", label: "Compare", icon: GitCompare },
  { href: "/upload", label: "Ingest Docs", icon: Upload },
  { href: "/admin", label: "Dashboard", icon: Activity },
  { href: "/eval", label: "Evaluations", icon: ShieldAlert },
];

export function AppLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden relative">
      <aside className="hidden md:flex w-72 flex-col border-r border-white/5 bg-card/40 backdrop-blur-2xl z-20">
        <div className="p-6 flex items-center gap-3">
          <div className="bg-primary/20 p-2 rounded-xl border border-primary/30 text-primary">
            <Film className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-display font-bold text-lg leading-tight text-white">Asif Movie Intel</h1>
            <p className="text-xs text-primary font-medium tracking-wide">STUDIO</p>
          </div>
        </div>

        <nav className="flex-1 px-4 space-y-1.5 mt-4">
          {navItems.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link key={item.href} to={item.href} className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group",
                isActive 
                  ? "bg-primary/10 text-primary shadow-[inset_0_1px_0_0_rgba(255,255,255,0.1)] border border-primary/20" 
                  : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
              )}>
                <item.icon className={cn("w-5 h-5 transition-transform duration-300", isActive ? "scale-110" : "group-hover:scale-110")} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="md:hidden absolute top-4 left-4 z-50">
        <button onClick={() => setMobileOpen(true)} className="p-2 bg-card rounded-xl border border-white/10 text-white">
          <Menu className="w-5 h-5" />
        </button>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div 
            initial={{ opacity: 0, x: -300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className="fixed inset-0 z-50 flex"
          >
            <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
            <div className="w-72 bg-card border-r border-white/10 h-full relative z-10 flex flex-col pt-16 px-4">
              <button onClick={() => setMobileOpen(false)} className="absolute top-4 right-4 p-2 text-muted-foreground hover:text-white">
                <X className="w-5 h-5" />
              </button>
              {navItems.map((item) => (
                <Link key={item.href} to={item.href} onClick={() => setMobileOpen(false)} className={cn(
                  "flex items-center gap-3 px-4 py-4 rounded-xl text-base font-medium mt-2",
                  location.pathname === item.href ? "bg-primary/20 text-primary" : "text-muted-foreground"
                )}>
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </Link>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <main className="flex-1 flex flex-col h-full overflow-hidden relative z-10">
        <div className="absolute inset-0 z-0 opacity-40 pointer-events-none" style={{ backgroundImage: `url(${import.meta.env.BASE_URL}images/hero-bg.png)`, backgroundSize: 'cover', backgroundPosition: 'center', mixBlendMode: 'screen' }} />
        <div className="relative z-10 flex-1 overflow-y-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
