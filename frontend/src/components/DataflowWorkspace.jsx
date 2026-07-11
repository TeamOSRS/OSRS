import React, { useState, useRef } from "react";
import { Maximize2, Minimize2, Activity, Play, Eye } from "lucide-react";

export default function DataflowWorkspace({ cameraActive, trackingEnabled, balancerActive, syncMode }) {
  // Zoom & Pan states
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });

  const handleMouseDown = (e) => {
    // Left-button only
    if (e.button !== 0) return;
    setIsDragging(true);
    dragStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.current.x,
      y: e.clientY - dragStart.current.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = 1.1;
    const newZoom = e.deltaY < 0 ? zoom * zoomFactor : zoom / zoomFactor;
    setZoom(Math.max(0.4, Math.min(2.5, newZoom)));
  };

  // Node specifications
  const nodes = [
    // Pipeline 1: Visual Hand Tracking
    {
      id: "node_camera",
      title: "Webcam Capture",
      type: "perception",
      status: cameraActive ? "active" : "idle",
      x: 50,
      y: 50,
      inputs: [],
      outputs: [{ name: "RGB Image", type: "frame" }]
    },
    {
      id: "node_mediapipe",
      title: "MediaPipe Hand Landmarker",
      type: "perception",
      status: cameraActive ? "active" : "idle",
      x: 270,
      y: 50,
      inputs: [{ name: "RGB Image", type: "frame" }],
      outputs: [{ name: "Landmarks (3D)", type: "vector" }]
    },
    {
      id: "node_posemapper",
      title: "Kinematic Pose Mapper",
      type: "control",
      status: trackingEnabled ? "active" : "idle",
      x: 500,
      y: 50,
      inputs: [{ name: "Landmarks (3D)", type: "vector" }],
      outputs: [{ name: "Motor Ticks", type: "ticks" }]
    },
    {
      id: "node_leap",
      title: "LEAP Hand Output",
      type: "actuator",
      status: (trackingEnabled && syncMode === "hardware") ? "active" : "idle",
      x: 730,
      y: 50,
      inputs: [{ name: "Motor Ticks", type: "ticks" }],
      outputs: []
    },

    // Pipeline 2: Ball on Plate Balancer Research
    {
      id: "node_loadcell",
      title: "Load Cell Matrix",
      type: "perception",
      status: balancerActive ? "active" : "idle",
      x: 50,
      y: 250,
      inputs: [],
      outputs: [{ name: "Force Vectors", type: "force" }]
    },
    {
      id: "node_estimator",
      title: "Ball State Estimator",
      type: "research",
      status: balancerActive ? "active" : "idle",
      x: 270,
      y: 250,
      inputs: [
        { name: "Force Vectors", type: "force" },
        { name: "Camera Frame", type: "frame" }
      ],
      outputs: [{ name: "Ball State", type: "state" }]
    },
    {
      id: "node_pid",
      title: "Balancing PID Controller",
      type: "control",
      status: balancerActive ? "active" : "idle",
      x: 500,
      y: 250,
      inputs: [{ name: "Ball State", type: "state" }],
      outputs: [{ name: "Tilt Angle (rad)", type: "delta" }]
    },
    {
      id: "node_humanoid",
      title: "Humanoid Arm Actuators",
      type: "actuator",
      status: balancerActive ? "active" : "idle",
      x: 730,
      y: 250,
      inputs: [{ name: "Tilt Angle (rad)", type: "delta" }],
      outputs: []
    }
  ];

  // Connections specifications (from node port outputs to inputs)
  const connections = [
    { from: ["node_camera", 0], to: ["node_mediapipe", 0] },
    { from: ["node_mediapipe", 0], to: ["node_posemapper", 0] },
    { from: ["node_posemapper", 0], to: ["node_leap", 0] },

    { from: ["node_loadcell", 0], to: ["node_estimator", 0] },
    { from: ["node_camera", 0], to: ["node_estimator", 1] },
    { from: ["node_estimator", 0], to: ["node_pid", 0] },
    { from: ["node_pid", 0], to: ["node_humanoid", 0] }
  ];

  const renderConnections = () => {
    return connections.map((conn, idx) => {
      const sourceNode = nodes.find(n => n.id === conn.from[0]);
      const destNode = nodes.find(n => n.id === conn.to[0]);
      if (!sourceNode || !destNode) return null;

      // Position calculations
      const x1 = sourceNode.x + 160; // Right side of source card
      const y1 = sourceNode.y + 40 + conn.from[1] * 20;
      
      const x2 = destNode.x; // Left side of dest card
      const y2 = destNode.y + 40 + conn.to[1] * 20;

      // Control points for cubic bezier curves
      const dx = Math.abs(x2 - x1) * 0.5;
      const pathData = `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;

      const active = sourceNode.status === "active" && destNode.status === "active";

      return (
        <g key={idx}>
          {/* Background thick path */}
          <path
            d={pathData}
            fill="none"
            stroke="#25282c"
            strokeWidth={4}
          />
          {/* Colored connection link */}
          <path
            d={pathData}
            fill="none"
            stroke={active ? "#CFFF3E" : "#475569"}
            strokeWidth={1.5}
            className={active ? "connection-active" : ""}
            style={{
              strokeDasharray: active ? "6, 6" : "none",
              animation: active ? "flowPackets 2s linear infinite" : "none"
            }}
          />
        </g>
      );
    });
  };

  return (
    <div className="relative w-full h-[450px] bg-[#131416] rounded-2xl border border-slate-800 overflow-hidden select-none font-sans shadow-inner">
      
      {/* Dynamic flow animation styles */}
      <style>{`
        @keyframes flowPackets {
          to {
            stroke-dashoffset: -20;
          }
        }
      `}</style>

      {/* Grid Canvas container */}
      <div
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: "0 0",
            transition: isDragging ? "none" : "transform 0.15s ease-out"
          }}
          className="relative w-full h-full"
        >
          {/* SVG Connector Layer */}
          <svg className="absolute inset-0 w-[2000px] h-[2000px] pointer-events-none" style={{ zIndex: 1 }}>
            {renderConnections()}
          </svg>

          {/* Nodes Layer */}
          <div className="absolute w-[2000px] h-[2000px]" style={{ zIndex: 2 }}>
            {nodes.map(node => (
              <div
                key={node.id}
                style={{ left: node.x, top: node.y }}
                className={`absolute w-[160px] bg-[#191A1B] rounded-xl border p-3 flex flex-col gap-1.5 shadow-md transition ${
                  node.status === "active" ? "border-[#CFFF3E]/60 shadow-[#CFFF3E]/5" : "border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5">
                  <span className="text-[10px] font-bold text-white tracking-wide truncate">{node.title}</span>
                  <span className={`h-1.5 w-1.5 rounded-full ${
                    node.status === "active" ? "bg-[#CFFF3E] shadow-[0_0_6px_#CFFF3E]" : "bg-slate-600"
                  }`} />
                </div>
                <div className="flex flex-col gap-1">
                  {node.inputs.map((inp, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-[8px] text-slate-500 font-semibold uppercase">
                      <span className="h-1 w-1 bg-slate-600 rounded-full" />
                      <span>{inp.name}</span>
                    </div>
                  ))}
                  {node.outputs.map((out, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-[8px] text-slate-500 font-semibold uppercase justify-end text-right">
                      <span>{out.name}</span>
                      <span className="h-1 w-1 bg-[#CFFF3E] rounded-full" />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Glassmorphic header overlay */}
      <div className="absolute top-4 left-4 bg-[#191a1b]/80 backdrop-blur-md px-3.5 py-2.5 rounded-xl border border-slate-700/50 flex flex-col gap-1 z-10 text-[10px] text-slate-300 shadow-md">
        <div className="flex items-center gap-1.5 text-[#CFFF3E] font-bold tracking-wider uppercase">
          <Activity className="h-3.5 w-3.5" />
          <span>ROS Pipeline Graph</span>
        </div>
        <span className="text-slate-500 text-[8px] uppercase mt-0.5 font-semibold">Hold click and drag to pan • Scroll to zoom</span>
      </div>

      {/* Grid Canvas buttons */}
      <div className="absolute bottom-4 left-4 bg-[#191a1b]/80 backdrop-blur-md p-1.5 rounded-xl border border-slate-700/50 flex gap-1 z-10 shadow-md">
        <button
          onClick={() => setZoom(prev => Math.min(2.5, prev * 1.2))}
          className="p-1.5 hover:bg-slate-800 rounded-lg text-white transition"
        >
          <Maximize2 className="h-3 w-3" />
        </button>
        <button
          onClick={() => setZoom(prev => Math.max(0.4, prev / 1.2))}
          className="p-1.5 hover:bg-slate-800 rounded-lg text-white transition"
        >
          <Minimize2 className="h-3 w-3" />
        </button>
        <button
          onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded-lg text-white text-[8px] font-bold uppercase transition"
        >
          Fit
        </button>
      </div>

    </div>
  );
}
