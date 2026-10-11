import React, { useState, useEffect } from "react";
import { 
  FileText, Download, ExternalLink, BookOpen, Layers, ShieldCheck, 
  Zap, EyeOff, Activity, Cpu, Sparkles, CheckCircle2, ArrowUpRight
} from "lucide-react";

export default function ResearchPaperViewer({ onNavigateToSimulations }) {
  const [paperInfo, setPaperInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const res = await fetch("/api/docs/paper/info");
        if (res.ok) {
          const data = await res.json();
          setPaperInfo(data);
        }
      } catch (err) {
        console.error("Failed to load paper info:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchInfo();
  }, []);

  const pdfUrl = "/api/docs/paper/pdf";

  return (
    <div className="space-y-6 animate-fluid">
      
      {/* HEADER SECTION (MINIMALIST HERO) */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-white/[0.06]">
        <div className="space-y-2 max-w-3xl">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
              <FileText className="w-3 h-3" />
              Official Research Paper
            </span>
            <span className="text-[10px] font-mono text-zinc-400 bg-white/[0.04] px-2 py-0.5 rounded border border-white/[0.04]">
              802 KB PDF
            </span>
          </div>

          <h1 className="text-xl md:text-3xl font-semibold tracking-tight text-zinc-100 leading-snug">
            Toward Vision-Independent Tactile Robotic Perception
          </h1>
          <p className="text-xs text-zinc-400 font-normal leading-relaxed">
            A Multi-Modal Force-Torque Closed Loop Control Framework for Dynamic Object Balancing
          </p>

          <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-500 pt-1">
            <span><strong className="text-zinc-300 font-medium">Authors:</strong> Aditya Jadav, Archie Veera, Bilal Sabugar</span>
            <span>•</span>
            <span><strong className="text-zinc-300 font-medium">Platform:</strong> Open Source Robotics System (OSRS)</span>
          </div>
        </div>

        {/* ACTIONS */}
        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          <a
            href={pdfUrl}
            download="Toward_Vision_Independent_Tactile_Robotic_Perception.pdf"
            className="px-4 py-2 rounded-xl bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 hover:text-sky-200 border border-sky-500/20 text-xs font-medium transition-all flex items-center gap-2 active:scale-[0.98]"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PDF</span>
          </a>

          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-zinc-300 hover:text-white border border-white/[0.06] text-xs font-medium transition-all flex items-center gap-2 active:scale-[0.98]"
          >
            <ExternalLink className="w-3.5 h-3.5 text-zinc-400" />
            <span>Fullscreen</span>
          </a>

          {onNavigateToSimulations && (
            <button
              onClick={onNavigateToSimulations}
              className="px-4 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-zinc-400 hover:text-zinc-200 border border-white/[0.06] text-xs font-medium transition-all flex items-center gap-2"
            >
              <Cpu className="w-3.5 h-3.5 text-sky-400" />
              <span>Simulations</span>
            </button>
          )}
        </div>
      </div>

      {/* SEGMENTED TAB SWITCHER */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {[
          { id: "overview", label: "Abstract & Stages", icon: BookOpen },
          { id: "motivation", label: "Why OSRS Was Developed", icon: ShieldCheck },
          { id: "pdf", label: "Read PDF Document", icon: FileText },
          { id: "math", label: "Control Theory", icon: Activity }
        ].map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 whitespace-nowrap ${
                active 
                  ? "bg-white/[0.08] text-zinc-100 border border-white/[0.08]" 
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03]"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: ABSTRACT & STAGES */}
      {activeTab === "overview" && (
        <div className="space-y-6 animate-fluid">
          <div className="mini-card p-6 space-y-3">
            <span className="text-[10px] font-medium text-amber-400 uppercase tracking-wider">
              Research Abstract
            </span>
            <p className="text-xs md:text-sm text-zinc-300 leading-relaxed font-normal text-justify">
              Dynamic robotic manipulation traditionally relies heavily on high-speed computer vision systems. However, camera-based perception suffers from transmission latency (30–80 ms), occlusion by robotic end-effectors, and sensitivity to environmental illumination. This research establishes the foundational development of OSRS (Open Source Robotics System) by demonstrating a progression from vision-dependent ball balancing to vision-independent, high-speed (80 Hz) tactile and force feedback. Through three developmental stages—ranging from dual OpenManipulator-X arms to asymmetric industrial arms and humanoid bimanual systems—we formulate Lagrangian contact dynamics, Recursive Least Squares (RLS) online parameter identification, and hybrid multi-modal fusion capable of maintaining sub-millimeter balance stability even during complete visual blackout.
            </p>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-400" />
              Development Stages
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                {
                  stage: "Stage 1",
                  title: "Dual OMX Simulation",
                  tech: "MuJoCo Physics + DLS IK",
                  desc: "Lagrangian contact physics derivation, dual 4-DOF height kinematics, and solvePnP triangulation.",
                  tag: "Validated"
                },
                {
                  stage: "Stage 2",
                  title: "Franka FR3 + HEAL",
                  tech: "7-DOF + 6-DOF Industrial Arms",
                  desc: "Scaled cooperative manipulation to heterogeneous industrial arms with 2-axis setpoint balancing.",
                  tag: "Heterogeneous"
                },
                {
                  stage: "Stage 3",
                  title: "Humanoid Bimanual",
                  tech: "Robotis OP3 Upper-Torso",
                  desc: "Upper-body dual-arm cooperative plate stabilization and vehicle steering wheel rotation.",
                  tag: "Humanoid"
                },
                {
                  stage: "Stage 4",
                  title: "Physical OSRS Platform",
                  tech: "Dynamixel + HX711 (80Hz)",
                  desc: "Physical execution platform with 50 Hz real-time multi-threaded control and 80 Hz strain gauges.",
                  tag: "Hardware"
                }
              ].map((item, idx) => (
                <div key={idx} className="mini-card p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-zinc-400 bg-white/[0.04] px-1.5 py-0.2 rounded">
                      {item.stage}
                    </span>
                    <span className="text-[10px] font-medium text-sky-400">
                      {item.tag}
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-zinc-100">{item.title}</h4>
                  <p className="text-[10px] text-zinc-500 font-medium">{item.tech}</p>
                  <p className="text-xs text-zinc-400 leading-relaxed font-normal">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: WHY OSRS WAS DEVELOPED */}
      {activeTab === "motivation" && (
        <div className="space-y-4 animate-fluid">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                icon: Zap,
                title: "1. Visual Latency Bottleneck",
                badge: "80Hz Tactile vs 30Hz Vision",
                badgeColor: "text-amber-400 bg-amber-500/10 border-amber-500/20",
                problem: "Camera pipelines (exposure, USB transfer, OpenCV HSV processing) introduce 30ms to 80ms of latency, causing severe phase lag during high-speed balancing.",
                solution: "HX711 strain-gauge scale readings stream at 80 Hz with <12 ms total latency, providing immediate derivative feedback before the ball accelerates out of range."
              },
              {
                icon: EyeOff,
                title: "2. End-Effector Occlusion",
                badge: "100% Occlusion Survival",
                badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
                problem: "During bimanual manipulation, robotic grippers and hands obstruct overhead camera lines of sight, blinding vision-only controllers.",
                solution: "OSRS force perception operates purely from physical reaction forces transmitted to the plate pivots, maintaining sub-millimeter tracking during complete visual blackout."
              },
              {
                icon: ShieldCheck,
                title: "3. Lighting Immunity",
                badge: "Zero Light Sensitivity",
                badgeColor: "text-sky-400 bg-sky-500/10 border-sky-500/20",
                problem: "Ambient room lighting shifts, shadows, and specular reflections on metallic spheres disrupt OpenCV HSV segmentation.",
                solution: "Strain-gauge differential force perception is completely immune to ambient illumination shifts, shadows, or reflective glare."
              },
              {
                icon: Activity,
                title: "4. Online Parameter Identification (RLS)",
                badge: "Adaptive Control",
                badgeColor: "text-purple-400 bg-purple-500/10 border-purple-500/20",
                problem: "Payloads vary in mass and rolling resistance. A controller tuned for a ping-pong ball oscillates wildly when balancing a heavy steel sphere.",
                solution: "Recursive Least Squares (RLS) running at 50 Hz estimates control authority 'a' and rolling damping 'b' online without requiring static manual calibration."
              }
            ].map((item, idx) => {
              const Icon = item.icon;
              return (
                <div key={idx} className="mini-card p-5 space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4 text-sky-400" />
                      <h4 className="text-xs font-semibold text-zinc-100">{item.title}</h4>
                    </div>
                    <span className={`text-[10px] font-medium px-2 py-0.5 rounded border ${item.badgeColor}`}>
                      {item.badge}
                    </span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="p-3 rounded-lg bg-rose-500/[0.06] border border-rose-500/15 text-rose-300">
                      <span className="text-[10px] font-semibold text-rose-400 block mb-0.5">Problem:</span>
                      {item.problem}
                    </div>

                    <div className="p-3 rounded-lg bg-emerald-500/[0.06] border border-emerald-500/15 text-emerald-300">
                      <span className="text-[10px] font-semibold text-emerald-400 block mb-0.5">OSRS Solution:</span>
                      {item.solution}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 3: READ PDF DOCUMENT */}
      {activeTab === "pdf" && (
        <div className="space-y-3 animate-fluid">
          <div className="w-full rounded-2xl overflow-hidden border border-white/[0.08] bg-[#0E1015]">
            <iframe
              src={pdfUrl}
              className="w-full h-[850px] bg-zinc-950 border-none"
              title="Toward Vision Independent Tactile Robotic Perception PDF Viewer"
            />
          </div>
        </div>
      )}

      {/* TAB 4: CONTROL THEORY */}
      {activeTab === "math" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fluid">
          <div className="mini-card p-5 space-y-2">
            <span className="text-[10px] font-mono text-zinc-400 bg-white/[0.04] px-1.5 py-0.2 rounded">
              Contact Dynamics
            </span>
            <h4 className="text-xs font-semibold text-zinc-100">Lagrangian Ball Motion on Tilted Plate</h4>
            <p className="text-xs text-zinc-400 leading-relaxed font-normal">
              Derived for a sphere of mass m, radius R, rolling without slipping on a plate inclined at angle θ:
            </p>
            <div className="p-3 mini-inset text-amber-300 font-mono text-xs text-center">
              {"s_ddot = (5 / 7) * g * sin(theta)"}
            </div>
            <p className="text-[11px] text-zinc-500">
              Linearized for small angles: s_ddot ≈ (5/7) * g * θ.
            </p>
          </div>

          <div className="mini-card p-5 space-y-2">
            <span className="text-[10px] font-mono text-zinc-400 bg-white/[0.04] px-1.5 py-0.2 rounded">
              Kinematics
            </span>
            <h4 className="text-xs font-semibold text-zinc-100">Differential Height & Tilt Mapping</h4>
            <p className="text-xs text-zinc-400 leading-relaxed font-normal">
              In Stage 1 (dual OpenManipulator-X) and Stage 4 (hardware), tilt angle θ is mapped via vertical offset Δz:
            </p>
            <div className="p-3 mini-inset text-amber-300 font-mono text-xs text-center">
              {"theta = atan2(2 * Delta_z, d_plate)"}
            </div>
            <p className="text-[11px] text-zinc-500">
              Low-pass filtered with α = 0.25 to prevent chattering.
            </p>
          </div>
        </div>
      )}

    </div>
  );
}
