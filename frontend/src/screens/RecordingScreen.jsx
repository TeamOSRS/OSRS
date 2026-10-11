import React from "react";
import DataRecorder from "../components/DataRecorder";

export default function RecordingScreen({ telemetry }) {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-2">
        <h2 className="text-3xl font-black text-white tracking-tight">Replay & Recording</h2>
        <p className="text-xs text-zinc-400 font-bold mt-0.5">Log telemetry frames to files and replay recorded trajectories.</p>
      </div>
      <div className="obsidian-card p-6 border border-white/[0.06]">
        <DataRecorder telemetry={telemetry} />
      </div>
    </div>
  );
}
