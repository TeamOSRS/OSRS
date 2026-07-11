import React, { useState, useEffect } from "react";
import { Save, Play, Square, Download, FileText, Loader, Info } from "lucide-react";

export default function DataRecorder({ recorderState, onToggleRecord, onExport, onLoadReplay }) {
  const [experimentName, setExperimentName] = useState("experiment_run_1");
  const [exportFormat, setExportFormat] = useState("json");
  const [filePath, setFilePath] = useState("");
  const [duration, setDuration] = useState(0);

  // Simple timer tracking recording length
  useEffect(() => {
    let interval;
    if (recorderState?.is_recording) {
      setDuration(0);
      interval = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [recorderState?.is_recording]);

  const formatDuration = (secs) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const handleExport = () => {
    onExport(exportFormat, experimentName);
  };

  const handleLoadReplay = () => {
    if (!filePath.trim()) return;
    onLoadReplay(filePath);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-sans">
      
      {/* Recording session card */}
      <div className="bg-[#191A1B] p-5 rounded-2xl border border-slate-800 flex flex-col gap-4 text-slate-300">
        <div className="flex items-center gap-2 text-white font-bold text-sm tracking-wider uppercase border-b border-slate-800 pb-2">
          <Save className="h-4 w-4 text-[#CFFF3E]" />
          <span>Telemetry Logger</span>
        </div>

        <div className="flex flex-col gap-1.5 mt-1">
          <label className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Run Name</label>
          <input
            type="text"
            value={experimentName}
            onChange={(e) => setExperimentName(e.target.value.replace(/[^a-zA-Z0-9_]/g, ""))}
            disabled={recorderState?.is_recording}
            className="bg-[#242628] border border-slate-700/80 rounded-xl px-3 py-2 text-white text-xs outline-none focus:border-[#CFFF3E] transition disabled:opacity-50"
          />
        </div>

        <div className="flex items-center justify-between gap-4 mt-2 bg-slate-900/60 p-3 rounded-xl border border-slate-800/80">
          <div className="flex flex-col gap-0.5">
            <span className="text-[9px] uppercase font-bold text-slate-500">Record Status</span>
            <span className={`text-xs font-bold ${recorderState?.is_recording ? "text-[#CFFF3E] animate-pulse" : "text-slate-400"}`}>
              {recorderState?.is_recording ? "RECORDING ACTIVE" : "SESSION IDLE"}
            </span>
          </div>
          <div className="flex flex-col gap-0.5 text-right">
            <span className="text-[9px] uppercase font-bold text-slate-500">Captured Frames</span>
            <span className="text-white font-bold text-xs">
              {recorderState?.recorded_frames ?? 0} frames ({formatDuration(duration)})
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-1">
          <button
            onClick={() => onToggleRecord(!recorderState?.is_recording, experimentName)}
            className={`py-3 rounded-xl font-bold uppercase tracking-wider text-[10px] flex items-center justify-center gap-1.5 transition ${
              recorderState?.is_recording
                ? "bg-[#ff4d4d]/10 text-[#ff4d4d] border border-[#ff4d4d]/30 hover:bg-[#ff4d4d]/20"
                : "bg-[#CFFF3E] text-slate-900 hover:scale-[1.02]"
            }`}
          >
            {recorderState?.is_recording ? (
              <>
                <Square className="h-3.5 w-3.5 fill-current" />
                <span>Stop Logger</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Start Logger</span>
              </>
            )}
          </button>

          <div className="flex items-center gap-1.5 border border-slate-850 rounded-xl px-1.5 bg-[#242628]">
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
              className="bg-transparent text-white text-[10px] font-bold outline-none flex-grow"
            >
              <option value="json">JSON Format</option>
              <option value="csv">CSV Format</option>
            </select>
            <button
              onClick={handleExport}
              disabled={recorderState?.is_recording || (recorderState?.recorded_frames ?? 0) === 0}
              className="p-2 bg-[#CFFF3E] hover:bg-[#bce63b] rounded-lg text-slate-900 transition disabled:opacity-40 disabled:hover:bg-[#CFFF3E]"
            >
              <Download className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Trajectory Replay card */}
      <div className="bg-[#191A1B] p-5 rounded-2xl border border-slate-800 flex flex-col gap-4 text-slate-300">
        <div className="flex items-center gap-2 text-white font-bold text-sm tracking-wider uppercase border-b border-slate-800 pb-2">
          <FileText className="h-4 w-4 text-[#B5ACF3]" />
          <span>Trajectory Replay</span>
        </div>

        <div className="flex flex-col gap-1.5 mt-1">
          <label className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Replay Log Path / Name</label>
          <input
            type="text"
            placeholder="e.g. experiment_run_1.json"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            disabled={recorderState?.is_replaying}
            className="bg-[#242628] border border-slate-700/80 rounded-xl px-3 py-2 text-white text-xs outline-none focus:border-[#CFFF3E] transition disabled:opacity-50"
          />
        </div>

        <div className="flex items-center gap-2 text-[10px] text-slate-400 bg-slate-900/30 p-2.5 rounded-xl border border-slate-800/40">
          <Info className="h-4 w-4 text-[#B5ACF3] shrink-0" />
          <span> Replay reads frames from local storage and sends joint trajectories straight to the visual twin workspace.</span>
        </div>

        <button
          onClick={handleLoadReplay}
          disabled={recorderState?.is_replaying || !filePath}
          className="w-full bg-[#B5ACF3] hover:bg-[#a397e8] text-slate-950 font-bold uppercase tracking-wider py-3 rounded-xl text-[10px] mt-2 flex items-center justify-center gap-1.5 transition disabled:opacity-50"
        >
          {recorderState?.is_replaying ? (
            <>
              <Loader className="h-3.5 w-3.5 animate-spin" />
              <span>Playing Trajectory...</span>
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Execute Replay</span>
            </>
          )}
        </button>
      </div>

    </div>
  );
}
