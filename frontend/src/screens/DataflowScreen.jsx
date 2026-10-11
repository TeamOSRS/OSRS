import React from "react";
import DataflowWorkspace from "../components/DataflowWorkspace";

export default function DataflowScreen({ telemetry }) {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-2">
        <h2 className="text-3xl font-black text-white tracking-tight">Dataflow Pipelines</h2>
        <p className="text-xs text-zinc-400 font-bold mt-0.5">ROS-inspired node graph visualizing active perception and control pipelines.</p>
      </div>
      <div className="obsidian-card p-4 min-h-[600px] border border-white/[0.06]">
        <DataflowWorkspace telemetry={telemetry} />
      </div>
    </div>
  );
}
