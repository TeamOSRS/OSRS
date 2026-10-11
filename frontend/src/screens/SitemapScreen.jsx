import React, { useState } from "react";
import { 
  SITEMAP, 
  SITEMAP_CATEGORIES, 
  getSitemapByCategory 
} from "../config/sitemap";
import { 
  LayoutDashboard, 
  Atom, 
  FileText, 
  SlidersHorizontal, 
  PlayCircle, 
  Network, 
  TrendingUp, 
  History, 
  Video, 
  Wrench, 
  Settings, 
  Activity, 
  BookOpen, 
  Info, 
  Map, 
  Search, 
  ArrowRight, 
  ExternalLink,
  Layers,
  Sparkles,
  CheckCircle2,
  Cpu
} from "lucide-react";

// Icon resolution lookup table
const ICON_MAP = {
  LayoutDashboard,
  Atom,
  FileText,
  SlidersHorizontal,
  PlayCircle,
  Network,
  TrendingUp,
  History,
  Video,
  Wrench,
  Settings,
  Activity,
  BookOpen,
  Info,
  Map
};

export default function SitemapScreen({ onNavigate }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("ALL");

  const filteredItems = SITEMAP.filter(item => {
    const matchesCat = selectedCategory === "ALL" || item.category === selectedCategory;
    const q = searchQuery.toLowerCase().trim();
    const matchesQuery = !q || (
      item.title.toLowerCase().includes(q) ||
      item.shortTitle.toLowerCase().includes(q) ||
      item.description.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q) ||
      (item.keywords && item.keywords.some(k => k.toLowerCase().includes(q)))
    );
    return matchesCat && matchesQuery;
  });

  const categories = getSitemapByCategory();

  return (
    <div className="space-y-8 animate-fade-in text-zinc-200">
      
      {/* Sitemap Hero Banner */}
      <div className="relative overflow-hidden rounded-[32px] bg-gradient-to-r from-[#000000] via-[#0D0F14] to-white/[0.04] p-6 md:p-8 border border-white/[0.08] shadow-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(16,185,129,0.08),transparent_60%)] pointer-events-none" />
        <div className="relative z-10 max-w-2xl">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-widest text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
              <Map className="w-3.5 h-3.5" />
              OSRS Architecture & Sitemap
            </span>
            <span className="text-[10px] font-mono text-zinc-400 bg-white/[0.04] px-2.5 py-1 rounded-full border border-white/[0.06]">
              {SITEMAP.length} Navigation Routes
            </span>
          </div>
          <h2 className="text-2xl md:text-3xl font-black text-white tracking-tight">
            System Sitemap & Route Directory
          </h2>
          <p className="text-xs md:text-sm text-zinc-400 mt-1 leading-relaxed">
            Hierarchical directory mapping all frontend screens, telemetry pipelines, hardware interfaces, and academic research modules. Click any route card to jump directly.
          </p>
        </div>

        {/* Search Input Island */}
        <div className="relative z-10 w-full md:w-80">
          <div className="relative">
            <Search className="w-4 h-4 text-zinc-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter sitemap routes..."
              className="w-full bg-[#040407] border border-white/[0.08] focus:border-emerald-500/50 rounded-2xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none transition-all shadow-inner"
            />
            {searchQuery && (
              <button 
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-bold text-zinc-400 hover:text-white"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Category Pills Filter */}
      <div className="flex flex-wrap items-center gap-2 border-b border-white/[0.06] pb-4">
        <button
          onClick={() => setSelectedCategory("ALL")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            selectedCategory === "ALL"
              ? "bg-white/[0.12] text-white border border-white/[0.2] shadow-sm"
              : "bg-white/[0.03] text-zinc-400 border border-white/[0.05] hover:text-white hover:bg-white/[0.1]/[0.06]"
          }`}
        >
          All Categories ({SITEMAP.length})
        </button>
        {SITEMAP_CATEGORIES.map(cat => {
          const count = categories[cat]?.length || 0;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                selectedCategory === cat
                  ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm"
                  : "bg-white/[0.03] text-zinc-400 border border-white/[0.05] hover:text-white hover:bg-white/[0.1]/[0.06]"
              }`}
            >
              {cat} ({count})
            </button>
          );
        })}
      </div>

      {/* Grouped Sitemap Cards */}
      {selectedCategory === "ALL" && !searchQuery ? (
        <div className="space-y-10">
          {SITEMAP_CATEGORIES.map((categoryName) => {
            const items = categories[categoryName] || [];
            if (!items.length) return null;
            return (
              <div key={categoryName} className="space-y-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-1.5 h-4 rounded-full bg-emerald-400" />
                  <h3 className="text-base font-bold text-white tracking-wide">
                    {categoryName}
                  </h3>
                  <span className="text-[11px] font-mono text-zinc-400 bg-white/[0.04] px-2 py-0.5 rounded-md border border-white/[0.06]">
                    {items.length} Screens
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {items.map((screen) => {
                    const IconComp = ICON_MAP[screen.iconName] || LayoutDashboard;
                    return (
                      <div
                        key={screen.id}
                        onClick={() => onNavigate(screen.id)}
                        className="bg-[#090A0E] hover:bg-[#0D0F14] border border-white/[0.07] hover:border-emerald-500/40 rounded-2xl p-5 flex flex-col justify-between gap-4 cursor-pointer group transition-all duration-200 hover:-translate-y-1 shadow-lg"
                      >
                        <div className="flex justify-between items-start gap-2">
                          <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06] text-zinc-200 group-hover:text-emerald-400 group-hover:bg-emerald-500/10 group-hover:border-emerald-500/20 transition-all">
                            <IconComp className="w-5 h-5" />
                          </div>
                          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 bg-white/[0.04] px-2.5 py-1 rounded-lg border border-white/[0.06]">
                            {screen.path}
                          </span>
                        </div>

                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
                              {screen.title}
                            </h4>
                          </div>
                          <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">
                            {screen.description}
                          </p>
                        </div>

                        <div className="pt-3 border-t border-white/[0.04] flex items-center justify-between text-xs text-zinc-400">
                          <span className="inline-flex items-center gap-1.5 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                            {screen.badge}
                          </span>
                          <span className="text-emerald-400 font-bold group-hover:translate-x-1 transition-transform inline-flex items-center gap-1">
                            Open Screen →
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Filtered Grid View */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map((screen) => {
            const IconComp = ICON_MAP[screen.iconName] || LayoutDashboard;
            return (
              <div
                key={screen.id}
                onClick={() => onNavigate(screen.id)}
                className="bg-[#090A0E] hover:bg-[#0D0F14] border border-white/[0.07] hover:border-emerald-500/40 rounded-2xl p-5 flex flex-col justify-between gap-4 cursor-pointer group transition-all duration-200 hover:-translate-y-1 shadow-lg"
              >
                <div className="flex justify-between items-start gap-2">
                  <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06] text-zinc-200 group-hover:text-emerald-400 group-hover:bg-emerald-500/10 group-hover:border-emerald-500/20 transition-all">
                    <IconComp className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 bg-white/[0.04] px-2.5 py-1 rounded-lg border border-white/[0.06]">
                    {screen.path}
                  </span>
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
                      {screen.title}
                    </h4>
                  </div>
                  <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">
                    {screen.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-white/[0.04] flex items-center justify-between text-xs text-zinc-400">
                  <span className="inline-flex items-center gap-1.5 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    {screen.badge}
                  </span>
                  <span className="text-emerald-400 font-bold group-hover:translate-x-1 transition-transform inline-flex items-center gap-1">
                    Open Screen →
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {filteredItems.length === 0 && (
        <div className="p-12 text-center obsidian-card">
          <p className="text-zinc-400 text-sm">No sitemap routes match your search query "{searchQuery}".</p>
        </div>
      )}
    </div>
  );
}
