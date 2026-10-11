import React, { useState, useEffect, useRef } from "react";
import {
  FileText, ChevronRight,
  Wifi, WifiOff, AlertTriangle, Settings, Sliders, Activity, Plus, Trash2, Repeat, Play, StopCircle, RefreshCw, Cpu, Wrench, Video, Terminal, Eye, Save, PlusCircle, Trash, Bell, Search, Home, HelpCircle, Keyboard, BookOpen, Bot, Map, Network, TrendingUp, Database, Info, Globe, ExternalLink
  , Zap, Menu, X, Command
} from "lucide-react";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: Home },
  { id: "simulations", label: "Simulations", icon: Cpu },
  { id: "paper", label: "Research Paper", icon: FileText },
  { id: "control", label: "Arm Control", icon: Sliders },
  { id: "emotemaker", label: "Emotes & Maker", icon: Play },
  { id: "dataflow", label: "Dataflow Graph", icon: Network },
  { id: "research", label: "Research Balancer", icon: TrendingUp },
  { id: "recording", label: "Replay & Record", icon: Database },
  { id: "calibration", label: "Calibration", icon: Wrench },
  { id: "mapper", label: "CAD ID Mapper", icon: Settings },
  { id: "vision", label: "Vision System", icon: Video },
  { id: "diagnostics", label: "Diagnostics", icon: Activity },
  { id: "about", label: "About Us", icon: Info },
  { id: "manual", label: "Product Manual", icon: BookOpen },
  { id: "sitemap", label: "Sitemap", icon: Map }
];

// Screen Components Architecture (Separated per screen)
import DashboardScreen from "./screens/DashboardScreen";
import SimulationsScreen from "./screens/SimulationsScreen";
import ResearchPaperScreen from "./screens/ResearchPaperScreen";
import ArmControlScreen from "./screens/ArmControlScreen";
import EmoteMakerScreen from "./screens/EmoteMakerScreen";
import DataflowScreen from "./screens/DataflowScreen";
import ResearchBalancerScreen from "./screens/ResearchBalancerScreen";
import RecordingScreen from "./screens/RecordingScreen";
import CalibrationScreen from "./screens/CalibrationScreen";
import CadMapperScreen from "./screens/CadMapperScreen";
import VisionScreen from "./screens/VisionScreen";
import DiagnosticsScreen from "./screens/DiagnosticsScreen";
import AboutScreen from "./screens/AboutScreen";
import ProductManualScreen from "./screens/ProductManualScreen";
import SitemapScreen from "./screens/SitemapScreen";

// Centralized Sitemap Configuration
import { SITEMAP, getScreenMetadata, searchSitemap } from "./config/sitemap";

const BAUDRATE_OPTIONS = [
  { value: 4000000, label: "4M bps" },
  { value: 1000000, label: "1M bps" },
  { value: 115200, label: "115200 bps" },
  { value: 57600, label: "57600 bps" }
];

const PRESET_EMOTE_FRAMES = {
  "HI Left": [
    { delay: 15, modifications: { "L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096 } },
    { delay: 5, modifications: { "L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "L6R": -2592 } },
    { delay: 5, modifications: { "L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "R6R": 1408 } },
    { delay: 5, modifications: { "L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "L6R": -2592 } },
    { delay: 5, modifications: { "L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "R6R": 1408 } },
    { delay: 5, modifications: { "L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "L6R": -2592 } },
    { delay: 5, modifications: { "L1P": -3392, "L2R": -3392, "L4F": 3008, "L8G": -4096, "R6R": 1408 } },
    { delay: 15, modifications: {} }
  ],
  "HI Right": [
    { delay: 15, modifications: { "R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096 } },
    { delay: 5, modifications: { "R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": 2592 } },
    { delay: 5, modifications: { "R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": -1408 } },
    { delay: 5, modifications: { "R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": 2592 } },
    { delay: 5, modifications: { "R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": -1408 } },
    { delay: 5, modifications: { "R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": 2592 } },
    { delay: 5, modifications: { "R1P": -3392, "R2R": 3392, "R4F": -3008, "R8G": -4096, "R6R": -1408 } },
    { delay: 15, modifications: {} }
  ],
  "Namaste": [
    { delay: 25, modifications: { "L1P": -992, "R1P": -992, "L2R": -1392, "R2R": 1392, "L3Y": -1792, "R3Y": 1792, "L4F": 3008, "R4F": -3008, "L7P": 0, "R7P": 0, "L8G": -4096, "R8G": -4096 } },
    { delay: 15, modifications: { "L1P": -992, "R1P": -992, "L2R": -1392, "R2R": 1392, "L3Y": -1792, "R3Y": 1792, "L4F": 3008, "R4F": -3008, "L7P": 0, "R7P": 0, "L8G": -4096, "R8G": -4096 } },
    { delay: 25, modifications: {} }
  ],
  "Clap": [
    { delay: 15, modifications: { "L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L2R": -2192, "R2R": 2192, "L8G": -4096, "R8G": -4096 } },
    { delay: 4, modifications: { "L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -792, "R2R": 792 } },
    { delay: 4, modifications: { "L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -2192, "R2R": 2192 } },
    { delay: 4, modifications: { "L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -792, "R2R": 792 } },
    { delay: 4, modifications: { "L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -2192, "R2R": 2192 } },
    { delay: 4, modifications: { "L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -792, "R2R": 792 } },
    { delay: 4, modifications: { "L1P": -992, "R1P": -992, "L4F": 1808, "R4F": -1808, "L8G": -4096, "R8G": -4096, "L2R": -2192, "R2R": 2192 } },
    { delay: 15, modifications: {} }
  ],
  "Victory": [
    { delay: 20, modifications: { "L1P": -4096, "R1P": -4096, "L2R": -4096, "R2R": 4096, "L4F": 0, "R4F": 0, "L8G": -4096, "R8G": -4096 } },
    { delay: 20, modifications: { "L1P": -4096, "R1P": -4096, "L2R": -4096, "R2R": 4096, "L4F": 0, "R4F": 0, "L8G": -4096, "R8G": -4096 } },
    { delay: 20, modifications: {} }
  ],
  "Heart": [
    { delay: 25, modifications: { "L1P": -592, "R1P": -592, "L2R": -1792, "R2R": 1792, "L4F": 3008, "R4F": -3008, "L6R": -2592, "R6R": 2592, "L7P": 3008, "R7P": -3008, "L8G": -2192, "R8G": -2192 } },
    { delay: 20, modifications: { "L1P": -592, "R1P": -592, "L2R": -1792, "R2R": 1792, "L4F": 3008, "R4F": -3008, "L6R": -2592, "R6R": 2592, "L7P": 3008, "R7P": -3008, "L8G": -2192, "R8G": -2192 } },
    { delay: 25, modifications: {} }
  ],
  "67": [
    { delay: 15, modifications: { "L3Y": -2048, "R3Y": 2048 } },
    { delay: 15, modifications: { "L3Y": -2048, "R3Y": 2048, "R4F": 2500, "R8G": -400 } },
    { delay: 15, modifications: { "L3Y": -2048, "R3Y": 2048, "L4F": 2500, "L8G": -400 } }
  ]
};

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [currentTime, setCurrentTime] = useState(new Date());
  const [showConnectionDropdown, setShowConnectionDropdown] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [commandQuery, setCommandQuery] = useState("");

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
  const [pauseLogs, setPauseLogsState] = useState(false);
  const pauseLogsRef = useRef(false);
  const [clearOffset, setClearOffset] = useState(0);

  const setPauseLogs = (val) => {
    pauseLogsRef.current = val;
    setPauseLogsState(val);
  };

  const handleClearLogs = () => {
    setClearOffset(logs.length);
  };

  const handleCopyLogs = () => {
    const visibleLogs = logs.slice(clearOffset);
    const text = visibleLogs.join("\n");
    navigator.clipboard.writeText(text);
  };

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

  const connectionDropdownRef = useRef(null);
  const profileDropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (showConnectionDropdown && connectionDropdownRef.current && !connectionDropdownRef.current.contains(event.target)) {
        setShowConnectionDropdown(false);
      }
      if (showProfileDropdown && profileDropdownRef.current && !profileDropdownRef.current.contains(event.target)) {
        setShowProfileDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showConnectionDropdown, showProfileDropdown]);

  const [showSplash, setShowSplash] = useState(true);
  const [splashFade, setSplashFade] = useState(false);
  const [splashProgress, setSplashProgress] = useState(0);
  const [splashMsg, setSplashMsg] = useState("Initializing core modules...");

  useEffect(() => {
    const messages = [
      "Detecting hardware nodes...",
      "Syncing Dynamixel motor bus...",
      "Initializing perception pipelines...",
      "Calibrating system parameters...",
      "Awaiting telemetry link...",
      "Ready!"
    ];

    let msgIndex = 0;
    const msgInterval = setInterval(() => {
      if (msgIndex < messages.length - 1) {
        setSplashMsg(messages[msgIndex]);
        msgIndex++;
      }
    }, 350);

    const progressInterval = setInterval(() => {
      setSplashProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return prev + 4;
      });
    }, 80);

    const fadeTimer = setTimeout(() => {
      setSplashFade(true);
    }, 2200);

    const removeTimer = setTimeout(() => {
      setShowSplash(false);
    }, 2900);

    return () => {
      clearInterval(msgInterval);
      clearInterval(progressInterval);
      clearTimeout(fadeTimer);
      clearTimeout(removeTimer);
    };
  }, []);

  // New Modular Workspace States
  const [digitalTwin, setDigitalTwin] = useState({ sync_mode: "hardware", joints: {}, model_geometry: {} });
  const [balancer, setBalancer] = useState({ is_active: false, data: {}, kp: 0.8, kd: 0.3, ki: 0.05, provider: "vision" });
  const [recorder, setRecorder] = useState({ is_recording: false, recorded_frames: 0, is_replaying: false });
  const [manualSearch, setManualSearch] = useState("");
  const [expandedSection, setExpandedSection] = useState("overview");
  const [showBaudDropdownHeader, setShowBaudDropdownHeader] = useState(false);
  const [showBaudDropdownDashboard, setShowBaudDropdownDashboard] = useState(false);

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
        if (data.logs && !pauseLogsRef.current) setLogs(data.logs);

        // Fetch mirror sync state on status reload
        try {
          const mirrorRes = await fetch("/api/robot/mirror-sync");
          if (mirrorRes.ok) {
            const mirrorData = await mirrorRes.json();
            setMirrorSyncActive(mirrorData.mirror_sync_active);
          }
        } catch (err) { }
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
    } catch (e) { }
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
    } catch (e) { }
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
    } catch (e) { }
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
          if (data.logs && !pauseLogsRef.current) setLogs(data.logs);
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
        } catch (e) { }
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
    } catch (e) { }
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
    } catch (e) { }
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
    } catch (e) { }
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
    } catch (e) { }
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
    } catch (e) { }
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
    } catch (e) { }
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

      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setShowCommandPalette(prev => !prev);
        return;
      }
      if (e.key === "Escape") {
        setShowCommandPalette(false);
        setMobileMenuOpen(false);
        setShowConnectionDropdown(false);
        setShowProfileDropdown(false);
      }
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
    } catch (e) { }
  };

  const toggleEstop = async () => {
    try {
      await fetch("/api/estop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: !estopActive })
      });
    } catch (e) { }
  };



  const rebootMotor = async (mid) => {
    try {
      await fetch("/api/reboot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motor_id: parseInt(mid) })
      });
      setAlertBanner({ type: "success", message: `Reboot sequence triggered for motor ${mid}` });
    } catch (e) { }
  };

  const toggleTorqueGlobal = async (enable) => {
    try {
      await fetch("/api/torque", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motor_id: "global", enable })
      });
    } catch (e) { }
  };

  const toggleTorqueIndividual = async (mid, enable) => {
    try {
      await fetch("/api/torque", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motor_id: String(mid), enable })
      });
    } catch (e) { }
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
    } catch (e) { }
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
    } catch (e) { }
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
    } catch (e) { }
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
        setAlertBanner({ type: "success", message: "Calibration offsets saved to humanoid_calibration.json successfully!" });
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
    } catch (e) { }
  };

  const toggleHandTracking = async () => {
    try {
      await fetch("/api/tracking", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enable: !trackingEnabled })
      });
    } catch (e) { }
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
    } catch (e) { }
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
    } catch (e) { }
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
    } catch (e) { }
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
    <>
      {showSplash && (
        <div className={`fixed inset-0 bg-[#0D0F14] z-[9999] flex flex-col items-center justify-center font-sans select-none overflow-hidden transition-all duration-700 ease-in-out ${splashFade ? "opacity-0 scale-105 pointer-events-none" : "opacity-100 scale-100"}`}>
          {/* Radial ambient glow */}
          <div className="absolute w-[500px] h-[500px] rounded-full bg-[#E4E4E7]/8 blur-[120px] pointer-events-none" />

          {/* Glowing emblem */}
          <div className="relative flex items-center justify-center w-28 h-28 mb-6">
            <div className="absolute inset-0 rounded-full border border-dashed border-[#E4E4E7]/25 animate-spin" style={{ animationDuration: "16s" }} />
            <div className="absolute inset-2 rounded-full border border-[#E4E4E7]/15 animate-spin" style={{ animationDuration: "12s", animationDirection: "reverse" }} />
            <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-[#E4E4E7] to-white flex items-center justify-center shadow-[0_0_55px_rgba(225,220,201,0.25)] border border-[#E4E4E7]/30">
              <Activity className="h-7 w-7 text-zinc-200 animate-pulse" />
            </div>
          </div>

          {/* Logo Title */}
          <h1 className="text-4xl font-black tracking-[0.25em] text-transparent bg-clip-text bg-gradient-to-r from-white via-[#E4E4E7] to-white select-none uppercase">OSRS</h1>
          <p className="text-[9px] uppercase font-black tracking-[0.5em] text-[#E4E4E7]/60 mt-2.5">Open Source Robotics System</p>

          {/* Progress Bar & Boot Logs */}
          <div className="flex flex-col items-center gap-2 mt-10">
            <div className="w-48 bg-white/[0.04] h-1 rounded-full overflow-hidden border border-white/[0.06] relative">
              <div className="bg-gradient-to-r from-[#E4E4E7] to-white h-full rounded-full transition-all duration-150" style={{ width: `${splashProgress}%` }} />
            </div>
            <div className="flex justify-between items-center w-48 text-[9px] font-bold text-[#E4E4E7]/60 uppercase tracking-wider font-mono">
              <span className="truncate max-w-[120px]">{splashMsg}</span>
              <span>{splashProgress}%</span>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#000000] bg-pitch-black text-zinc-200 select-none font-sans">

        {/* SLEEK MINIMALIST TOP BAR */}
        <header className="h-14 bg-black/85 backdrop-blur-xl border-b border-white/[0.08] text-xs font-medium text-zinc-300 flex items-center justify-between px-3 md:px-5 shrink-0 z-40 relative">

          {/* Left: Hamburger (Mobile) + OSRS Brand + Breadcrumbs + Platform Selector */}
          <div className="flex items-center gap-2.5 sm:gap-3.5 min-w-0">
            {/* Mobile Menu Hamburger Button */}
            <button
              onClick={() => setMobileMenuOpen(prev => !prev)}
              className="lg:hidden p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition active:scale-95"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5 text-zinc-200" /> : <Menu className="w-5 h-5" />}
            </button>

            {/* OSRS Brand Logo */}
            <div
              onClick={() => setActiveTab("dashboard")}
              className="flex items-center gap-2 cursor-pointer group shrink-0"
            >
              <Activity className="h-4 w-4 text-sky-400 group-hover:scale-110 transition-transform" />
              <span className="font-bold text-xs tracking-wider text-white">OSRS</span>
              <span className="text-[10px] font-mono text-zinc-400 bg-white/[0.05] border border-white/[0.08] px-1.5 py-0.5 rounded-md">v1.2</span>
            </div>

            <span className="text-zinc-700 hidden xl:inline select-none">/</span>

            {/* Active Screen Breadcrumb */}
            <span className="hidden xl:inline-flex items-center px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider text-zinc-300 bg-white/[0.04] border border-white/[0.06] select-none truncate">
              {getScreenMetadata(activeTab).title}
            </span>

            <span className="text-zinc-700 hidden lg:inline select-none">/</span>

            {/* Platform Selector Dropdown */}
            <div className="relative hidden lg:block" ref={profileDropdownRef}>
              <button
                onClick={() => setShowProfileDropdown(prev => !prev)}
                className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-zinc-300 hover:text-white transition-all border border-white/[0.08] shadow-sm active:scale-95"
              >
                <Bot className="h-3.5 w-3.5 text-sky-400 shrink-0" />
                <span className="font-semibold text-xs tracking-wide uppercase truncate max-w-[120px]">{handVersion}</span>
                <span className={`text-[8px] text-zinc-500 transition-transform duration-200 ${showProfileDropdown ? "rotate-180" : ""}`}>▼</span>
              </button>

              {showProfileDropdown && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowProfileDropdown(false)}
                  />

                  <div className="absolute left-0 mt-3 bg-[#0D0F14]/95 backdrop-blur-xl rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-white/[0.06] p-2.5 z-50 w-72 animate-in fade-in slide-in-from-top-2 duration-200 flex flex-col gap-1 text-white font-sans">
                    <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest px-3.5 py-2 block border-b border-white/[0.06]">Select Active Platform</span>
                    {[
                      { value: "Humanoid V1", desc: "16-Axis Humanoid Rig", nodes: "16 Nodes" },
                      { value: "Open Manipulator X", desc: "5-Axis Robotic Arm", nodes: "5 Nodes" },
                      { value: "V1", label: "LEAP Hand V1", desc: "16-Motor Biomimetic Hand", nodes: "16 Nodes" }
                    ].map((item) => {
                      const isSelected = handVersion === item.value;
                      const displayName = item.label || item.value;
                      return (
                        <button
                          key={item.value}
                          onClick={() => {
                            handleSwitchProfile(item.value);
                            setShowProfileDropdown(false);
                          }}
                          className={`w-full flex items-center justify-between text-left px-3.5 py-2.5 rounded-xl transition-all ${isSelected ? "bg-white/[0.12] text-white font-bold" : "text-[#E4E4E7]/80 hover:bg-white/[0.06] hover:text-white"}`}
                        >
                          <div className="flex flex-col gap-0.5">
                            <span className="text-xs">{displayName}</span>
                            <span className="text-[9px] text-slate-555 font-medium">{item.desc}</span>
                          </div>
                          <span className={`text-[9px] font-semibold px-2 py-0.5 rounded-full ${isSelected ? "bg-[#E4E4E7]/20 text-[#E4E4E7]" : "bg-white/[0.04] text-[#E4E4E7]/60"}`}>
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

          {/* Center: Command Palette Trigger Capsule */}
          <div className="flex items-center">
            <button
              onClick={() => setShowCommandPalette(true)}
              className="hidden lg:flex items-center gap-2.5 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/[0.14] border border-white/[0.07] rounded-full px-3.5 py-1.5 text-xs text-zinc-400 transition-all cursor-pointer w-48 xl:w-72 shadow-inner group active:scale-[0.99]"
            >
              <Search className="w-3.5 h-3.5 text-zinc-500 group-hover:text-zinc-300 transition-colors shrink-0" />
              <span className="truncate text-zinc-400 group-hover:text-zinc-200 text-[11px]">Search commands, tabs...</span>
              <span className="ml-auto text-[9px] font-mono text-zinc-500 bg-white/[0.04] px-1.5 py-0.5 rounded border border-white/[0.06]">⌘K</span>
            </button>

            {/* Mobile Search Icon Button */}
            <button
              onClick={() => setShowCommandPalette(true)}
              className="lg:hidden p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
              aria-label="Open Command Search"
            >
              <Search className="w-4 h-4" />
            </button>
          </div>

          {/* Right: Unified Action Island (Telemetry + Controls) */}
          <div className="flex items-center gap-1.5 sm:gap-2">
            {/* Live Connection Telemetry Pill */}
            <div className="relative" ref={connectionDropdownRef}>
              <button
                onClick={() => setShowConnectionDropdown(prev => !prev)}
                className={`inline-flex items-center gap-2 px-2.5 sm:px-3.5 py-1.5 rounded-full text-[10px] font-bold tracking-wider transition-all duration-200 border backdrop-blur-sm active:scale-95 ${connected
                  ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20 shadow-[0_0_12px_rgba(16,185,129,0.15)]"
                  : "bg-rose-500/10 text-rose-300 border-rose-500/30 hover:bg-rose-500/20 shadow-[0_0_12px_rgba(244,63,94,0.15)]"
                  }`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-emerald-400 animate-ping" : "bg-rose-400"}`} />
                <span className="hidden sm:inline">{connected ? (mockMode ? "MOCK TELEMETRY" : "LIVE BUS") : "OFFLINE"}</span>
                <span className="sm:hidden">{connected ? "LIVE" : "OFF"}</span>
                <span className="text-[7px] text-zinc-400">▼</span>
              </button>

              {showConnectionDropdown && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowConnectionDropdown(false)}
                  />

                  <div className="absolute right-0 sm:left-1/2 sm:transform sm:-translate-x-1/2 mt-3 bg-[#0D0F14]/95 backdrop-blur-xl rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-white/[0.06] p-5 z-50 w-72 text-white flex flex-col gap-4 font-sans animate-in fade-in slide-in-from-top-2 duration-200">
                    <span className="text-[10px] font-bold text-[#E4E4E7]/80 uppercase tracking-widest block border-b border-white/[0.06] pb-2 mb-1">Connection Manager</span>

                    {connected ? (
                      <div className="space-y-4">
                        <div className="text-[10px] font-semibold space-y-2">
                          <div className="flex justify-between items-center text-zinc-500">
                            <span>Status:</span>
                            <span className="text-emerald-400 font-bold bg-emerald-500/20 px-2.5 py-0.5 rounded">CONNECTED</span>
                          </div>
                          <div className="flex justify-between items-center text-zinc-500">
                            <span>Port:</span>
                            <span className="text-white font-mono bg-white/[0.04] px-2.5 py-0.5 rounded">{port}</span>
                          </div>
                          <div className="flex justify-between items-center text-zinc-500">
                            <span>Baudrate:</span>
                            <span className="text-white font-mono bg-white/[0.04] px-2.5 py-0.5 rounded">{baudrate / 1000000}M bps</span>
                          </div>
                          <div className="flex justify-between items-center text-zinc-500">
                            <span>Mock Mode:</span>
                            <span className="text-white bg-white/[0.04] px-2.5 py-0.5 rounded">{mockMode ? "ACTIVE" : "OFF"}</span>
                          </div>
                        </div>

                        <button
                          onClick={() => {
                            triggerDisconnect();
                            setShowConnectionDropdown(false);
                          }}
                          className="w-full bg-red-600 hover:bg-red-750 active:scale-[0.98] text-white font-bold text-xs py-2.5 rounded-xl transition-all uppercase tracking-wider shadow-md hover:shadow-lg hover:shadow-red-500/10"
                        >
                          Disconnect Bus
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-4 font-sans">
                        <div className="space-y-3 text-[10px]">
                          <div className="space-y-1.5">
                            <label className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider block">Port</label>
                            <input
                              type="text"
                              value={connPort}
                              onChange={(e) => setConnPort(e.target.value)}
                              placeholder="COM14"
                              className="w-full bg-[#000000]/40 border border-white/[0.06] hover:border-white/[0.06] focus:border-[#E4E4E7] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-[#E4E4E7] transition-all"
                            />
                          </div>

                          <div className="space-y-1.5 relative">
                            <label className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider block">Baudrate</label>
                            <button
                              type="button"
                              onClick={() => setShowBaudDropdownHeader(!showBaudDropdownHeader)}
                              className="bg-[#000000]/40 border border-white/[0.06] hover:border-white/[0.06] focus:border-[#E4E4E7] rounded-lg px-3 py-2 text-xs text-white flex items-center justify-between cursor-pointer w-full transition-all h-[32px]"
                            >
                              <span>{BAUDRATE_OPTIONS.find(o => o.value === connBaud)?.label || "Select speed"}</span>
                              <svg className={`w-3 h-3 text-zinc-500 transition-transform duration-200 ${showBaudDropdownHeader ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 9l-7 7-7-7" />
                              </svg>
                            </button>

                            {showBaudDropdownHeader && (
                              <>
                                <div
                                  className="fixed inset-0 z-40"
                                  onClick={() => setShowBaudDropdownHeader(false)}
                                />
                                <div className="absolute left-0 right-0 mt-1 bg-[#0D0F14] rounded-lg shadow-[0_10px_30px_rgba(0,0,0,0.5)] border border-white/[0.06] p-1 z-50 flex flex-col gap-0.5 text-white font-sans animate-in fade-in slide-in-from-top-2 duration-150">
                                  {BAUDRATE_OPTIONS.map((opt) => (
                                    <button
                                      key={opt.value}
                                      type="button"
                                      onClick={() => {
                                        setConnBaud(opt.value);
                                        setShowBaudDropdownHeader(false);
                                      }}
                                      className={`w-full text-left px-3 py-2 rounded-md text-xs font-bold transition-all duration-150 ${connBaud === opt.value
                                        ? "bg-[#E4E4E7] text-zinc-200"
                                        : "hover:bg-white/[0.04] text-[#E4E4E7]/90 hover:text-white"
                                        }`}
                                    >
                                      {opt.label}
                                    </button>
                                  ))}
                                </div>
                              </>
                            )}
                          </div>

                          <label className="flex items-center gap-2.5 font-semibold text-slate-300 hover:text-white cursor-pointer pt-2 transition-colors">
                            <input
                              type="checkbox"
                              checked={connMock}
                              onChange={(e) => setConnMock(e.target.checked)}
                              className="rounded text-[#E4E4E7] bg-[#000000]/40 border-white/[0.06] w-4 h-4 cursor-pointer focus:ring-0 focus:ring-offset-0 focus:outline-none transition-colors"
                            />
                            <span className="text-[10px]">Enable Mock Mode</span>
                          </label>
                        </div>

                        <button
                          onClick={() => {
                            triggerConnect();
                            setShowConnectionDropdown(false);
                          }}
                          className="w-full bg-[#000] text-zinc-200 hover:bg-[#222]/90 active:scale-[0.98] font-bold text-xs py-2.5 rounded-xl transition-all uppercase tracking-wider shadow-md hover:shadow-lg hover:shadow-[#E4E4E7]/10"
                        >
                          Connect Bus
                        </button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>

            {/* Right Island: Torque + Guide + ESTOP */}
            <div className="flex items-center gap-1 bg-white/[0.02] p-1 rounded-full border border-white/[0.06]">
              {/* Torque Global Toggle Button */}
              <button
                onClick={() => toggleTorqueGlobal(!isAnyTorqueActive)}
                disabled={!connected}
                className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all duration-200 active:scale-95 ${!connected
                  ? "bg-white/[0.03] text-zinc-400 border border-white/[0.06] opacity-75 cursor-not-allowed"
                  : isAnyTorqueActive
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow-[0_0_12px_rgba(16,185,129,0.2)] hover:bg-emerald-500/30"
                    : "bg-white/[0.05] text-zinc-300 hover:text-white hover:bg-white/[0.1] border border-white/[0.08]"
                  }`}
                title={!connected ? "Connect serial bus to engage torque" : (isAnyTorqueActive ? "Click to release torque globally" : "Click to enable torque globally")}
              >
                <Cpu className="h-3.5 w-3.5 shrink-0" />
                <span className="hidden sm:inline">Torque {isAnyTorqueActive ? "ON" : "OFF"}</span>
              </button>

              {/* Shortcuts Guide Button */}
              <button
                onClick={() => setShowShortcutHelp(true)}
                className="flex items-center gap-1.5 px-2 sm:px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider text-zinc-300 hover:text-white hover:bg-white/[0.06] border border-transparent hover:border-white/[0.08] transition-all duration-200 active:scale-95"
                title="How to Use & Keyboard Shortcuts (Alt+H)"
              >
                <HelpCircle className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                <span className="hidden md:inline">Guide</span>
              </button>

              {/* E-Stop Indicator/Toggle */}
              <button
                onClick={toggleEstop}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider transition-all duration-200 active:scale-95 ${estopActive
                  ? "bg-red-500 text-white animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.5)] border border-red-400"
                  : "bg-rose-500/15 text-rose-300 border border-rose-500/35 hover:bg-rose-500/25 hover:text-rose-200"
                  }`}
                title="Alt+S to toggle emergency stop"
              >
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                <span>ESTOP</span>
              </button>
            </div>
          </div>

        </header>

        {/* MOBILE OFF-CANVAS SIDEBAR DRAWER */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div
              className="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity"
              onClick={() => setMobileMenuOpen(false)}
            />

            <aside className="fixed top-0 bottom-0 left-0 w-72 bg-[#07080B] border-r border-white/[0.1] z-50 flex flex-col justify-between p-4 shadow-2xl animate-slide-right select-none">
              <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
                <div className="flex items-center justify-between px-2 py-3 mb-3 border-b border-white/[0.06] shrink-0">
                  <div className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-sky-400 animate-pulse" />
                    <span className="text-lg font-bold tracking-tight text-white">OSRS</span>
                    <span className="text-[10px] font-mono text-zinc-400 bg-white/10 px-1.5 py-0.5 rounded">v1.2</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setMobileMenuOpen(false)}
                    className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.08] cursor-pointer"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Mobile Platform Selector */}
                <div className="mb-3 shrink-0">
                  <label className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest block mb-1.5 px-2">Active Platform</label>
                  <select
                    value={handVersion}
                    onChange={(e) => setHandVersion(e.target.value)}
                    className="w-full bg-white/[0.04] border border-white/[0.08] text-white rounded-xl px-3 py-2 text-xs font-semibold focus:outline-none"
                  >
                    <option value="Humanoid V1">Humanoid V1 (16-Axis)</option>
                    <option value="Open Manipulator X">Open Manipulator X (5-Axis)</option>
                    <option value="V1">LEAP Hand V1 (16-Motor)</option>
                  </select>
                </div>

                {/* Independently Scrollable Navigation Links */}
                <nav className="flex-1 min-h-0 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                  {NAV_ITEMS.map((item) => {
                    const Icon = item.icon;
                    const active = activeTab === item.id;
                    let badge = null;
                    if (item.id === "dashboard" && connected) badge = activeMotorIds.length;
                    else if (item.id === "vision" && cameraActive) badge = "ON";
                    else if (item.id === "calibration" && calibrationState.running) badge = "RUN";

                    return (
                      <button
                        key={item.id}
                        type="button"
                        id={`mobile-nav-${item.id}`}
                        onClick={() => {
                          setActiveTab(item.id);
                          setSelectedJoint(null);
                          setMobileMenuOpen(false);
                        }}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${active
                          ? "bg-white/[0.12] text-white border border-white/[0.12] font-semibold"
                          : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]"
                          }`}
                      >
                        <div className="flex items-center gap-3">
                          <Icon className={`h-4 w-4 shrink-0 ${active ? "text-sky-400" : "text-zinc-500"}`} />
                          <span className="truncate">{item.label}</span>
                        </div>
                        {badge !== null && (
                          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${active ? "bg-white/[0.15] text-white" : "bg-white/[0.05] text-zinc-500"
                            }`}>
                            {badge}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </nav>
              </div>

              {/* Mobile Bottom Autopilot Guard Card */}
              <div className="pt-3 mt-2 border-t border-white/[0.06] shrink-0">
                <div className="mini-card p-3.5 flex flex-col gap-2">
                  <div>
                    <span className="text-[9px] font-bold uppercase tracking-wider text-white/50 block">Autopilot Protection</span>
                    <h4 className="text-xs font-bold text-white mt-0.5">OSRS Guard Active</h4>
                    <p className="text-[10px] text-zinc-400">Velocity Cap: {connSpeedLimit} RPM</p>
                  </div>
                  <button
                    type="button"
                    onClick={toggleEstop}
                    className={`w-full font-bold py-2 px-3 rounded-lg text-xs uppercase tracking-wider transition cursor-pointer ${estopActive ? "bg-rose-600 text-white" : "bg-white/[0.08] text-white"
                      }`}
                  >
                    {estopActive ? "DISABLE ESTOP" : "ENGAGE ESTOP"}
                  </button>
                </div>
              </div>
            </aside>
          </div>
        )}

        {/* INTERACTIVE COMMAND PALETTE (⌘K / Ctrl+K) */}
        {showCommandPalette && (
          <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4">
            <div
              className="fixed inset-0 bg-black/80 backdrop-blur-md animate-fade-in"
              onClick={() => setShowCommandPalette(false)}
            />

            <div className="relative w-full max-w-xl bg-[#090A0E] border border-white/[0.12] rounded-2xl shadow-2xl overflow-hidden z-50 animate-scale-up">
              <div className="flex items-center gap-3 px-4 py-3.5 border-b border-white/[0.08] bg-white/[0.02]">
                <Search className="w-4 h-4 text-zinc-400 shrink-0" />
                <input
                  type="text"
                  autoFocus
                  value={commandQuery}
                  onChange={(e) => setCommandQuery(e.target.value)}
                  placeholder="Search commands, views, or joints..."
                  className="w-full bg-transparent text-sm text-white placeholder-zinc-500 focus:outline-none"
                />
                {commandQuery && (
                  <button
                    onClick={() => setCommandQuery("")}
                    className="text-xs text-zinc-500 hover:text-white px-1.5 py-0.5 rounded"
                  >
                    Clear
                  </button>
                )}
                <span className="text-[10px] font-mono text-zinc-500 bg-white/[0.06] border border-white/[0.08] px-1.5 py-0.5 rounded">
                  ESC
                </span>
              </div>

              <div className="max-h-80 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                <div className="px-3 py-1 text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                  Quick Actions
                </div>
                {[
                  {
                    label: "Emergency Stop (ESTOP)",
                    desc: estopActive ? "Currently ENGAGED - Click to release" : "Instantly release all motor torque",
                    icon: AlertTriangle,
                    action: () => { toggleEstop(); setShowCommandPalette(false); }
                  },
                  {
                    label: "Toggle Global Motor Torque",
                    desc: isAnyTorqueActive ? "Release torque globally" : "Enable torque globally",
                    icon: Cpu,
                    action: () => { toggleTorqueGlobal(!isAnyTorqueActive); setShowCommandPalette(false); }
                  },
                  {
                    label: "Open Navigation & Shortcuts Guide",
                    desc: "View complete keyboard navigation cheatsheet",
                    icon: HelpCircle,
                    action: () => { setShowShortcutHelp(true); setShowCommandPalette(false); }
                  }
                ]
                  .filter(act => act.label.toLowerCase().includes(commandQuery.toLowerCase()))
                  .map((act, i) => {
                    const Icon = act.icon;
                    return (
                      <button
                        key={i}
                        onClick={act.action}
                        className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-white/[0.06] transition text-left group"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-7 h-7 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-zinc-400 group-hover:text-white">
                            <Icon className="w-3.5 h-3.5" />
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-white block">{act.label}</span>
                            <span className="text-[10px] text-zinc-500 block">{act.desc}</span>
                          </div>
                        </div>
                        <span className="text-[9px] text-zinc-500 font-mono">Action</span>
                      </button>
                    );
                  })}

                <div className="px-3 py-1 pt-2 text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                  Navigation Screens
                </div>
                {NAV_ITEMS
                  .filter(item =>
                    item.label.toLowerCase().includes(commandQuery.toLowerCase()) ||
                    item.id.toLowerCase().includes(commandQuery.toLowerCase())
                  )
                  .map((item) => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.id}
                        onClick={() => {
                          setActiveTab(item.id);
                          setShowCommandPalette(false);
                        }}
                        className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-white/[0.06] transition text-left group"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-7 h-7 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-zinc-400 group-hover:text-sky-400">
                            <Icon className="w-3.5 h-3.5" />
                          </div>
                          <span className="text-xs font-semibold text-white">{item.label}</span>
                        </div>
                        <span className="text-[9px] text-zinc-500 font-mono">Go to Tab</span>
                      </button>
                    );
                  })}
              </div>

              <div className="px-4 py-2 border-t border-white/[0.06] bg-white/[0.01] flex items-center justify-between text-[10px] text-zinc-500">
                <span>Navigate with mouse or shortcuts</span>
                <span>Press <kbd className="font-mono text-zinc-400 bg-white/[0.06] px-1 py-0.5 rounded">ESC</kbd> to close</span>
              </div>
            </div>
          </div>
        )}

        {/* SEAMLESS WORKSPACE BODY */}
        <div className="flex-1 flex overflow-hidden min-h-0 relative">

          {/* MINIMALIST SIDEBAR NAVIGATION */}
          <aside className="hidden lg:flex w-60 bg-[#000000] border-r border-white/[0.06] flex-col h-full max-h-full overflow-hidden p-3 shrink-0 relative z-30 select-none">
            {/* Top Brand Logo */}
            <div className="shrink-0 px-3 py-3 mb-2 flex items-center gap-3">
              <Activity className="h-6 w-6 text-[#E4E4E7] animate-pulse shrink-0" />
              <span className="text-xl font-extrabold tracking-tight text-white flex items-center gap-1.5">
                OSRS <span className="text-[#E4E4E7] font-medium text-xs bg-white/10 px-2 py-0.5 rounded-full">v1.2</span>
              </span>
            </div>

            {/* Independently Scrollable Navigation List */}
            <nav className="flex-1 min-h-0 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                const active = activeTab === item.id;

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
                    type="button"
                    id={`sidebar-nav-${item.id}`}
                    onClick={() => {
                      setActiveTab(item.id);
                      setSelectedJoint(null);
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-150 cursor-pointer ${active
                      ? "bg-gradient-to-r from-white/[0.14] to-white/[0.05] text-white border border-white/[0.12] shadow-[inset_0_1px_0_rgba(255,255,255,0.12)] font-semibold"
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]"
                      }`}
                  >
                    <div className="flex items-center gap-3.5">
                      <Icon className={`h-4 w-4 shrink-0 ${active ? "text-sky-400" : "text-zinc-500"}`} />
                      <span className="truncate">{item.label}</span>
                    </div>
                    {badge !== null && (
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${active ? "bg-white/[0.12] text-zinc-200" : "bg-white/[0.04] text-zinc-500"
                        }`}>
                        {badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>

            {/* Pinned Bottom Autopilot Protection Card */}
            <div className="pt-3 mt-2 shrink-0 border-t border-white/[0.06]">
              <div className="mini-card p-3.5 flex flex-col gap-2">
                <div>
                  <span className="text-[9px] font-bold uppercase tracking-wider text-white/45 block">Autopilot Protection</span>
                  <h4 className="text-xs font-bold text-white mt-0.5">OSRS Guard Active</h4>
                  <p className="text-[10px] text-white/60 mt-0.5">Velocity Cap: {connSpeedLimit} RPM</p>
                </div>
                <button
                  type="button"
                  onClick={toggleEstop}
                  className={`w-full font-bold py-2 px-3 rounded-xl text-xs tracking-wider uppercase transition-all cursor-pointer active:scale-[0.98] ${estopActive
                    ? "bg-rose-600 hover:bg-rose-500 animate-pulse text-white shadow-lg shadow-rose-900/40"
                    : "bg-white/[0.08] hover:bg-white/[0.14] text-white border border-white/[0.08]"
                    }`}
                >
                  {estopActive ? "DISABLE ESTOP" : "ENGAGE ESTOP"}
                </button>
              </div>
            </div>
          </aside>

          {/* MAIN WORKSPACE CANVAS */}
          <main className="flex-1 bg-[#000000] bg-pitch-black overflow-y-auto p-6 md:p-8 custom-scrollbar space-y-6">

            {/* ALERT NOTIFICATIONS */}
            {alertBanner && (
              <div className={`p-4 mb-6 rounded-2xl flex items-center justify-between shadow-sm border ${alertBanner.type === "error" ? "bg-red-50 border-red-200 text-red-600" :
                alertBanner.type === "warning" ? "bg-amber-50 border-amber-200 text-amber-600" :
                  "bg-green-50 border-green-200 text-green-700"
                }`}>
                <span className="text-sm font-bold flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" /> {alertBanner.message}
                </span>
                <button onClick={() => setAlertBanner(null)} className="opacity-75 hover:opacity-100 font-extrabold">✕</button>
              </div>
            )}
            {/* SCREEN ROUTING (MODULAR SCREENS VIA SITEMAP ARCHITECTURE) */}
            {(() => {
              const screenProps = {
                // UI & Global State
                activeTab,
                setActiveTab,
                handVersion,
                setHandVersion,
                alertBanner,
                setAlertBanner,
                systemStats,
                mirrorSyncActive,
                handleToggleMirrorSync,

                // Hardware Connection
                connected,
                connPort,
                setConnPort,
                connBaud,
                setConnBaud,
                connMock,
                setConnMock,
                connCurrentLimit,
                setConnCurrentLimit,
                connSpeedLimit,
                setConnSpeedLimit,
                triggerConnect,
                triggerDisconnect,
                toggleEstop,
                estopActive,
                BAUDRATE_OPTIONS,
                showBaudDropdownDashboard,
                setShowBaudDropdownDashboard,

                // Telemetry & Hardware Logs
                telemetry,
                limits,
                activeMotorIds,
                logs,
                clearOffset,
                setClearOffset,
                pauseLogs,
                setPauseLogs,
                handleCopyLogs,
                handleClearLogs,
                rebootMotor,
                toggleTorqueGlobal,
                toggleTorqueIndividual,
                isAnyTorqueActive,

                // Arm Control & Visual Dials
                positions: localDrags,
                localDrags,
                setLocalDrags,
                inputValues,
                setInputValues,
                handleInputChange,
                handleSliderDrag,
                handleSliderRelease,
                handleInputBlur,
                handlePositionChange: handleSliderDrag,
                sendZeroPose: resetAllToDefault,
                resetAllToDefault,
                selectedJoint,
                setSelectedJoint,
                handleJointClick: (id) => setSelectedJoint(id),
                handleSendCommand,
                rotateJointByDeg,
                expandedSections,
                setExpandedSections,

                // Emote Maker Studio
                savedEmotes,
                fetchCustomEmotes,
                emoteFrames,
                setEmoteFrames,
                activeFrameIdx: 0,
                setActiveFrameIdx: () => {},
                newEmoteName: saveName,
                setNewEmoteName: setSaveName,
                saveName,
                setSaveName,
                emoteInputValues,
                setEmoteInputValues,
                emoteSpeed,
                setEmoteSpeed,
                emoteLoop,
                setEmoteLoop,
                showSaveModal,
                setShowSaveModal,
                playingPreset,
                playPresetEmote: (name) => playSavedCustomEmote(name, PRESET_EMOTE_FRAMES[name]),
                loadPresetEmoteIntoMaker,
                loadSavedEmoteIntoMaker,
                playCustomEmote,
                playSavedCustomEmote,
                handleDeleteCustomEmote,
                handleSaveCustomEmote: handleSaveEmote,
                handleSaveEmote,
                addEmoteFrame,
                removeEmoteFrame,
                previewFrame: () => {},
                updateFrameDelay,
                updateFrameHold,

                // Calibration Wizard
                calibrationState,
                calibBaseInputs,
                setCalibBaseInputs,
                calibration,
                setCalibration,
                calibInputValues,
                setCalibInputValues,
                controlCalibration,
                handleTorqueArm,
                handleCaptureCalibration,
                handleGoToBase,
                handleSaveCalibration,
                handleSetZeroCalibration,
                handleSaveBaseFrame,

                // CAD Mapper Editor
                mapperId,
                setMapperId,
                mapperNewId,
                setMapperNewId,
                mapperName,
                setMapperName,
                mapperDefault,
                setMapperDefault,
                mapperMin,
                setMapperMin,
                mapperMax,
                setMapperMax,
                mapperInverted: false,
                setMapperInverted: () => {},
                editingMapper,
                startEditMapper,
                resetMapperForm,
                handleSaveMapper,
                handleDeleteMapper,

                // Perception Vision
                cameraIdx,
                setCameraIdx,
                cameraActive,
                toggleVisionSystem,
                trackingEnabled,
                toggleTracking: () => setTrackingEnabled(prev => !prev),
                setTrackingEnabled,
                videoFrame,

                // Ball Balancer Research
                balancer,
                balancerData: balancer.data || {},
                handleTune: handleTuneBalancer,
                handleTuneBalancer,
                handleResearchToggle: handleToggleBalancer,
                handleToggleBalancer,
                handleGoToStart,
                handleInitializeArms,
                handleBalancerCommand: handleSendCommand,
                backendState: {},
                digitalTwin,

                // Diagnostics Bus
                runPingTest: () => {},
                pingStatus: null,
                pingRunning: false,

                // Navigation
                onNavigate: (id) => setActiveTab(id)
              };

              return (
                <>
                  {activeTab === "dashboard" && <DashboardScreen {...screenProps} />}
                  {activeTab === "simulations" && <SimulationsScreen {...screenProps} onNavigateToPaper={() => setActiveTab("paper")} />}
                  {activeTab === "paper" && <ResearchPaperScreen {...screenProps} onNavigateToSimulations={() => setActiveTab("simulations")} />}
                  {activeTab === "sitemap" && <SitemapScreen {...screenProps} onNavigate={(id) => setActiveTab(id)} />}
                  {activeTab === "control" && <ArmControlScreen {...screenProps} />}
                  {activeTab === "emotemaker" && <EmoteMakerScreen {...screenProps} />}
                  {activeTab === "dataflow" && <DataflowScreen {...screenProps} />}
                  {activeTab === "research" && <ResearchBalancerScreen {...screenProps} />}
                  {activeTab === "recording" && <RecordingScreen {...screenProps} />}
                  {activeTab === "calibration" && <CalibrationScreen {...screenProps} />}
                  {activeTab === "mapper" && <CadMapperScreen {...screenProps} />}
                  {activeTab === "vision" && <VisionScreen {...screenProps} />}
                  {activeTab === "diagnostics" && <DiagnosticsScreen {...screenProps} />}
                  {activeTab === "about" && <AboutScreen {...screenProps} />}
                  {activeTab === "manual" && <ProductManualScreen {...screenProps} />}
                </>
              );
            })()}

            {/* KEYBOARD SHORTCUTS & HOW TO USE MANUAL MODAL */}
            {showShortcutHelp && (
              <div className="fixed inset-0 bg-[#090A0E]/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div className="obsidian-card bg-[#0A0A0E] text-white rounded-[32px] p-8 max-w-2xl w-full shadow-2xl border border-white/[0.1] animate-in fade-in zoom-in-95 duration-200 max-h-[85vh] overflow-y-auto">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-black text-white flex items-center gap-2">
                      <BookOpen className="h-5 w-5 text-[#B5ACF3]" /> OSRS System Navigation & Keyboard Shortcuts
                    </h3>
                    <button
                      onClick={() => setShowShortcutHelp(false)}
                      className="p-1 rounded-full hover:bg-slate-150 transition text-zinc-500 hover:text-slate-800"
                    >
                      ✕
                    </button>
                  </div>

                  <div className="space-y-6 text-xs text-white">
                    {/* Keyboard Shortcuts Section */}
                    <div className="obsidian-inset rounded-2xl p-5 border border-white/[0.06]">
                      <h4 className="font-extrabold text-white mb-3 flex items-center gap-2">
                        <Keyboard className="w-4 h-4 text-[#B5ACF3]" /> Keyboard Shortcuts (Visual Studio Navigation style)
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-semibold text-zinc-300">
                        <div className="flex justify-between items-center obsidian-inset p-2.5 rounded-xl border border-white/[0.06]">
                          <span>Alt + 1</span>
                          <span className="bg-white/[0.08] text-white px-2.5 py-1 rounded-lg font-bold text-[11px] border border-white/[0.06]">Go to Dashboard</span>
                        </div>
                        <div className="flex justify-between items-center obsidian-inset p-2.5 rounded-xl border border-white/[0.06]">
                          <span>Alt + 2</span>
                          <span className="bg-white/[0.08] text-white px-2.5 py-1 rounded-lg font-bold text-[11px] border border-white/[0.06]">Go to Arm Control</span>
                        </div>
                        <div className="flex justify-between items-center obsidian-inset p-2.5 rounded-xl border border-white/[0.06]">
                          <span>Alt + 3</span>
                          <span className="bg-white/[0.08] text-white px-2.5 py-1 rounded-lg font-bold text-[11px] border border-white/[0.06]">Go to Emote Maker</span>
                        </div>
                        <div className="flex justify-between items-center obsidian-inset p-2.5 rounded-xl border border-white/[0.06]">
                          <span>Alt + 4</span>
                          <span className="bg-white/[0.08] text-white px-2.5 py-1 rounded-lg font-bold text-[11px] border border-white/[0.06]">Go to Calibration</span>
                        </div>
                        <div className="flex justify-between items-center obsidian-inset p-2.5 rounded-xl border border-white/[0.06]">
                          <span>Alt + 5</span>
                          <span className="bg-white/[0.08] text-white px-2.5 py-1 rounded-lg font-bold text-[11px] border border-white/[0.06]">Go to CAD Mapper</span>
                        </div>
                        <div className="flex justify-between items-center obsidian-inset p-2.5 rounded-xl border border-white/[0.06]">
                          <span>Alt + 6</span>
                          <span className="bg-white/[0.08] text-white px-2.5 py-1 rounded-lg font-bold text-[11px] border border-white/[0.06]">Go to Diagnostics</span>
                        </div>
                        <div className="flex justify-between items-center obsidian-inset p-2.5 rounded-xl border border-white/[0.06]">
                          <span>Alt + 7</span>
                          <span className="bg-white/[0.08] text-white px-2.5 py-1 rounded-lg font-bold text-[11px] border border-white/[0.06]">Go to Vision Pipeline</span>
                        </div>
                        <div className="flex justify-between items-center obsidian-inset p-2.5 rounded-xl border border-white/[0.06]">
                          <span>Alt + H</span>
                          <span className="bg-white/[0.08] text-white px-2.5 py-1 rounded-lg font-bold text-[11px] border border-white/[0.06]">Toggle Shortcuts/Help</span>
                        </div>
                        <div className="flex justify-between items-center obsidian-inset p-2.5 rounded-xl border border-white/[0.06] col-span-1 md:col-span-2">
                          <span className="text-red-500 font-bold">Alt + S</span>
                          <span className="bg-red-500/20 text-red-400 px-2.5 py-1 rounded-lg font-bold text-[11px] border border-red-500/30">Engage/Disable Emergency E-Stop</span>
                        </div>
                        <div className="flex justify-between items-center obsidian-inset p-2.5 rounded-xl border border-white/[0.06] col-span-1 md:col-span-2">
                          <span>Alt + R</span>
                          <span className="bg-white/[0.08] text-zinc-300 px-2.5 py-1 rounded-lg font-bold text-[11px] border border-white/[0.06]">Reset Joints to Rest Position (0)</span>
                        </div>
                      </div>
                    </div>

                    {/* Manual Section */}
                    <div className="space-y-4">
                      <h4 className="font-extrabold text-sm border-b border-slate-155 pb-2 text-white">How to Use the Robotic Platform</h4>

                      <div className="space-y-2">
                        <h5 className="font-black text-white">1. System Calibration</h5>
                        <p className="text-slate-600 font-semibold leading-relaxed">
                          To calibrate joint centers, click <span className="font-bold">Calibration Wizard</span>. Physically position the robot arms at their straight baseline positions. Click <span className="font-bold">"Set Current Pose as Zero (Initial)"</span>. This updates joint limits and maps all manual dials so that <span className="font-bold">0</span> is the perfect rest state.
                        </p>
                      </div>

                      <div className="space-y-2">
                        <h5 className="font-black text-white">2. Custom Emotes & Existing Presets Editor</h5>
                        <p className="text-slate-600 font-semibold leading-relaxed">
                          Use the <span className="font-bold">Emote Maker & Sequence Control</span> tab to load existing preset motions (like Namaste, Victory, HI Left) directly into the editor canvas by clicking the <span className="font-bold">Edit icon (sliders)</span> next to any preset. You can add or delete frames, slide joint parameters, and drag playback speed dials (from 0.25x up to 2x speed) or loop counts before saving or testing!
                        </p>
                      </div>

                      <div className="space-y-2">
                        <h5 className="font-black text-white">3. Joint Wireframe Skeleton Interaction</h5>
                        <p className="text-slate-600 font-semibold leading-relaxed">
                          On the <span className="font-bold">Visual Arm Control</span> view, click any joint circle on the interactive skeleton diagram. The right-hand sliders panel will automatically scroll to highlight the selected actuator. Type exact position values inside the numerical fields or use the sliders for live preview.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end pt-6 border-t border-white/[0.06] mt-6">
                    <button
                      onClick={() => setShowShortcutHelp(false)}
                      className="bg-[#090A0E] hover:bg-black text-white px-6 py-3 rounded-full font-bold transition shadow-md"
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
    </>
  );
}
