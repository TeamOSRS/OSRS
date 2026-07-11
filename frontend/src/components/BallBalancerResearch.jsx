import React, { useState, useEffect, useRef } from "react";
import { Play, Square, Settings, RefreshCw, BarChart2, Video, Compass, Crosshair, Cpu, Sliders } from "lucide-react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";

export default function BallBalancerResearch({ 
  telemetry, 
  backendState, 
  onTune, 
  onToggle, 
  balancerData, 
  onGoToStart,
  onInitializeArms,
  onSendCommand,
  videoFrame,
  cameraActive,
  onToggleVision,
  limits = {},
  connected = false
}) {
  // Local App Menu State
  const [activeApp, setActiveApp] = useState("home"); // "home", "vision", "tune", "sequence", "calibration", "loadcell"
  
  const loadcellMode = balancerData?.loadcell_mode ?? balancerData?.data?.loadcell_mode ?? 2;
  const loadcellArm = balancerData?.loadcell_arm ?? balancerData?.data?.loadcell_arm ?? "left";
  const ballWeightRefVal = balancerData?.ball_weight_ref ?? balancerData?.data?.ball_weight_ref ?? 100.0;
  const invertOutput = balancerData?.invert_output ?? balancerData?.data?.invert_output ?? false;
  const ballType = balancerData?.ball_type ?? balancerData?.data?.ball_type ?? "green_ping_pong";
  const avgMappingError = balancerData?.avg_mapping_error ?? balancerData?.data?.avg_mapping_error ?? 0.1;

  const [timeString, setTimeString] = useState("");
  const [dateString, setDateString] = useState("");
  const [deadband, setDeadband] = useState(15); // pixels threshold for center
  const [expandedSections, setExpandedSections] = useState({
    left: true,
    right: true,
    head: false,
    general: false
  });

  // Local PID Gains states
  const [kp, setKp] = useState(balancerData?.kp ?? 0.8);
  const [kd, setKd] = useState(balancerData?.kd ?? 0.3);
  const [ki, setKi] = useState(balancerData?.ki ?? 0.05);
  const [speed, setSpeed] = useState(balancerData?.speed_multiplier ?? 1.0);
  const [maxTiltPos, setMaxTiltPos] = useState(balancerData?.max_tilt_positive ?? 150);
  const [maxTiltNeg, setMaxTiltNeg] = useState(balancerData?.max_tilt_negative ?? 178);
  const [autoTune, setAutoTune] = useState(balancerData?.auto_tune_enabled ?? false);
  const [learningLog, setLearningLog] = useState([]);
  const [calibWeightL, setCalibWeightL] = useState(100);
  const [calibWeightR, setCalibWeightR] = useState(100);
  const [selectedPort, setSelectedPort] = useState("");
  const [ballWeightRef, setBallWeightRef] = useState(100);
  const [availablePorts, setAvailablePorts] = useState([]);

  const [activeSettingsTab, setActiveSettingsTab] = useState("camera"); // "camera", "color", "filter"

  // Local settings states
  const [laserPower, setLaserPower] = useState(150);
  const [exposure, setExposure] = useState(1560);
  const [whiteBalance, setWhiteBalance] = useState(4600);
  
  const [hMin, setHMin] = useState(35);
  const [hMax, setHMax] = useState(85);
  const [sMin, setSMin] = useState(40);
  const [sMax, setSMax] = useState(255);
  const [vMin, setVMin] = useState(40);
  const [vMax, setVMax] = useState(255);

  const [filterWindow, setFilterWindow] = useState(8);
  const [processNoise, setProcessNoise] = useState(1e-4);
  const [measurementNoise, setMeasurementNoise] = useState(1e-2);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeString(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
      setDateString(now.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Sync from props if not dragging
  const isDraggingRef = useRef(false);

  // Arm Calibration State and Handlers
  const [calibration, setCalibration] = useState({ calib_left: {}, calib_right: {} });
  const [calibInputValues, setCalibInputValues] = useState({});

  const fetchCalibration = async () => {
    try {
      const res = await fetch("/api/research/balancer/calibration");
      const data = await res.json();
      if (res.ok) {
        setCalibration(data);
      }
    } catch (e) {
      console.error("Failed to fetch calibration", e);
    }
  };

  useEffect(() => {
    fetchCalibration();
  }, []);

  const handleTorqueArm = async (arm, enable) => {
    try {
      const res = await fetch("/api/torque", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motor_id: arm, enable })
      });
      if (!res.ok) {
        const err = await res.json();
        alert(`Failed to set torque: ${err.detail || 'Unknown error'}`);
      }
    } catch (e) {
      console.error("Failed to toggle arm torque", e);
    }
  };

  const handleTorqueMotor = async (motorId, enable) => {
    try {
      const res = await fetch("/api/torque", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motor_id: String(motorId), enable })
      });
      if (!res.ok) {
        const err = await res.json();
        alert(`Failed to toggle motor torque: ${err.detail || 'Unknown error'}`);
      }
    } catch (e) {
      console.error("Failed to toggle motor torque", e);
    }
  };

  const handleCaptureCalibration = async (arm) => {
    try {
      const res = await fetch("/api/research/balancer/calibration/capture", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ arm })
      });
      const data = await res.json();
      if (res.ok) {
        alert(`${arm.toUpperCase()} arm calibration captured successfully!`);
        fetchCalibration();
      } else {
        alert(`Capture failed: ${data.detail || 'Unknown error'}`);
      }
    } catch (e) {
      console.error("Failed to capture calibration", e);
    }
  };

  const handleSaveCalibration = async () => {
    try {
      const res = await fetch("/api/research/balancer/calibration/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(calibration)
      });
      if (res.ok) {
        alert("Calibration offsets saved to chiman_calibration.json successfully!");
        fetchCalibration();
      } else {
        const err = await res.json();
        alert(`Save failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (e) {
      console.error("Failed to save calibration", e);
    }
  };

  useEffect(() => {
    if (!isDraggingRef.current && balancerData?.vision_details?.camera_settings) {
      const s = balancerData.vision_details.camera_settings;
      if (s.laser_power !== undefined) setLaserPower(s.laser_power);
      if (s.exposure_us !== undefined) setExposure(s.exposure_us);
      if (s.white_balance_temp !== undefined) setWhiteBalance(s.white_balance_temp);
      if (s.hsv_bounds) {
        setHMin(s.hsv_bounds.h_low ?? 35);
        setHMax(s.hsv_bounds.h_high ?? 85);
        setSMin(s.hsv_bounds.s_low ?? 40);
        setSMax(s.hsv_bounds.s_high ?? 255);
        setVMin(s.hsv_bounds.v_low ?? 40);
        setVMax(s.hsv_bounds.v_high ?? 255);
      }
      if (s.filter_window !== undefined) setFilterWindow(s.filter_window);
      if (s.filter_process_noise !== undefined) setProcessNoise(s.filter_process_noise);
      if (s.filter_measurement_noise !== undefined) setMeasurementNoise(s.filter_measurement_noise);
    }
  }, [balancerData]);

  const updateCameraSettings = async (newSettings) => {
    try {
      await fetch("/api/perception/realsense/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newSettings)
      });
    } catch (e) {
      console.error("Failed to update camera settings", e);
    }
  };
  
  // History for Recharts plot
  const [history, setHistory] = useState([]);

  // Pose Sequence Editor state
  const [sequences, setSequences] = useState([]);
  const [activeSeqIndex, setActiveSeqIndex] = useState(0);
  const [playbackLoop, setPlaybackLoop] = useState(1);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [selectedStepIndex, setSelectedStepIndex] = useState(0);
  const [seqInputValues, setSeqInputValues] = useState({});

  // Sync state parameters from backend
  useEffect(() => {
    if (!isDraggingRef.current && balancerData) {
      if (balancerData.kp !== undefined) setKp(balancerData.kp);
      if (balancerData.kd !== undefined) setKd(balancerData.kd);
      if (balancerData.ki !== undefined) setKi(balancerData.ki);
      if (balancerData.speed_multiplier !== undefined) setSpeed(balancerData.speed_multiplier);
      if (balancerData.max_tilt_positive !== undefined) setMaxTiltPos(balancerData.max_tilt_positive);
      if (balancerData.max_tilt_negative !== undefined) setMaxTiltNeg(balancerData.max_tilt_negative);
      if (balancerData.auto_tune_enabled !== undefined) setAutoTune(balancerData.auto_tune_enabled);
      if (balancerData.loadcell?.port !== undefined && !selectedPort) setSelectedPort(balancerData.loadcell.port);
      if (balancerData.ball_weight_ref !== undefined) setBallWeightRef(balancerData.ball_weight_ref);
    }
  }, [balancerData, selectedPort]);

  const fetchPorts = async () => {
    try {
      const res = await fetch("/api/research/balancer/loadcell/ports");
      if (res.ok) {
        const data = await res.json();
        setAvailablePorts(data.ports || []);
        if (data.ports?.length > 0 && !selectedPort) {
          setSelectedPort(data.ports[0]);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchPorts();
  }, []);

  // Handle local tuning gain applications
  const handleApplyConfig = () => {
    onTune({ kp, kd, ki, speed, max_tilt_positive: maxTiltPos, max_tilt_negative: maxTiltNeg, provider: "vision", auto_tune: false });
  };

  const handleSliderRelease = () => {
    isDraggingRef.current = false;
    onTune({ kp, kd, ki, speed, max_tilt_positive: maxTiltPos, max_tilt_negative: maxTiltNeg, provider: "vision", auto_tune: false });
  };

  const handleToggleAutoTune = (val) => {
    setAutoTune(val);
    onTune({ kp, kd, ki, speed, max_tilt_positive: maxTiltPos, max_tilt_negative: maxTiltNeg, provider: "vision", auto_tune: val });
  };

  // Keep a sliding window of past parameters
  useEffect(() => {
    if (balancerData?.is_active && balancerData?.data) {
      setHistory(prev => {
        const next = [
          ...prev,
          {
            time: new Date().toLocaleTimeString().split(" ")[0],
            pos: Math.round((balancerData.data.ball_error ?? balancerData.data.ball_y / 0.22 ?? 0.0) * 100), // percent error [-100, 100]
            tilt: Math.round((balancerData.data.delta_z ?? 0.0) * 1000) // mm delta
          }
        ];
        if (next.length > 50) next.shift();
        return next;
      });
    }
  }, [balancerData]);

  // Collect system identification and adaptive learning logs from telemetry
  useEffect(() => {
    if (balancerData?.data?.est_a !== undefined) {
      const now = new Date().toLocaleTimeString().split(" ")[0];
      setLearningLog(prev => {
        if (prev.length > 0) {
          const last = prev[prev.length - 1];
          if (last.a === balancerData.data.est_a && last.b === balancerData.data.est_b && last.kp === balancerData.kp) {
            return prev;
          }
        }
        const next = [
          ...prev,
          {
            time: now,
            a: balancerData.data.est_a,
            b: balancerData.data.est_b,
            kp: balancerData.kp,
            kd: balancerData.kd,
            status: balancerData.auto_tune_enabled ? "AUTO" : "MANUAL"
          }
        ];
        if (next.length > 6) next.shift();
        return next;
      });
    }
  }, [balancerData?.data?.est_a, balancerData?.data?.est_b, balancerData?.kp, balancerData?.kd, balancerData?.auto_tune_enabled]);

  // Load Sequences API calls
  const fetchSequences = async () => {
    try {
      const res = await fetch("/api/research/balancer/sequences");
      const data = await res.json();
      if (res.ok) {
        setSequences(data);
      }
    } catch (e) {
      console.error("Failed to load balancer sequences", e);
    }
  };

  useEffect(() => {
    fetchSequences();
  }, []);

  const handleSaveSequences = async (updatedSeqs) => {
    try {
      const res = await fetch("/api/research/balancer/sequences/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sequences: updatedSeqs || sequences })
      });
      if (res.ok) {
        alert("Sequences saved successfully!");
        fetchSequences();
      }
    } catch (e) {
      console.error("Failed to save sequences", e);
    }
  };

  const handlePlaySequence = async (name) => {
    try {
      await fetch("/api/research/balancer/sequences/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, loop: playbackLoop, speed: playbackSpeed })
      });
    } catch (e) {
      console.error("Failed to play sequence", e);
    }
  };

  const handleStopSequence = async () => {
    try {
      await fetch("/api/research/balancer/sequences/stop", { method: "POST" });
    } catch (e) {
      console.error("Failed to stop sequence", e);
    }
  };

  const handlePreviewStep = async (step) => {
    try {
      await fetch("/api/research/balancer/sequences/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ modifications: step.modifications })
      });
    } catch (e) {
      console.error("Failed to preview step", e);
    }
  };

  // Sequence CRUD operations
  const handleAddSequence = () => {
    const newSeq = {
      name: `New Sequence ${sequences.length + 1}`,
      steps: [
        { delay: 20, modifications: {} }
      ]
    };
    const next = [...sequences, newSeq];
    setSequences(next);
    setActiveSeqIndex(next.length - 1);
    setSelectedStepIndex(0);
  };

  const handleDeleteSequence = (index) => {
    if (sequences.length <= 1) {
      alert("You must keep at least one sequence.");
      return;
    }
    const next = sequences.filter((_, i) => i !== index);
    setSequences(next);
    setActiveSeqIndex(0);
    setSelectedStepIndex(0);
  };

  // Steps CRUD operations
  const activeSeq = sequences[activeSeqIndex];

  const handleAddStep = () => {
    if (!activeSeq) return;
    const newStep = {
      delay: 20,
      modifications: activeSeq.steps.length > 0 
        ? JSON.parse(JSON.stringify(activeSeq.steps[activeSeq.steps.length - 1].modifications))
        : {}
    };
    const updatedSteps = [...activeSeq.steps, newStep];
    const updatedSeq = { ...activeSeq, steps: updatedSteps };
    const next = [...sequences];
    next[activeSeqIndex] = updatedSeq;
    setSequences(next);
    setSelectedStepIndex(updatedSteps.length - 1);
  };

  const handleDeleteStep = (stepIdx) => {
    if (!activeSeq) return;
    if (activeSeq.steps.length <= 1) {
      alert("You must keep at least one step in a sequence.");
      return;
    }
    const updatedSteps = activeSeq.steps.filter((_, i) => i !== stepIdx);
    const updatedSeq = { ...activeSeq, steps: updatedSteps };
    const next = [...sequences];
    next[activeSeqIndex] = updatedSeq;
    setSequences(next);
    setSelectedStepIndex(0);
  };

  const handleUpdateStepDelay = (stepIdx, val) => {
    if (!activeSeq) return;
    const updatedSteps = [...activeSeq.steps];
    updatedSteps[stepIdx].delay = parseInt(val) || 10;
    const updatedSeq = { ...activeSeq, steps: updatedSteps };
    const next = [...sequences];
    next[activeSeqIndex] = updatedSeq;
    setSequences(next);
  };

  const handleUpdateStepJoint = (stepIdx, jointName, val) => {
    if (!activeSeq) return;
    const updatedSteps = [...activeSeq.steps];
    updatedSteps[stepIdx].modifications[jointName] = parseInt(val);
    const updatedSeq = { ...activeSeq, steps: updatedSteps };
    const next = [...sequences];
    next[activeSeqIndex] = updatedSeq;
    setSequences(next);
  };

  const handleCaptureCurrentPose = (stepIdx) => {
    if (!activeSeq || !limits) return;
    const mods = {};
    Object.keys(limits).forEach((mid) => {
      const info = limits[mid];
      const telemData = telemetry[mid];
      if (telemData && telemData.present !== "--") {
        const presentVal = parseInt(telemData.present);
        const offsetVal = presentVal - info.default;
        mods[info.name] = offsetVal;
      }
    });
    const updatedSteps = [...activeSeq.steps];
    updatedSteps[stepIdx].modifications = mods;
    const updatedSeq = { ...activeSeq, steps: updatedSteps };
    const next = [...sequences];
    next[activeSeqIndex] = updatedSeq;
    setSequences(next);
  };

  const handleMoveStep = (stepIdx, direction) => {
    if (!activeSeq) return;
    const steps = [...activeSeq.steps];
    const targetIdx = stepIdx + direction;
    if (targetIdx < 0 || targetIdx >= steps.length) return;
    const temp = steps[stepIdx];
    steps[stepIdx] = steps[targetIdx];
    steps[targetIdx] = temp;
    
    const updatedSeq = { ...activeSeq, steps };
    const next = [...sequences];
    next[activeSeqIndex] = updatedSeq;
    setSequences(next);
    setSelectedStepIndex(targetIdx);
  };

  const active = balancerData?.is_active ?? false;

  // Compute live center coordinates and LHS/RHS decisions
  const visDetails = balancerData?.vision_details || {};
  const frameWidth = visDetails.frame_width || 1280;
  const frameHeight = visDetails.frame_height || 720;
  const ballCenter = visDetails.ball_center || [0, 0];
  const ballStateRaw = visDetails.ball_state || "LOST_BALL";
  
  const hasBall = visDetails.ball_state && !visDetails.ball_state.startsWith("LOST");
  
  const centerX = frameWidth / 2;
  const centerY = frameHeight / 2;
  
  // Ball pixel coordinates relative to camera center
  const xPx = hasBall ? Math.round(ballCenter[0] - centerX) : 0;
  const yPx = hasBall ? Math.round(centerY - ballCenter[1]) : 0;
  
  // Deadband check for CENTER decision
  const isCenter = hasBall ? Math.abs(xPx) < deadband : false;
  
  // Ball side relative to camera center
  let ballSide = "BALL LOST";
  let sideColorClass = "text-red-400 bg-red-500/10 border-red-500/20";
  
  if (hasBall) {
    if (isCenter) {
      ballSide = "CENTERED";
      sideColorClass = "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    } else if (xPx < 0) {
      ballSide = "LEFT HAND SIDE";
      sideColorClass = "text-amber-400 bg-amber-500/10 border-amber-500/20";
    } else {
      ballSide = "RIGHT HAND SIDE";
      sideColorClass = "text-[#B5ACF3] bg-[#B5ACF3]/10 border-[#B5ACF3]/20";
    }
  } else if (ballStateRaw === "LOST_MARKERS") {
    ballSide = "LOST MARKERS";
    sideColorClass = "text-rose-500 bg-rose-500/10 border-rose-500/20";
  }

  // Active Control Scenario state
  const activeScenario = balancerData?.data?.active_scenario || "NOMINAL";
  let scenarioColorClass = "text-slate-400 bg-slate-500/10 border-slate-500/20";
  if (activeScenario === "FINE_TUNING") {
    scenarioColorClass = "text-[#CFFF3E] bg-[#CFFF3E]/10 border-[#CFFF3E]/20";
  } else if (activeScenario === "PREEMPTIVE_BRAKING") {
    scenarioColorClass = "text-sky-400 bg-sky-500/10 border-sky-500/20 animate-pulse";
  } else if (activeScenario === "EMERGENCY_RETRIEVE") {
    scenarioColorClass = "text-rose-400 bg-rose-500/10 border-rose-500/20 animate-pulse font-black";
  } else if (activeScenario === "STUCK_RECOVERY") {
    scenarioColorClass = "text-amber-400 bg-amber-500/10 border-amber-500/20 animate-pulse";
  }

  // Ball 3D coordinates relative to camera optical center (in mm)
  const xyz = visDetails.ball_xyz_mm || [0.0, 0.0, 0.0];
  const xMm = xyz[0];
  const yMm = -xyz[1]; // +Y is up for UI display
  const zMm = xyz[2];

  const ballX3d = visDetails.ball_x_3d_filtered !== undefined ? visDetails.ball_x_3d_filtered : visDetails.ball_x_3d || 0.0;
  const ballY3d = visDetails.ball_y_3d_filtered !== undefined ? visDetails.ball_y_3d_filtered : visDetails.ball_y_3d || 0.0;

  // Sequence status text
  const seqStatus = balancerData?.sequence_status || {};

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 font-sans">
      
      {/* 1. Left Panel: Controller Configuration */}
      <div className="bg-[#191A1B] p-5 rounded-2xl border border-slate-800 flex flex-col gap-4 text-slate-300">
        <div className="flex items-center gap-2 text-white font-bold text-sm tracking-wider uppercase border-b border-slate-800 pb-2">
          <Settings className="h-4 w-4 text-[#CFFF3E]" />
          <span>Tuning Controls</span>
        </div>

        {/* Start / Stop Toggle */}
        <button
          onClick={() => onToggle(!active)}
          className={`w-full py-3.5 rounded-xl font-bold uppercase tracking-wider text-xs flex items-center justify-center gap-2 transition ${
            active 
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25" 
              : "bg-[#1e293b] text-slate-400 border border-slate-700 hover:text-white hover:bg-slate-800"
          }`}
        >
          {active ? (
            <>
              <Square className="h-4 w-4 fill-current" />
              <span>Auto balancer: ON</span>
            </>
          ) : (
            <>
              <Play className="h-4 w-4 fill-current" />
              <span>Auto balancer: OFF</span>
            </>
          )}
        </button>

        <button
          onClick={onGoToStart}
          className="w-full py-2.5 rounded-xl font-bold uppercase tracking-wider text-[10px] bg-slate-800 text-white border border-slate-700/80 hover:bg-slate-700 transition flex items-center justify-center gap-2"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Move to Start Pose</span>
        </button>

        <button
          onClick={onInitializeArms}
          className="w-full py-2.5 rounded-xl font-bold uppercase tracking-wider text-[10px] bg-slate-800 text-white border border-slate-700/80 hover:bg-slate-700 transition flex items-center justify-center gap-2"
        >
          <Compass className="h-3.5 w-3.5 text-[#B5ACF3]" />
          <span>Initialize Arm Position</span>
        </button>

        {/* Read-Only Feedback Provider Status (Hides force cells dropdown per requirements) */}
        <div className="flex flex-col gap-1.5 mt-2">
          <label className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Feedback Provider</label>
          <div className="bg-[#242628] border border-slate-700/80 rounded-xl px-3 py-2 text-white text-xs font-semibold flex items-center gap-2">
            <Crosshair className="h-3.5 w-3.5 text-[#CFFF3E]" />
            <span>Vision System (RealSense D415)</span>
          </div>
        </div>

        {/* PID Gains Sliders */}
        <div className="flex flex-col gap-3.5 mt-2">
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-slate-400">Proportional Gain (Kp)</span>
              <span className="text-white font-mono">{kp.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="3.0"
              step="0.05"
              value={kp}
              onMouseDown={() => { isDraggingRef.current = true; }}
              onTouchStart={() => { isDraggingRef.current = true; }}
              onMouseUp={handleSliderRelease}
              onTouchEnd={handleSliderRelease}
              onChange={(e) => setKp(parseFloat(e.target.value))}
              className="accent-[#CFFF3E]"
            />
          </div>

          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-slate-400">Derivative Gain (Kd)</span>
              <span className="text-white font-mono">{kd.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="2.0"
              step="0.05"
              value={kd}
              onMouseDown={() => { isDraggingRef.current = true; }}
              onTouchStart={() => { isDraggingRef.current = true; }}
              onMouseUp={handleSliderRelease}
              onTouchEnd={handleSliderRelease}
              onChange={(e) => setKd(parseFloat(e.target.value))}
              className="accent-[#CFFF3E]"
            />
          </div>

          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-slate-400">Integral Gain (Ki)</span>
              <span className="text-white font-mono">{ki.toFixed(3)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="0.5"
              step="0.01"
              value={ki}
              onMouseDown={() => { isDraggingRef.current = true; }}
              onTouchStart={() => { isDraggingRef.current = true; }}
              onMouseUp={handleSliderRelease}
              onTouchEnd={handleSliderRelease}
              onChange={(e) => setKi(parseFloat(e.target.value))}
              className="accent-[#CFFF3E]"
            />
          </div>
        </div>

        {/* Speed Multiplier Slider */}
        <div className="flex flex-col gap-1.5 mt-2 border-t border-slate-800 pt-4">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-slate-400">Balancing Speed</span>
            <span className={`font-mono px-2 py-0.5 rounded-md text-[10px] font-bold ${
              speed < 0.7 ? "text-sky-400 bg-sky-500/10" :
              speed > 1.4 ? "text-rose-400 bg-rose-500/10" :
              "text-[#CFFF3E] bg-[#CFFF3E]/10"
            }`}>
              {speed.toFixed(2)}x
            </span>
          </div>
          <input
            type="range"
            min="0.1"
            max="2.0"
            step="0.05"
            value={speed}
            onMouseDown={() => { isDraggingRef.current = true; }}
            onTouchStart={() => { isDraggingRef.current = true; }}
            onMouseUp={handleSliderRelease}
            onTouchEnd={handleSliderRelease}
            onChange={(e) => setSpeed(parseFloat(e.target.value))}
            className="accent-[#CFFF3E] w-full"
          />
          <div className="flex justify-between text-[9px] text-slate-600 font-mono mt-0.5">
            <span>0.1x Cautious</span>
            <span className="text-slate-500">1.0x Default</span>
            <span>2.0x Aggressive</span>
          </div>
        </div>

        {/* Max Tilt Sliders */}
        <div className="flex flex-col gap-3.5 mt-2 border-t border-slate-800 pt-4">
          <label className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Max Tilt Range</label>

          {/* Positive (up) tilt */}
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-slate-400">Max Tilt Up (+)</span>
              <span className="font-mono text-[#CFFF3E] bg-[#CFFF3E]/10 px-2 py-0.5 rounded-md text-[10px] font-bold">
                {maxTiltPos} units
              </span>
            </div>
            <input
              type="range"
              min="10"
              max="400"
              step="5"
              value={maxTiltPos}
              onMouseDown={() => { isDraggingRef.current = true; }}
              onTouchStart={() => { isDraggingRef.current = true; }}
              onMouseUp={handleSliderRelease}
              onTouchEnd={handleSliderRelease}
              onChange={(e) => setMaxTiltPos(parseInt(e.target.value))}
              className="accent-[#CFFF3E] w-full"
            />
            <div className="flex justify-between text-[9px] text-slate-600 font-mono mt-0.5">
              <span>10 (Min)</span>
              <span className="text-slate-500">150 (Default)</span>
              <span>400 (Max)</span>
            </div>
          </div>

          {/* Negative (down) tilt */}
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-slate-400">Max Tilt Down (−)</span>
              <span className="font-mono text-[#CFFF3E] bg-[#CFFF3E]/10 px-2 py-0.5 rounded-md text-[10px] font-bold">
                {maxTiltNeg} units
              </span>
            </div>
            <input
              type="range"
              min="10"
              max="400"
              step="5"
              value={maxTiltNeg}
              onMouseDown={() => { isDraggingRef.current = true; }}
              onTouchStart={() => { isDraggingRef.current = true; }}
              onMouseUp={handleSliderRelease}
              onTouchEnd={handleSliderRelease}
              onChange={(e) => setMaxTiltNeg(parseInt(e.target.value))}
              className="accent-[#CFFF3E] w-full"
            />
            <div className="flex justify-between text-[9px] text-slate-600 font-mono mt-0.5">
              <span>10 (Min)</span>
              <span className="text-slate-500">178 (Default)</span>
              <span>400 (Max)</span>
            </div>
          </div>
        </div>

        <button
          onClick={handleApplyConfig}
          className="w-full bg-slate-800 text-white font-bold uppercase tracking-wider py-2.5 rounded-xl text-[10px] mt-2 border border-slate-700/80 hover:bg-slate-750 transition"
        >
          Apply Tuning Profile
        </button>

        {/* Quick Presets Deck */}
        <div className="flex flex-col gap-2 mt-2 border-t border-slate-800 pt-4">
          <label className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Quick Target Presets</label>
          
          <button
            onClick={() => onSendCommand("both_arms")}
            disabled={!connected}
            className="w-full py-2.5 rounded-xl font-bold uppercase tracking-wider text-[10px] bg-slate-800 text-[#CFFF3E] border border-slate-700/80 hover:bg-slate-700 transition disabled:opacity-40"
          >
            Go To Both Arms Pose
          </button>
          
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => onSendCommand("left_pose")}
              disabled={!connected}
              className="py-2.5 rounded-xl font-bold uppercase tracking-wider text-[10px] bg-slate-800 text-white border border-slate-700/80 hover:bg-slate-700 transition disabled:opacity-40"
            >
              Left Arm Pose
            </button>
            <button
              onClick={() => onSendCommand("right_pose")}
              disabled={!connected}
              className="py-2.5 rounded-xl font-bold uppercase tracking-wider text-[10px] bg-slate-800 text-white border border-slate-700/80 hover:bg-slate-700 transition disabled:opacity-40"
            >
              Right Arm Pose
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 mt-1">
            <button
              onClick={() => onSendCommand("tilt_up")}
              disabled={!connected}
              className="py-2 rounded-xl font-bold uppercase tracking-wider text-[9px] bg-slate-800 text-white border border-slate-700/80 hover:bg-slate-700 transition disabled:opacity-40"
            >
              Tilt Up
            </button>
            <button
              onClick={() => onSendCommand("tilt_center")}
              disabled={!connected}
              className="py-2 rounded-xl font-bold uppercase tracking-wider text-[9px] bg-slate-800 text-white border border-slate-700/80 hover:bg-slate-700 transition disabled:opacity-40"
            >
              Centre
            </button>
            <button
              onClick={() => onSendCommand("tilt_down")}
              disabled={!connected}
              className="py-2 rounded-xl font-bold uppercase tracking-wider text-[9px] bg-slate-800 text-white border border-slate-700/80 hover:bg-slate-700 transition disabled:opacity-40"
            >
              Tilt Down
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 mt-1">
            <button
              onClick={() => onSendCommand("gripper_open")}
              disabled={!connected}
              className="py-2 rounded-xl font-bold uppercase tracking-wider text-[9px] bg-slate-800 text-white border border-slate-700/80 hover:bg-slate-700 transition disabled:opacity-40"
            >
              Open Gripper
            </button>
            <button
              onClick={() => onSendCommand("gripper_closed")}
              disabled={!connected}
              className="py-2 rounded-xl font-bold uppercase tracking-wider text-[9px] bg-slate-800 text-white border border-slate-700/80 hover:bg-slate-700 transition disabled:opacity-40"
            >
              Close Gripper
            </button>
          </div>
        </div>
      </div>

      {/* 2. Middle & Right merged: Research Applications Panel */}
      <div className="lg:col-span-2 bg-[#191A1B] p-5 rounded-2xl border border-slate-800 flex flex-col gap-4 text-slate-300">
        
        {/* Device Status Bar Mockup */}
        {activeApp !== "home" && (
          <div className="flex justify-between items-center bg-[#151618] border border-slate-850 px-4 py-1.5 rounded-xl text-[10px] font-mono text-slate-500 select-none">
            <span>{timeString || "12:00 PM"}</span>
            <span className="text-[#CFFF3E] font-bold tracking-wider uppercase text-[8px]">
              {activeApp === "vision" ? "Camera Vision App" :
               activeApp === "tune" ? "Physics Auto-Tuner App" :
               activeApp === "loadcell" ? "Load Cell Setup App" :
               activeApp === "sequence" ? "Pose Sequences App" :
               activeApp === "calibration" ? "Arm Calibration App" : "OSRS System App"}
            </span>
            <div className="flex items-center gap-1.5">
              <span className={connected ? "text-emerald-500" : "text-rose-500"}>{connected ? "📶" : "📶 Offline"}</span>
              <span>🔋 100%</span>
            </div>
          </div>
        )}

        {/* Back Navigation Action Bar */}
        {activeApp !== "home" && (
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <button
              onClick={() => setActiveApp("home")}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-[10px] font-black uppercase tracking-wider transition hover:scale-102 active:scale-95"
            >
              <span>← Back to Launcher</span>
            </button>
            
            <div className="flex items-center gap-2">
              {seqStatus.is_playing && (
                <span className="text-[9px] bg-amber-500/10 text-amber-400 px-2.5 py-1 rounded-lg border border-amber-500/20 font-black animate-pulse uppercase tracking-wider">
                  Playing Step {seqStatus.current_step}/{seqStatus.total_steps}
                </span>
              )}
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest bg-slate-900 px-3 py-1 rounded-lg border border-slate-800">
                Pipeline: 30Hz
              </span>
            </div>
          </div>
        )}

        {/* Launcher Home Screen App */}
        {activeApp === "home" && (
          <div className="flex flex-col gap-6 animate-fade-in text-slate-300 w-full min-h-[500px]">
            {/* Top widgets layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
              
              {/* Clock Widget */}
              <div className="bg-gradient-to-br from-slate-900/60 to-slate-950/60 backdrop-blur-xl border border-slate-850 p-6 rounded-3xl flex flex-col justify-center items-center text-center gap-2 min-h-[160px] relative overflow-hidden shadow-2xl">
                <div className="absolute top-0 right-0 w-32 h-32 bg-[#CFFF3E]/5 blur-3xl rounded-full" />
                <span className="text-4xl md:text-5xl font-black tracking-tight text-white drop-shadow-md">
                  {timeString || "12:00 PM"}
                </span>
                <span className="text-xs text-[#CFFF3E] font-bold uppercase tracking-wider">
                  {dateString || "Loading Date..."}
                </span>
                <span className="text-[9px] text-slate-500 font-mono mt-1 uppercase tracking-widest">
                  OSRS SMART ECOSYSTEM v1.4
                </span>
              </div>

              {/* Status Widget */}
              <div className="bg-[#1b1c1e]/60 backdrop-blur-xl border border-slate-850 p-6 rounded-3xl flex flex-col justify-between min-h-[160px] shadow-2xl">
                <div className="flex justify-between items-start">
                  <div className="flex flex-col">
                    <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">System Connectivity</span>
                    <span className={`text-sm font-black mt-0.5 ${connected ? "text-emerald-400" : "text-rose-400"}`}>
                      {connected ? "● Connected" : "● Offline"}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800">
                    Pipeline: 30Hz
                  </span>
                </div>
                
                <div className="flex justify-between items-end border-t border-slate-850/60 pt-4 mt-2 font-mono text-[10px]">
                  <div className="flex flex-col">
                    <span className="text-slate-500">Feedback Provider</span>
                    <span className="text-[#CFFF3E] font-bold uppercase mt-0.5">
                      {balancerData?.provider === "vision" ? "Camera Vision" : balancerData?.provider === "force" ? "Load Cell Sensors" : "Fusion"}
                    </span>
                  </div>
                  <div className="flex flex-col text-right">
                    <span className="text-slate-500">Ball Stability</span>
                    <span className="text-white font-bold mt-0.5">
                      {balancerData?.exploration_mode 
                        ? `${Math.round((balancerData?.exploration_progress ?? 0) * 100)}%` 
                        : (hasBall ? "Stabilizing" : "No Ball Detected")
                      }
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* App Icons Grid */}
            <div className="flex flex-col gap-3 mt-4">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono px-1"> E-SYSTEM APPLICATIONS </span>
              
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-4">
                
                {/* App 1: Vision Stream */}
                <div 
                  onClick={() => setActiveApp("vision")}
                  className="bg-slate-900/40 backdrop-blur-md border border-slate-850/80 p-4 rounded-2xl flex flex-col items-center justify-center gap-2.5 hover:bg-[#CFFF3E]/10 hover:border-[#CFFF3E]/20 hover:scale-105 active:scale-95 transition cursor-pointer text-center group aspect-square max-w-[120px] mx-auto w-full shadow-lg"
                >
                  <div className="p-3 rounded-2xl bg-sky-500/10 text-sky-400 group-hover:bg-sky-500/25 transition">
                    <Video className="h-6 w-6" />
                  </div>
                  <span className="text-[10px] font-black uppercase text-slate-350 tracking-wider leading-none">Camera Vision</span>
                </div>

                {/* App 2: PID Controller */}
                <div 
                  onClick={() => setActiveApp("tune")}
                  className="bg-slate-900/40 backdrop-blur-md border border-slate-850/80 p-4 rounded-2xl flex flex-col items-center justify-center gap-2.5 hover:bg-[#CFFF3E]/10 hover:border-[#CFFF3E]/20 hover:scale-105 active:scale-95 transition cursor-pointer text-center group aspect-square max-w-[120px] mx-auto w-full shadow-lg"
                >
                  <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-400 group-hover:bg-amber-500/25 transition">
                    <Sliders className="h-6 w-6" />
                  </div>
                  <span className="text-[10px] font-black uppercase text-slate-350 tracking-wider leading-none">PID Controls</span>
                </div>

                {/* App 3: Model Training */}
                <div 
                  onClick={() => setActiveApp("training")}
                  className="bg-slate-900/40 backdrop-blur-md border border-slate-850/80 p-4 rounded-2xl flex flex-col items-center justify-center gap-2.5 hover:bg-[#CFFF3E]/10 hover:border-[#CFFF3E]/20 hover:scale-105 active:scale-95 transition cursor-pointer text-center group aspect-square max-w-[120px] mx-auto w-full shadow-lg"
                >
                  <div className="p-3 rounded-2xl bg-fuchsia-500/10 text-fuchsia-400 group-hover:bg-fuchsia-500/25 transition">
                    <Cpu className="h-6 w-6" />
                  </div>
                  <span className="text-[10px] font-black uppercase text-slate-350 tracking-wider leading-none">Model Training</span>
                </div>

                {/* App 4: Load Cell Settings */}
                <div 
                  onClick={() => setActiveApp("loadcell")}
                  className="bg-slate-900/40 backdrop-blur-md border border-slate-850/80 p-4 rounded-2xl flex flex-col items-center justify-center gap-2.5 hover:bg-[#CFFF3E]/10 hover:border-[#CFFF3E]/20 hover:scale-105 active:scale-95 transition cursor-pointer text-center group aspect-square max-w-[120px] mx-auto w-full shadow-lg"
                >
                  <div className="p-3 rounded-2xl bg-purple-500/10 text-purple-400 group-hover:bg-purple-500/25 transition">
                    <Settings className="h-6 w-6" />
                  </div>
                  <span className="text-[10px] font-black uppercase text-slate-350 tracking-wider leading-none">Load Cells</span>
                </div>

                {/* App 5: Pose Sequences */}
                <div 
                  onClick={() => setActiveApp("sequence")}
                  className="bg-slate-900/40 backdrop-blur-md border border-slate-850/80 p-4 rounded-2xl flex flex-col items-center justify-center gap-2.5 hover:bg-[#CFFF3E]/10 hover:border-[#CFFF3E]/20 hover:scale-105 active:scale-95 transition cursor-pointer text-center group aspect-square max-w-[120px] mx-auto w-full shadow-lg"
                >
                  <div className="p-3 rounded-2xl bg-teal-500/10 text-teal-400 group-hover:bg-teal-500/25 transition">
                    <Crosshair className="h-6 w-6" />
                  </div>
                  <span className="text-[10px] font-black uppercase text-slate-350 tracking-wider leading-none">Pose Editor</span>
                </div>

                {/* App 6: Arm Calibration */}
                <div 
                  onClick={() => setActiveApp("calibration")}
                  className="bg-slate-900/40 backdrop-blur-md border border-slate-850/80 p-4 rounded-2xl flex flex-col items-center justify-center gap-2.5 hover:bg-[#CFFF3E]/10 hover:border-[#CFFF3E]/20 hover:scale-105 active:scale-95 transition cursor-pointer text-center group aspect-square max-w-[120px] mx-auto w-full shadow-lg"
                >
                  <div className="p-3 rounded-2xl bg-rose-500/10 text-rose-400 group-hover:bg-rose-500/25 transition">
                    <Compass className="h-6 w-6" />
                  </div>
                  <span className="text-[10px] font-black uppercase text-slate-350 tracking-wider leading-none">Arm Calib</span>
                </div>

              </div>
            </div>

            {/* Android Home Screen Dock */}
            <div className="mt-auto pt-6 border-t border-slate-850/60 w-full max-w-[520px] mx-auto pb-2">
              <div className="bg-slate-900/50 backdrop-blur-2xl border border-slate-800/80 p-3 rounded-2xl flex justify-around items-center shadow-xl">
                <div onClick={() => setActiveApp("vision")} className="p-2 rounded-xl text-sky-400 hover:bg-sky-500/10 active:scale-90 transition cursor-pointer" title="Vision">
                  <Video className="h-5 w-5" />
                </div>
                <div onClick={() => setActiveApp("tune")} className="p-2 rounded-xl text-amber-400 hover:bg-amber-500/10 active:scale-90 transition cursor-pointer" title="PID Controls">
                  <Sliders className="h-5 w-5" />
                </div>
                <div onClick={() => setActiveApp("training")} className="p-2 rounded-xl text-fuchsia-400 hover:bg-fuchsia-500/10 active:scale-90 transition cursor-pointer" title="Model Training">
                  <Cpu className="h-5 w-5" />
                </div>
                <div onClick={() => setActiveApp("loadcell")} className="p-2 rounded-xl text-purple-400 hover:bg-purple-500/10 active:scale-90 transition cursor-pointer" title="Load Cells">
                  <Settings className="h-5 w-5" />
                </div>
                <div onClick={() => setActiveApp("calibration")} className="p-2 rounded-xl text-rose-400 hover:bg-rose-500/10 active:scale-90 transition cursor-pointer" title="Arm Calibration">
                  <Compass className="h-5 w-5" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Vision System Application */}
        {activeApp === "vision" && (
          <div className="flex flex-col gap-4">
            
            {/* Live Feed Monitor */}
            {cameraActive && videoFrame ? (
              <div className="relative border border-slate-800 rounded-xl overflow-hidden bg-black max-w-full flex items-center justify-center">
                <img 
                  src={`data:image/jpeg;base64,${videoFrame}`} 
                  className="w-full max-h-[360px] object-contain block" 
                  alt="RealSense D415 Stream" 
                />
                
                {/* HUD Overlay for Active Scenario */}
                <div className="absolute top-3 left-3">
                  <span className={`px-3 py-1 text-[10px] font-black uppercase tracking-wider rounded-lg border shadow-lg ${scenarioColorClass}`}>
                    Model: {activeScenario.replace("_", " ")}
                  </span>
                </div>
                
                {/* HUD Overlay for Side Decision */}
                <div className="absolute top-3 right-3">
                  <span className={`px-3 py-1 text-[10px] font-black uppercase tracking-wider rounded-lg border shadow-lg ${sideColorClass}`}>
                    {ballSide}
                  </span>
                </div>
              </div>
            ) : (
              <div className="w-full h-[280px] border border-slate-800 rounded-xl bg-[#161719] flex flex-col items-center justify-center gap-4 text-center px-4">
                <div className="p-4 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 animate-pulse">
                  <Video className="h-8 w-8" />
                </div>
                <div>
                  <h4 className="font-bold text-white text-sm">RealSense D415i Camera Offline</h4>
                  <p className="text-[10px] text-slate-500 max-w-[240px] mt-1 mx-auto">The background vision acquisition pipeline is stopped. Enable camera stream to view live feedback and coordinates.</p>
                </div>
                <button
                  onClick={onToggleVision}
                  className="bg-[#CFFF3E] text-slate-900 text-[10px] uppercase font-black px-5 py-2.5 rounded-xl hover:scale-[1.02] active:scale-95 transition"
                >
                  Power On RealSense D415 Camera
                </button>
              </div>
            )}

            {/* Telemetry Readouts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Box 1: Coordinates relative to Plate Center */}
              <div className="bg-[#202123] border border-slate-800/80 p-4 rounded-xl flex flex-col gap-2">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Plate Center Origin (Physical)</span>
                <div className="flex flex-col gap-1 mt-1 font-mono">
                  <div className="flex justify-between text-xs border-b border-slate-800/60 pb-1">
                    <span className="text-slate-500">Plate Dimensions</span>
                    <span className="text-slate-300">380 x 50 mm (Inner)</span>
                  </div>
                  <div className="flex justify-between text-xs border-b border-slate-800/60 pb-1">
                    <span className="text-slate-500">Ball Y (Longitudinal)</span>
                    <span className="text-[#CFFF3E] font-bold">
                      {hasBall ? `${(ballY3d * 1000.0).toFixed(1)} mm` : "N/A"}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs border-b border-slate-800/60 pb-1">
                    <span className="text-slate-500">Ball X (Transverse)</span>
                    <span className="text-[#CFFF3E] font-bold">
                      {hasBall ? `${(ballX3d * 1000.0).toFixed(1)} mm` : "N/A"}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs border-b border-slate-800/60 pb-1">
                    <span className="text-slate-500">Decision State</span>
                    <span className={`font-bold uppercase ${hasBall ? (isCenter ? "text-emerald-400" : "text-amber-400") : "text-red-400"}`}>
                      {ballSide}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs pt-1 font-mono">
                    <span className="text-slate-500">Control Model</span>
                    <span className={`font-bold uppercase ${activeScenario === "NOMINAL" ? "text-slate-400" : activeScenario === "FINE_TUNING" ? "text-[#CFFF3E]" : "text-amber-400 animate-pulse"}`}>
                      {activeScenario.replace("_", " ")}
                    </span>
                  </div>
                </div>
              </div>

              {/* Box 2: Optical Coordinates & Scale */}
              <div className="bg-[#202123] border border-slate-800/80 p-4 rounded-xl flex flex-col gap-2">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Optical telemetry & scaling</span>
                <div className="flex flex-col gap-1 mt-1 font-mono">
                  <div className="flex justify-between text-xs border-b border-slate-800/60 pb-1">
                    <span className="text-slate-500">Raw Pixel Offset</span>
                    <span className="text-white">{hasBall ? `${xPx} px` : "0 px"}</span>
                  </div>
                  <div className="flex justify-between text-xs border-b border-slate-800/60 pb-1">
                    <span className="text-slate-500">Dynamic Resolution Scale</span>
                    <span className="text-white">
                      {visDetails.plate_center ? `${(384.0 / (visDetails.plate_width || 640)).toFixed(3)} mm/px` : "N/A"}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">Depth (Z Position)</span>
                    <span className="text-white">{hasBall ? `${(zMm).toFixed(1)} mm` : "0.0 mm"}</span>
                  </div>
                </div>
              </div>

            </div>

            {/* Camera settings & filters card deck (OSRS style) */}
            <div className="bg-[#202123] border border-slate-800/80 rounded-xl overflow-hidden mt-2">
              {/* Tab Selector */}
              <div className="flex border-b border-slate-800/60 bg-[#161719] p-2 gap-1.5">
                <button
                  onClick={() => setActiveSettingsTab("camera")}
                  className={`flex-1 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded-lg transition ${
                    activeSettingsTab === "camera"
                      ? "bg-[#CFFF3E] text-slate-900 font-extrabold shadow"
                      : "bg-slate-900/60 text-slate-400 hover:text-white"
                  }`}
                >
                  Camera Settings
                </button>
                <button
                  onClick={() => setActiveSettingsTab("color")}
                  className={`flex-1 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded-lg transition ${
                    activeSettingsTab === "color"
                      ? "bg-[#CFFF3E] text-slate-900 font-extrabold shadow"
                      : "bg-slate-900/60 text-slate-400 hover:text-white"
                  }`}
                >
                  Color Tuning (HSV)
                </button>
                <button
                  onClick={() => setActiveSettingsTab("filter")}
                  className={`flex-1 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded-lg transition ${
                    activeSettingsTab === "filter"
                      ? "bg-[#CFFF3E] text-slate-900 font-extrabold shadow"
                      : "bg-slate-900/60 text-slate-400 hover:text-white"
                  }`}
                >
                  Coordinate Filters
                </button>
              </div>

              {/* Tab Content */}
              <div className="p-4 flex flex-col gap-4 text-xs">
                {activeSettingsTab === "camera" && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Column 1: Options */}
                    <div className="flex flex-col gap-3">
                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] font-bold uppercase tracking-wider text-slate-400 font-mono">Visual Preset</label>
                        <select
                          value={balancerData?.vision_details?.camera_settings?.visual_preset ?? 1}
                          onChange={(e) => updateCameraSettings({ visual_preset: parseInt(e.target.value) })}
                          className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-[#CFFF3E] cursor-pointer"
                        >
                          <option value={0}>Custom (0)</option>
                          <option value={1}>Default (1)</option>
                          <option value={2}>Hand (2)</option>
                          <option value={3}>High Accuracy (3)</option>
                          <option value={4}>High Density (4)</option>
                          <option value={5}>Medium Density (5)</option>
                        </select>
                      </div>

                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] font-bold uppercase tracking-wider text-slate-400 font-mono">IR Projector / Emitter</label>
                        <select
                          value={balancerData?.vision_details?.camera_settings?.emitter_state ?? 1}
                          onChange={(e) => updateCameraSettings({ emitter_state: parseInt(e.target.value) })}
                          className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-[#CFFF3E] cursor-pointer"
                        >
                          <option value={0}>Disabled (Off)</option>
                          <option value={1}>Enabled (Laser Projector)</option>
                          <option value={2}>Auto Projector Mode</option>
                        </select>
                      </div>

                      <div className="flex flex-col gap-1">
                        <div className="flex justify-between items-center text-[10px] font-mono">
                          <span className="font-bold text-slate-400 uppercase tracking-wider">Laser Projector Power</span>
                          <span className="text-[#CFFF3E] font-bold">{laserPower} mW</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="360"
                          step="10"
                          value={laserPower}
                          onMouseDown={() => { isDraggingRef.current = true; }}
                          onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ laser_power: laserPower }); }}
                          onChange={(e) => setLaserPower(parseInt(e.target.value))}
                          className="w-full accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none"
                        />
                      </div>
                    </div>

                    {/* Column 2: Exposure & WB */}
                    <div className="flex flex-col gap-3">
                      <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800/80 flex flex-col gap-3">
                        <div className="flex items-center justify-between">
                          <label className="text-[9px] font-bold uppercase tracking-wider text-slate-400 font-mono">Auto Exposure</label>
                          <input
                            type="checkbox"
                            checked={balancerData?.vision_details?.camera_settings?.auto_exposure ?? true}
                            onChange={(e) => updateCameraSettings({ auto_exposure: e.target.checked })}
                            className="w-4 h-4 accent-[#CFFF3E] rounded cursor-pointer"
                          />
                        </div>
                        {!(balancerData?.vision_details?.camera_settings?.auto_exposure ?? true) && (
                          <div className="flex flex-col gap-1 mt-1">
                            <div className="flex justify-between items-center text-[10px] font-mono">
                              <span className="text-slate-400">Exposure Time</span>
                              <span className="text-[#CFFF3E] font-bold">{exposure} us</span>
                            </div>
                            <input
                              type="range"
                              min="20"
                              max="10000"
                              step="50"
                              value={exposure}
                              onMouseDown={() => { isDraggingRef.current = true; }}
                              onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ exposure_us: exposure }); }}
                              onChange={(e) => setExposure(parseInt(e.target.value))}
                              className="w-full accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none"
                            />
                          </div>
                        )}
                      </div>

                      <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800/80 flex flex-col gap-3">
                        <div className="flex items-center justify-between">
                          <label className="text-[9px] font-bold uppercase tracking-wider text-slate-400 font-mono">Auto White Balance</label>
                          <input
                            type="checkbox"
                            checked={balancerData?.vision_details?.camera_settings?.auto_white_balance ?? true}
                            onChange={(e) => updateCameraSettings({ auto_white_balance: e.target.checked })}
                            className="w-4 h-4 accent-[#CFFF3E] rounded cursor-pointer"
                          />
                        </div>
                        {!(balancerData?.vision_details?.camera_settings?.auto_white_balance ?? true) && (
                          <div className="flex flex-col gap-1 mt-1">
                            <div className="flex justify-between items-center text-[10px] font-mono">
                              <span className="text-slate-400">White Balance</span>
                              <span className="text-[#CFFF3E] font-bold">{whiteBalance} K</span>
                            </div>
                            <input
                              type="range"
                              min="2800"
                              max="6500"
                              step="100"
                              value={whiteBalance}
                              onMouseDown={() => { isDraggingRef.current = true; }}
                              onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ white_balance_temp: whiteBalance }); }}
                              onChange={(e) => setWhiteBalance(parseInt(e.target.value))}
                              className="w-full accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none"
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {activeSettingsTab === "color" && (
                  <div className="flex flex-col gap-3">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider font-mono">Tuning Ball Color Thresholds (HSV)</span>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {/* Hue Sliders */}
                      <div className="bg-slate-900/40 p-3 rounded-xl border border-slate-800/80 flex flex-col gap-2">
                        <div className="flex justify-between items-center text-[10px] font-mono">
                          <span className="text-slate-400">Min Hue (Color tint)</span>
                          <span className="text-[#CFFF3E] font-bold">{hMin}</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="180"
                          value={hMin}
                          onMouseDown={() => { isDraggingRef.current = true; }}
                          onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ hsv_bounds: { ...balancerData?.vision_details?.camera_settings?.hsv_bounds, h_low: hMin } }); }}
                          onChange={(e) => setHMin(parseInt(e.target.value))}
                          className="accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none"
                        />

                        <div className="flex justify-between items-center text-[10px] font-mono mt-1">
                          <span className="text-slate-400">Max Hue</span>
                          <span className="text-[#CFFF3E] font-bold">{hMax}</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="180"
                          value={hMax}
                          onMouseDown={() => { isDraggingRef.current = true; }}
                          onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ hsv_bounds: { ...balancerData?.vision_details?.camera_settings?.hsv_bounds, h_high: hMax } }); }}
                          onChange={(e) => setHMax(parseInt(e.target.value))}
                          className="accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none"
                        />
                      </div>

                      {/* Saturation Sliders */}
                      <div className="bg-slate-900/40 p-3 rounded-xl border border-slate-800/80 flex flex-col gap-2">
                        <div className="flex justify-between items-center text-[10px] font-mono">
                          <span className="text-slate-400">Min Saturation (Vibrancy)</span>
                          <span className="text-[#CFFF3E] font-bold">{sMin}</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="255"
                          value={sMin}
                          onMouseDown={() => { isDraggingRef.current = true; }}
                          onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ hsv_bounds: { ...balancerData?.vision_details?.camera_settings?.hsv_bounds, s_low: sMin } }); }}
                          onChange={(e) => setSMin(parseInt(e.target.value))}
                          className="accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none"
                        />

                        <div className="flex justify-between items-center text-[10px] font-mono mt-1">
                          <span className="text-slate-400">Max Saturation</span>
                          <span className="text-[#CFFF3E] font-bold">{sMax}</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="255"
                          value={sMax}
                          onMouseDown={() => { isDraggingRef.current = true; }}
                          onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ hsv_bounds: { ...balancerData?.vision_details?.camera_settings?.hsv_bounds, s_high: sMax } }); }}
                          onChange={(e) => setSMax(parseInt(e.target.value))}
                          className="accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none"
                        />
                      </div>

                      {/* Value Sliders */}
                      <div className="bg-slate-900/40 p-3 rounded-xl border border-slate-800/80 flex flex-col gap-2 sm:col-span-2">
                        <div className="flex justify-between items-center text-[10px] font-mono">
                          <span className="text-slate-400">Min Value (Brightness)</span>
                          <span className="text-[#CFFF3E] font-bold">{vMin}</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="255"
                          value={vMin}
                          onMouseDown={() => { isDraggingRef.current = true; }}
                          onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ hsv_bounds: { ...balancerData?.vision_details?.camera_settings?.hsv_bounds, v_low: vMin } }); }}
                          onChange={(e) => setVMin(parseInt(e.target.value))}
                          className="accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none w-full"
                        />

                        <div className="flex justify-between items-center text-[10px] font-mono mt-1">
                          <span className="text-slate-400">Max Value</span>
                          <span className="text-[#CFFF3E] font-bold">{vMax}</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="255"
                          value={vMax}
                          onMouseDown={() => { isDraggingRef.current = true; }}
                          onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ hsv_bounds: { ...balancerData?.vision_details?.camera_settings?.hsv_bounds, v_high: vMax } }); }}
                          onChange={(e) => setVMax(parseInt(e.target.value))}
                          className="accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none w-full"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {activeSettingsTab === "filter" && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex flex-col gap-3">
                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] font-bold uppercase tracking-wider text-slate-400 font-mono">Motion Filter Type</label>
                        <select
                          value={balancerData?.vision_details?.camera_settings?.filter_mode ?? "moving_average"}
                          onChange={(e) => updateCameraSettings({ filter_mode: e.target.value })}
                          className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-[#CFFF3E] cursor-pointer"
                        >
                          <option value="none">None (No Smoothing)</option>
                          <option value="moving_average">Moving Average Filter</option>
                          <option value="kalman">1D Kalman Filter</option>
                        </select>
                      </div>

                      {(balancerData?.vision_details?.camera_settings?.filter_mode ?? "moving_average") === "moving_average" && (
                        <div className="flex flex-col gap-1">
                          <div className="flex justify-between items-center text-[10px] font-mono">
                            <span className="text-slate-400">Smoothing Window Size</span>
                            <span className="text-[#CFFF3E] font-bold">{filterWindow} frames</span>
                          </div>
                          <input
                            type="range"
                            min="2"
                            max="30"
                            step="1"
                            value={filterWindow}
                            onMouseDown={() => { isDraggingRef.current = true; }}
                            onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ filter_window: filterWindow }); }}
                            onChange={(e) => setFilterWindow(parseInt(e.target.value))}
                            className="w-full accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none"
                          />
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col gap-3">
                      {(balancerData?.vision_details?.camera_settings?.filter_mode) === "kalman" && (
                        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800/80 flex flex-col gap-3">
                          <div className="flex flex-col gap-1">
                            <div className="flex justify-between items-center text-[10px] font-mono">
                              <span className="text-slate-400">Process Noise Covariance (Q)</span>
                              <span className="text-[#CFFF3E] font-bold">{processNoise.toExponential(1)}</span>
                            </div>
                            <input
                              type="range"
                              min="-7"
                              max="-2"
                              step="0.5"
                              value={Math.log10(processNoise)}
                              onMouseDown={() => { isDraggingRef.current = true; }}
                              onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ filter_process_noise: Math.pow(10, Math.log10(processNoise)) }); }}
                              onChange={(e) => setProcessNoise(Math.pow(10, parseFloat(e.target.value)))}
                              className="w-full accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none"
                            />
                          </div>

                          <div className="flex flex-col gap-1">
                            <div className="flex justify-between items-center text-[10px] font-mono">
                              <span className="text-slate-400">Measurement Noise Covariance (R)</span>
                              <span className="text-[#CFFF3E] font-bold">{measurementNoise.toExponential(1)}</span>
                            </div>
                            <input
                              type="range"
                              min="-4"
                              max="0"
                              step="0.5"
                              value={Math.log10(measurementNoise)}
                              onMouseDown={() => { isDraggingRef.current = true; }}
                              onMouseUp={() => { isDraggingRef.current = false; updateCameraSettings({ filter_measurement_noise: Math.pow(10, Math.log10(measurementNoise)) }); }}
                              onChange={(e) => setMeasurementNoise(Math.pow(10, parseFloat(e.target.value)))}
                              className="w-full accent-[#CFFF3E] cursor-pointer h-1 bg-slate-800 rounded-lg appearance-none"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

          </div>
        )}

        {/* PID Response Dynamics */}
        {activeApp === "tune" && (
          <div className="flex flex-col gap-4">
            
            {/* Chart Area */}
            <div className="bg-[#161719] p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2 block">PID Error Response Log</span>
              <div className="h-[240px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#25282c" />
                    <XAxis dataKey="time" stroke="#64748b" fontSize={9} />
                    <YAxis stroke="#64748b" fontSize={9} label={{ value: 'Error % / Tilt (mm)', angle: -90, position: 'insideLeft', fill: '#64748b', offset: 5 }} />
                    <Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#475569", color: "#fff" }} />
                    <Line type="monotone" dataKey="pos" stroke="#ff4d4d" dot={false} strokeWidth={2} name="Normalized Error (%)" />
                    <Line type="monotone" dataKey="tilt" stroke="#cfff3e" dot={false} strokeWidth={1.5} name="Plate Tilt Delta (mm)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Diagnostic Metrics underneath graph */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs mt-1">
              <div className="bg-[#202123] p-3.5 rounded-xl border border-slate-800/80 flex flex-col gap-1 font-mono">
                <span className="text-slate-500 text-[9px] font-bold uppercase tracking-wider">Plate Axis Error</span>
                <span className="text-white font-bold text-sm">
                  {Math.round((balancerData?.data?.ball_y ?? 0.0) * 1000)} mm
                </span>
              </div>
              <div className="bg-[#202123] p-3.5 rounded-xl border border-slate-800/80 flex flex-col gap-1 font-mono">
                <span className="text-slate-500 text-[9px] font-bold uppercase tracking-wider">Controller Action</span>
                <span className="text-[#CFFF3E] font-bold text-sm">
                  {Math.round((balancerData?.data?.delta_z ?? 0.0) * 1000)} mm tilt
                </span>
              </div>
              <div className="bg-[#202123] p-3.5 rounded-xl border border-slate-800/80 flex flex-col gap-1 font-mono">
                <span className="text-slate-500 text-[9px] font-bold uppercase tracking-wider">Confidence Index</span>
                <span className="text-[#B5ACF3] font-bold text-sm">
                  {Math.round((balancerData?.data?.confidence ?? 0.0) * 100)} %
                </span>
              </div>
            </div>

            {/* Direction Inversion Card */}
            <div className="bg-[#202123] p-4 rounded-xl border border-slate-800 flex justify-between items-center mt-1">
              <div>
                <span className="text-white font-bold text-xs uppercase tracking-wide block">Invert Balancer Output Direction</span>
                <span className="text-[10px] text-slate-500 mt-0.5 block">
                  Toggle this if the plate tilts in the opposite direction of the ball error.
                </span>
              </div>
              <button
                onClick={() => {
                  onTune({
                    kp, kd, ki, speed,
                    max_tilt_positive: maxTiltPos,
                    max_tilt_negative: maxTiltNeg,
                    provider: balancerData?.provider ?? "vision",
                    auto_tune: autoTune,
                    loadcell_mode: loadcellMode,
                    loadcell_arm: loadcellArm,
                    ball_weight_ref: ballWeightRefVal,
                    invert_output: !invertOutput
                  });
                }}
                className={`px-4 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition ${
                  invertOutput
                    ? "bg-rose-500 text-white shadow-lg shadow-rose-950/40 hover:bg-rose-400"
                    : "bg-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                {invertOutput ? "Direction: Inverted" : "Direction: Normal"}
              </button>
            </div>

          </div>
        )}

        {/* Model Training Application */}
        {activeApp === "training" && (
          <div className="flex flex-col gap-6 animate-fade-in text-slate-300">
            
            {/* 1. Online Self-Tuning & System Identification Panel */}
            <div className="bg-[#202123] border border-slate-800 p-5 rounded-xl flex flex-col gap-4">
              <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <div className={`h-2.5 w-2.5 rounded-full ${autoTune ? "bg-[#CFFF3E] animate-pulse" : "bg-slate-600"}`} />
                  <span className="text-xs uppercase font-bold text-white tracking-wider">Online Model Learning & Diagnostics</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 font-mono uppercase font-bold">Self-Learning Auto-Tune</span>
                  <button
                    onClick={() => handleToggleAutoTune(!autoTune)}
                    className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition ${
                      autoTune 
                        ? "bg-[#CFFF3E] text-slate-900 shadow hover:scale-105" 
                        : "bg-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    {autoTune ? "Active" : "Disabled"}
                  </button>
                </div>
              </div>

              {/* Physical Parameters Estimates */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Authority a */}
                <div className="bg-[#161719] p-3.5 rounded-xl border border-slate-800/80 flex flex-col gap-2">
                  <div className="flex justify-between items-center text-[10px] font-mono">
                    <span className="text-slate-400 uppercase font-bold">Control Authority (a)</span>
                    <span className="text-[#CFFF3E] font-bold">
                      {balancerData?.data?.est_a !== undefined ? balancerData.data.est_a.toFixed(4) : "0.5000"}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-[#CFFF3E] h-full rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(100, Math.max(0, ((balancerData?.data?.est_a ?? 0.5) / 3.0) * 100))}%` }}
                    />
                  </div>
                  <span className="text-[9px] text-slate-500 font-mono">Acceleration response per unit of plate tilt. Clamped [0.1, 3.0]</span>
                </div>

                {/* Damping b */}
                <div className="bg-[#161719] p-3.5 rounded-xl border border-slate-800/80 flex flex-col gap-2">
                  <div className="flex justify-between items-center text-[10px] font-mono">
                    <span className="text-slate-400 uppercase font-bold">Rolling Resistance (b)</span>
                    <span className="text-[#B5ACF3] font-bold">
                      {balancerData?.data?.est_b !== undefined ? balancerData.data.est_b.toFixed(4) : "-0.1000"}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-[#B5ACF3] h-full rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(100, Math.max(0, (((balancerData?.data?.est_b ?? -0.1) + 1.0) / 1.2) * 100))}%` }}
                    />
                  </div>
                  <span className="text-[9px] text-slate-500 font-mono">Frictional damping resisting ball velocity. Clamped [-1.0, 0.2]</span>
                </div>
              </div>

              {/* Dynamically Tuned Gains Display */}
              <div className="bg-[#161719] p-4 rounded-xl border border-slate-800/80 flex flex-col gap-2">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Model-Tuned Target Gains (Critical Damping)</span>
                <div className="grid grid-cols-2 gap-4 text-xs font-mono mt-1">
                  <div className="flex justify-between items-center border-r border-slate-800/60 pr-4">
                    <span className="text-slate-500 font-bold">Kp (Proportional)</span>
                    <span className={`font-bold text-sm ${autoTune ? "text-[#CFFF3E]" : "text-slate-400"}`}>
                      {autoTune ? kp.toFixed(3) : (balancerData?.data?.est_a ? ((3.2 * speed * 3.2 * speed) / balancerData.data.est_a).toFixed(3) : "1.300")}
                    </span>
                  </div>
                  <div className="flex justify-between items-center pl-2">
                    <span className="text-slate-500 font-bold">Kd (Derivative)</span>
                    <span className={`font-bold text-sm ${autoTune ? "text-[#B5ACF3]" : "text-slate-400"}`}>
                      {autoTune ? kd.toFixed(3) : (balancerData?.data?.est_a ? ((2.0 * 3.2 * speed + (balancerData.data.est_b ?? -0.1)) / balancerData.data.est_a).toFixed(3) : "0.500")}
                    </span>
                  </div>
                </div>
              </div>

              {/* Console Logs */}
              <div className="flex flex-col gap-1.5">
                <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono">Real-Time Parameter Log</span>
                <div className="bg-black/50 border border-slate-800/80 p-3 rounded-xl font-mono text-[10px] text-slate-400 overflow-y-auto max-h-[120px] flex flex-col gap-1">
                  {learningLog.length === 0 ? (
                    <span className="text-slate-600 italic">Console idle: Waiting for telemetry updates...</span>
                  ) : (
                    learningLog.map((log, idx) => (
                      <div key={idx} className="flex justify-between items-center border-b border-slate-900/60 pb-1 last:border-b-0 last:pb-0">
                        <span className="text-slate-600">[{log.time}]</span>
                        <span>a: <strong className="text-[#CFFF3E]">{log.a.toFixed(3)}</strong> | b: <strong className="text-[#B5ACF3]">{log.b.toFixed(3)}</strong></span>
                        <span>Kp: <strong className="text-white">{log.kp.toFixed(2)}</strong> | Kd: <strong className="text-white">{log.kd.toFixed(2)}</strong></span>
                        <span className={`text-[8px] font-black px-1.5 py-0.5 rounded-md ${log.status === "AUTO" ? "bg-[#CFFF3E]/10 text-[#CFFF3E]" : "bg-slate-800 text-slate-500"}`}>
                          {log.status}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* 2. Grid of Exploration and Coefficients */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Active Model Exploration & Excitation Panel */}
              <div className="bg-[#202123] border border-slate-800 p-5 rounded-xl flex flex-col gap-4">
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <div className={`h-2.5 w-2.5 rounded-full ${balancerData?.exploration_mode ? "bg-[#CFFF3E] animate-pulse" : "bg-slate-600"}`} />
                    <span className="text-xs uppercase font-bold text-white tracking-wider">Active Exploration Mode</span>
                  </div>
                  <button
                    onClick={() => {
                      const nextMode = !(balancerData?.exploration_mode ?? false);
                      onTune({ 
                        kp, kd, ki, speed, 
                        max_tilt_positive: maxTiltPos, 
                        max_tilt_negative: maxTiltNeg, 
                        provider: balancerData?.provider ?? "vision", 
                        auto_tune: autoTune,
                        exploration_mode: nextMode
                      });
                    }}
                    className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition ${
                      balancerData?.exploration_mode 
                        ? "bg-[#CFFF3E] text-slate-900 shadow hover:scale-105" 
                        : "bg-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    {balancerData?.exploration_mode ? "ACTIVE" : "DISABLED"}
                  </button>
                </div>

                {/* Stability hold progress bar */}
                <div className="bg-[#161719] p-4 rounded-xl border border-slate-800/80 flex flex-col gap-2 font-mono">
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-slate-500 uppercase font-bold">Stability Countdown</span>
                    <span className="text-[#CFFF3E] font-bold">
                      {balancerData?.exploration_mode ? `${Math.round((balancerData?.exploration_progress ?? 0) * 100)}%` : "0%"}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mt-1">
                    <div 
                      className="bg-[#CFFF3E] h-full rounded-full transition-all duration-200"
                      style={{ width: `${balancerData?.exploration_mode ? Math.min(100, (balancerData?.exploration_progress ?? 0) * 100) : 0}%` }}
                    />
                  </div>
                </div>

                {/* Target coordinates readouts */}
                <div className="bg-[#161719] p-4 rounded-xl border border-slate-800/80 flex flex-col gap-2 font-mono">
                  <div className="flex justify-between text-xs pb-1 border-b border-slate-850/60 font-mono">
                    <span className="text-slate-500">Active Exploration Target</span>
                    <span className="text-[#CFFF3E] font-bold">
                      {balancerData?.exploration_mode ? `${(balancerData?.data?.target_y * 1000.0).toFixed(0)} mm` : "Center (0 mm)"}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs pt-1">
                    <span className="text-slate-500 font-bold">Live Coordinates Proximity</span>
                    <span className="text-white">
                      {hasBall ? `${(balancerData?.data?.ball_y * 1000.0).toFixed(1)} mm` : "N/A"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Polynomial Model Coefficients */}
              <div className="bg-[#202123] border border-slate-800 p-5 rounded-xl flex flex-col gap-3 font-mono">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2.5 mb-0.5">
                  <span className="text-xs uppercase font-bold text-white tracking-wider">Cubic Polynomial Map</span>
                  <button
                    onClick={async () => {
                      try {
                        await fetch("/api/research/balancer/loadcell/reset-model", { method: "POST" });
                      } catch (e) {
                        console.error(e);
                      }
                    }}
                    className="px-2.5 py-1.5 bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/25 rounded-lg text-[9px] font-black uppercase tracking-wider transition"
                  >
                    Reset Model
                  </button>
                </div>
                
                <div className="flex justify-between text-xs border-b border-slate-850/60 pb-1">
                  <span className="text-slate-500">Offset (c0)</span>
                  <span className="text-[#CFFF3E] font-bold">
                    {balancerData?.data?.loadcell_c0 !== undefined ? balancerData.data.loadcell_c0.toFixed(4) : "0.0000"}
                  </span>
                </div>

                <div className="flex justify-between text-xs border-b border-slate-850/60 pb-1">
                  <span className="text-slate-500">Linear (c1)</span>
                  <span className="text-[#CFFF3E] font-bold">
                    {balancerData?.data?.loadcell_c1 !== undefined ? balancerData.data.loadcell_c1.toFixed(4) : "0.2200"}
                  </span>
                </div>

                <div className="flex justify-between text-xs border-b border-slate-850/60 pb-1">
                  <span className="text-slate-500">Quadratic (c2)</span>
                  <span className="text-[#B5ACF3] font-bold">
                    {balancerData?.data?.loadcell_c2 !== undefined ? balancerData.data.loadcell_c2.toFixed(4) : "0.0000"}
                  </span>
                </div>

                <div className="flex justify-between text-xs border-b border-slate-850/60 pb-1">
                  <span className="text-slate-500">Cubic (c3)</span>
                  <span className="text-[#B5ACF3] font-bold">
                    {balancerData?.data?.loadcell_c3 !== undefined ? balancerData.data.loadcell_c3.toFixed(4) : "0.0000"}
                  </span>
                </div>

                <p className="text-[8px] text-slate-650 leading-normal leading-relaxed">
                  Formula: y_est = c3*r³ + c2*r² + c1*r + c0. The parameters adjust under vision tracking to match physical coordinates.
                </p>
              </div>

            </div>

          </div>
        )}

        {/* Pose Sequence Editor Application */}
        {activeApp === "sequence" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in text-slate-300">
            
            {/* Sidebar: Saved sequences */}
            <div className="bg-[#202123] p-4 rounded-xl border border-slate-800 flex flex-col gap-4 h-fit">
              <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-wider text-slate-400">
                <span>Preset Sequences</span>
                <button
                  onClick={handleAddSequence}
                  className="px-2.5 py-1 bg-[#CFFF3E] text-slate-900 font-extrabold rounded-lg hover:scale-105 active:scale-95 transition text-[9px]"
                >
                  + Create New
                </button>
              </div>
              
              <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-1">
                {sequences.map((seq, sidx) => {
                  const isSelected = activeSeqIndex === sidx;
                  const isSeqPlaying = seqStatus.is_playing && seqStatus.current_sequence === seq.name;
                  return (
                    <div
                      key={sidx}
                      className={`flex justify-between items-center p-3 rounded-xl border transition cursor-pointer ${
                        isSelected 
                          ? "bg-[#CFFF3E]/10 border-[#CFFF3E] text-white font-extrabold" 
                          : "bg-slate-900 border-slate-800/60 text-slate-400 hover:text-white"
                      }`}
                      onClick={() => {
                        setActiveSeqIndex(sidx);
                        setSelectedStepIndex(0);
                      }}
                    >
                      <div className="flex flex-col gap-0.5 truncate">
                        <span className="text-xs truncate">{seq.name}</span>
                        <span className="text-[9px] text-slate-500 font-mono">
                          {seq.steps.length} Step(s) {isSeqPlaying && "(Playing)"}
                        </span>
                      </div>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSequence(sidx);
                        }}
                        className="p-1 rounded-lg text-slate-500 hover:text-red-400 transition ml-2"
                      >
                        ✕
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Editor Detail View */}
            <div className="md:col-span-2 flex flex-col gap-4">
              
              {activeSeq ? (
                <div className="flex flex-col gap-4">
                  
                  {/* Active sequence header configurations */}
                  <div className="bg-[#202123] p-4 rounded-xl border border-slate-800 flex flex-col gap-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="flex flex-col gap-1.5">
                        <label className="text-[9px] uppercase font-bold tracking-wider text-slate-400">Sequence Name</label>
                        <input
                          type="text"
                          value={activeSeq.name}
                          onChange={(e) => {
                            const next = [...sequences];
                            next[activeSeqIndex].name = e.target.value;
                            setSequences(next);
                          }}
                          className="bg-slate-900 border border-slate-800 px-3 py-2 rounded-xl text-xs font-bold text-white focus:outline-none focus:border-[#CFFF3E]"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div className="flex flex-col gap-1.5">
                          <label className="text-[9px] uppercase font-bold tracking-wider text-slate-400">Play Loops</label>
                          <input
                            type="number"
                            min="1"
                            max="50"
                            value={playbackLoop}
                            onChange={(e) => setPlaybackLoop(parseInt(e.target.value) || 1)}
                            className="bg-slate-900 border border-slate-800 px-3 py-2 rounded-xl text-xs font-bold text-center text-white focus:outline-none"
                          />
                        </div>
                        <div className="flex flex-col gap-1.5">
                          <label className="text-[9px] uppercase font-bold tracking-wider text-slate-400">Speed Ratio</label>
                          <select
                            value={playbackSpeed}
                            onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
                            className="bg-slate-900 border border-slate-800 px-2 py-2 rounded-xl text-xs font-bold text-white focus:outline-none cursor-pointer"
                          >
                            <option value={0.5}>0.5x</option>
                            <option value={1.0}>1.0x (Normal)</option>
                            <option value={1.5}>1.5x</option>
                            <option value={2.0}>2.0x</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-2 border-t border-slate-800/60 pt-3">
                      <button
                        onClick={() => handlePlaySequence(activeSeq.name)}
                        disabled={!connected || seqStatus.is_playing}
                        className="flex-1 bg-[#CFFF3E] text-slate-900 py-2 rounded-xl font-black uppercase tracking-wider text-[10px] transition hover:scale-[1.02] disabled:opacity-40 disabled:scale-100"
                      >
                        Play Sequence
                      </button>
                      <button
                        onClick={handleStopSequence}
                        disabled={!connected || !seqStatus.is_playing}
                        className="flex-1 bg-red-500/10 text-red-400 border border-red-500/20 py-2 rounded-xl font-bold uppercase tracking-wider text-[10px] transition hover:bg-red-500/20 disabled:opacity-40"
                      >
                        Stop Movement
                      </button>
                      <button
                        onClick={() => handleSaveSequences()}
                        className="flex-1 bg-slate-800 text-white border border-slate-700 py-2 rounded-xl font-bold uppercase tracking-wider text-[10px] transition hover:bg-slate-700"
                      >
                        Save Configuration
                      </button>
                    </div>
                  </div>

                  {/* Step Editor timeline */}
                  <div className="flex flex-col gap-3">
                    <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-wider text-slate-400">
                      <span>Timeline Steps</span>
                      <button
                        onClick={handleAddStep}
                        className="px-3 py-1 bg-slate-800 text-white font-bold rounded-lg border border-slate-700 text-[9px]"
                      >
                        + Add Pose Step
                      </button>
                    </div>

                    <div className="flex flex-col gap-3 max-h-[380px] overflow-y-auto pr-1">
                      {activeSeq.steps.map((step, idx) => {
                        const isSelectedStep = selectedStepIndex === idx;
                        const modCount = Object.keys(step.modifications).length;
                        return (
                          <div
                            key={idx}
                            className={`p-4 rounded-xl border flex flex-col gap-3 transition cursor-pointer ${
                              isSelectedStep
                                ? "bg-[#202123] border-[#B5ACF3]"
                                : "bg-[#161719] border-slate-800/80 hover:border-slate-850"
                            }`}
                            onClick={() => setSelectedStepIndex(idx)}
                          >
                            <div className="flex justify-between items-center pb-2 border-b border-slate-800/30">
                              <div className="flex items-center gap-3">
                                <span className="text-xs font-black text-white">Pose Frame {idx + 1}</span>
                                <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                                  <span className="text-[10px] text-slate-450">Delay:</span>
                                  <input
                                    type="number"
                                    value={step.delay}
                                    onChange={(e) => handleUpdateStepDelay(idx, e.target.value)}
                                    className="w-12 bg-slate-900 border border-slate-800 rounded px-1.5 py-0.5 text-center text-white font-mono text-[10px]"
                                  />
                                  <span className="text-[9px] text-slate-500">({step.delay * 50}ms)</span>
                                </div>
                              </div>

                              <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                                <button
                                  onClick={() => handlePreviewStep(step)}
                                  disabled={!connected}
                                  className="px-2.5 py-1 bg-[#B5ACF3]/10 text-[#B5ACF3] border border-[#B5ACF3]/30 rounded-lg text-[9px] font-black uppercase transition hover:bg-[#B5ACF3]/25 disabled:opacity-40"
                                >
                                  Preview
                                </button>
                                <button
                                  onClick={() => handleCaptureCurrentPose(idx)}
                                  disabled={!connected}
                                  className="px-2.5 py-1 bg-slate-800 text-slate-300 border border-slate-700 rounded-lg text-[9px] font-black uppercase transition hover:bg-slate-700 disabled:opacity-40"
                                  title="Capture current physical motor tick offsets"
                                >
                                  Capture Pose
                                </button>
                                <button
                                  onClick={() => handleMoveStep(idx, -1)}
                                  disabled={idx === 0}
                                  className="p-1 bg-slate-800 rounded hover:bg-slate-700 text-slate-400 disabled:opacity-30"
                                >
                                  ▲
                                </button>
                                <button
                                  onClick={() => handleMoveStep(idx, 1)}
                                  disabled={idx === activeSeq.steps.length - 1}
                                  className="p-1 bg-slate-800 rounded hover:bg-slate-700 text-slate-400 disabled:opacity-30"
                                >
                                  ▼
                                </button>
                                <button
                                  onClick={() => handleDeleteStep(idx)}
                                  className="p-1 bg-red-500/10 text-red-400 border border-red-500/20 rounded hover:bg-red-500/20 transition"
                                >
                                  ✕
                                </button>
                              </div>
                            </div>

                            {/* Summary of modifications */}
                            <div className="text-[10px] text-slate-500 font-mono flex flex-wrap gap-1.5">
                              {modCount === 0 ? (
                                <span>No joints modified (all defaults)</span>
                              ) : (
                                Object.entries(step.modifications).map(([joint, val]) => (
                                  <span key={joint} className="bg-slate-900 border border-slate-800/80 px-2 py-0.5 rounded text-slate-400">
                                    {joint}: <span className="text-[#CFFF3E] font-bold">{val > 0 ? `+${val}` : val}</span>
                                  </span>
                                ))
                              )}
                            </div>

                            {/* Slider panel for selected step */}
                              {isSelectedStep && (
                              <div className="mt-2 border-t border-slate-800/40 pt-3 flex flex-col gap-3" onClick={(e) => e.stopPropagation()}>
                                {Object.keys(limits).length > 0 ? (
                                  (() => {
                                    const categories = {
                                      left: {
                                        title: "🦾 Left Arm (IDs 21 - 28)",
                                        joints: []
                                      },
                                      right: {
                                        title: "🦾 Right Arm (IDs 11 - 18, 2)",
                                        joints: []
                                      },
                                      head: {
                                        title: "👤 Head & Neck (IDs 31 - 32)",
                                        joints: []
                                      },
                                      general: {
                                        title: "⚙ Auxiliary / General Actuators",
                                        joints: []
                                      }
                                    };

                                    Object.keys(limits).forEach((mid) => {
                                      const info = limits[mid];
                                      const name = info.name || "";
                                      const midNum = parseInt(mid);
                                      
                                      if (name.startsWith("L ") || name.startsWith("L1") || name.startsWith("L2") || name.startsWith("L3") || name.startsWith("L4") || name.startsWith("L5") || name.startsWith("L6") || name.startsWith("L7") || name.startsWith("L8") || [21, 12, 13, 24, 25, 26, 27, 28].includes(midNum)) {
                                        categories.left.joints.push(mid);
                                      } else if (name.startsWith("R ") || name.startsWith("R1") || name.startsWith("R2") || name.startsWith("R3") || name.startsWith("R4") || name.startsWith("R5") || name.startsWith("R6") || name.startsWith("R7") || name.startsWith("R8") || midNum === 2 || [11, 22, 23, 14, 15, 16, 17, 18].includes(midNum)) {
                                        categories.right.joints.push(mid);
                                      } else if (name.toLowerCase().includes("head") || [31, 32].includes(midNum)) {
                                        categories.head.joints.push(mid);
                                      } else {
                                        categories.general.joints.push(mid);
                                      }
                                    });

                                    return Object.entries(categories).map(([catKey, catData]) => {
                                      if (catData.joints.length === 0) return null;
                                      const isExpanded = expandedSections[catKey];
                                      
                                      return (
                                        <div key={catKey} className="bg-slate-950/40 rounded-xl border border-slate-800/60 p-3 space-y-2">
                                          <button
                                            onClick={() => setExpandedSections(prev => ({ ...prev, [catKey]: !prev[catKey] }))}
                                            className="w-full flex items-center justify-between font-bold text-[10px] uppercase tracking-wider text-slate-400 hover:text-white transition focus:outline-none"
                                          >
                                            <div className="flex items-center gap-1.5">
                                              <span className="font-extrabold text-slate-200">{catData.title}</span>
                                              <span className="bg-slate-800 text-slate-400 text-[8px] px-1.5 py-0.5 rounded font-mono font-bold">{catData.joints.length}</span>
                                            </div>
                                            <span className="text-[8px] font-black font-mono transition-transform duration-200" style={{ display: 'inline-block', transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}>
                                              ▶
                                            </span>
                                          </button>
                                          
                                          {isExpanded && (
                                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1 animate-fade-in">
                                              {catData.joints.map((mid) => {
                                                const info = limits[mid];
                                                const val = step.modifications[info.name] ?? 0;
                                                const minVal = info.min - info.default;
                                                const maxVal = info.max - info.default;
                                                const tempKey = `${idx}_${info.name}`;
                                                const displayVal = seqInputValues[tempKey] !== undefined ? seqInputValues[tempKey] : val;
                                                return (
                                                  <div key={mid} className="bg-slate-900 p-2.5 rounded-lg border border-slate-800/80 flex flex-col gap-1">
                                                    <div className="flex justify-between items-center text-[10px]">
                                                      <span className="font-bold text-slate-400">{info.name} <span className="text-[8px] text-slate-500 font-normal">(ID {mid})</span></span>
                                                      <input
                                                        type="text"
                                                        value={displayVal}
                                                        onChange={(e) => {
                                                          const rawVal = e.target.value;
                                                          setSeqInputValues(prev => ({ ...prev, [tempKey]: rawVal }));
                                                          const parsed = parseInt(rawVal);
                                                          if (!isNaN(parsed)) {
                                                            const clamped = Math.max(minVal, Math.min(maxVal, parsed));
                                                            handleUpdateStepJoint(idx, info.name, clamped);
                                                            const updatedStep = {
                                                              ...step,
                                                              modifications: {
                                                                ...step.modifications,
                                                                [info.name]: clamped
                                                              }
                                                            };
                                                            handlePreviewStep(updatedStep);
                                                          }
                                                        }}
                                                        onBlur={() => {
                                                          setSeqInputValues(prev => {
                                                            const next = { ...prev };
                                                            delete next[tempKey];
                                                            return next;
                                                          });
                                                        }}
                                                        className="w-14 text-center text-[10px] font-mono font-bold text-[#CFFF3E] bg-slate-950 border border-slate-850 rounded py-0.5 focus:outline-none focus:border-[#CFFF3E]"
                                                      />
                                                    </div>
                                                    <input
                                                      type="range"
                                                      min={minVal}
                                                      max={maxVal}
                                                      value={val}
                                                      onChange={(e) => {
                                                        const newVal = parseInt(e.target.value) || 0;
                                                        handleUpdateStepJoint(idx, info.name, newVal);
                                                        const updatedStep = {
                                                          ...step,
                                                          modifications: {
                                                            ...step.modifications,
                                                            [info.name]: newVal
                                                          }
                                                        };
                                                        handlePreviewStep(updatedStep);
                                                      }}
                                                      className="w-full accent-[#CFFF3E]"
                                                    />
                                                  </div>
                                                );
                                              })}
                                            </div>
                                          )}
                                        </div>
                                      );
                                    });
                                  })()
                                ) : (
                                  <div className="text-slate-500 italic text-[10px] col-span-2 text-center py-4">
                                    No active joint mapping. Please connect robot/simulator first.
                                  </div>
                                )}
                              </div>
                            )}

                          </div>
                        );
                      })}
                    </div>

                  </div>

                </div>
              ) : (
                <div className="text-slate-500 text-center py-20 italic bg-[#202123] rounded-xl border border-slate-800/80">
                  Select a sequence to edit, or click "Create New".
                </div>
              )}

            </div>

          </div>
        )}

        {/* Arm Calibration Application */}
        {activeApp === "calibration" && (
          <div className="flex flex-col gap-6 animate-fade-in text-slate-300">
            {/* Action Header Card */}
            <div className="bg-[#202123] p-4 rounded-xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <h3 className="text-white font-extrabold text-sm tracking-wider uppercase flex items-center gap-2">
                  <Compass className="h-4 w-4 text-[#CFFF3E]" />
                  <span>Physical Arm Calibration Wizard</span>
                </h3>
                <p className="text-[10px] text-slate-500 max-w-xl mt-1">
                  1. Power ON torques. 2. Manually position the arm joints to their exact physical neutral/balancing poses. 3. Click **Capture Arm Calibration** to save present encoder ticks. 4. Click **Save Offsets** to persist calibration.
                </p>
              </div>
              <button
                onClick={handleSaveCalibration}
                className="w-full md:w-auto bg-[#CFFF3E] text-slate-900 px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider hover:scale-[1.02] active:scale-95 transition"
              >
                Save Offsets to File
              </button>
            </div>

            {/* Arm Panels Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left Arm Calibration Card */}
              <div className="bg-[#202123] p-4 rounded-xl border border-slate-800/80 flex flex-col gap-4">
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <span className="text-white font-bold text-xs tracking-wide uppercase">🦾 Left Arm Calibration</span>
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => handleTorqueArm("left", true)}
                      disabled={!connected}
                      className="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg text-[9px] font-black uppercase hover:bg-emerald-500/25 transition disabled:opacity-40"
                    >
                      Torque ON
                    </button>
                    <button
                      onClick={() => handleTorqueArm("left", false)}
                      disabled={!connected}
                      className="px-2.5 py-1 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg text-[9px] font-black uppercase hover:bg-red-500/25 transition disabled:opacity-40"
                    >
                      Relax
                    </button>
                    <button
                      onClick={() => handleCaptureCalibration("left")}
                      disabled={!connected}
                      className="px-2.5 py-1 bg-slate-800 text-slate-300 border border-slate-700 rounded-lg text-[9px] font-black uppercase hover:bg-slate-700 transition disabled:opacity-40"
                    >
                      Capture
                    </button>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-[11px]">
                    <thead>
                      <tr className="border-b border-slate-850 text-slate-500">
                        <th className="py-2 font-semibold">Joint</th>
                        <th className="py-2 font-semibold text-center">ID</th>
                        <th className="py-2 font-semibold text-center">Live Position</th>
                        <th className="py-2 font-semibold text-center">Calibrated Center</th>
                        <th className="py-2 font-semibold text-center">Torque</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-850/40 text-slate-350">
                      {[
                        { id: 21, defaultName: "L1P" },
                        { id: 12, defaultName: "L2R" },
                        { id: 13, defaultName: "L3Y" },
                        { id: 24, defaultName: "L4F" },
                        { id: 25, defaultName: "L5Y" },
                        { id: 26, defaultName: "L6R" },
                        { id: 27, defaultName: "L7P" },
                        { id: 28, defaultName: "L8G" }
                      ].map((item) => {
                        const mid = item.id;
                        const jointName = limits[mid]?.name || item.defaultName;
                        const livePos = telemetry[mid]?.present !== undefined ? telemetry[mid].present : "--";
                        const isTorqueOn = telemetry[mid]?.torque ?? false;
                        const calibVal = calibration.calib_left[mid] ?? 0;
                        const tempKey = `left_${mid}`;
                        const displayVal = calibInputValues[tempKey] !== undefined ? calibInputValues[tempKey] : calibVal;

                        return (
                          <tr key={mid} className="hover:bg-slate-900/20">
                            <td className="py-2 text-slate-200 font-bold">{jointName}</td>
                            <td className="py-2 text-center text-slate-500 font-mono">{mid}</td>
                            <td className={`py-2 text-center font-mono font-bold ${livePos === "--" ? "text-slate-600" : "text-white"}`}>
                              {livePos}
                            </td>
                            <td className="py-2 text-center">
                              <input
                                type="text"
                                value={displayVal}
                                onChange={(e) => {
                                  const rawVal = e.target.value;
                                  setCalibInputValues(prev => ({ ...prev, [tempKey]: rawVal }));
                                  const parsed = parseInt(rawVal);
                                  if (!isNaN(parsed)) {
                                    setCalibration(prev => ({
                                      ...prev,
                                      calib_left: {
                                        ...prev.calib_left,
                                        [mid]: parsed
                                      }
                                    }));
                                  }
                                }}
                                onBlur={() => {
                                  setCalibInputValues(prev => {
                                    const next = { ...prev };
                                    delete next[tempKey];
                                    return next;
                                  });
                                }}
                                className="w-20 text-center font-mono font-bold text-[#CFFF3E] bg-slate-950 border border-slate-850 rounded py-0.5 focus:outline-none focus:border-[#CFFF3E]"
                              />
                            </td>
                            <td className="py-2 text-center">
                              <button
                                onClick={() => handleTorqueMotor(mid, !isTorqueOn)}
                                disabled={!connected}
                                className={`px-2 py-0.5 text-[9px] font-bold uppercase rounded transition ${
                                  isTorqueOn
                                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                    : "bg-slate-900 text-slate-500 border border-slate-800"
                                }`}
                              >
                                {isTorqueOn ? "ON" : "OFF"}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Right Arm Calibration Card */}
              <div className="bg-[#202123] p-4 rounded-xl border border-slate-800/80 flex flex-col gap-4">
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <span className="text-white font-bold text-xs tracking-wide uppercase">🦾 Right Arm Calibration</span>
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => handleTorqueArm("right", true)}
                      disabled={!connected}
                      className="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg text-[9px] font-black uppercase hover:bg-emerald-500/25 transition disabled:opacity-40"
                    >
                      Torque ON
                    </button>
                    <button
                      onClick={() => handleTorqueArm("right", false)}
                      disabled={!connected}
                      className="px-2.5 py-1 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg text-[9px] font-black uppercase hover:bg-red-500/25 transition disabled:opacity-40"
                    >
                      Relax
                    </button>
                    <button
                      onClick={() => handleCaptureCalibration("right")}
                      disabled={!connected}
                      className="px-2.5 py-1 bg-slate-800 text-slate-300 border border-slate-700 rounded-lg text-[9px] font-black uppercase hover:bg-slate-700 transition disabled:opacity-40"
                    >
                      Capture
                    </button>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-[11px]">
                    <thead>
                      <tr className="border-b border-slate-850 text-slate-500">
                        <th className="py-2 font-semibold">Joint</th>
                        <th className="py-2 font-semibold text-center">ID</th>
                        <th className="py-2 font-semibold text-center">Live Position</th>
                        <th className="py-2 font-semibold text-center">Calibrated Center</th>
                        <th className="py-2 font-semibold text-center">Torque</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-850/40 text-slate-350">
                      {[
                        { id: 11, defaultName: "R1P" },
                        { id: 22, defaultName: "R2R" },
                        { id: 23, defaultName: "R3Y" },
                        { id: 14, defaultName: "R4F" },
                        { id: 15, defaultName: "R5Y" },
                        { id: 16, defaultName: "R6R" },
                        { id: 17, defaultName: "R7P" },
                        { id: 18, defaultName: "R8G" }
                      ].map((item) => {
                        const mid = item.id;
                        const jointName = limits[mid]?.name || item.defaultName;
                        const livePos = telemetry[mid]?.present !== undefined ? telemetry[mid].present : "--";
                        const isTorqueOn = telemetry[mid]?.torque ?? false;
                        const calibVal = calibration.calib_right[mid] ?? 0;
                        const tempKey = `right_${mid}`;
                        const displayVal = calibInputValues[tempKey] !== undefined ? calibInputValues[tempKey] : calibVal;

                        return (
                          <tr key={mid} className="hover:bg-slate-900/20">
                            <td className="py-2 text-slate-200 font-bold">{jointName}</td>
                            <td className="py-2 text-center text-slate-500 font-mono">{mid}</td>
                            <td className={`py-2 text-center font-mono font-bold ${livePos === "--" ? "text-slate-600" : "text-white"}`}>
                              {livePos}
                            </td>
                            <td className="py-2 text-center">
                              <input
                                type="text"
                                value={displayVal}
                                onChange={(e) => {
                                  const rawVal = e.target.value;
                                  setCalibInputValues(prev => ({ ...prev, [tempKey]: rawVal }));
                                  const parsed = parseInt(rawVal);
                                  if (!isNaN(parsed)) {
                                    setCalibration(prev => ({
                                      ...prev,
                                      calib_right: {
                                        ...prev.calib_right,
                                        [mid]: parsed
                                      }
                                    }));
                                  }
                                }}
                                onBlur={() => {
                                  setCalibInputValues(prev => {
                                    const next = { ...prev };
                                    delete next[tempKey];
                                    return next;
                                  });
                                }}
                                className="w-20 text-center font-mono font-bold text-[#CFFF3E] bg-slate-950 border border-slate-850 rounded py-0.5 focus:outline-none focus:border-[#CFFF3E]"
                              />
                            </td>
                            <td className="py-2 text-center">
                              <button
                                onClick={() => handleTorqueMotor(mid, !isTorqueOn)}
                                disabled={!connected}
                                className={`px-2 py-0.5 text-[9px] font-bold uppercase rounded transition ${
                                  isTorqueOn
                                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                    : "bg-slate-900 text-slate-500 border border-slate-800"
                                }`}
                              >
                                {isTorqueOn ? "ON" : "OFF"}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Load Cell Settings Application */}
        {activeApp === "loadcell" && (
          <div className="flex flex-col gap-6 animate-fade-in text-slate-300">
            {/* Header Card */}
            <div className="bg-[#202123] p-5 rounded-xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <h3 className="text-white font-extrabold text-sm tracking-wider uppercase flex items-center gap-2">
                  <Settings className="h-4 w-4 text-[#CFFF3E]" />
                  <span>Dual Load Cell Configuration</span>
                </h3>
                <p className="text-[10px] text-slate-500 max-w-xl mt-1">
                  Configure serial connection, tare offsets, perform individual load cell weight calibrations, and monitor the dynamic coordinate system learning loop.
                </p>
              </div>
              <div className="flex items-center gap-2 w-full md:w-auto">
                <div className="relative">
                  <select
                    value={selectedPort}
                    onChange={(e) => setSelectedPort(e.target.value)}
                    className="bg-slate-950 border border-slate-800 text-white rounded-xl pl-3 pr-8 py-2 text-xs font-mono focus:outline-none focus:border-[#CFFF3E] w-32 appearance-none cursor-pointer"
                  >
                    {availablePorts.length === 0 ? (
                      <option value="">No ports found</option>
                    ) : (
                      availablePorts.map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))
                    )}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500">
                    <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                      <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                    </svg>
                  </div>
                </div>

                <button
                  onClick={fetchPorts}
                  title="Rescan COM Ports"
                  className="p-2.5 bg-slate-800 text-slate-400 hover:text-white rounded-xl border border-slate-700 transition"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                </button>

                {balancerData?.loadcell?.connected ? (
                  <button
                    onClick={async () => {
                      try {
                        await fetch("/api/research/balancer/loadcell/disconnect", { method: "POST" });
                      } catch (e) {
                        console.error(e);
                      }
                    }}
                    className="bg-rose-600 hover:bg-rose-500 text-white px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition"
                  >
                    Disconnect
                  </button>
                ) : (
                  <button
                    onClick={async () => {
                      try {
                        // First set the active port
                        await fetch("/api/research/balancer/loadcell/port", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ port: selectedPort })
                        });
                        // Then trigger connection
                        await fetch("/api/research/balancer/loadcell/connect", { method: "POST" });
                      } catch (e) {
                        console.error(e);
                      }
                    }}
                    disabled={!selectedPort}
                    className="bg-[#CFFF3E] hover:scale-[1.02] text-slate-900 px-4 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition disabled:opacity-40"
                  >
                    Connect
                  </button>
                )}
              </div>
            </div>

            {/* Main Details Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Box 1: Sensor Readings & Live Calibration */}
              <div className="bg-[#202123] p-5 rounded-xl border border-slate-800/80 flex flex-col gap-4">
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <span className="text-white font-bold text-xs uppercase tracking-wide">⚖️ Sensor Readings & Tare</span>
                  <button
                    onClick={async () => {
                      try {
                        await fetch("/api/research/balancer/loadcell/tare", { method: "POST" });
                      } catch (e) {
                        console.error(e);
                      }
                    }}
                    className="px-4 py-2 bg-[#CFFF3E] text-slate-900 rounded-xl text-xs font-black uppercase hover:scale-[1.02] active:scale-95 transition"
                  >
                    Tare Scale (Zero Out)
                  </button>
                </div>

                {/* Left/Right Live Stats */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Left Load Cell */}
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-850 flex flex-col gap-2 font-mono">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Left Load Cell</span>
                    <div className="flex justify-between text-xs pt-1 border-b border-slate-850/60 pb-1">
                      <span className="text-slate-500">Raw ADC</span>
                      <span className="text-white font-bold">{(balancerData?.loadcell?.raw_L ?? 0).toFixed(0)}</span>
                    </div>
                    <div className="flex justify-between text-xs pt-1 border-b border-slate-850/60 pb-1">
                      <span className="text-slate-500">Tare Offset</span>
                      <span className="text-white">{(balancerData?.loadcell?.tare_L ?? 0).toFixed(0)}</span>
                    </div>
                    <div className="flex justify-between text-xs pt-1 border-b border-slate-850/60 pb-1">
                      <span className="text-slate-500">Scale Factor</span>
                      <span className="text-[#CFFF3E]">{(balancerData?.loadcell?.cal_factor_L ?? 1).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm pt-2">
                      <span className="text-slate-400 font-bold">Weight</span>
                      <span className="text-[#CFFF3E] font-black">{(balancerData?.loadcell?.weight_L ?? 0).toFixed(2)} g</span>
                    </div>
                  </div>

                  {/* Right Load Cell */}
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-850 flex flex-col gap-2 font-mono">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Right Load Cell</span>
                    <div className="flex justify-between text-xs pt-1 border-b border-slate-850/60 pb-1">
                      <span className="text-slate-500">Raw ADC</span>
                      <span className="text-white font-bold">{(balancerData?.loadcell?.raw_R ?? 0).toFixed(0)}</span>
                    </div>
                    <div className="flex justify-between text-xs pt-1 border-b border-slate-850/60 pb-1">
                      <span className="text-slate-500">Tare Offset</span>
                      <span className="text-white">{(balancerData?.loadcell?.tare_R ?? 0).toFixed(0)}</span>
                    </div>
                    <div className="flex justify-between text-xs pt-1 border-b border-slate-850/60 pb-1">
                      <span className="text-slate-500">Scale Factor</span>
                      <span className="text-[#B5ACF3]">{(balancerData?.loadcell?.cal_factor_R ?? 1).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm pt-2">
                      <span className="text-slate-400 font-bold">Weight</span>
                      <span className="text-[#B5ACF3] font-black">{(balancerData?.loadcell?.weight_R ?? 0).toFixed(2)} g</span>
                    </div>
                  </div>
                </div>

                {/* Scale Weight Calibration Forms */}
                <div className="flex flex-col gap-3.5 border-t border-slate-850 pt-4 mt-1">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Weight Calibration (Known Mass)</span>
                  
                  {/* Calibrate Left */}
                  <div className="flex justify-between items-center gap-4">
                    <div className="flex items-center gap-2">
                      <span className="text-xs">Left Weight:</span>
                      <input
                        type="number"
                        value={calibWeightL}
                        onChange={(e) => setCalibWeightL(parseFloat(e.target.value) || 0)}
                        className="bg-slate-950 border border-slate-800 text-white rounded-lg px-2.5 py-1 text-xs font-mono focus:outline-none focus:border-[#CFFF3E] w-20"
                      />
                      <span className="text-xs text-slate-500">g</span>
                    </div>
                    <button
                      onClick={async () => {
                        try {
                          await fetch("/api/research/balancer/loadcell/calibrate", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ side: "left", known_weight: calibWeightL })
                          });
                        } catch (e) {
                          console.error(e);
                        }
                      }}
                      className="px-3 py-1.5 bg-slate-800 text-slate-350 border border-slate-700 hover:text-white rounded-lg text-[10px] font-bold uppercase tracking-wider transition"
                    >
                      Calibrate Left
                    </button>
                  </div>

                  {/* Calibrate Right */}
                  <div className="flex justify-between items-center gap-4">
                    <div className="flex items-center gap-2">
                      <span className="text-xs">Right Weight:</span>
                      <input
                        type="number"
                        value={calibWeightR}
                        onChange={(e) => setCalibWeightR(parseFloat(e.target.value) || 0)}
                        className="bg-slate-955 border border-slate-800 text-white rounded-lg px-2.5 py-1 text-xs font-mono focus:outline-none focus:border-[#CFFF3E] w-20"
                      />
                      <span className="text-xs text-slate-500">g</span>
                    </div>
                    <button
                      onClick={async () => {
                        try {
                          await fetch("/api/research/balancer/loadcell/calibrate", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ side: "right", known_weight: calibWeightR })
                          });
                        } catch (e) {
                          console.error(e);
                        }
                      }}
                      className="px-3 py-1.5 bg-slate-800 text-slate-350 border border-slate-700 hover:text-white rounded-lg text-[10px] font-bold uppercase tracking-wider transition"
                    >
                      Calibrate Right
                    </button>
                  </div>
                </div>
              </div>

              {/* Box 2: Deployment Config, Convergence & Learning Status */}
              <div className="bg-[#202123] p-5 rounded-xl border border-slate-800/80 flex flex-col gap-4">
                
                {/* 1. Deployment Configuration */}
                <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-850 flex flex-col gap-3 font-mono">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Deployment Configuration</span>
                  
                  {/* Select Mode */}
                  <div className="flex flex-col gap-1.5 mt-1">
                    <span className="text-slate-500 text-[10px]">Active Sensor Quantity:</span>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => {
                          const mode = 1;
                          onTune({ kp, kd, ki, speed, max_tilt_positive: maxTiltPos, max_tilt_negative: maxTiltNeg, provider: balancerData?.provider ?? "vision", auto_tune: autoTune, loadcell_mode: mode, loadcell_arm: loadcellArm, ball_weight_ref: ballWeightRef, invert_output: invertOutput, ball_type: ballType });
                        }}
                        className={`py-1.5 rounded-lg text-[10px] font-bold uppercase transition ${
                          loadcellMode === 1
                            ? "bg-[#CFFF3E] text-slate-900 font-extrabold"
                            : "bg-slate-800 text-slate-400 hover:text-white"
                        }`}
                      >
                        Single Load Cell (1)
                      </button>
                      <button
                        onClick={() => {
                          const mode = 2;
                          onTune({ kp, kd, ki, speed, max_tilt_positive: maxTiltPos, max_tilt_negative: maxTiltNeg, provider: balancerData?.provider ?? "vision", auto_tune: autoTune, loadcell_mode: mode, loadcell_arm: loadcellArm, ball_weight_ref: ballWeightRef, invert_output: invertOutput, ball_type: ballType });
                        }}
                        className={`py-1.5 rounded-lg text-[10px] font-bold uppercase transition ${
                          loadcellMode !== 1
                            ? "bg-[#CFFF3E] text-slate-900 font-extrabold"
                            : "bg-slate-800 text-slate-400 hover:text-white"
                        }`}
                      >
                        Dual Load Cells (2)
                      </button>
                    </div>
                  </div>

                  {/* Select Arm (If Single Mode) */}
                  {loadcellMode === 1 && (
                    <div className="flex flex-col gap-1.5 mt-1.5 animate-fade-in border-t border-slate-850 pt-2">
                      <span className="text-slate-500 text-[10px]">Active Arm Placement:</span>
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => {
                            const mode = 1;
                            const arm = "left";
                            onTune({ kp, kd, ki, speed, max_tilt_positive: maxTiltPos, max_tilt_negative: maxTiltNeg, provider: balancerData?.provider ?? "vision", auto_tune: autoTune, loadcell_mode: mode, loadcell_arm: arm, ball_weight_ref: ballWeightRef, invert_output: invertOutput, ball_type: ballType });
                          }}
                          className={`py-1.5 rounded-lg text-[10px] font-bold uppercase transition ${
                            loadcellArm === "left"
                              ? "bg-[#B5ACF3] text-slate-900 font-extrabold"
                              : "bg-slate-800 text-slate-400 hover:text-white"
                          }`}
                        >
                          Left Arm placement
                        </button>
                        <button
                          onClick={() => {
                            const mode = 1;
                            const arm = "right";
                            onTune({ kp, kd, ki, speed, max_tilt_positive: maxTiltPos, max_tilt_negative: maxTiltNeg, provider: balancerData?.provider ?? "vision", auto_tune: autoTune, loadcell_mode: mode, loadcell_arm: arm, ball_weight_ref: ballWeightRef, invert_output: invertOutput, ball_type: ballType });
                          }}
                          className={`py-1.5 rounded-lg text-[10px] font-bold uppercase transition ${
                            loadcellArm === "right"
                              ? "bg-[#B5ACF3] text-slate-900 font-extrabold"
                              : "bg-slate-800 text-slate-400 hover:text-white"
                          }`}
                        >
                          Right Arm placement
                        </button>
                      </div>

                      {/* Reference Ball weight input */}
                      <div className="flex flex-col gap-1 mt-2">
                        <div className="flex justify-between items-center text-[10px]">
                          <span className="text-slate-500">Reference Ball Weight (g):</span>
                          <span className="text-white font-mono">{ballWeightRef} g</span>
                        </div>
                        <div className="flex gap-2 items-center">
                          <input
                            type="range"
                            min="20"
                            max="250"
                            step="5"
                            value={ballWeightRef}
                            onChange={(e) => setBallWeightRef(parseInt(e.target.value))}
                            onMouseUp={() => {
                              onTune({
                                kp, kd, ki, speed,
                                max_tilt_positive: maxTiltPos,
                                max_tilt_negative: maxTiltNeg,
                                provider: balancerData?.provider ?? "vision",
                                auto_tune: autoTune,
                                loadcell_mode: 1,
                                loadcell_arm: loadcellArm,
                                ball_weight_ref: ballWeightRef,
                                invert_output: invertOutput,
                                ball_type: ballType
                              });
                            }}
                            onTouchEnd={() => {
                              onTune({
                                kp, kd, ki, speed,
                                max_tilt_positive: maxTiltPos,
                                max_tilt_negative: maxTiltNeg,
                                provider: balancerData?.provider ?? "vision",
                                auto_tune: autoTune,
                                loadcell_mode: 1,
                                loadcell_arm: loadcellArm,
                                ball_weight_ref: ballWeightRef,
                                invert_output: invertOutput,
                                ball_type: ballType
                              });
                            }}
                            className="w-full accent-[#B5ACF3] h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Select Ball Target Type */}
                  <div className="flex flex-col gap-1.5 mt-2.5 border-t border-slate-850 pt-2 font-mono">
                    <span className="text-slate-500 text-[10px]">Tracked Ball Target Type:</span>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => {
                          onTune({
                            kp, kd, ki, speed,
                            max_tilt_positive: maxTiltPos,
                            max_tilt_negative: maxTiltNeg,
                            provider: balancerData?.provider ?? "vision",
                            auto_tune: autoTune,
                            loadcell_mode: loadcellMode,
                            loadcell_arm: loadcellArm,
                            ball_weight_ref: 100,
                            invert_output: invertOutput,
                            ball_type: "green_ping_pong"
                          });
                        }}
                        className={`py-1.5 rounded-lg text-[10px] font-bold uppercase transition ${
                          ballType !== "metal_chrome"
                            ? "bg-[#CFFF3E] text-slate-900 font-extrabold"
                            : "bg-slate-800 text-slate-400 hover:text-white"
                        }`}
                      >
                        🟢 Ping Pong (100g)
                      </button>
                      <button
                        onClick={() => {
                          onTune({
                            kp, kd, ki, speed,
                            max_tilt_positive: maxTiltPos,
                            max_tilt_negative: maxTiltNeg,
                            provider: balancerData?.provider ?? "vision",
                            auto_tune: autoTune,
                            loadcell_mode: loadcellMode,
                            loadcell_arm: loadcellArm,
                            ball_weight_ref: 225,
                            invert_output: invertOutput,
                            ball_type: "metal_chrome"
                          });
                        }}
                        className={`py-1.5 rounded-lg text-[10px] font-bold uppercase transition ${
                          ballType === "metal_chrome"
                            ? "bg-[#CFFF3E] text-slate-900 font-extrabold"
                            : "bg-slate-800 text-slate-400 hover:text-white"
                        }`}
                      >
                        🔘 Chrome Metal (225g)
                      </button>
                    </div>
                  </div>
                </div>

                {/* 2. Learning Progress & Status Indicator */}
                <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-850 flex flex-col gap-3 font-mono">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Calibration Accuracy status</span>
                  
                  {/* Status Badge */}
                  {avgMappingError <= 0.03 ? (
                    <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-3 rounded-xl flex flex-col gap-1 text-[10px]">
                      <span className="font-black text-[11px] uppercase tracking-wide">✅ Coordinates Learning Completed!</span>
                      <span className="text-slate-450 font-normal leading-normal">
                        Average calibration mapping offset error is low ({((avgMappingError) * 1000.0).toFixed(1)} mm). The load cell coordinate system is converged and ready.
                      </span>
                    </div>
                  ) : (
                    <div className="bg-amber-500/10 border border-amber-500/20 text-amber-400 p-3 rounded-xl flex flex-col gap-1 text-[10px]">
                      <span className="font-black text-[11px] uppercase tracking-wide">⚠️ Improve Learning In Progress</span>
                      <span className="text-slate-450 font-normal leading-normal">
                        Current offset error is high ({((avgMappingError) * 1000.0).toFixed(1)} mm). Keep the ball rolling under camera vision or launch Active Exploration in the Model Training App to converge.
                      </span>
                    </div>
                  )}

                  {/* Suggested actions grid */}
                  <div className="flex flex-col gap-2 mt-1">
                    {avgMappingError <= 0.03 ? (
                      <button
                        onClick={() => onTune({ kp, kd, ki, speed, max_tilt_positive: maxTiltPos, max_tilt_negative: maxTiltNeg, provider: "force", auto_tune: autoTune, loadcell_mode: loadcellMode, loadcell_arm: loadcellArm, ball_weight_ref: ballWeightRef, invert_output: invertOutput, ball_type: ballType })}
                        className="py-2.5 rounded-xl font-bold uppercase tracking-wider text-[10px] bg-[#CFFF3E] text-slate-900 hover:scale-102 active:scale-95 transition"
                      >
                        Balance Using Load Cell Only
                      </button>
                    ) : (
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => setActiveApp("training")}
                          className="py-2 rounded-xl font-bold uppercase tracking-wider text-[9px] bg-slate-800 text-slate-350 hover:text-white border border-slate-700 transition"
                        >
                          Improve Learning (Go to Train)
                        </button>
                        <button
                          onClick={() => onTune({ kp, kd, ki, speed, max_tilt_positive: maxTiltPos, max_tilt_negative: maxTiltNeg, provider: "vision", auto_tune: autoTune, loadcell_mode: loadcellMode, loadcell_arm: loadcellArm, ball_weight_ref: ballWeightRef, invert_output: invertOutput, ball_type: ballType })}
                          disabled={balancerData?.provider === "vision"}
                          className="py-2 rounded-xl font-bold uppercase tracking-wider text-[9px] bg-[#CFFF3E]/10 text-[#CFFF3E] border border-[#CFFF3E]/20 hover:bg-[#CFFF3E]/20 transition disabled:opacity-40"
                        >
                          Balance on Vision (Default)
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* 3. Feedback Source Toggle */}
                <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-850 flex flex-col gap-2 mt-1">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider font-mono">Feedback Controller Source</span>
                  <div className="grid grid-cols-2 gap-2 mt-1 font-mono text-[10px]">
                    <button
                      onClick={() => onTune({ kp, kd, ki, speed, max_tilt_positive: maxTiltPos, max_tilt_negative: maxTiltNeg, provider: "vision", auto_tune: autoTune, loadcell_mode: loadcellMode, loadcell_arm: loadcellArm, ball_weight_ref: ballWeightRef, invert_output: invertOutput, ball_type: ballType })}
                      className={`py-2 rounded-lg font-bold uppercase transition ${
                        balancerData?.provider === "vision"
                          ? "bg-[#CFFF3E] text-slate-900 font-extrabold"
                          : "bg-slate-850 text-slate-400 hover:text-white"
                      }`}
                    >
                      Use Camera Vision
                    </button>
                    <button
                      onClick={() => onTune({ kp, kd, ki, speed, max_tilt_positive: maxTiltPos, max_tilt_negative: maxTiltNeg, provider: "force", auto_tune: autoTune, loadcell_mode: loadcellMode, loadcell_arm: loadcellArm, ball_weight_ref: ballWeightRef, invert_output: invertOutput, ball_type: ballType })}
                      className={`py-2 rounded-lg font-bold uppercase transition ${
                        balancerData?.provider === "force"
                          ? "bg-[#CFFF3E] text-slate-900 font-extrabold"
                          : "bg-slate-850 text-slate-400 hover:text-white"
                      }`}
                    >
                      Use Load Cells
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
      
    </div>
  );
}
