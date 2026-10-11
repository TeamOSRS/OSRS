import React, { useState, useEffect } from "react";
import { 
  Play, Square, RefreshCw, Cpu, CheckCircle2, 
  AlertCircle, Clock, Zap, ArrowUpRight
} from "lucide-react";

export default function SimulationLauncher({ onNavigateToPaper }) {
  const [simulations, setSimulations] = useState([]);
  const [activeSim, setActiveSim] = useState(null);
  const [loadingSimId, setLoadingSimId] = useState(null);
  const [stopping, setStopping] = useState(false);
  const [filterStage, setFilterStage] = useState("all");
  const [statusToast, setStatusToast] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchSimulations = async () => {
    try {
      setRefreshing(true);
      const res = await fetch("/api/simulation/list");
      if (res.ok) {
        const data = await res.json();
        setSimulations(data.simulations || []);
      }
      
      const statusRes = await fetch("/api/simulation/status");
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setActiveSim(statusData.active ? statusData : null);
      }
    } catch (err) {
      console.error("Failed to fetch simulations:", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSimulations();
    const interval = setInterval(fetchSimulations, 2500);
    return () => clearInterval(interval);
  }, []);

  const showToast = (type, text) => {
    setStatusToast({ type, text });
    setTimeout(() => {
      setStatusToast(prev => (prev?.text === text ? null : prev));
    }, 4000);
  };

  const handleLaunch = async (simId) => {
    try {
      setLoadingSimId(simId);
      showToast("info", `Launching MuJoCo simulation...`);
      const res = await fetch("/api/simulation/launch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ simulation_id: simId })
      });
      let data = {};
      try {
        data = await res.json();
      } catch (parseErr) {
        data = { detail: res.statusText || "Server response was not JSON" };
      }
      if (res.ok) {
        showToast("success", data.message || "Simulation launched successfully.");
        await fetchSimulations();
      } else {
        showToast("error", data.detail || `Failed to launch simulation (HTTP ${res.status})`);
      }
    } catch (err) {
      showToast("error", `Launch error: ${err.message}`);
    } finally {
      setLoadingSimId(null);
    }
  };

  const handleStop = async () => {
    try {
      setStopping(true);
      const res = await fetch("/api/simulation/stop", { method: "POST" });
      let data = {};
      try {
        data = await res.json();
      } catch (parseErr) {
        data = { detail: res.statusText || "Server response was not JSON" };
      }
      if (res.ok) {
        showToast("success", data.message || "Simulation stopped.");
        await fetchSimulations();
      } else {
        showToast("error", data.detail || `Failed to stop simulation (HTTP ${res.status})`);
      }
    } catch (err) {
      showToast("error", `Stop error: ${err.message}`);
    } finally {
      setStopping(false);
    }
  };

  const filteredSims = simulations.filter(sim => {
    if (filterStage === "all") return true;
    if (filterStage === "stage1") return sim.stage.includes("Stage 1");
    if (filterStage === "stage2") return sim.stage.includes("Stage 2");
    if (filterStage === "stage3") return sim.stage.includes("Stage 3");
    return true;
  });

  return (
    <div className="space-y-6 animate-fluid">
      
      {/* FLOATING STATUS TOAST */}
      {statusToast && (
        <div className="fixed top-18 right-6 z-50 animate-fluid">
          <div className={`px-4 py-2.5 rounded-xl backdrop-blur-xl shadow-lg border flex items-center gap-2.5 text-xs font-medium ${
            statusToast.type === "success" 
              ? "bg-emerald-950/80 text-emerald-300 border-emerald-500/20" 
              : statusToast.type === "error"
              ? "bg-rose-950/80 text-rose-300 border-rose-500/20"
              : "bg-sky-950/80 text-sky-300 border-sky-500/20"
          }`}>
            {statusToast.type === "success" ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            ) : statusToast.type === "error" ? (
              <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
            ) : (
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-ping shrink-0" />
            )}
            <span>{statusToast.text}</span>
          </div>
        </div>
      )}

      {/* HEADER SECTION (MINIMALIST HERO) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl md:text-2xl font-semibold tracking-tight text-zinc-100">
              Physics Simulations
            </h1>
            <span className="text-[10px] font-medium text-sky-400 bg-sky-500/10 border border-sky-500/20 px-2 py-0.5 rounded-full">
              MuJoCo Physics
            </span>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed max-w-2xl font-normal">
            Launch multi-arm balancing, PID benchmarks, and bimanual robotics simulations directly in high-fidelity physics.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {onNavigateToPaper && (
            <button
              onClick={onNavigateToPaper}
              className="px-3.5 py-1.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-zinc-300 hover:text-white text-xs font-medium border border-white/[0.06] transition-all flex items-center gap-1.5 active:scale-[0.98]"
            >
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>Research Paper</span>
              <ArrowUpRight className="w-3 h-3 text-zinc-500" />
            </button>
          )}

          <button
            onClick={fetchSimulations}
            disabled={refreshing}
            className="p-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-zinc-400 hover:text-zinc-200 border border-white/[0.06] transition-all active:scale-[0.96] disabled:opacity-50"
            title="Refresh list"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* ACTIVE RUNNING STATUS BAR */}
      {activeSim && activeSim.active && (
        <div className="p-4 rounded-xl bg-emerald-500/[0.06] border border-emerald-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fluid">
          <div className="flex items-center gap-3">
            <span className="relative flex h-2.5 w-2.5 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400"></span>
            </span>

            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-zinc-100">
                  {activeSim.details?.title || activeSim.simulation_id}
                </span>
                <span className="font-mono text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded">
                  PID {activeSim.pid}
                </span>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-zinc-400 mt-0.5">
                <Clock className="w-3 h-3 text-emerald-400" />
                <span className="font-mono">{activeSim.elapsed_seconds}s elapsed</span>
                <span>•</span>
                <span>{activeSim.details?.hardware_target || "MuJoCo Scene"}</span>
              </div>
            </div>
          </div>

          <button
            onClick={handleStop}
            disabled={stopping}
            className="px-3.5 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/20 text-xs font-medium transition-all flex items-center justify-center gap-1.5 active:scale-[0.98]"
          >
            <Square className="w-3 h-3 fill-current" />
            <span>{stopping ? "Stopping..." : "Stop Simulation"}</span>
          </button>
        </div>
      )}

      {/* STAGE SELECTOR PILLS */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {[
          { id: "all", label: "All Simulations", count: simulations.length },
          { id: "stage1", label: "Stage 1: OMX", count: simulations.filter(s => s.stage.includes("Stage 1")).length },
          { id: "stage2", label: "Stage 2: Franka + HEAL", count: simulations.filter(s => s.stage.includes("Stage 2")).length },
          { id: "stage3", label: "Stage 3: Humanoid OP3", count: simulations.filter(s => s.stage.includes("Stage 3")).length }
        ].map((tab) => {
          const active = filterStage === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setFilterStage(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 whitespace-nowrap ${
                active 
                  ? "bg-white/[0.08] text-zinc-100 border border-white/[0.08]" 
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03]"
              }`}
            >
              <span>{tab.label}</span>
              <span className="text-[10px] text-zinc-500 font-mono">
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* SIMULATIONS CARDS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredSims.map((sim) => {
          const isRunning = activeSim && activeSim.active && activeSim.simulation_id === sim.id;
          const isLoading = loadingSimId === sim.id;

          return (
            <div
              key={sim.id}
              className={`mini-card p-5 flex flex-col justify-between ${
                isRunning ? "border-emerald-500/30 bg-emerald-950/[0.08]" : ""
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] font-medium text-zinc-400 bg-white/[0.04] px-2 py-0.5 rounded border border-white/[0.04]">
                    {sim.stage}
                  </span>

                  {isRunning ? (
                    <span className="text-[10px] font-medium text-emerald-400 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                      Running
                    </span>
                  ) : (
                    <span className="text-[10px] text-zinc-500">
                      {sim.badge}
                    </span>
                  )}
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-zinc-100 tracking-tight leading-snug">
                    {sim.title}
                  </h3>
                  <p className="text-xs text-zinc-400 leading-relaxed mt-1 font-normal">
                    {sim.description}
                  </p>
                </div>

                <div className="mini-inset p-3 text-[11px] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500">Platform:</span>
                    <span className="text-zinc-300 font-medium">{sim.hardware_target}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500">Directory:</span>
                    <span className="font-mono text-[10px] text-sky-400">{sim.rel_dir}/</span>
                  </div>
                </div>
              </div>

              <div className="pt-4">
                {isRunning ? (
                  <button
                    onClick={handleStop}
                    disabled={stopping}
                    className="w-full py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/20 text-xs font-medium transition-all flex items-center justify-center gap-1.5 active:scale-[0.98]"
                  >
                    <Square className="w-3 h-3 fill-current" />
                    <span>Stop</span>
                  </button>
                ) : (
                  <button
                    onClick={() => handleLaunch(sim.id)}
                    disabled={isLoading}
                    className="w-full py-2 rounded-xl bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 hover:text-sky-200 border border-sky-500/20 text-xs font-medium transition-all flex items-center justify-center gap-1.5 active:scale-[0.98] disabled:opacity-50"
                  >
                    <Play className={`w-3 h-3 fill-current ${isLoading ? "animate-spin" : ""}`} />
                    <span>{isLoading ? "Launching..." : "Launch Simulation"}</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
