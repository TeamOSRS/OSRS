import React, { useState, useEffect, useRef } from "react";
import { 
  Wifi, WifiOff, AlertTriangle, Settings, Sliders, Activity, Plus, Trash2, Repeat, Play, StopCircle, RefreshCw, Cpu, Wrench, Video, Terminal, Eye, Save, PlusCircle, Trash, Bell, Search, Home, HelpCircle, Keyboard, BookOpen, Bot, Network, TrendingUp, Database
} from "lucide-react";

import DigitalTwinViewer from "./components/DigitalTwinViewer";
import DataflowWorkspace from "./components/DataflowWorkspace";
import BallBalancerResearch from "./components/BallBalancerResearch";
import DataRecorder from "./components/DataRecorder";

const PRESET_EMOTE_FRAMES = {
  "HI Left": [
    { delay: 15, modifications: {"L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096} },
    { delay: 5, modifications: {"L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "L6R": -2592} },
    { delay: 5, modifications: {"L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "R6R": 1408} },
    { delay: 5, modifications: {"L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "L6R": -2592} },
    { delay: 5, modifications: {"L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "R6R": 1408} },
    { delay: 5, modifications: {"L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "L6R": -2592} },
    { delay: 5, modifications: {"L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "R6R": 1408} },
    { delay: 15, modifications: {} }
  ],
  "HI Right": [
    { delay: 15, modifications: {"R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096} },
    { delay: 5, modifications: {"R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": 2592} },
    { delay: 5, modifications: {"R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": -1408} },
    { delay: 5, modifications: {"R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": 2592} },
    { delay: 5, modifications: {"R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": -1408} },
    { delay: 5, modifications: {"R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": 2592} },
    { delay: 5, modifications: {"R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": -1408} },
    { delay: 15, modifications: {} }
  ],
  "Namaste": [
    { delay: 25, modifications: {"L1P": -992, "R1P": -992, "L2R": -1392, "R2R": 1392, "L3Y": -1792, "R3Y": 1792, "L4F": 3008, "R4F": -3008, "L7P": 0, "R7P": 0, "L8G": -4096, "R8G": -4096} },
    { delay: 15, modifications: {"L1P": -992, "R1P": -992, "L2R": -1392, "R2R": 1392, "L3Y": -1792, "R3Y": 1792, "L4F": 3008, "R4F": -3008, "L7P": 0, "R7P": 0, "L8G": -4096, "R8G": -4096} },
    { delay: 25, modifications: {} }
  ],
  "Clap": [
    { delay: 15, modifications: {"L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L2R": -2192, "R2R": 2192, "L8G": -4096, "R8G": -4096} },
    { delay: 4, modifications: {"L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -792, "R2R": 792} },
    { delay: 4, modifications: {"L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -2192, "R2R": 2192} },
    { delay: 4, modifications: {"L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -792, "R2R": 792} },
    { delay: 4, modifications: {"L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -2192, "R2R": 2192} },
    { delay: 4, modifications: {"L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -792, "R2R": 792} },
    { delay: 4, modifications: {"L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -2192, "R2R": 2192} },
    { delay: 15, modifications: {} }
  ],
  "Victory": [
    { delay: 20, modifications: {"L1P": -4096, "R1P": -4096, "L2R": -4096, "R2R": 4096, "L4F": 0, "R4F": 0, "L8G": -4096, "R8G": -4096} },
    { delay: 20, modifications: {"L1P": -4096, "R1P": -4096, "L2R": -4096, "R2R": 4096, "L4F": 0, "R4F": 0, "L8G": -4096, "R8G": -4096} },
    { delay: 20, modifications: {} }
  ],
  "Heart": [
    { delay: 25, modifications: {"L1P": -592, "R1P": -592, "L2R": -1792, "R2R": 1792, "L4F": 3008, "R4F": -3008, "L6R": -2592, "R6R": 2592, "L7P": 3008, "R7P": -3008, "L8G": -2192, "R8G": -2192} },
    { delay: 20, modifications: {"L1P": -592, "R1P": -592, "L2R": -1792, "R2R": 1792, "L4F": 3008, "R4F": -3008, "L6R": -2592, "R6R": 2592, "L7P": 3008, "R7P": -3008, "L8G": -2192, "R8G": -2192} },
    { delay: 25, modifications: {} }
  ],
  "67": [
    { delay: 15, modifications: {"L3Y": -2048, "R3Y": 2048} },
    { delay: 15, modifications: {"L3Y": -2048, "R3Y": 2048, "R4F": 2500, "R8G": -400} },
    { delay: 15, modifications: {"L3Y": -2048, "R3Y": 2048, "L4F": 2500, "L8G": -400} }
  ]
};

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [currentTime, setCurrentTime] = useState(new Date());
  const [showConnectionDropdown, setShowConnectionDropdown] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Server state
  const [connected, setConnected] = useState(false);
  const [port, setPort] = useState("COM14");
  const [baudrate, setBaudrate] = useState(4000000);
  const [mockMode, setMockMode] = useState(false);
  const [handVersion, setHandVersion] = useState("Humanoid V1");
  const [estopActive, setEstopActive] = useState(false);
  const [mirrorSyncActive, setMirrorSyncActive] = useState(false);


  // Connection config
  const [connPort, setConnPort] = useState("COM14");
  const [connBaud, setConnBaud] = useState(4000000);
  const [connMock, setConnMock] = useState(false);
  const [connCurrentLimit, setConnCurrentLimit] = useState(250);
  const [connSpeedLimit, setConnSpeedLimit] = useState(150);

  // Live telemetry & limits
  const [limits, setLimits] = useState({});
  const [activeMotorIds, setActiveMotorIds] = useState([]);
  const [telemetry, setTelemetry] = useState({});
  const [systemStats, setSystemStats] = useState({ health: 100, cpu: 0, ram: 0, latency: 0, fps: 0 });
  const [alertBanner, setAlertBanner] = useState(null);
  const [calibBaseInputs, setCalibBaseInputs] = useState({});
  const [calibration, setCalibration] = useState({ calib_left: {}, calib_right: {} });
  const [calibInputValues, setCalibInputValues] = useState({});

  // Calibration state
  const [calibrationState, setCalibrationState] = useState({
    running: false,
    progress: 0.0,
    status_msg: "Idle",
    paused: false,
    fault_reason: ""
  });

  // Vision system state
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraIdx, setCameraIdx] = useState(0);
  const [trackingEnabled, setTrackingEnabled] = useState(false);
  const [videoFrame, setVideoFrame] = useState(null);

  // System logs
  const [logs, setLogs] = useState([]);

  // Local drag/input state for sliders to prevent lag
  const [localDrags, setLocalDrags] = useState({});
  const [inputValues, setInputValues] = useState({});
  const [selectedJoint, setSelectedJoint] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    left: true,
    right: true,
    head: false,
    general: false
  });

  // CAD ID Mapper state
  const [mapperId, setMapperId] = useState("");
  const [mapperNewId, setMapperNewId] = useState("");
  const [mapperName, setMapperName] = useState("");
  const [mapperMin, setMapperMin] = useState(-4096);
  const [mapperMax, setMapperMax] = useState(4096);
  const [mapperDefault, setMapperDefault] = useState(0);
  const [editingMapper, setEditingMapper] = useState(false);

  // Mock error states
  const [mockErrorId, setMockErrorId] = useState("");
  const [mockErrorByte, setMockErrorByte] = useState("32");

  // Saved custom emotes state
  const [savedEmotes, setSavedEmotes] = useState({});
  const [saveName, setSaveName] = useState("");
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [playingPreset, setPlayingPreset] = useState(null);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  // New Modular Workspace States
  const [digitalTwin, setDigitalTwin] = useState({ sync_mode: "hardware", joints: {}, model_geometry: {} });
  const [balancer, setBalancer] = useState({ is_active: false, data: {}, kp: 0.8, kd: 0.3, ki: 0.05, provider: "vision" });
  const [recorder, setRecorder] = useState({ is_recording: false, recorded_frames: 0, is_replaying: false });

  const ws = useRef(null);
  const logEndRef = useRef(null);
  const terminalRef = useRef(null);
  const sliderRefs = useRef({});

  // Emote Maker State
  const [emoteFrames, setEmoteFrames] = useState([{ delay: 15, hold: 0, modifications: {} }]);
  const [emoteInputValues, setEmoteInputValues] = useState({});
  const [emoteLoop, setEmoteLoop] = useState(1);
  const [emoteSpeed, setEmoteSpeed] = useState(1.0);
  const [playingEmote, setPlayingEmote] = useState(false);
  const [showShortcutHelp, setShowShortcutHelp] = useState(false);

  // Throttled WebSocket sender logic
  const lastSentTime = useRef({});
  const pendingUpdates = useRef({});
  const throttleInterval = 30; // ms

  const sendManualWS = (positions) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return;
    
    const now = Date.now();
    let shouldSend = false;
    
    // Check if we can send now
    Object.keys(positions).forEach(mid => {
      const lastSent = lastSentTime.current[mid] || 0;
      if (now - lastSent > throttleInterval) {
        shouldSend = true;
      }
    });

    if (shouldSend) {
      ws.current.send(JSON.stringify({
        action: "manual",
        positions: positions
      }));
      Object.keys(positions).forEach(mid => {
        lastSentTime.current[mid] = now;
      });
    } else {
      // Store in pending
      pendingUpdates.current = { ...pendingUpdates.current, ...positions };
    }
  };

  // Periodically flush pending manual websocket updates
  useEffect(() => {
    const timer = setInterval(() => {
      if (Object.keys(pendingUpdates.current).length > 0) {
        const toSend = { ...pendingUpdates.current };
        pendingUpdates.current = {};
        sendManualWS(toSend);
      }
    }, 30);
    return () => clearInterval(timer);
  }, []);

  // Fetch initial profile limits
  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        setConnected(data.connected);
        setPort(data.port);
        setBaudrate(data.baudrate);
        setMockMode(data.mock_mode);
        setHandVersion(data.hand_version);
        setEstopActive(data.estop_active);
        const activeLimits = data.limits || {};
        setLimits(activeLimits);
        setCalibBaseInputs(prev => {
          const next = { ...prev };
          Object.keys(activeLimits).forEach(mid => {
            if (next[mid] === undefined) {
              next[mid] = activeLimits[mid].default;
            }
          });
          return next;
        });
        setActiveMotorIds(data.active_motor_ids || []);
        setCameraActive(data.camera_active);
        setCameraIdx(data.camera_index);
        setTrackingEnabled(data.tracking_enabled);
        if (data.logs) setLogs(data.logs);
        
        // Fetch mirror sync state on status reload
        try {
          const mirrorRes = await fetch("/api/robot/mirror-sync");
          if (mirrorRes.ok) {
            const mirrorData = await mirrorRes.json();
            setMirrorSyncActive(mirrorData.mirror_sync_active);
          }
        } catch (err) {}
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleMirrorSync = async (active) => {
    try {
      const res = await fetch("/api/robot/mirror-sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active })
      });
      const data = await res.json();
      if (res.ok) {
        setMirrorSyncActive(data.mirror_sync_active);
        setAlertBanner({ type: "success", message: `Mirror sync state set to ${data.mirror_sync_active ? "ENABLED" : "DISABLED"}` });
      }
    } catch (e) {
      console.error("Failed to toggle mirror sync", e);
    }
  };


  const fetchCustomEmotes = async () => {
    try {
      const res = await fetch("/api/emote/custom/list");
      if (res.ok) {
        const data = await res.json();
        setSavedEmotes(data);
      }
    } catch (e) {}
  };

  const handleSaveEmote = async () => {
    if (!saveName.trim()) return;
    try {
      const res = await fetch("/api/emote/custom/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: saveName, frames: emoteFrames })
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: `Emote "${saveName}" saved successfully!` });
        setSaveName("");
        setShowSaveModal(false);
        fetchCustomEmotes();
      }
    } catch (e) {}
  };

  const handleDeleteCustomEmote = async (name) => {
    if (!window.confirm(`Delete saved emote "${name}"?`)) return;
    try {
      const res = await fetch("/api/emote/custom/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name })
      });
      if (res.ok) {
        setAlertBanner({ type: "warning", message: `Deleted custom emote "${name}".` });
        fetchCustomEmotes();
      }
    } catch (e) {}
  };

  const playSavedCustomEmote = async (name, frames) => {
    setPlayingPreset(name);
    try {
      const res = await fetch("/api/emote/custom", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          loop: emoteLoop,
          frames: frames,
          speed: emoteSpeed
        })
      });
      if (res.ok) {
        const data = await res.json();
        const duration = (data.frames_compiled * (50 / emoteSpeed)) + 500;
        setTimeout(() => setPlayingPreset(null), duration);
      } else {
        setPlayingPreset(null);
      }
    } catch (e) {
      setPlayingPreset(null);
    }
  };

  const loadSavedEmoteIntoMaker = (name, frames) => {
    setEmoteFrames(JSON.parse(JSON.stringify(frames))); // deep clone
    setAlertBanner({ type: "success", message: `Loaded emote "${name}" into the editor.` });
  };

  const loadPresetEmoteIntoMaker = (name) => {
    const frames = PRESET_EMOTE_FRAMES[name];
    if (frames) {
      setEmoteFrames(JSON.parse(JSON.stringify(frames))); // deep clone
      setAlertBanner({ type: "success", message: `Loaded preset "${name}" into Custom Emote Maker. You can now edit and customize it.` });
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchCustomEmotes();
    fetchCalibration();
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const connectWS = () => {
      ws.current = new WebSocket(`${protocol}//${host}/ws/telemetry`);
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.telemetry) {
            setTelemetry(data.telemetry);
            if (!window._lastLogTime || Date.now() - window._lastLogTime > 2000) {
              window._lastLogTime = Date.now();
              console.log("[PAYLOAD DIAGNOSTIC] Forces:", data.forces);
              console.log("[PAYLOAD DIAGNOSTIC] Currents (mA):", Object.keys(data.telemetry).reduce((acc, k) => {
                acc[k] = data.telemetry[k].current;
                return acc;
              }, {}));
            }
          }
          if (data.system) setSystemStats(data.system);
          if (data.calibration) setCalibrationState(data.calibration);
          if (data.logs) setLogs(data.logs);
          if (data.video_frame !== undefined) setVideoFrame(data.video_frame);
          
          if (data.digital_twin) setDigitalTwin(data.digital_twin);
          if (data.balancer) setBalancer(data.balancer);
          if (data.recorder) setRecorder(data.recorder);
          
          setConnected(data.connected);
          setEstopActive(data.estop_active);
          setTrackingEnabled(data.tracking_enabled);
          setCameraActive(data.camera_active);
          if (data.mirror_sync_active !== undefined) setMirrorSyncActive(data.mirror_sync_active);

          if (data.active_motor_ids) setActiveMotorIds(data.active_motor_ids);
        } catch (e) {}
      };
      ws.current.onclose = () => setTimeout(connectWS, 2000);
    };
    connectWS();
    return () => ws.current?.close();
  }, []);

  // Scroll logs terminal to bottom without scrolling outer window
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs, activeTab]);

  const handleSyncModeChange = async (mode) => {
    try {
      const res = await fetch("/api/simulation/sync-mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode })
      });
      if (res.ok) {
        setDigitalTwin(prev => ({ ...prev, sync_mode: mode }));
        setAlertBanner({ type: "success", message: `Digital Twin sync mode changed to ${mode.toUpperCase()}` });
      }
    } catch (e) {}
  };

  const handleTuneBalancer = async ({ kp, kd, ki, provider, speed, max_tilt_positive, max_tilt_negative, auto_tune, exploration_mode, loadcell_mode, loadcell_arm, ball_weight_ref, invert_output, ball_type }) => {
    try {
      const res = await fetch("/api/research/ball-balancer/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kp, kd, ki, provider, speed, max_tilt_positive, max_tilt_negative, auto_tune, exploration_mode, loadcell_mode, loadcell_arm, ball_weight_ref, invert_output, ball_type })
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: "Balancer tuning parameters successfully updated on controller." });
      }
    } catch (e) {}
  };

  const handleToggleBalancer = async (active) => {
    try {
      const res = await fetch("/api/research/ball-balancer/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active })
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: active ? "Ball balancing loop engaged." : "Ball balancing loop halted." });
      }
    } catch (e) {}
  };

  const handleGoToStart = async () => {
    try {
      const res = await fetch("/api/research/ball-balancer/go-to-start", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: "Arms moving to ball balancing start pose." });
      } else {
        const err = await res.json();
        setAlertBanner({ type: "error", message: `Failed to move to start: ${err.detail || "Unknown error"}` });
      }
    } catch (e) {
      setAlertBanner({ type: "error", message: "Failed to communicate with robot controller." });
    }
  };

  const handleInitializeArms = async () => {
    try {
      const res = await fetch("/api/research/ball-balancer/initialize-arms", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: "Arms moving to target initialized pose." });
      } else {
        const err = await res.json();
        setAlertBanner({ type: "error", message: `Failed to initialize arms: ${err.detail || "Unknown error"}` });
      }
    } catch (e) {
      setAlertBanner({ type: "error", message: "Failed to communicate with robot controller." });
    }
  };

  const handleSendCommand = async (command) => {
    try {
      const res = await fetch("/api/research/ball-balancer/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command })
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: `Command "${command}" executed successfully.` });
      } else {
        const err = await res.json();
        setAlertBanner({ type: "error", message: `Failed: ${err.detail || "Unknown error"}` });
      }
    } catch (e) {
      setAlertBanner({ type: "error", message: "Failed to communicate with robot controller." });
    }
  };


  const handleToggleRecord = async (active, experiment) => {
    try {
      const res = await fetch("/api/recording/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active, experiment })
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: active ? "Telemetry logging started." : "Telemetry logging stopped." });
      }
    } catch (e) {}
  };

  const handleExportRecording = async (format, filename) => {
    try {
      const res = await fetch("/api/recording/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format, filename })
      });
      if (res.ok) {
        const data = await res.json();
        setAlertBanner({ type: "success", message: `Session logs exported to ${data.filepath}` });
      }
    } catch (e) {}
  };

  const handleLoadReplay = async (filepath) => {
    try {
      const res = await fetch("/api/recording/load-replay", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filepath })
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: `Started trajectory playback from log: ${filepath}` });
      } else {
        const data = await res.json();
        setAlertBanner({ type: "error", message: data.detail || "Load replay failed" });
      }
    } catch (e) {}
  };

  // Keyboard navigation shortcuts (Visual Studio style) & Global actions
  useEffect(() => {
    const handleKeyDown = (e) => {
      const activeEl = document.activeElement;
      const isTyping = activeEl && (
        activeEl.tagName === "INPUT" || 
        activeEl.tagName === "TEXTAREA" || 
        activeEl.tagName === "SELECT" ||
        activeEl.isContentEditable
      );

      if (e.altKey && !e.shiftKey && !e.metaKey) {
        const tabMap = {
          "1": "dashboard",
          "2": "control",
          "3": "emotemaker",
          "4": "calibration",
          "5": "cadmapper",
          "6": "diagnostics",
          "7": "vision"
        };
        if (tabMap[e.key]) {
          e.preventDefault();
          setActiveTab(tabMap[e.key]);
          setAlertBanner({ type: "success", message: `Switched view tab to ${tabMap[e.key].toUpperCase()} via hotkey` });
        }
        if (e.key.toLowerCase() === "h") {
          e.preventDefault();
          setShowShortcutHelp(prev => !prev);
        }
        if (e.key.toLowerCase() === "s") {
          e.preventDefault();
          toggleEstop();
        }
        if (e.key.toLowerCase() === "r") {
          e.preventDefault();
          resetAllToDefault();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [connected, estopActive, limits]);

  const triggerConnect = async () => {
    try {
      const res = await fetch("/api/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          port: connPort, 
          baudrate: parseInt(connBaud), 
          mock_mode: connMock,
          current_limit: parseInt(connCurrentLimit),
          speed_limit: parseInt(connSpeedLimit)
        })
      });
      if (!res.ok) {
        const data = await res.json();
        setAlertBanner({ type: "error", message: data.detail || "Connect failed" });
      } else {
        setAlertBanner({ type: "success", message: "Connected successfully." });
        fetchStatus();
      }
    } catch (e) {
      setAlertBanner({ type: "error", message: "Failed to communicate with backend." });
    }
  };

  const triggerDisconnect = async () => {
    try {
      await fetch("/api/disconnect", { method: "POST" });
      setAlertBanner({ type: "warning", message: "Disconnected." });
      fetchStatus();
    } catch (e) {}
  };

  const toggleEstop = async () => {
    try {
      await fetch("/api/estop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: !estopActive })
      });
    } catch (e) {}
  };



  const rebootMotor = async (mid) => {
    try {
      await fetch("/api/reboot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motor_id: parseInt(mid) })
      });
      setAlertBanner({ type: "success", message: `Reboot sequence triggered for motor ${mid}` });
    } catch (e) {}
  };

  const toggleTorqueGlobal = async (enable) => {
    try {
      await fetch("/api/torque", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motor_id: "global", enable })
      });
    } catch (e) {}
  };

  const toggleTorqueIndividual = async (mid, enable) => {
    try {
      await fetch("/api/torque", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motor_id: String(mid), enable })
      });
    } catch (e) {}
  };

  const changeProfile = async (version) => {
    try {
      const res = await fetch("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version })
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: `Switched profile to ${version}` });
        fetchStatus();
      }
    } catch (e) {}
  };

  const handleSliderDrag = (mid, val) => {
    const intVal = parseInt(val);
    setLocalDrags(prev => ({ ...prev, [mid]: intVal }));
    sendManualWS({ [parseInt(mid)]: intVal });
  };

  const handleSliderRelease = (mid) => {
    if (localDrags[mid] !== undefined) {
      sendManualWS({ [parseInt(mid)]: localDrags[mid] });
    }
    setTimeout(() => {
      setLocalDrags(prev => {
        const next = { ...prev };
        delete next[mid];
        return next;
      });
    }, 400);
  };

  const handleInputChange = (mid, valStr, minVal, maxVal) => {
    setInputValues(prev => ({ ...prev, [mid]: valStr }));
    const val = parseInt(valStr);
    if (!isNaN(val)) {
      const clamped = Math.max(minVal, Math.min(maxVal, val));
      handleSliderDrag(mid, clamped);
    }
  };

  const handleInputBlur = (mid) => {
    handleSliderRelease(mid);
    setInputValues(prev => {
      const next = { ...prev };
      delete next[mid];
      return next;
    });
  };

  const resetAllToDefault = () => {
    if (!connected) return;
    const positions = {};
    Object.keys(limits).forEach((mid) => {
      positions[parseInt(mid)] = 0; // 0-centered default is 0
      setLocalDrags(prev => ({ ...prev, [mid]: 0 }));
    });
    sendManualWS(positions);
    setAlertBanner({ type: "success", message: "All joints reset to initial position (0)." });
    setTimeout(() => {
      setLocalDrags({});
    }, 500);
  };

  const rotateJointByDeg = (mid, deg) => {
    const info = limits[mid];
    if (!info) return;
    const tickChange = Math.round(deg * (4096 / 360));
    
    const currentPhysical = telemetry[mid]?.present !== undefined && telemetry[mid].present !== "--"
      ? parseInt(telemetry[mid].present)
      : info.default;
      
    const currentTarget = localDrags[mid] !== undefined
      ? localDrags[mid] + info.default
      : currentPhysical;
      
    const nextTarget = Math.max(info.min, Math.min(info.max, currentTarget + tickChange));
    const newOffset = nextTarget - info.default;
    
    setLocalDrags(prev => ({ ...prev, [mid]: newOffset }));
    sendManualWS({ [parseInt(mid)]: newOffset });
    
    setTimeout(() => {
      setLocalDrags(prev => {
        const next = { ...prev };
        delete next[mid];
        return next;
      });
    }, 1000);
  };

  // -------------------------
  // Emote Maker Logic
  // -------------------------
  const addEmoteFrame = () => {
    if (emoteFrames.length > 0) {
      const lastFrame = emoteFrames[emoteFrames.length - 1];
      setEmoteFrames([
        ...emoteFrames,
        {
          delay: lastFrame.delay,
          hold: lastFrame.hold ?? 0,
          modifications: JSON.parse(JSON.stringify(lastFrame.modifications))
        }
      ]);
    } else {
      setEmoteFrames([{ delay: 15, hold: 0, modifications: {} }]);
    }
  };
  
  const removeEmoteFrame = (index) => {
    setEmoteFrames(emoteFrames.filter((_, i) => i !== index));
  };
  
  const updateFrameDelay = (index, val) => {
    const newFrames = [...emoteFrames];
    newFrames[index].delay = parseInt(val) || 10;
    setEmoteFrames(newFrames);
  };

  const updateFrameHold = (index, val) => {
    const newFrames = [...emoteFrames];
    newFrames[index].hold = parseInt(val) || 0;
    setEmoteFrames(newFrames);
  };
  
  const updateFrameJoint = (frameIndex, jointName, val) => {
    const newFrames = [...emoteFrames];
    newFrames[frameIndex].modifications[jointName] = parseInt(val);
    setEmoteFrames(newFrames);
  };

  const previewFrame = (frame) => {
    if (!connected) return;
    const positions = {};
    Object.keys(limits).forEach((mid) => {
      const info = limits[mid];
      const val = frame.modifications[info.name] ?? 0;
      positions[parseInt(mid)] = val;
    });
    sendManualWS(positions);
  };
  
  const playCustomEmote = async () => {
    setPlayingEmote(true);
    try {
      const res = await fetch("/api/emote/custom", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          loop: emoteLoop,
          frames: emoteFrames,
          speed: emoteSpeed
        })
      });
      if (res.ok) {
        const data = await res.json();
        const duration = (data.frames_compiled * (50 / emoteSpeed)) + 500;
        setTimeout(() => setPlayingEmote(false), duration);
      } else {
        const data = await res.json();
        alert(data.detail);
        setPlayingEmote(false);
      }
    } catch (e) {
      setPlayingEmote(false);
    }
  };

  const playPresetEmote = async (name) => {
    setPlayingPreset(name);
    try {
      const res = await fetch("/api/emote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, loop: emoteLoop, speed: emoteSpeed })
      });
      if (res.ok) {
        const data = await res.json();
        const duration = (data.frames_compiled * (50 / emoteSpeed)) + 500;
        setTimeout(() => setPlayingPreset(null), duration);
      } else {
        setPlayingPreset(null);
      }
    } catch (e) {
      setPlayingPreset(null);
    }
  };

  // -------------------------
  // Calibration
  // -------------------------
  const controlCalibration = async (action) => {
    try {
      await fetch("/api/calibration/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action })
      });
    } catch (e) {}
  };

  const handleSetZeroCalibration = async () => {
    if (!window.confirm("Calibrate Zero: Capture current physical pose as baseline initial (0) state?")) return;
    try {
      const res = await fetch("/api/calibration/set-zero", {
        method: "POST"
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: "Zero calibration saved. All joint baseline values updated." });
        fetchStatus();
      }
    } catch (e) {}
  };

  const handleSaveBaseFrame = async () => {
    try {
      const res = await fetch("/api/calibration/save-base-frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(calibBaseInputs)
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: "Base frame calibration saved to disk successfully." });
        fetchStatus();
      } else {
        const err = await res.json();
        setAlertBanner({ type: "error", message: `Failed to save base frame: ${err.detail || "Unknown error"}` });
      }
    } catch (e) {
      setAlertBanner({ type: "error", message: "Error communicating with server." });
    }
  };

  const handleGoToBase = async () => {
    try {
      const res = await fetch("/api/calibration/go-to-base", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: "Actuators moving to the calibrated base frame." });
      } else {
        const err = await res.json();
        setAlertBanner({ type: "error", message: `Failed to move: ${err.detail || "Unknown error"}` });
      }
    } catch (e) {
      setAlertBanner({ type: "error", message: "Error communicating with server." });
    }
  };

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

  const handleTorqueArm = async (arm, enable) => {
    try {
      const res = await fetch("/api/torque", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motor_id: arm, enable })
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: `${arm.toUpperCase()} arm torque set to ${enable ? "ON" : "OFF"}` });
      } else {
        const err = await res.json();
        setAlertBanner({ type: "error", message: `Failed to set torque: ${err.detail || 'Unknown error'}` });
      }
    } catch (e) {
      console.error("Failed to toggle arm torque", e);
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
        setAlertBanner({ type: "success", message: `${arm.toUpperCase()} arm calibration captured successfully!` });
        fetchCalibration();
        fetchStatus();
      } else {
        setAlertBanner({ type: "error", message: `Capture failed: ${data.detail || 'Unknown error'}` });
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
        setAlertBanner({ type: "success", message: "Calibration offsets saved to chiman_calibration.json successfully!" });
        fetchCalibration();
        fetchStatus();
      } else {
        const err = await res.json();
        setAlertBanner({ type: "error", message: `Save failed: ${err.detail || 'Unknown error'}` });
      }
    } catch (e) {
      console.error("Failed to save calibration", e);
    }
  };

  // -------------------------
  // Vision
  // -------------------------
  const toggleVisionSystem = async () => {
    try {
      await fetch("/api/vision/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ camera_index: parseInt(cameraIdx), enable: !cameraActive })
      });
    } catch (e) {}
  };

  const toggleHandTracking = async () => {
    try {
      await fetch("/api/tracking", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enable: !trackingEnabled })
      });
    } catch (e) {}
  };

  // -------------------------
  // CAD Mapper
  // -------------------------
  const handleSaveMapper = async () => {
    if (!mapperId) return;
    try {
      const res = await fetch("/api/config/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          motor_id: parseInt(mapperId),
          new_id: parseInt(mapperNewId || mapperId),
          name: mapperName,
          min_val: parseInt(mapperMin),
          max_val: parseInt(mapperMax)
        })
      });
      if (res.ok) {
        setAlertBanner({ type: "success", message: `Joint configuration updated.` });
        fetchStatus();
        resetMapperForm();
      }
    } catch (e) {}
  };

  const handleDeleteMapper = async (mid) => {
    if (!window.confirm(`Delete configuration for joint ID ${mid}?`)) return;
    try {
      const res = await fetch("/api/config/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motor_id: parseInt(mid) })
      });
      if (res.ok) {
        setAlertBanner({ type: "warning", message: `Deleted joint ID ${mid}.` });
        fetchStatus();
      }
    } catch (e) {}
  };

  const startEditMapper = (mid, info) => {
    setMapperId(mid);
    setMapperNewId(mid);
    setMapperName(info.name);
    setMapperMin(info.min);
    setMapperMax(info.max);
    setEditingMapper(true);
  };

  const resetMapperForm = () => {
    setMapperId("");
    setMapperNewId("");
    setMapperName("");
    setMapperMin(-4096);
    setMapperMax(4096);
    setEditingMapper(false);
  };

  // -------------------------
  // Diagnostics Mock Error
  // -------------------------
  const triggerMockError = async () => {
    if (!mockErrorId) return;
    try {
      const res = await fetch("/api/mock/trigger-error", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          motor_id: parseInt(mockErrorId),
          error_byte: parseInt(mockErrorByte)
        })
      });
      if (res.ok) {
        setAlertBanner({ type: "warning", message: `Injected Overload fault on motor ${mockErrorId}.` });
      }
    } catch (e) {}
  };

  // Joint skeleton structures
  const humanoidJointMap = [
    { id: 21, align: "left" }, { id: 11, align: "right" },
    { id: 12, align: "left" }, { id: 22, align: "right" },
    { id: 13, align: "left" }, { id: 23, align: "right" },
    { id: 24, align: "left" }, { id: 14, align: "right" },
    { id: 25, align: "left" }, { id: 15, align: "right" },
    { id: 26, align: "left" }, { id: 16, align: "right" },
    { id: 27, align: "left" }, { id: 17, align: "right" },
    { id: 28, align: "left" }, { id: 18, align: "right" },
  ];

  const handleJointClick = (id) => {
    setSelectedJoint(id);
    if (sliderRefs.current[id]) {
      sliderRefs.current[id].scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  const isAnyTorqueActive = Object.values(telemetry).some(t => t.torque === true);

  return (
    <div className="flex flex-col min-h-screen bg-[#EAEDF1] text-[#1E2022] select-none pt-10 font-sans">
      
      {/* FIXED TOP BAR (sticky top panel) */}
      <div className="fixed top-0 left-0 right-0 h-10 bg-[#191A1B]/95 backdrop-blur-md border-b border-slate-800 text-[11px] font-medium text-slate-300 flex items-center justify-between px-4 z-50 shadow-sm select-none font-sans">
        
        {/* Left: Brand/Logo & View selector & Platform dropdown */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5 text-[#CFFF3E] animate-pulse" />
            <span className="font-bold text-[11px] tracking-widest text-[#CFFF3E] uppercase">OSRS</span>
          </div>
          <span className="text-slate-700">|</span>
          <span className="bg-white/10 text-[#B5ACF3] px-2 py-0.5 rounded-md font-semibold text-[9px] uppercase tracking-wider">
            {activeTab === "emotemaker" ? "Emotes & Maker" : activeTab === "cadmapper" ? "CAD ID Mapper" : activeTab.toUpperCase()}
          </span>
          <span className="text-slate-700">|</span>
          
          {/* Custom Bot Selector Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowProfileDropdown(prev => !prev)}
              className="flex items-center gap-1.5 text-slate-300 hover:text-white transition font-medium"
            >
              <Bot className="h-3.5 w-3.5 text-[#B5ACF3]" />
              <span className="uppercase tracking-wider">{handVersion}</span>
              <span className="text-[7px] text-slate-500">▼</span>
            </button>

            {showProfileDropdown && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setShowProfileDropdown(false)} 
                />
                
                <div className="absolute left-0 mt-2 bg-[#1E2022] rounded-2xl shadow-2xl border border-slate-700/50 p-2.5 z-50 w-72 animate-in fade-in slide-in-from-top-3 duration-200 flex flex-col gap-1 text-white font-sans">
                  <span className="text-[9px] font-semibold text-[#7E8B93] uppercase tracking-wider px-3.5 py-1.5 block border-b border-slate-800">Select Active Platform</span>
                  {[
                    { value: "Humanoid V1", desc: "16-Axis Humanoid Rig", nodes: "16 Nodes" },
                    { value: "Open Manipulator X", desc: "5-Axis Robotic Arm", nodes: "5 Nodes" },
                    { value: "V1", label: "LEAP Hand V1", desc: "16-Motor Biomimetic Hand", nodes: "16 Nodes" },
                    { value: "V2", label: "LEAP Hand V2", desc: "8-Motor Biomimetic Hand", nodes: "8 Nodes" },
                    { value: "Rover Bot", desc: "6-Wheel Drive Autonomous Rover", nodes: "6 Nodes" }
                  ].map((item) => {
                    const isSelected = handVersion === item.value;
                    const displayName = item.label || item.value;
                    return (
                      <button
                        key={item.value}
                        onClick={() => {
                          changeProfile(item.value);
                          setShowProfileDropdown(false);
                        }}
                        className={`w-full text-left px-3.5 py-2.5 rounded-xl flex items-center justify-between transition ${
                          isSelected 
                            ? "bg-[#CFFF3E]/10 text-[#CFFF3E] font-bold border-l-4 border-[#CFFF3E]" 
                            : "hover:bg-white/5 text-slate-450 hover:text-white font-medium"
                        }`}
                      >
                        <div className="flex flex-col gap-0.5">
                          <span className="text-xs">{displayName}</span>
                          <span className="text-[9px] text-slate-500 font-medium">{item.desc}</span>
                        </div>
                        <span className={`text-[9px] font-semibold px-2 py-0.5 rounded-full ${isSelected ? "bg-[#CFFF3E]/20 text-[#CFFF3E]" : "bg-slate-800 text-slate-500"}`}>
                          {item.nodes}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Center: Live Clock & Connection Pill with wifi dropdown manager */}
        <div className="absolute left-1/2 transform -translate-x-1/2 flex items-center gap-3 font-sans font-medium text-slate-200 tracking-wide">
          <span>{currentTime.toLocaleDateString("en-US", { weekday: 'short', month: 'short', day: 'numeric' })}  {currentTime.toLocaleTimeString("en-US", { hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true })}</span>
          
          <div className="relative">
            <button
              onClick={() => setShowConnectionDropdown(prev => !prev)}
              className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[9px] font-medium tracking-wide transition border ${
                connected 
                  ? "bg-green-500/10 text-green-400 border-green-500/20 hover:bg-green-500/20" 
                  : "bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20"
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-green-400 animate-pulse" : "bg-red-400"}`} />
              <span>{connected ? (mockMode ? "MOCK" : "LIVE") : "OFFLINE"}</span>
              <span className="text-[6px] text-slate-400">▼</span>
            </button>

            {showConnectionDropdown && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setShowConnectionDropdown(false)} 
                />
                
                <div className="absolute left-1/2 transform -translate-x-1/2 mt-2 bg-[#1E2022] rounded-2xl shadow-2xl border border-slate-700/60 p-5 z-50 w-64 text-white flex flex-col gap-4 font-sans animate-in fade-in slide-in-from-top-3 duration-200">
                  <span className="text-[10px] font-bold text-[#7E8B93] uppercase tracking-widest block border-b border-slate-800 pb-2 mb-1 font-sans">Connection Manager</span>
                  
                  {connected ? (
                    <div className="space-y-4">
                      <div className="text-[10px] font-semibold space-y-2">
                        <div className="flex justify-between items-center text-slate-400">
                          <span>Status:</span>
                          <span className="text-green-400 font-bold bg-green-500/10 px-2 py-0.5 rounded">CONNECTED</span>
                        </div>
                        <div className="flex justify-between items-center text-slate-400">
                          <span>Port:</span>
                          <span className="text-white font-mono bg-white/5 px-2 py-0.5 rounded">{port}</span>
                        </div>
                        <div className="flex justify-between items-center text-slate-400">
                          <span>Baudrate:</span>
                          <span className="text-white font-mono bg-white/5 px-2 py-0.5 rounded">{baudrate / 1000000}M bps</span>
                        </div>
                        <div className="flex justify-between items-center text-slate-400">
                          <span>Mock Mode:</span>
                          <span className="text-white bg-white/5 px-2 py-0.5 rounded">{mockMode ? "ACTIVE" : "OFF"}</span>
                        </div>
                      </div>

                      <button
                        onClick={() => {
                          triggerDisconnect();
                          setShowConnectionDropdown(false);
                        }}
                        className="w-full bg-red-600 hover:bg-red-700 active:scale-[0.98] text-white font-bold text-xs py-2.5 rounded-xl transition-all uppercase tracking-wider shadow-md hover:shadow-lg hover:shadow-red-500/10"
                      >
                        Disconnect Bus
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-4 font-sans">
                      <div className="space-y-3 text-[10px]">
                        <div className="space-y-1.5">
                          <label className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block">Port</label>
                          <input 
                            type="text" 
                            value={connPort}
                            onChange={(e) => setConnPort(e.target.value)}
                            placeholder="COM14"
                            className="w-full bg-[#161718] border border-slate-700 hover:border-slate-600 focus:border-[#B5ACF3] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-[#B5ACF3] transition-all"
                          />
                        </div>
                        
                        <div className="space-y-1.5">
                          <label className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block">Baudrate</label>
                          <select
                            value={connBaud}
                            onChange={(e) => setConnBaud(parseInt(e.target.value))}
                            className="w-full bg-[#161718] border border-slate-700 hover:border-slate-600 focus:border-[#B5ACF3] rounded-lg px-2.5 py-2 text-xs text-white focus:outline-none cursor-pointer transition-all"
                          >
                            <option value={4000000}>4M bps</option>
                            <option value={1000000}>1M bps</option>
                            <option value={115200}>115200 bps</option>
                            <option value={57600}>57600 bps</option>
                          </select>
                        </div>

                        <label className="flex items-center gap-2.5 font-semibold text-slate-300 hover:text-white cursor-pointer pt-2 transition-colors">
                          <input 
                            type="checkbox"
                            checked={connMock}
                            onChange={(e) => setConnMock(e.target.checked)}
                            className="rounded text-[#CFFF3E] bg-[#161718] border-slate-700 w-4 h-4 cursor-pointer focus:ring-0 focus:ring-offset-0 focus:outline-none transition-colors"
                          />
                          <span className="text-[10px]">Enable Mock Mode</span>
                        </label>
                      </div>

                      <button
                        onClick={() => {
                          triggerConnect();
                          setShowConnectionDropdown(false);
                        }}
                        className="w-full bg-[#CFFF3E] text-[#1E2022] hover:bg-[#bce634] active:scale-[0.98] font-bold text-xs py-2.5 rounded-xl transition-all uppercase tracking-wider shadow-md hover:shadow-lg hover:shadow-[#CFFF3E]/10"
                      >
                        Connect Bus
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Right: Telemetry Mini-status, Torque Toggle, Shortcuts, E-Stop, Profile avatar */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3 text-slate-400 font-sans font-medium">
            <div className="flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5 text-[#B5ACF3]" />
              <span>CPU: <span className="text-white font-medium">{systemStats.cpu}%</span></span>
            </div>
            <div className="flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-[#CFFF3E]" />
              <span>LATENCY: <span className="text-white font-medium">{systemStats.latency}ms</span></span>
            </div>
          </div>
          <span className="text-slate-700">|</span>
          
          {/* Torque Global Toggle Button */}
          <button
            onClick={() => toggleTorqueGlobal(!isAnyTorqueActive)}
            disabled={!connected}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider transition ${
              !connected ? "opacity-40 cursor-not-allowed bg-slate-800 text-slate-500" :
              isAnyTorqueActive 
                ? "bg-[#CFFF3E]/20 text-[#CFFF3E] border border-[#CFFF3E]/30" 
                : "bg-slate-800 text-slate-450 hover:bg-slate-700 hover:text-white"
            }`}
            title={isAnyTorqueActive ? "Click to release torque globally" : "Click to enable torque globally"}
          >
            <Cpu className="h-3 w-3" />
            <span>Torque {isAnyTorqueActive ? "ON" : "OFF"}</span>
          </button>
          
          <span className="text-slate-700">|</span>

          {/* Shortcuts Guide Button */}
          <button
            onClick={() => setShowShortcutHelp(true)}
            className="flex items-center gap-1 text-slate-400 hover:text-white transition font-medium"
            title="How to Use & Keyboard Shortcuts (Alt+H)"
          >
            <HelpCircle className="h-3.5 w-3.5 text-[#B5ACF3]" />
            <span className="uppercase tracking-wider">GUIDE</span>
          </button>
          
          <span className="text-slate-700">|</span>

          {/* E-Stop Indicator/Toggle */}
          <button
            onClick={toggleEstop}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider transition ${
              estopActive 
                ? "bg-red-650 text-white animate-pulse" 
                : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white"
            }`}
            title="Alt+S to toggle emergency stop"
          >
            <AlertTriangle className="h-3 w-3" />
            <span>ESTOP</span>
          </button>

          <span className="text-slate-700">|</span>

          {/* Profile Avatar & Username */}
          <div className="flex items-center gap-1.5">
            <div className="w-5 h-5 rounded-full bg-[#B5ACF3] text-white flex items-center justify-center font-semibold text-[9px] shadow-sm">
              OP
            </div>
            <span className="text-white hidden sm:inline font-medium">Bilal</span>
          </div>
        </div>

      </div>

      {/* WRAPPER FOR SIDEBAR AND MAIN CONTENT */}
      <div className="flex-1 flex p-5 w-full">
        <div className="w-full max-w-[1600px] mx-auto bg-[#EAEDF1] flex rounded-[40px] shadow-2xl overflow-hidden border-8 border-[#1E2022]/10 min-h-[90vh]">
        
        {/* SIDEBAR NAVIGATION */}
        <aside className="w-72 bg-[#1E2022] flex flex-col justify-between p-6 text-white rounded-[32px] m-3 shadow-xl">
          <div>
            <div className="flex items-center gap-3 px-3 py-4 mb-6">
              <Activity className="h-6 w-6 text-[#CFFF3E] animate-pulse" />
              <span className="text-xl font-extrabold tracking-tight text-white flex items-center gap-1">
                OSRS <span className="text-[#CFFF3E] font-medium text-xs bg-white/10 px-2 py-0.5 rounded-full">v1.2</span>
              </span>
            </div>

            <nav className="space-y-1.5">
              {[
                { id: "dashboard", label: "Dashboard", icon: Home },
                { id: "control", label: "Arm Control", icon: Sliders },
                { id: "emotemaker", label: "Emotes & Maker", icon: Play },
                { id: "digitaltwin", label: "Digital Twin", icon: Eye },
                { id: "dataflow", label: "Dataflow Graph", icon: Network },
                { id: "research", label: "Research Balancer", icon: TrendingUp },
                { id: "recording", label: "Replay & Record", icon: Database },
                { id: "calibration", label: "Calibration", icon: Wrench },
                { id: "mapper", label: "CAD ID Mapper", icon: Settings },
                { id: "vision", label: "Vision System", icon: Video },
                { id: "diagnostics", label: "Diagnostics", icon: Activity }
              ].map((item) => {
                const Icon = item.icon;
                const active = activeTab === item.id;
                
                // Set badges for visual dashboard style
                let badge = null;
                if (item.id === "dashboard" && connected) {
                  badge = activeMotorIds.length;
                } else if (item.id === "vision" && cameraActive) {
                  badge = "ON";
                } else if (item.id === "calibration" && calibrationState.running) {
                  badge = "RUN";
                }

                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveTab(item.id);
                      setSelectedJoint(null);
                    }}
                    className={`w-full flex items-center justify-between px-5 py-3.5 rounded-full text-sm font-bold transition-all duration-200 ${
                      active 
                        ? "bg-white text-[#1E2022] shadow-lg" 
                        : "text-[#7E8B93] hover:text-white hover:bg-white/5"
                    }`}
                  >
                    <div className="flex items-center gap-3.5">
                      <Icon className={`h-5 w-5 shrink-0 ${active ? "text-[#1E2022]" : "text-[#7E8B93]"}`} />
                      <span>{item.label}</span>
                    </div>
                    {badge !== null && (
                      <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${
                        active ? "bg-[#1E2022] text-[#CFFF3E]" : "bg-[#CFFF3E] text-[#1E2022]"
                      }`}>
                        {badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* SIDEBAR BOTTOM QUICK AUTOPILOT / ESTOP CARD */}
          <div className="mt-8">
            <div className="bg-[#CFFF3E] text-[#1E2022] p-5 rounded-[28px] flex flex-col gap-4 shadow-md relative overflow-hidden">
              <div className="absolute -right-4 -bottom-4 w-20 h-20 bg-black/5 rounded-full pointer-events-none" />
              <div>
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#1E2022]/60">Autopilot Center</span>
                <h4 className="text-base font-black leading-tight mt-0.5">OSRS GUARD ACTIVE</h4>
                <p className="text-[11px] font-bold text-[#1E2022]/70 mt-1">Speed limit: {connSpeedLimit} RPM</p>
              </div>
              <button 
                onClick={toggleEstop}
                className={`w-full text-white font-extrabold py-3 px-4 rounded-full text-xs shadow-sm tracking-wider uppercase transition-all ${
                  estopActive 
                    ? "bg-red-600 hover:bg-red-700 animate-bounce" 
                    : "bg-[#1E2022] hover:bg-black"
                }`}
              >
                {estopActive ? "DISABLE ESTOP" : "ENGAGE ESTOP"}
              </button>
            </div>
          </div>
        </aside>

        {/* MAIN WORKSPACE CANVAS */}
        <main className="flex-1 flex flex-col p-6 overflow-y-auto bg-[#EAEDF1]">

          {/* ALERT NOTIFICATIONS */}
          {alertBanner && (
            <div className={`p-4 mb-6 rounded-2xl flex items-center justify-between shadow-sm border ${
              alertBanner.type === "error" ? "bg-red-50 border-red-200 text-red-600" :
              alertBanner.type === "warning" ? "bg-amber-50 border-amber-200 text-amber-600" :
              "bg-green-50 border-green-200 text-green-700"
            }`}>
              <span className="text-sm font-bold flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" /> {alertBanner.message}
              </span>
              <button onClick={() => setAlertBanner(null)} className="opacity-75 hover:opacity-100 font-extrabold">✕</button>
            </div>
          )}

          {/* TAB 1: DASHBOARD */}
          {activeTab === "dashboard" && (
            <div className="space-y-6 animate-fade-in">
              
              {/* Operator Welcome Panel */}
              <div className="mb-4">
                <h2 className="text-3xl font-black text-[#1E2022] tracking-tight">Robot Overview</h2>
                <p className="text-xs text-[#7E8B93] font-bold mt-0.5">Take control of your robotic system today!</p>
              </div>

              {/* Startup Connection Bar if offline */}
              {!connected && (
                <div className="bg-white rounded-[32px] p-6 shadow-sm border border-slate-200/50 flex flex-col md:flex-row justify-between items-center gap-6">
                  <div>
                    <h3 className="text-xl font-extrabold text-[#1E2022] flex items-center gap-2">
                      <WifiOff className="h-5 w-5 text-slate-400" /> Start Connection
                    </h3>
                    <p className="text-slate-500 mt-1 text-xs font-semibold">Configure serial link parameters and establish communication line.</p>
                  </div>
                  <div className="flex flex-wrap gap-3 items-center bg-slate-50 p-2 rounded-2xl border border-slate-200">
                    <input 
                      type="text" 
                      value={connPort}
                      onChange={(e) => setConnPort(e.target.value)}
                      placeholder="COM14"
                      className="bg-white px-4 py-2 rounded-xl text-xs font-bold w-28 focus:outline-none border border-slate-200"
                    />
                    <select
                      value={connBaud}
                      onChange={(e) => setConnBaud(parseInt(e.target.value))}
                      className="bg-white border border-slate-200 px-3 py-2 rounded-xl text-xs font-bold focus:outline-none cursor-pointer"
                    >
                      <option value={4000000}>4M bps</option>
                      <option value={1000000}>1M bps</option>
                      <option value={115200}>115200 bps</option>
                      <option value={57600}>57600 bps</option>
                    </select>
                    <label className="flex items-center gap-2 text-xs font-bold text-slate-600 cursor-pointer px-2">
                      <input 
                        type="checkbox"
                        checked={connMock}
                        onChange={(e) => setConnMock(e.target.checked)}
                        className="rounded text-blue-600 w-4 h-4 cursor-pointer"
                      />
                      Mock Mode
                    </label>
                    <button
                      onClick={triggerConnect}
                      className="bg-[#1E2022] hover:bg-black text-white px-6 py-2.5 rounded-full text-xs font-bold transition shadow-md"
                    >
                      CONNECT
                    </button>
                  </div>
                </div>
              )}

              {/* Main Overhaul Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Column 1: Joint Energy/Load Distribution (Large card) */}
                <div className="bg-white rounded-[32px] p-6 shadow-sm border border-slate-200/50 flex flex-col justify-between min-h-[460px]">
                  <div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-black text-[#7E8B93] uppercase tracking-wider">Actuator Ticks Distribution</span>
                      <span className="text-[10px] font-black text-green-600 bg-green-50 px-2.5 py-0.5 rounded-full">+12% load</span>
                    </div>
                    <h3 className="text-3xl font-black text-[#1E2022] mt-1">4.2k <span className="text-xs font-bold text-[#7E8B93]">ticks today</span></h3>
                  </div>

                  {/* Overlapping Circles graphic */}
                  <div className="relative h-44 flex items-center justify-center my-4">
                    {/* Purple/Lavender load bubble */}
                    <div 
                      className="absolute left-[15%] w-32 h-32 bg-[#B5ACF3] bg-opacity-95 flex flex-col items-center justify-center text-white shadow-lg border-2 border-white/50 animate-bounce z-10"
                      style={{ borderRadius: "50%", animationDuration: "3s" }}
                    >
                      <span className="text-xl font-extrabold tracking-tight">2.6k</span>
                      <span className="text-[9px] font-bold opacity-80 uppercase tracking-widest">Left Arm</span>
                    </div>
                    
                    {/* Dark Charcoal load bubble */}
                    <div 
                      className="absolute right-[20%] w-28 h-28 bg-[#1E2022] flex flex-col items-center justify-center text-white shadow-lg border-2 border-white/20"
                      style={{ borderRadius: "50%" }}
                    >
                      <span className="text-lg font-extrabold tracking-tight">1.2k</span>
                      <span className="text-[8px] font-bold opacity-80 uppercase tracking-widest text-[#7E8B93]">Right Arm</span>
                    </div>
                    
                    {/* Neon Lime load bubble */}
                    <div 
                      className="absolute bottom-[5%] left-[45%] w-20 h-20 bg-[#CFFF3E] flex flex-col items-center justify-center text-[#1E2022] shadow-md border-2 border-white animate-pulse z-20"
                      style={{ borderRadius: "50%" }}
                    >
                      <span className="text-base font-black tracking-tight">500</span>
                      <span className="text-[7px] font-bold opacity-90 uppercase tracking-widest">Grip</span>
                    </div>
                  </div>

                  {/* Progress bars matching Reference Colors */}
                  <div className="space-y-3">
                    <div className="flex justify-between items-center text-[10px] font-bold text-slate-500">
                      <span>Left Arm</span>
                      <span>45%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-[#B5ACF3] h-full rounded-full" style={{ width: "45%" }} />
                    </div>

                    <div className="flex justify-between items-center text-[10px] font-bold text-slate-500">
                      <span>Right Arm</span>
                      <span>30%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-[#1E2022] h-full rounded-full" style={{ width: "30%" }} />
                    </div>

                    <div className="flex justify-between items-center text-[10px] font-bold text-slate-500">
                      <span>Peripherals</span>
                      <span>25%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-[#CFFF3E] h-full rounded-full" style={{ width: "25%" }} />
                    </div>
                  </div>
                </div>

                {/* Column 2: Stats cards & Signal Activity */}
                <div className="space-y-6 flex flex-col justify-between">
                  {/* Small card 1: Temp / CPU */}
                  <div className="bg-white rounded-[32px] p-5 shadow-sm border border-slate-200/50 flex justify-between items-center">
                    <div>
                      <span className="text-[10px] font-black text-[#7E8B93] uppercase tracking-wider block">System CPU Load</span>
                      <h4 className="text-2xl font-black text-[#1E2022] mt-1">{systemStats.cpu}%</h4>
                      <span className="text-[9px] text-[#7E8B93] font-bold mt-0.5 block">Avg: 5.4%</span>
                    </div>
                    <div className="w-10 h-10 rounded-full bg-[#B5ACF3]/20 flex items-center justify-center">
                      <Cpu className="w-5 h-5 text-[#B5ACF3]" />
                    </div>
                  </div>

                  {/* Small card 2: Telemetry latency */}
                  <div className="bg-white rounded-[32px] p-5 shadow-sm border border-slate-200/50 flex justify-between items-center">
                    <div>
                      <span className="text-[10px] font-black text-[#7E8B93] uppercase tracking-wider block">Bus Latency</span>
                      <h4 className="text-2xl font-black text-[#1E2022] mt-1">{systemStats.latency} ms</h4>
                      <span className="text-[9px] text-[#7E8B93] font-bold mt-0.5 block">FPS: {systemStats.fps} Hz</span>
                    </div>
                    <div className="w-10 h-10 rounded-full bg-[#CFFF3E]/20 flex items-center justify-center">
                      <Activity className="w-5 h-5 text-[#1E2022]" />
                    </div>
                  </div>

                  {/* Live Telemetry Terminal in Column 2 */}
                  <div className="bg-[#1E2022] rounded-[32px] p-6 shadow-lg text-white flex-1 flex flex-col justify-between min-h-[220px]">
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex items-center gap-2">
                        <Terminal className="h-5 w-5 text-[#CFFF3E]" />
                        <span className="font-extrabold text-sm tracking-tight text-slate-100">Live Telemetry Terminal</span>
                      </div>
                    </div>
                    <div ref={terminalRef} className="bg-black/40 font-mono text-[10px] p-3.5 rounded-2xl h-36 overflow-y-auto border border-white/5 flex flex-col gap-0.5 text-slate-300 flex-1">
                      {logs.length > 0 ? (
                        logs.map((log, index) => {
                          let textColor = "text-slate-300";
                          if (log.includes("ERROR")) textColor = "text-red-400 font-bold";
                          else if (log.includes("WARNING")) textColor = "text-amber-400";
                          else if (log.includes("AUTO-RESTART")) textColor = "text-[#CFFF3E]";
                          return <div key={index} className={textColor}>{log}</div>;
                        })
                      ) : (
                        <div className="text-slate-600 text-center py-8 italic text-xs">Terminal lines empty. Verify hardware connection.</div>
                      )}
                      <div ref={logEndRef} />
                    </div>
                  </div>
                </div>

                {/* Column 3: Wellness Index / Node Integrity Matrix */}
                <div className="bg-white rounded-[32px] p-6 shadow-sm border border-slate-200/50 flex flex-col justify-between min-h-[460px]">
                  <div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-black text-[#7E8B93] uppercase tracking-wider">Integrity Channel Index</span>
                      <span className="text-[10px] font-black text-[#CFFF3E] bg-[#1E2022] px-2.5 py-0.5 rounded-full">{systemStats.health}% Good</span>
                    </div>
                    <h3 className="text-3xl font-black text-[#1E2022] mt-1">{activeMotorIds.length} <span className="text-xs font-bold text-[#7E8B93]">Nodes Connected</span></h3>
                  </div>

                  <div className="flex-1 flex flex-col justify-center my-6">
                    <div className="grid grid-cols-4 gap-2.5 p-3.5 bg-slate-50 rounded-[24px] border border-slate-100 shadow-inner">
                      {activeMotorIds.map((mid) => {
                        const telemData = telemetry[mid] || { error: 0, torque: false };
                        const hasError = telemData.error !== 0;
                        const isTorqued = telemData.torque === true;
                        
                        let dotBg = "bg-slate-200 border-slate-300";
                        if (connected) {
                          if (hasError) dotBg = "bg-red-500 border-red-600 text-white animate-pulse";
                          else if (isTorqued) dotBg = "bg-[#CFFF3E] border-[#1E2022]/10";
                          else dotBg = "bg-[#B5ACF3]/60 border-[#B5ACF3]/20";
                        }

                        return (
                          <div 
                            key={mid}
                            onClick={() => {
                              setSelectedJoint(parseInt(mid));
                              setActiveTab("control");
                            }}
                            title={`Joint ID ${mid}: ${limits[mid]?.name || "Actuator"}`}
                            className={`h-11 rounded-xl ${dotBg} border flex flex-col items-center justify-center text-[10px] font-black shadow-sm cursor-pointer hover:scale-105 transition-transform`}
                          >
                            <span className="opacity-60 text-[8px]">ID</span>
                            <span>{mid}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="flex justify-between items-center text-[9px] text-[#7E8B93] font-black border-t border-slate-100 pt-3">
                    <span className="flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded bg-[#CFFF3E] border border-slate-300" /> Active Torque</span>
                    <span className="flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded bg-[#B5ACF3]/60 border border-slate-300" /> Standby/Hold</span>
                    <span className="flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded bg-red-500 border border-red-600" /> Register Fault</span>
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* TAB 2: VISUAL CONTROL */}
          {activeTab === "control" && (
            <div className="bg-white rounded-[32px] p-8 shadow-sm border border-slate-200 animate-fade-in">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 border-b border-slate-100 pb-4 gap-4">
                <div>
                  <h3 className="text-2xl font-black text-[#1E2022]">Visual Structure Control</h3>
                  <p className="text-xs text-[#7E8B93] font-bold mt-0.5">Highlight joints in the map to filter. Slide parameters or click direct values to override coordinates.</p>
                </div>
                <div className="bg-[#B5ACF3]/10 border border-[#B5ACF3]/30 rounded-2xl p-4 text-[11px] text-[#1D192B] font-bold max-w-sm">
                  <span className="block font-black text-[#1E2022]">Horn Convention:</span>
                  <span className="block mt-0.5">● (+) values move Counter-Clockwise (CCW).</span>
                  <span className="block">● (-) values move Clockwise (CW).</span>
                  <span className="block">● Reference baseline offset is mapped at 0.</span>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* SVG Skeleton Map (Center) */}
                <div className="bg-[#EAEDF1]/50 rounded-[28px] p-6 border border-slate-200/50 flex flex-col items-center justify-center min-h-[460px]">
                  <h4 className="text-[10px] font-black text-[#7E8B93] uppercase tracking-widest mb-6">Joint Wireframe Mapper</h4>
                  
                  {handVersion === "Humanoid V1" || handVersion === "V1" || handVersion === "V2" ? (
                    <svg viewBox="0 0 340 380" className="w-full max-w-[280px] h-auto">
                      {/* Neck & Head trunk */}
                      <line x1="170" y1="20" x2="170" y2="48" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="170" y1="48" x2="170" y2="75" stroke="#CBD5E1" strokeWidth="4" />
                      
                      {/* Shoulders */}
                      <line x1="170" y1="75" x2="120" y2="90" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="170" y1="75" x2="220" y2="90" stroke="#CBD5E1" strokeWidth="4" />
                      
                      {/* Left Arm Links */}
                      <line x1="120" y1="90" x2="105" y2="130" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="105" y1="130" x2="90" y2="170" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="90" y1="170" x2="75" y2="210" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="75" y1="210" x2="60" y2="250" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="60" y1="250" x2="45" y2="290" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="45" y1="290" x2="30" y2="330" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="30" y1="330" x2="18" y2="365" stroke="#CBD5E1" strokeWidth="3" strokeDasharray="3,3" />

                      {/* Right Arm Links */}
                      <line x1="220" y1="90" x2="235" y2="130" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="235" y1="130" x2="250" y2="170" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="250" y1="170" x2="265" y2="210" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="265" y1="210" x2="280" y2="250" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="280" y1="250" x2="295" y2="290" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="295" y1="290" x2="310" y2="330" stroke="#CBD5E1" strokeWidth="4" />
                      <line x1="310" y1="330" x2="322" y2="365" stroke="#CBD5E1" strokeWidth="3" strokeDasharray="3,3" />

                      {/* Neck Base center connector node (fixed helper dot) */}
                      <circle cx="170" cy="75" r="7" fill="#1E2022" />

                      {[
                        // Head (IDs 31, 32)
                        { id: 32, label: "H-P", cx: 170, cy: 20 },
                        { id: 31, label: "H-Y", cx: 170, cy: 48 },
                        
                        // Left Arm (IDs 21, 12, 13, 24, 25, 26, 27, 28)
                        { id: 21, label: "L1P", cx: 120, cy: 90 },
                        { id: 12, label: "L2R", cx: 105, cy: 130 },
                        { id: 13, label: "L3Y", cx: 90, cy: 170 },
                        { id: 24, label: "L4F", cx: 75, cy: 210 },
                        { id: 25, label: "L5Y", cx: 60, cy: 250 },
                        { id: 26, label: "L6R", cx: 45, cy: 290 },
                        { id: 27, label: "L7P", cx: 30, cy: 330 },
                        { id: 28, label: "L8G", cx: 18, cy: 365 },

                        // Right Arm (IDs 11, 22, 23, 14, 15, 16, 17, 18)
                        { id: 11, label: "R1P", cx: 220, cy: 90 },
                        { id: 22, label: "R2R", cx: 235, cy: 130 },
                        { id: 23, label: "R3Y", cx: 250, cy: 170 },
                        { id: 14, label: "R4F", cx: 265, cy: 210 },
                        { id: 15, label: "R5Y", cx: 280, cy: 250 },
                        { id: 16, label: "R6R", cx: 295, cy: 290 },
                        { id: 17, label: "R7P", cx: 310, cy: 330 },
                        { id: 18, label: "R8G", cx: 322, cy: 365 }
                      ].map((node) => {
                        const hasError = telemetry[node.id]?.error !== 0;
                        const isSelected = selectedJoint === node.id;
                        const isTorqued = telemetry[node.id]?.torque === true;
                        
                        let fillVal = "#CBD5E1";
                        if (hasError) fillVal = "#EF4444";
                        else if (isSelected) fillVal = "#B5ACF3";
                        else if (isTorqued) fillVal = "#CFFF3E";

                        return (
                          <g key={node.id} className="cursor-pointer" onClick={() => handleJointClick(node.id)}>
                            <circle 
                              cx={node.cx} 
                              cy={node.cy} 
                              r="13" 
                              fill={fillVal} 
                              stroke="#1E2022" 
                              strokeWidth="1.5"
                              className="transition-colors duration-200" 
                            />
                            <text x={node.cx} y={node.cy + 3.5} textAnchor="middle" fill="#1E2022" className="font-extrabold text-[7.5px] select-none pointer-events-none">
                              {node.label}
                            </text>
                          </g>
                        );
                      })}
                    </svg>
                  ) : (
                    <div className="flex flex-col items-center justify-center flex-1 text-slate-400 italic text-xs">
                      <span>No skeleton mapping view available for {handVersion}</span>
                    </div>
                  )}
                  
                  {selectedJoint && (
                    <div className="mt-4 text-xs bg-[#B5ACF3]/20 text-[#1E2022] px-4 py-2 rounded-full font-black">
                      Selected Joint ID: {selectedJoint}
                    </div>
                  )}

                  {/* Dual-Arm Mirroring & Pose Presets Card */}
                  <div className="mt-6 w-full bg-slate-50/50 rounded-[24px] border border-slate-200/60 p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-black text-slate-800 uppercase tracking-wide">Dual-Arm Mirroring</span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={mirrorSyncActive} 
                          onChange={(e) => handleToggleMirrorSync(e.target.checked)} 
                          className="sr-only peer" 
                        />
                        <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-350 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#CFFF3E]"></div>
                      </label>
                    </div>
                    
                    <div className="border-t border-slate-200/60 pt-3">
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2.5">Calibrated Pose Presets</span>
                      <div className="grid grid-cols-2 gap-2">
                        <button 
                          onClick={() => handleSendCommand("both_arms")}
                          disabled={!connected}
                          className="py-2 bg-[#1E2022] hover:bg-black text-white text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Both Arms Pose
                        </button>
                        <button 
                          onClick={() => handleSendCommand("left_pose")}
                          disabled={!connected}
                          className="py-2 bg-slate-100 hover:bg-slate-200 text-[#1E2022] border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Left Arm Pose
                        </button>
                        <button 
                          onClick={() => handleSendCommand("right_pose")}
                          disabled={!connected}
                          className="py-2 bg-slate-100 hover:bg-slate-200 text-[#1E2022] border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Right Arm Pose
                        </button>
                        <button 
                          onClick={() => handleSendCommand("tilt_up")}
                          disabled={!connected}
                          className="py-2 bg-slate-100 hover:bg-slate-200 text-[#1E2022] border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Both Arms Up
                        </button>
                        <button 
                          onClick={() => handleSendCommand("tilt_center")}
                          disabled={!connected}
                          className="py-2 bg-slate-100 hover:bg-slate-200 text-[#1E2022] border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Both Arms Center
                        </button>
                        <button 
                          onClick={() => handleSendCommand("tilt_down")}
                          disabled={!connected}
                          className="py-2 bg-slate-100 hover:bg-slate-200 text-[#1E2022] border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Both Arms Down
                        </button>
                        <button 
                          onClick={() => handleSendCommand("left_hand_open")}
                          disabled={!connected}
                          className="py-2 bg-slate-100 hover:bg-slate-200 text-[#1E2022] border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Left Hand Open
                        </button>
                        <button 
                          onClick={() => handleSendCommand("left_hand_closed")}
                          disabled={!connected}
                          className="py-2 bg-slate-100 hover:bg-slate-200 text-[#1E2022] border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Left Hand Closed
                        </button>
                        <button 
                          onClick={() => handleSendCommand("zero_all")}
                          disabled={!connected}
                          className="py-2 bg-white hover:bg-red-50 text-red-650 border border-red-200 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Zero All Joints
                        </button>
                        <button 
                          onClick={() => handleSendCommand("sync_goals")}
                          disabled={!connected}
                          className="py-2 bg-white hover:bg-blue-50 text-blue-605 border border-blue-200 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Sync Goals
                        </button>
                      </div>
                    </div>
                  </div>
                </div>


                {/* Sliders Panel */}
                <div className="lg:col-span-2 space-y-4 max-h-[520px] overflow-y-auto pr-2">
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
                          <div key={catKey} className="bg-slate-50/60 rounded-[28px] border border-slate-200/60 p-4 space-y-3 transition-all duration-300">
                            <button
                              onClick={() => setExpandedSections(prev => ({ ...prev, [catKey]: !prev[catKey] }))}
                              className="w-full flex items-center justify-between font-bold text-xs uppercase tracking-wider text-slate-500 hover:text-slate-800 px-2 py-1 transition focus:outline-none"
                            >
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-black text-slate-800">{catData.title}</span>
                                <span className="bg-slate-200 text-slate-700 text-[10px] px-2.5 py-0.5 rounded-full font-extrabold">{catData.joints.length} Node{catData.joints.length > 1 ? 's' : ''}</span>
                              </div>
                              <span className="text-[10px] font-black font-mono transition-transform duration-200" style={{ display: 'inline-block', transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}>
                                ▶
                              </span>
                            </button>
                            
                            {isExpanded && (
                              <div className="space-y-4 pt-1 animate-fade-in">
                                {catData.joints.map((mid) => {
                                  const info = limits[mid];
                                  const telemData = telemetry[mid] || { present: info.default, error: 0 };
                                  const hasError = telemData.error !== 0;
                                  const isSelected = selectedJoint === parseInt(mid);
                                  
                                  const currentPhysical = telemData.present === "--" ? info.default : parseInt(telemData.present);
                                  const currentGoal = telemData.goal === undefined || telemData.goal === "--" ? info.default : parseInt(telemData.goal);
                                  const telemValue = currentGoal - info.default;
                                  const displayValue = localDrags[mid] !== undefined ? localDrags[mid] : telemValue;


                                  const minVal = info.min - info.default;
                                  const maxVal = info.max - info.default;
                                  const isTorqued = telemData.torque === true;

                                  return (
                                    <div 
                                      key={mid}
                                      ref={el => sliderRefs.current[mid] = el}
                                      className={`p-5 rounded-[24px] border transition-all ${
                                        hasError ? "border-red-400 bg-red-50/10" : 
                                        isSelected ? "border-[#B5ACF3] ring-4 ring-[#B5ACF3]/10" : 
                                        isTorqued 
                                          ? "bg-[#B5ACF3]/10 border-[#B5ACF3]/50" 
                                          : "bg-white border-slate-200 hover:border-slate-300"
                                      }`}
                                    >
                                      <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                          <span className="font-extrabold text-base text-[#1E2022]">{info.name}</span>
                                          <span className="text-[9px] bg-slate-100 text-[#7E8B93] font-bold px-2 py-0.5 rounded-full">ID {mid}</span>
                                          <button 
                                            onClick={() => toggleTorqueIndividual(mid, true)}
                                            className="text-[9px] bg-slate-100 hover:bg-[#CFFF3E] text-[#1E2022] font-black px-2.5 py-0.5 rounded-full transition"
                                          >
                                            TORQUE ON
                                          </button>
                                          <button 
                                            onClick={() => toggleTorqueIndividual(mid, false)}
                                            className="text-[9px] bg-slate-100 hover:bg-red-500 hover:text-white text-[#7E8B93] font-black px-2.5 py-0.5 rounded-full transition"
                                          >
                                            TORQUE OFF
                                          </button>
                                        </div>
                                        {hasError ? (
                                          <button onClick={() => rebootMotor(mid)} className="bg-red-100 text-red-700 px-3.5 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 hover:bg-red-200">
                                            <RefreshCw className="w-3.5 h-3.5 animate-spin" /> RESTART SERVO
                                          </button>
                                        ) : (
                                          <input 
                                            type="text"
                                            value={inputValues[mid] !== undefined ? inputValues[mid] : displayValue}
                                            onChange={(e) => handleInputChange(mid, e.target.value, minVal, maxVal)}
                                            onBlur={() => handleInputBlur(mid)}
                                            className="w-16 text-center text-xs font-mono font-bold text-[#1E2022] bg-[#EAEDF1] border border-slate-200 rounded-lg py-1 focus:outline-none focus:ring-2 focus:ring-[#B5ACF3]"
                                            title="Click to manually edit angle value"
                                          />
                                        )}
                                      </div>

                                      {/* Quick Rotate & Value readout row */}
                                      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 bg-slate-50/50 p-3 rounded-2xl border border-slate-100 text-xs">
                                        <div className="flex items-center gap-2">
                                          <span className="text-[#7E8B93] font-bold">Quick Rotate:</span>
                                          <button
                                            onClick={() => rotateJointByDeg(mid, -90)}
                                            disabled={hasError}
                                            className="px-3 py-1.5 bg-white hover:bg-slate-100 text-[#1E2022] font-extrabold rounded-xl border border-slate-200 transition text-[10px] uppercase tracking-wider flex items-center gap-1 disabled:opacity-40"
                                          >
                                            -90° (CW)
                                          </button>
                                          <button
                                            onClick={() => rotateJointByDeg(mid, 90)}
                                            disabled={hasError}
                                            className="px-3 py-1.5 bg-white hover:bg-slate-100 text-[#1E2022] font-extrabold rounded-xl border border-slate-200 transition text-[10px] uppercase tracking-wider flex items-center gap-1 disabled:opacity-40"
                                          >
                                            +90° (CCW)
                                          </button>
                                        </div>
                                        <div className="flex items-center gap-3 text-[#7E8B93] font-bold font-mono text-[10px]">
                                          <span>OFFSET: <span className="text-blue-600 font-black">{displayValue} ticks</span> ({(displayValue * 360 / 4096).toFixed(1)}°)</span>
                                          <span className="text-slate-350">|</span>
                                          <span>ABS: <span className="text-[#1E2022] font-black">{currentPhysical} ticks</span></span>
                                        </div>
                                      </div>
                                      
                                      <div className="flex items-center gap-4">
                                        <span className="text-[10px] text-[#7E8B93] font-bold">{minVal}</span>
                                        <div className="flex-1">
                                          <input 
                                            type="range"
                                            min={minVal}
                                            max={maxVal}
                                            value={displayValue}
                                            onChange={(e) => handleSliderDrag(mid, e.target.value)}
                                            onPointerUp={() => handleSliderRelease(mid)}
                                            className="w-full"
                                            disabled={hasError}
                                          />
                                          <div className="flex justify-between text-[8px] text-[#7E8B93] font-bold mt-1 px-1">
                                            <span>(-) Clockwise (CW)</span>
                                            <span>(+) Counter-Clockwise (CCW)</span>
                                          </div>
                                        </div>
                                        <span className="text-[10px] text-[#7E8B93] font-bold">{maxVal}</span>
                                      </div>
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
                    <div className="text-slate-400 text-center py-20 italic">Please establish device bus connection first.</div>
                  )}
                </div>

              </div>
            </div>
          )}

          {/* TAB 3: EMOTE CONTROL & MAKER */}
          {activeTab === "emotemaker" && (
            <div className="space-y-6 animate-fade-in">
              
              {/* Presets Motions card */}
              <div className="bg-white rounded-[32px] p-6 shadow-sm border border-slate-200/50">
                <h3 className="text-xl font-black text-[#1E2022] mb-4">Preset Robot Expressive Motions</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                  {[
                    { name: "HI Left", color: "text-purple-700 bg-purple-50/50 hover:bg-purple-100 border border-purple-200" },
                    { name: "HI Right", color: "text-purple-700 bg-purple-50/50 hover:bg-purple-100 border border-purple-200" },
                    { name: "Namaste", color: "text-green-800 bg-green-50/50 hover:bg-green-100 border border-green-200" },
                    { name: "Clap", color: "text-fuchsia-800 bg-fuchsia-50/50 hover:bg-fuchsia-100 border border-fuchsia-200" },
                    { name: "Victory", color: "text-amber-800 bg-amber-50/50 hover:bg-amber-100 border border-amber-200" },
                    { name: "Heart", color: "text-red-800 bg-red-50/50 hover:bg-red-100 border border-red-200" },
                    { name: "67", color: "text-slate-800 bg-slate-50/50 hover:bg-slate-100 border border-slate-200" }
                  ].map((emote, i) => {
                    const isPlaying = playingPreset === emote.name;
                    return (
                      <div key={i} className={`p-4 rounded-[24px] flex flex-col justify-between items-center text-center gap-3 transition ${emote.color}`}>
                        <span className="font-extrabold text-xs tracking-tight">{emote.name}</span>
                        <div className="flex gap-2 w-full">
                          <button
                            onClick={() => playPresetEmote(emote.name)}
                            disabled={isPlaying || !connected}
                            className="flex-1 py-2 bg-[#1E2022] text-white hover:bg-black rounded-xl text-[10px] font-black flex items-center justify-center gap-1 transition disabled:opacity-40"
                            title="Play this motion preset on the arm"
                          >
                            {isPlaying ? <StopCircle className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                            <span>{isPlaying ? "Playing" : "Play"}</span>
                          </button>
                          <button
                            onClick={() => loadPresetEmoteIntoMaker(emote.name)}
                            className="p-2 bg-white/75 text-[#1E2022] hover:bg-white border border-slate-200 rounded-xl text-[10px] font-black flex items-center justify-center transition"
                            title="Load preset frames into Editor to edit"
                          >
                            <Sliders className="w-3.5 h-3.5 text-[#B5ACF3]" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Emote Maker Workspace */}
              <div className="bg-white rounded-[32px] p-8 shadow-sm border border-slate-200/50">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 border-b border-slate-100 pb-4 gap-4">
                  <div>
                    <h3 className="text-2xl font-black text-[#1E2022]">Custom Emote Maker Sequence</h3>
                    <p className="text-xs text-[#7E8B93] font-bold mt-0.5">Define poses and steps to create a custom loop. Edits broadcast live frames to the physical arm.</p>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-3">
                    <label className="flex items-center gap-2 bg-slate-50 px-4 py-2 rounded-full border border-slate-200">
                      <Repeat className="w-4 h-4 text-slate-500" />
                      <span className="text-xs font-bold text-slate-600">Loops</span>
                      <input 
                        type="number" 
                        min="1" 
                        max="100" 
                        value={emoteLoop} 
                        onChange={(e) => setEmoteLoop(parseInt(e.target.value) || 1)}
                        className="w-12 bg-white border border-slate-200 rounded-lg py-1 text-center font-bold focus:outline-none text-xs"
                      />
                    </label>
                    <label className="flex items-center gap-2 bg-slate-50 px-4 py-2 rounded-full border border-slate-200">
                      <Sliders className="w-4 h-4 text-slate-500" />
                      <span className="text-xs font-bold text-slate-600">Speed</span>
                      <select 
                        value={emoteSpeed} 
                        onChange={(e) => setEmoteSpeed(parseFloat(e.target.value))}
                        className="bg-white border border-slate-250/30 rounded-lg py-1 px-2 font-bold focus:outline-none text-xs cursor-pointer hover:border-slate-350"
                      >
                        <option value={0.25}>0.25x</option>
                        <option value={0.5}>0.5x</option>
                        <option value={1.0}>1.0x (Normal)</option>
                        <option value={1.5}>1.5x</option>
                        <option value={2.0}>2.0x</option>
                      </select>
                    </label>
                    <button 
                      onClick={playCustomEmote}
                      disabled={playingEmote || !connected}
                      className={`px-6 py-2.5 rounded-full text-xs font-bold flex items-center gap-2 transition shadow-md ${
                        playingEmote 
                          ? "bg-amber-100 text-amber-700 cursor-wait shadow-none"
                          : "bg-[#1E2022] text-white hover:bg-black"
                      }`}
                    >
                      {playingEmote ? <StopCircle className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                      {playingEmote ? "PLAYING..." : "PLAY SEQUENCE"}
                    </button>

                    <button 
                      onClick={() => setShowSaveModal(true)}
                      className="px-6 py-2.5 rounded-full text-xs font-bold bg-[#CFFF3E] text-[#1E2022] hover:bg-[#bce634] shadow-md transition flex items-center gap-2"
                    >
                      <Save className="w-4 h-4" /> SAVE EMOTE
                    </button>
                  </div>
                </div>

                <div className="space-y-6">
                  {emoteFrames.map((frame, fidx) => (
                    <div key={fidx} className="bg-slate-50 rounded-[28px] p-6 border border-slate-250/50 relative group">
                      <div className="absolute -left-4 -top-4 w-8 h-8 bg-white border-2 border-slate-200 rounded-full flex items-center justify-center font-black text-slate-400 text-xs shadow-md">
                        {fidx + 1}
                      </div>
                      
                      <div className="flex justify-between items-center mb-4 border-b border-slate-200/50 pb-3">
                        <div className="flex items-center gap-6">
                          <div className="flex items-center gap-3">
                            <span className="text-xs font-bold text-slate-500">Transition Frames:</span>
                            <input 
                              type="number" 
                              value={frame.delay} 
                              onChange={(e) => updateFrameDelay(fidx, e.target.value)}
                              className="w-16 px-3 py-1 rounded-lg border border-slate-350 focus:outline-none font-bold text-xs"
                            />
                          </div>

                          <div className="flex items-center gap-3">
                            <span className="text-xs font-bold text-slate-500">Hold Frames:</span>
                            <input 
                              type="number" 
                              value={frame.hold ?? 0} 
                              onChange={(e) => updateFrameHold(fidx, e.target.value)}
                              className="w-16 px-3 py-1 rounded-lg border border-slate-350 focus:outline-none font-bold text-xs"
                            />
                          </div>

                          <button
                            onClick={() => previewFrame(frame)}
                            disabled={!connected}
                            className="bg-[#B5ACF3]/10 text-[#1E2022] hover:bg-[#B5ACF3]/20 border border-[#B5ACF3]/30 px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition disabled:opacity-40"
                            title="Move robot to this frame pose for layout alignment"
                          >
                            <Eye className="w-3.5 h-3.5" /> PREVIEW ON ROBOT
                          </button>
                        </div>
                        <button 
                          onClick={() => removeEmoteFrame(fidx)}
                          className="p-1.5 rounded-full hover:bg-red-50 text-slate-400 hover:text-red-500 transition"
                        >
                          <Trash className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {Object.keys(limits).map((mid) => {
                          const info = limits[mid];
                          const val = frame.modifications[info.name] ?? 0;
                          const minVal = info.min - info.default;
                          const maxVal = info.max - info.default;
                          const tempKey = `${fidx}_${info.name}`;
                          const displayVal = emoteInputValues[tempKey] !== undefined ? emoteInputValues[tempKey] : val;

                          return (
                            <div key={mid} className="bg-white px-4 py-3 rounded-[16px] border border-slate-200 shadow-sm">
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-xs font-bold text-slate-500">{info.name}</span>
                                <input 
                                  type="text"
                                  value={displayVal}
                                  onChange={(e) => {
                                    const rawVal = e.target.value;
                                    setEmoteInputValues(prev => ({ ...prev, [tempKey]: rawVal }));
                                    
                                    const parsed = parseInt(rawVal);
                                    if (!isNaN(parsed)) {
                                      const clamped = Math.max(minVal, Math.min(maxVal, parsed));
                                      updateFrameJoint(fidx, info.name, clamped);
                                      
                                      const updatedFrame = {
                                        ...frame,
                                        modifications: {
                                          ...frame.modifications,
                                          [info.name]: clamped
                                        }
                                      };
                                      previewFrame(updatedFrame);
                                    }
                                  }}
                                  onBlur={() => {
                                    setEmoteInputValues(prev => {
                                      const next = { ...prev };
                                      delete next[tempKey];
                                      return next;
                                    });
                                  }}
                                  className="w-14 text-center text-[10px] font-mono font-bold text-[#1E2022] bg-slate-50 border border-slate-200 rounded-lg py-0.5 focus:outline-none"
                                />
                              </div>
                              <input 
                                type="range"
                                min={minVal}
                                max={maxVal}
                                value={val}
                                onChange={(e) => {
                                  const parsedValue = parseInt(e.target.value) || 0;
                                  updateFrameJoint(fidx, info.name, parsedValue);
                                  const updatedFrame = {
                                    ...frame,
                                    modifications: {
                                      ...frame.modifications,
                                      [info.name]: parsedValue
                                    }
                                  };
                                  previewFrame(updatedFrame);
                                }}
                                className="w-full"
                              />
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}

                  <button 
                    onClick={addEmoteFrame}
                    className="w-full py-4 rounded-[24px] border-2 border-dashed border-slate-300 text-slate-500 font-bold hover:border-[#B5ACF3] hover:text-[#1E2022] hover:bg-slate-50 transition flex justify-center items-center gap-2"
                  >
                    <Plus className="w-4 h-4" /> ADD SEQUENCE FRAME
                  </button>
                </div>
              </div>

              {/* Saved Custom Emotes List */}
              <div className="bg-white rounded-[32px] p-8 shadow-sm border border-slate-200/50">
                <h3 className="text-xl font-black text-[#1E2022] mb-4">Saved Custom Emotes</h3>
                {Object.keys(savedEmotes).length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(savedEmotes).map(([name, frames]) => {
                      const isPlaying = playingPreset === name;
                      return (
                        <div key={name} className="bg-slate-50 p-5 rounded-[24px] border border-slate-200 flex flex-col justify-between gap-4">
                          <div>
                            <span className="font-extrabold text-base text-[#1E2022] block truncate">{name}</span>
                            <span className="text-[10px] bg-slate-250 text-[#7E8B93] font-bold px-2 py-0.5 rounded-full inline-block mt-1">
                              {frames.length} Frame(s)
                            </span>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => playSavedCustomEmote(name, frames)}
                              disabled={isPlaying || !connected}
                              className={`flex-1 py-2 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                                isPlaying
                                  ? "bg-amber-100 text-amber-700"
                                  : "bg-[#1E2022] text-white hover:bg-black disabled:opacity-40"
                              }`}
                            >
                              {isPlaying ? <StopCircle className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                              <span>{isPlaying ? "Playing" : "Play"}</span>
                            </button>
                            <button
                              onClick={() => loadSavedEmoteIntoMaker(name, frames)}
                              className="px-3 py-2 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-xl transition font-bold text-xs flex items-center justify-center gap-1"
                              title="Load into Editor"
                            >
                              <Sliders className="w-3.5 h-3.5" />
                              <span>Edit</span>
                            </button>
                            <button
                              onClick={() => handleDeleteCustomEmote(name)}
                              className="px-3 py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-xl transition flex items-center justify-center"
                              title="Delete"
                            >
                              <Trash className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-slate-400 text-center py-12 italic text-xs">
                    No custom emotes saved yet. Build a sequence above and click "Save Emote".
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB: DIGITAL TWIN */}
          {activeTab === "digitaltwin" && (
            <div className="space-y-6 animate-fade-in w-full h-full min-h-[450px]">
              <div className="mb-2">
                <h2 className="text-3xl font-black text-[#1E2022] tracking-tight">Digital Twin Workspace</h2>
                <p className="text-xs text-[#7E8B93] font-bold mt-0.5">Real-time synchronized 3D representation of your robot.</p>
              </div>
              <div className="w-full h-[550px]">
                <DigitalTwinViewer 
                  joints={digitalTwin.joints}
                  activeRobot={handVersion}
                  syncMode={digitalTwin.sync_mode}
                  onSyncModeChange={handleSyncModeChange}
                />
              </div>
            </div>
          )}

          {/* TAB: DATAFLOW GRAPH */}
          {activeTab === "dataflow" && (
            <div className="space-y-6 animate-fade-in">
              <div className="mb-2">
                <h2 className="text-3xl font-black text-[#1E2022] tracking-tight">Dataflow Pipelines</h2>
                <p className="text-xs text-[#7E8B93] font-bold mt-0.5">ROS-inspired node graph visualizing active perception and control pipelines.</p>
              </div>
              <DataflowWorkspace 
                cameraActive={cameraActive}
                trackingEnabled={trackingEnabled}
                balancerActive={balancer.is_active}
                syncMode={digitalTwin.sync_mode}
              />
            </div>
          )}

          {/* TAB: BALL BALANCER RESEARCH */}
          {activeTab === "research" && (
            <div className="space-y-6 animate-fade-in">
              <div className="mb-2">
                <h2 className="text-3xl font-black text-[#1E2022] tracking-tight">Ball Balancer Research</h2>
                <p className="text-xs text-[#7E8B93] font-bold mt-0.5">Tune and monitor the plate balancing algorithm.</p>
              </div>
              <BallBalancerResearch 
                telemetry={telemetry}
                balancerData={balancer}
                onTune={handleTuneBalancer}
                onToggle={handleToggleBalancer}
                onGoToStart={handleGoToStart}
                onInitializeArms={handleInitializeArms}
                onSendCommand={handleSendCommand}
                videoFrame={videoFrame}
                cameraActive={cameraActive}
                onToggleVision={toggleVisionSystem}
                limits={limits}
                connected={connected}
              />
            </div>
          )}

          {/* TAB: TELEMETRY RECORDER & REPLAY */}
          {activeTab === "recording" && (
            <div className="space-y-6 animate-fade-in">
              <div className="mb-2">
                <h2 className="text-3xl font-black text-[#1E2022] tracking-tight">Replay & Recording</h2>
                <p className="text-xs text-[#7E8B93] font-bold mt-0.5">Log telemetry frames to files and replay recorded trajectories.</p>
              </div>
              <DataRecorder 
                recorderState={recorder}
                onToggleRecord={handleToggleRecord}
                onExport={handleExportRecording}
                onLoadReplay={handleLoadReplay}
              />
            </div>
          )}

          {/* TAB 4: CALIBRATION */}
          {activeTab === "calibration" && (
            <div className="space-y-8 max-w-3xl mx-auto animate-fade-in">
              {/* Wizard Card */}
              <div className="bg-white rounded-[32px] p-8 shadow-sm border border-slate-200/50">
                <div className="flex items-center gap-3 border-b border-slate-100 pb-4 mb-6">
                  <Wrench className="h-6 w-6 text-[#1E2022]" />
                  <h3 className="text-2xl font-black text-[#1E2022]">Calibration Wizard</h3>
                </div>
                
                <p className="text-xs text-[#7E8B93] font-bold mb-8 leading-relaxed">
                  Calibration calculates individual actuator endpoints and maps absolute zero coordinates. The wizard uses quintic polynomial path generation to smoothly shift joints, detecting mechanical cable binding or thermal obstructions.
                </p>

                <div className="bg-slate-50 rounded-[24px] p-6 border border-slate-200/50 mb-8 space-y-6">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black text-slate-500 uppercase">Operational Status</span>
                    <span className={`text-xs font-black px-3 py-1 rounded-full ${
                      calibrationState.running 
                        ? (calibrationState.paused ? "bg-amber-100 text-amber-700 animate-pulse" : "bg-blue-100 text-blue-750 animate-pulse") 
                        : "bg-slate-200 text-slate-600"
                    }`}>
                      {calibrationState.status_msg}
                    </span>
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs font-bold text-slate-400">
                      <span>Task Progress</span>
                      <span>{Math.round(calibrationState.progress * 100)}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden shadow-inner">
                      <div 
                        className="bg-[#1E2022] h-full rounded-full transition-all duration-300"
                        style={{ width: `${calibrationState.progress * 100}%` }}
                      />
                    </div>
                  </div>

                  {calibrationState.fault_reason && (
                    <div className="bg-red-50 text-red-650 p-4 rounded-xl border border-red-100 text-xs font-bold flex items-start gap-2.5">
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                      <div>
                        <span className="block text-red-800 uppercase tracking-wide text-[10px]">Safety Fault Triggered</span>
                        <span className="block font-medium mt-0.5">{calibrationState.fault_reason}</span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-center gap-4">
                  {!calibrationState.running ? (
                    <div className="flex gap-4">
                      <button
                        onClick={() => controlCalibration("start")}
                        disabled={!connected}
                        className="bg-[#1E2022] hover:bg-black text-white font-bold text-xs px-8 py-3.5 rounded-full transition disabled:opacity-40"
                      >
                        START CALIBRATION PROFILE
                      </button>
                      <button
                        onClick={handleSetZeroCalibration}
                        disabled={!connected}
                        className="bg-[#CFFF3E] hover:bg-[#bce634] text-[#1E2022] font-black text-xs px-8 py-3.5 rounded-full transition disabled:opacity-40"
                      >
                        SET CURRENT POSE AS ZERO (INITIAL)
                      </button>
                    </div>
                  ) : (
                    <>
                      {calibrationState.paused ? (
                        <button
                          onClick={() => controlCalibration("resume")}
                          className="bg-green-600 hover:bg-green-700 text-white font-bold text-xs px-6 py-2.5 rounded-full transition shadow-sm"
                        >
                          RESUME MOTION
                        </button>
                      ) : (
                        <button
                          onClick={() => controlCalibration("pause")}
                          className="bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs px-6 py-2.5 rounded-full transition shadow-sm"
                        >
                          PAUSE MOTION
                        </button>
                      )}
                      
                      <button
                        onClick={() => controlCalibration("retry")}
                        className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs px-6 py-2.5 rounded-full border border-slate-200 transition"
                      >
                        RETRY SEGMENT
                      </button>
                      
                      <button
                        onClick={() => controlCalibration("abort")}
                        className="bg-red-600 hover:bg-red-700 text-white font-bold text-xs px-6 py-2.5 rounded-full transition"
                      >
                        ABORT CALIBRATION
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Physical Arm Calibration Wizard Card */}
              <div className="bg-white rounded-[32px] p-8 shadow-sm border border-slate-200/50">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 mb-6 gap-4">
                  <div className="flex items-center gap-3">
                    <Wrench className="h-6 w-6 text-[#1E2022]" />
                    <h3 className="text-2xl font-black text-[#1E2022]">Physical Arm Calibration Wizard</h3>
                  </div>
                  
                  <button
                    onClick={handleSaveCalibration}
                    disabled={!connected}
                    className="bg-[#CFFF3E] hover:bg-[#bce634] text-[#1E2022] font-black text-xs px-6 py-2.5 rounded-full transition disabled:opacity-40 self-start sm:self-auto"
                  >
                    SAVE CALIBRATION TO FILE
                  </button>
                </div>

                <p className="text-xs text-[#7E8B93] font-bold mb-8 leading-relaxed">
                  Power on torques, physically position the arms to their neutral straight poses, capture calibration offsets, and click "Save Calibration to File".
                </p>

                {/* Arm Panels Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Left Arm Calibration Card */}
                  <div className="bg-slate-50/50 p-5 rounded-[24px] border border-slate-200/60 flex flex-col gap-4">
                    <div className="flex justify-between items-center border-b border-slate-200/65 pb-3">
                      <span className="text-[#1E2022] font-black text-sm uppercase tracking-wide">Left Arm Calibration</span>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleTorqueArm("left", true)}
                          disabled={!connected}
                          className="px-2.5 py-1 bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 rounded-lg text-[9px] font-black uppercase hover:bg-emerald-500/25 transition disabled:opacity-40"
                        >
                          Torque ON
                        </button>
                        <button
                          onClick={() => handleTorqueArm("left", false)}
                          disabled={!connected}
                          className="px-2.5 py-1 bg-red-500/10 text-red-650 border border-red-500/20 rounded-lg text-[9px] font-black uppercase hover:bg-red-500/25 transition disabled:opacity-40"
                        >
                          Relax
                        </button>
                        <button
                          onClick={() => handleCaptureCalibration("left")}
                          disabled={!connected}
                          className="px-2.5 py-1 bg-slate-200 text-[#1E2022] border border-slate-350 rounded-lg text-[9px] font-black uppercase hover:bg-slate-300 transition disabled:opacity-40"
                        >
                          Capture
                        </button>
                      </div>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-[9px]">
                            <th className="py-2 font-semibold">Joint</th>
                            <th className="py-2 font-semibold text-center">ID</th>
                            <th className="py-2 font-semibold text-center">Live Position</th>
                            <th className="py-2 font-semibold text-center">Calibrated Center</th>
                            <th className="py-2 font-semibold text-center">Torque</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200/60 text-slate-700">
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
                            const calibVal = calibration.calib_left?.[mid] ?? 0;
                            const tempKey = `left_${mid}`;
                            const displayVal = calibInputValues[tempKey] !== undefined ? calibInputValues[tempKey] : calibVal;

                            return (
                              <tr key={mid} className="hover:bg-slate-100/40">
                                <td className="py-2 text-[#1E2022] font-extrabold">{jointName}</td>
                                <td className="py-2 text-center text-slate-400 font-mono">{mid}</td>
                                <td className={`py-2 text-center font-mono font-bold ${livePos === "--" ? "text-slate-400" : "text-slate-900"}`}>
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
                                    className="w-16 text-center font-mono font-bold text-blue-605 bg-slate-150/40 border border-slate-200 rounded py-0.5 focus:outline-none focus:ring-1 focus:ring-[#B5ACF3]"
                                  />
                                </td>
                                <td className="py-2 text-center">
                                  <button
                                    onClick={() => toggleTorqueIndividual(mid, !isTorqueOn)}
                                    disabled={!connected}
                                    className={`px-2 py-0.5 text-[9px] font-bold uppercase rounded border transition ${
                                      isTorqueOn
                                        ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                                        : "bg-slate-100 text-slate-400 border-slate-200"
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
                  <div className="bg-slate-50/50 p-5 rounded-[24px] border border-slate-200/60 flex flex-col gap-4">
                    <div className="flex justify-between items-center border-b border-slate-200/65 pb-3">
                      <span className="text-[#1E2022] font-black text-sm uppercase tracking-wide">Right Arm Calibration</span>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleTorqueArm("right", true)}
                          disabled={!connected}
                          className="px-2.5 py-1 bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 rounded-lg text-[9px] font-black uppercase hover:bg-emerald-500/25 transition disabled:opacity-40"
                        >
                          Torque ON
                        </button>
                        <button
                          onClick={() => handleTorqueArm("right", false)}
                          disabled={!connected}
                          className="px-2.5 py-1 bg-red-500/10 text-red-650 border border-red-500/20 rounded-lg text-[9px] font-black uppercase hover:bg-red-500/25 transition disabled:opacity-40"
                        >
                          Relax
                        </button>
                        <button
                          onClick={() => handleCaptureCalibration("right")}
                          disabled={!connected}
                          className="px-2.5 py-1 bg-slate-200 text-[#1E2022] border border-slate-350 rounded-lg text-[9px] font-black uppercase hover:bg-slate-300 transition disabled:opacity-40"
                        >
                          Capture
                        </button>
                      </div>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-[9px]">
                            <th className="py-2 font-semibold">Joint</th>
                            <th className="py-2 font-semibold text-center">ID</th>
                            <th className="py-2 font-semibold text-center">Live Position</th>
                            <th className="py-2 font-semibold text-center">Calibrated Center</th>
                            <th className="py-2 font-semibold text-center">Torque</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200/60 text-slate-700">
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
                            const calibVal = calibration.calib_right?.[mid] ?? 0;
                            const tempKey = `right_${mid}`;
                            const displayVal = calibInputValues[tempKey] !== undefined ? calibInputValues[tempKey] : calibVal;

                            return (
                              <tr key={mid} className="hover:bg-slate-100/40">
                                <td className="py-2 text-[#1E2022] font-extrabold">{jointName}</td>
                                <td className="py-2 text-center text-slate-400 font-mono">{mid}</td>
                                <td className={`py-2 text-center font-mono font-bold ${livePos === "--" ? "text-slate-400" : "text-slate-900"}`}>
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
                                    className="w-16 text-center font-mono font-bold text-blue-605 bg-slate-150/40 border border-slate-200 rounded py-0.5 focus:outline-none focus:ring-1 focus:ring-[#B5ACF3]"
                                  />
                                </td>
                                <td className="py-2 text-center">
                                  <button
                                    onClick={() => toggleTorqueIndividual(mid, !isTorqueOn)}
                                    disabled={!connected}
                                    className={`px-2 py-0.5 text-[9px] font-bold uppercase rounded border transition ${
                                      isTorqueOn
                                        ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                                        : "bg-slate-100 text-slate-400 border-slate-200"
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

              {/* Base Frame Editor Card */}
              <div className="bg-white rounded-[32px] p-8 shadow-sm border border-slate-200/50">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 mb-6 gap-4">
                  <div className="flex items-center gap-3">
                    <Settings className="h-6 w-6 text-[#1E2022]" />
                    <h3 className="text-2xl font-black text-[#1E2022]">Base Frame Configurator</h3>
                  </div>
                  
                  <button
                    onClick={handleGoToBase}
                    disabled={!connected}
                    className="bg-[#1E2022] hover:bg-black text-white font-bold text-xs px-6 py-2.5 rounded-full transition disabled:opacity-40 self-start sm:self-auto"
                  >
                    GO TO BASE FRAME
                  </button>
                </div>

                <p className="text-xs text-[#7E8B93] font-bold mb-6 leading-relaxed">
                  Set the absolute tick values for your calibrated base frame. Read the live servo tick values, enter your custom baseline targets, and click "Save Base Frame Configurations" to persist them.
                </p>

                {Object.keys(limits).length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-100 text-[#7E8B93] text-[10px] font-black uppercase tracking-wider">
                          <th className="py-3 px-4">Joint Name</th>
                          <th className="py-3 px-4">Motor ID</th>
                          <th className="py-3 px-4">Live Position</th>
                          <th className="py-3 px-4">Base Frame (Ticks)</th>
                          <th className="py-3 px-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50 text-xs">
                        {Object.keys(limits).map((mid) => {
                          const info = limits[mid];
                          const telemData = telemetry[mid] || { present: "--" };
                          const currentVal = calibBaseInputs[mid] ?? info.default;
                          return (
                            <tr key={mid} className="hover:bg-slate-50/50">
                              <td className="py-3.5 px-4 font-bold text-[#1E2022]">{info.name}</td>
                              <td className="py-3.5 px-4 font-mono text-slate-500">ID {mid}</td>
                              <td className="py-3.5 px-4 font-mono font-bold text-blue-600">
                                {telemData.present}
                              </td>
                              <td className="py-3.5 px-4">
                                <input
                                  type="number"
                                  value={currentVal}
                                  onChange={(e) => {
                                    const val = parseInt(e.target.value) || 0;
                                    setCalibBaseInputs(prev => ({ ...prev, [mid]: val }));
                                  }}
                                  className="w-24 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 font-mono font-bold text-[#1E2022] focus:outline-none focus:border-[#1E2022]"
                                />
                              </td>
                              <td className="py-3.5 px-4 text-right">
                                <button
                                  onClick={() => {
                                    if (telemData.present !== "--") {
                                      const liveVal = parseInt(telemData.present);
                                      setCalibBaseInputs(prev => ({ ...prev, [mid]: liveVal }));
                                    }
                                  }}
                                  disabled={telemData.present === "--"}
                                  className="text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-3 py-1 rounded transition disabled:opacity-40"
                                >
                                  Use Live Position
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>

                    <div className="flex justify-end mt-6 pt-4 border-t border-slate-100">
                      <button
                        onClick={handleSaveBaseFrame}
                        className="bg-[#CFFF3E] hover:bg-[#bce634] text-[#1E2022] font-black text-xs px-8 py-3.5 rounded-full transition"
                      >
                        SAVE BASE FRAME CONFIGURATIONS
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400 italic text-xs">
                    Please connect robot/simulator to load motor mapping.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 5: CAD ID MAPPER */}
          {activeTab === "mapper" && (
            <div className="bg-white rounded-[32px] p-8 shadow-sm border border-slate-200/50 animate-fade-in">
              <div className="flex items-center gap-3 border-b border-slate-100 pb-4 mb-6">
                <Settings className="h-6 w-6 text-[#1E2022]" />
                <h3 className="text-2xl font-black text-[#1E2022]">CAD ID Joint Mapping Editor</h3>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Form Editor */}
                <div className="bg-slate-50 rounded-[28px] p-6 border border-slate-200 h-fit space-y-4">
                  <h4 className="text-[10px] font-black text-[#7E8B93] uppercase tracking-widest mb-2">
                    {editingMapper ? `Edit Joint ID ${mapperId}` : "Register New Joint Mapping"}
                  </h4>
                  
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-[#7E8B93] uppercase block">Active Actuator ID</label>
                    <input 
                      type="number"
                      value={mapperId}
                      onChange={(e) => setMapperId(e.target.value)}
                      disabled={editingMapper}
                      placeholder="e.g. 21"
                      className="w-full bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs font-bold focus:outline-none focus:ring-2 focus:ring-[#B5ACF3] disabled:opacity-50"
                    />
                  </div>

                  {editingMapper && (
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-[#7E8B93] uppercase block">Map to New ID</label>
                      <input 
                        type="number"
                        value={mapperNewId}
                        onChange={(e) => setMapperNewId(e.target.value)}
                        placeholder="New ID key"
                        className="w-full bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs font-bold focus:outline-none focus:ring-2 focus:ring-[#B5ACF3]"
                      />
                    </div>
                  )}

                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-[#7E8B93] uppercase block">Acronym / Name Label</label>
                    <input 
                      type="text"
                      value={mapperName}
                      onChange={(e) => setMapperName(e.target.value)}
                      placeholder="e.g. L1P"
                      className="w-full bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs font-bold focus:outline-none focus:ring-2 focus:ring-[#B5ACF3]"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-[#7E8B93] uppercase block">Min Raw Tick</label>
                      <input 
                        type="number"
                        value={mapperMin}
                        onChange={(e) => setMapperMin(parseInt(e.target.value) || 0)}
                        className="w-full bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs font-mono font-bold focus:outline-none focus:ring-2 focus:ring-[#B5ACF3]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-[#7E8B93] uppercase block">Max Raw Tick</label>
                      <input 
                        type="number"
                        value={mapperMax}
                        onChange={(e) => setMapperMax(parseInt(e.target.value) || 0)}
                        className="w-full bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs font-mono font-bold focus:outline-none focus:ring-2 focus:ring-[#B5ACF3]"
                      />
                    </div>
                  </div>

                  <div className="flex gap-3 pt-3">
                    <button
                      onClick={handleSaveMapper}
                      className="bg-[#1E2022] hover:bg-black text-white font-bold text-xs px-4 py-3 rounded-full flex-1 transition"
                    >
                      SAVE CONFIG
                    </button>
                    {editingMapper && (
                      <button
                        onClick={resetMapperForm}
                        className="bg-slate-200 hover:bg-slate-300 text-slate-700 font-bold text-xs px-4 py-3 rounded-full flex-1 transition"
                      >
                        CANCEL
                      </button>
                    )}
                  </div>
                </div>

                {/* Limits Table */}
                <div className="lg:col-span-2 overflow-x-auto">
                  <table className="w-full text-left text-xs font-medium border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                        <th className="py-3 px-4">Node ID</th>
                        <th className="py-3 px-4">Joint Label</th>
                        <th className="py-3 px-4">Min Tick</th>
                        <th className="py-3 px-4">Max Tick</th>
                        <th className="py-3 px-4">Center (Default)</th>
                        <th className="py-3 px-4 text-center">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.keys(limits).map((mid) => {
                        const info = limits[mid];
                        return (
                          <tr key={mid} className="border-b border-slate-100 hover:bg-slate-50/50">
                            <td className="py-3 px-4 font-mono font-bold">{mid}</td>
                            <td className="py-3 px-4 font-bold text-slate-750">{info.name}</td>
                            <td className="py-3 px-4 font-mono text-slate-500">{info.min}</td>
                            <td className="py-3 px-4 font-mono text-slate-500">{info.max}</td>
                            <td className="py-3 px-4 font-mono text-slate-500">{info.default}</td>
                            <td className="py-3 px-4 text-center flex justify-center gap-2">
                              <button
                                onClick={() => startEditMapper(mid, info)}
                                className="bg-[#B5ACF3]/10 hover:bg-[#B5ACF3]/25 text-[#1E2022] font-bold px-3 py-1.5 rounded-xl transition"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleDeleteMapper(mid)}
                                className="bg-red-50 hover:bg-red-100 text-red-650 font-bold px-3 py-1.5 rounded-xl transition"
                              >
                                Delete
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
          )}

          {/* TAB 6: VISION SYSTEM */}
          {activeTab === "vision" && (
            <div className="bg-white rounded-[32px] p-8 shadow-sm border border-slate-200/50 max-w-4xl mx-auto animate-fade-in">
              <div className="flex items-center gap-3 border-b border-slate-100 pb-4 mb-6">
                <Video className="h-6 w-6 text-[#1E2022]" />
                <h3 className="text-2xl font-black text-[#1E2022]">Perception Vision Pipeline</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Control settings */}
                <div className="bg-slate-50 rounded-[28px] p-6 border border-slate-200 h-fit space-y-5">
                  <h4 className="text-[10px] font-black text-[#7E8B93] uppercase tracking-widest">Camera Settings</h4>
                  
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500 uppercase block">Select Device Index</label>
                    <select
                      value={cameraIdx}
                      onChange={(e) => setCameraIdx(parseInt(e.target.value))}
                      disabled={cameraActive}
                      className="w-full bg-white border border-slate-200 px-3.5 py-2.5 rounded-xl text-xs font-bold focus:outline-none cursor-pointer"
                    >
                      <option value={0}>Camera Index 0 (Primary)</option>
                      <option value={1}>Camera Index 1 (Secondary)</option>
                      <option value={2}>Camera Index 2</option>
                    </select>
                  </div>

                  <div className="pt-2 space-y-3">
                    <button
                      onClick={toggleVisionSystem}
                      className={`w-full py-3 rounded-full text-xs font-bold transition shadow-sm ${
                        cameraActive 
                          ? "bg-red-100 text-red-650 hover:bg-red-200" 
                          : "bg-[#1E2022] text-white hover:bg-black"
                      }`}
                    >
                      {cameraActive ? "TURN CAMERA OFF" : "INITIALIZE CAMERA"}
                    </button>

                    <label className={`w-full flex items-center justify-between gap-4 p-3.5 rounded-2xl border text-xs font-bold cursor-pointer transition ${
                      trackingEnabled ? "bg-[#CFFF3E]/20 border-[#CFFF3E] text-[#1E2022]" : "bg-white border-slate-200 text-slate-650"
                    }`}>
                      <span>Hand-Tracking Autopilot</span>
                      <div className={`w-8 h-5 rounded-full p-0.5 flex-shrink-0 transition-colors ${trackingEnabled ? "bg-[#CFFF3E] border-[#1E2022]/10" : "bg-slate-300"}`}>
                        <div className={`w-4 h-4 bg-white rounded-full shadow-sm transform transition-transform ${trackingEnabled ? "translate-x-3" : "translate-x-0"}`} />
                      </div>
                      <input 
                        type="checkbox" 
                        checked={trackingEnabled} 
                        onChange={toggleHandTracking} 
                        disabled={!cameraActive}
                        className="hidden" 
                      />
                    </label>
                  </div>
                </div>

                {/* Webcam previews */}
                <div className="md:col-span-2 flex flex-col items-center justify-center">
                  <div className="w-full aspect-video rounded-[28px] bg-slate-900 border border-slate-800 shadow-inner overflow-hidden flex items-center justify-center relative">
                    {cameraActive ? (
                      videoFrame ? (
                        <img 
                          src={`data:image/jpeg;base64,${videoFrame}`} 
                          className="w-full h-full object-cover" 
                          alt="Perception Feed" 
                        />
                      ) : (
                        <div className="flex flex-col items-center gap-2 text-slate-500 font-mono text-xs">
                          <RefreshCw className="w-5 h-5 animate-spin text-[#B5ACF3]" />
                          <span>Streaming perception canvas pipeline...</span>
                        </div>
                      )
                    ) : (
                      <div className="text-slate-500 text-xs font-mono text-center px-4">
                        <span>Webcam line offline. Tap 'Initialize Camera'</span>
                        <span className="block mt-1 opacity-70">to start Mediapipe perception stream.</span>
                      </div>
                    )}
                    
                    {cameraActive && (
                      <span className="absolute bottom-4 right-4 bg-slate-900/80 backdrop-blur-md px-3 py-1 rounded-lg text-[10px] font-mono text-green-400 border border-slate-700">
                        FPS: {systemStats.fps}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: DIAGNOSTICS */}
          {activeTab === "diagnostics" && (
            <div className="space-y-6 animate-fade-in">
              <div className="bg-white rounded-[32px] p-8 shadow-sm border border-slate-200/50">
                <div className="flex items-center gap-3 border-b border-slate-100 pb-4 mb-6">
                  <Activity className="h-6 w-6 text-[#1E2022]" />
                  <h3 className="text-2xl font-black text-[#1E2022]">Health Diagnostics & Telemetry Bus</h3>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                        <th className="py-3 px-4">ID</th>
                        <th className="py-3 px-4">Joint Label</th>
                        <th className="py-3 px-4">Goal Tick</th>
                        <th className="py-3 px-4">Present Tick</th>
                        <th className="py-3 px-4">Current (mA)</th>
                        <th className="py-3 px-4">Error Status</th>
                        <th className="py-3 px-4 text-center">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.keys(limits).map((mid) => {
                        const info = limits[mid];
                        const telemData = telemetry[mid] || { goal: "--", present: "--", current: "--", error: 0 };
                        const hasError = telemData.error !== 0;
                        return (
                          <tr key={mid} className="border-b border-slate-100 hover:bg-slate-50/50">
                            <td className="py-3 px-4 font-mono font-bold">{mid}</td>
                            <td className="py-3 px-4 font-bold text-slate-750">{info.name}</td>
                            <td className="py-3 px-4 font-mono text-slate-500">{telemData.goal}</td>
                            <td className="py-3 px-4 font-mono text-slate-500">{telemData.present}</td>
                            <td className="py-3 px-4 font-mono text-slate-500">{telemData.current}</td>
                            <td className="py-3 px-4">
                              {hasError ? (
                                <span className="bg-red-150 text-red-700 px-2 py-0.5 rounded-full text-[10px] font-bold">
                                  0x{telemData.error.toString(16).toUpperCase()} ERROR
                                </span>
                              ) : (
                                <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-[10px] font-bold">NORMAL</span>
                              )}
                            </td>
                            <td className="py-3 px-4 text-center">
                              <button
                                onClick={() => rebootMotor(mid)}
                                className="bg-[#B5ACF3]/10 hover:bg-[#B5ACF3]/25 text-[#1E2022] font-bold px-3 py-1.5 rounded-xl transition text-[11px]"
                              >
                                Reboot
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Overload inject */}
                <div className="bg-white rounded-[32px] p-6 shadow-sm border border-slate-200/50">
                  <h3 className="text-lg font-extrabold text-[#1E2022] mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-red-500" /> Error Injection Simulator
                  </h3>
                  <p className="text-xs text-[#7E8B93] font-bold mb-5 leading-relaxed">
                    Inject artificial register errors into individual servos to simulate hardware faults (e.g. Overload 0x20 / 32).
                  </p>
                  
                  <div className="flex gap-4 items-center">
                    <input 
                      type="number"
                      placeholder="ID"
                      value={mockErrorId}
                      onChange={(e) => setMockErrorId(e.target.value)}
                      className="bg-[#EAEDF1] border border-slate-200 rounded-xl px-4 py-2 text-xs font-bold w-20 focus:outline-none focus:ring-2 focus:ring-[#B5ACF3]"
                    />
                    <select
                      value={mockErrorByte}
                      onChange={(e) => setMockErrorByte(e.target.value)}
                      className="bg-[#EAEDF1] border border-slate-200 rounded-xl px-4 py-2 text-xs font-bold focus:outline-none cursor-pointer"
                    >
                      <option value="32">0x20 Overload (OL)</option>
                      <option value="4">0x04 Overheating (OH)</option>
                      <option value="1">0x01 Input Voltage (V)</option>
                    </select>
                    <button
                      onClick={triggerMockError}
                      disabled={!mockErrorId}
                      className="bg-red-50 hover:bg-red-100 text-red-650 border border-red-100 font-bold text-xs px-6 py-2.5 rounded-full transition disabled:opacity-40"
                    >
                      INJECT ERROR
                    </button>
                  </div>
                </div>

                {/* Safety Register Limits settings */}
                <div className="bg-white rounded-[32px] p-6 shadow-sm border border-slate-200/50">
                  <h3 className="text-lg font-extrabold text-[#1E2022] mb-3 flex items-center gap-2">
                    <Settings className="h-5 w-5 text-[#B5ACF3]" /> Global Safety Limits
                  </h3>
                  <p className="text-xs text-[#7E8B93] font-bold mb-5 leading-relaxed">
                    Configure thresholds for maximum velocity and maximum current draw (mA). Adjustments apply during serial bus connections.
                  </p>
                  
                  <div className="space-y-4">
                    <div className="flex justify-between items-center bg-slate-50 p-3 rounded-xl border border-slate-150">
                      <span className="text-xs font-bold text-slate-600">Peak Current Limit</span>
                      <input 
                        type="number"
                        value={connCurrentLimit}
                        onChange={(e) => setConnCurrentLimit(parseInt(e.target.value) || 0)}
                        className="bg-white border border-slate-200 rounded-lg px-2 py-1 text-center font-mono font-bold text-xs w-20 focus:outline-none focus:border-[#B5ACF3]"
                      />
                      <span className="text-[10px] text-slate-400 font-bold">mA</span>
                    </div>

                    <div className="flex justify-between items-center bg-slate-50 p-3 rounded-xl border border-slate-150">
                      <span className="text-xs font-bold text-slate-600">Peak Speed Limit</span>
                      <input 
                        type="number"
                        value={connSpeedLimit}
                        onChange={(e) => setConnSpeedLimit(parseInt(e.target.value) || 0)}
                        className="bg-white border border-slate-200 rounded-lg px-2 py-1 text-center font-mono font-bold text-xs w-20 focus:outline-none focus:border-[#B5ACF3]"
                      />
                      <span className="text-[10px] text-slate-400 font-bold">RPM</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          {/* SAVE EMOTE MODAL */}
          {showSaveModal && (
            <div className="fixed inset-0 bg-[#1E2022]/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-white rounded-[32px] p-8 max-w-md w-full shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95 duration-200">
                <h3 className="text-lg font-black text-[#1E2022] mb-2 flex items-center gap-2">
                  <Save className="h-5 w-5 text-[#B5ACF3]" /> Save Custom Emote
                </h3>
                <p className="text-xs text-[#7E8B93] font-bold mb-6">
                  Name your custom sequence to save it to the server. You can replay or reload it to edit later.
                </p>
                <div className="space-y-4">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase block">Emote Name</label>
                    <input 
                      type="text"
                      value={saveName}
                      onChange={(e) => setSaveName(e.target.value)}
                      placeholder="e.g. Wave Hand, Dance Pose"
                      className="w-full bg-[#EAEDF1] border border-slate-200 rounded-xl px-4 py-2.5 text-xs font-bold focus:outline-none focus:ring-2 focus:ring-[#B5ACF3] focus:bg-white"
                      autoFocus
                    />
                  </div>
                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={handleSaveEmote}
                      disabled={!saveName.trim()}
                      className="bg-[#1E2022] hover:bg-black text-white font-bold text-xs px-6 py-3 rounded-full flex-1 transition disabled:opacity-40"
                    >
                      SAVE EMOTE
                    </button>
                    <button
                      onClick={() => {
                        setShowSaveModal(false);
                        setSaveName("");
                      }}
                      className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs px-6 py-3 rounded-full flex-1 transition"
                    >
                      CANCEL
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* KEYBOARD SHORTCUTS & HOW TO USE MANUAL MODAL */}
          {showShortcutHelp && (
            <div className="fixed inset-0 bg-[#1E2022]/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-white rounded-[32px] p-8 max-w-2xl w-full shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95 duration-200 max-h-[85vh] overflow-y-auto">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-black text-[#1E2022] flex items-center gap-2">
                    <BookOpen className="h-5 w-5 text-[#B5ACF3]" /> OSRS System Navigation & Keyboard Shortcuts
                  </h3>
                  <button 
                    onClick={() => setShowShortcutHelp(false)}
                    className="p-1 rounded-full hover:bg-slate-150 transition text-slate-400 hover:text-slate-800"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="space-y-6 text-xs text-[#1E2022]">
                  {/* Keyboard Shortcuts Section */}
                  <div className="bg-slate-50 rounded-2xl p-5 border border-slate-200/50">
                    <h4 className="font-extrabold text-[#1E2022] mb-3 flex items-center gap-2">
                      <Keyboard className="w-4 h-4 text-[#B5ACF3]" /> Keyboard Shortcuts (Visual Studio Navigation style)
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-semibold text-slate-650">
                      <div className="flex justify-between items-center bg-white p-2 rounded-xl border border-slate-200">
                        <span>Alt + 1</span>
                        <span className="bg-[#B5ACF3]/20 text-[#1D192B] px-2 py-0.5 rounded font-bold">Go to Dashboard</span>
                      </div>
                      <div className="flex justify-between items-center bg-white p-2 rounded-xl border border-slate-200">
                        <span>Alt + 2</span>
                        <span className="bg-[#B5ACF3]/20 text-[#1D192B] px-2 py-0.5 rounded font-bold">Go to Arm Control</span>
                      </div>
                      <div className="flex justify-between items-center bg-white p-2 rounded-xl border border-slate-200">
                        <span>Alt + 3</span>
                        <span className="bg-[#B5ACF3]/20 text-[#1D192B] px-2 py-0.5 rounded font-bold">Go to Emote Maker</span>
                      </div>
                      <div className="flex justify-between items-center bg-white p-2 rounded-xl border border-slate-200">
                        <span>Alt + 4</span>
                        <span className="bg-[#B5ACF3]/20 text-[#1D192B] px-2 py-0.5 rounded font-bold">Go to Calibration</span>
                      </div>
                      <div className="flex justify-between items-center bg-white p-2 rounded-xl border border-slate-200">
                        <span>Alt + 5</span>
                        <span className="bg-[#B5ACF3]/20 text-[#1D192B] px-2 py-0.5 rounded font-bold">Go to CAD Mapper</span>
                      </div>
                      <div className="flex justify-between items-center bg-white p-2 rounded-xl border border-slate-200">
                        <span>Alt + 6</span>
                        <span className="bg-[#B5ACF3]/20 text-[#1D192B] px-2 py-0.5 rounded font-bold">Go to Diagnostics</span>
                      </div>
                      <div className="flex justify-between items-center bg-white p-2 rounded-xl border border-slate-200">
                        <span>Alt + 7</span>
                        <span className="bg-[#B5ACF3]/20 text-[#1D192B] px-2 py-0.5 rounded font-bold">Go to Vision Pipeline</span>
                      </div>
                      <div className="flex justify-between items-center bg-white p-2 rounded-xl border border-slate-200">
                        <span>Alt + H</span>
                        <span className="bg-[#B5ACF3]/20 text-[#1D192B] px-2 py-0.5 rounded font-bold">Toggle Shortcuts/Help</span>
                      </div>
                      <div className="flex justify-between items-center bg-white p-2 rounded-xl border border-slate-200 col-span-1 md:col-span-2">
                        <span className="text-red-500 font-bold">Alt + S</span>
                        <span className="bg-red-50 text-red-700 px-2 py-0.5 rounded font-bold">Engage/Disable Emergency E-Stop</span>
                      </div>
                      <div className="flex justify-between items-center bg-white p-2 rounded-xl border border-slate-200 col-span-1 md:col-span-2">
                        <span>Alt + R</span>
                        <span className="bg-slate-100 text-slate-800 px-2 py-0.5 rounded font-bold">Reset Joints to Rest Position (0)</span>
                      </div>
                    </div>
                  </div>

                  {/* Manual Section */}
                  <div className="space-y-4">
                    <h4 className="font-extrabold text-sm border-b border-slate-155 pb-2 text-[#1E2022]">How to Use the Robotic Platform</h4>
                    
                    <div className="space-y-2">
                      <h5 className="font-black text-[#1E2022]">1. System Calibration</h5>
                      <p className="text-slate-600 font-semibold leading-relaxed">
                        To calibrate joint centers, click <span className="font-bold">Calibration Wizard</span>. Physically position the robot arms at their straight baseline positions. Click <span className="font-bold">"Set Current Pose as Zero (Initial)"</span>. This updates joint limits and maps all manual dials so that <span className="font-bold">0</span> is the perfect rest state.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <h5 className="font-black text-[#1E2022]">2. Custom Emotes & Existing Presets Editor</h5>
                      <p className="text-slate-600 font-semibold leading-relaxed">
                        Use the <span className="font-bold">Emote Maker & Sequence Control</span> tab to load existing preset motions (like Namaste, Victory, HI Left) directly into the editor canvas by clicking the <span className="font-bold">Edit icon (sliders)</span> next to any preset. You can add or delete frames, slide joint parameters, and drag playback speed dials (from 0.25x up to 2x speed) or loop counts before saving or testing!
                      </p>
                    </div>

                    <div className="space-y-2">
                      <h5 className="font-black text-[#1E2022]">3. Joint Wireframe Skeleton Interaction</h5>
                      <p className="text-slate-600 font-semibold leading-relaxed">
                        On the <span className="font-bold">Visual Arm Control</span> view, click any joint circle on the interactive skeleton diagram. The right-hand sliders panel will automatically scroll to highlight the selected actuator. Type exact position values inside the numerical fields or use the sliders for live preview.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end pt-6 border-t border-slate-100 mt-6">
                  <button
                    onClick={() => setShowShortcutHelp(false)}
                    className="bg-[#1E2022] hover:bg-black text-white px-6 py-3 rounded-full font-bold transition shadow-md"
                  >
                    CLOSE USER GUIDE
                  </button>
                </div>
              </div>
            </div>
          )}

      </main>
        </div>
      </div>
    </div>
  );
}
