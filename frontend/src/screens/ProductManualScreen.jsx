import React, { useState, useEffect } from "react";
import { AlertTriangle, HelpCircle, Search, Server } from "lucide-react";

/**
 * Product Manual Screen - Comprehensive engineering manual, quickstart guide and troubleshooting
 */
export default function ProductManualScreen(props) {
  // Destructure shared state and actions with safe defaults
  const {
    // Hardware & Connection
    connected = false,
    connPort = "COM9",
    setConnPort = () => {},
    connBaud = 1000000,
    setConnBaud = () => {},
    connMock = false,
    setConnMock = () => {},
    triggerConnect = () => {},
    triggerDisconnect = () => {},
    toggleEstop = () => {},
    estopActive = false,
    handVersion = "Humanoid V1",
    setHandVersion = () => {},
    BAUDRATE_OPTIONS = [
      { value: 4000000, label: "4M bps" },
      { value: 1000000, label: "1M bps" },
      { value: 115200, label: "115200 bps" },
      { value: 57600, label: "57600 bps" }
    ],
    showBaudDropdownDashboard = false,
    setShowBaudDropdownDashboard = () => {},
    
    // UI Routing & Banners
    activeTab = "",
    setActiveTab = () => {},
    alertBanner = null,
    setAlertBanner = () => {},
    
    // Telemetry & Logs
    telemetry = {},
    limits = {},
    logs = [],
    clearOffset = 0,
    setClearOffset = () => {},
    pauseLogs = false,
    setPauseLogs = () => {},
    handleCopyLogs = () => {},
    handleClearLogs = () => {},
    rebootMotor = () => {},
    toggleTorqueGlobal = () => {},
    toggleTorqueIndividual = () => {},
    isAnyTorqueActive = false,
    
    // Positions & Joints
    positions = {},
    handlePositionChange = () => {},
    sendZeroPose = () => {},
    selectedJoint = null,
    setSelectedJoint = () => {},
    handleJointClick = () => {},
    handleSendCommand = () => {},
    rotateJointByDeg = () => {},
    expandedSections = { leftArm: true, rightArm: true, head: true },
    setExpandedSections = () => {},
    
    // Emotes
    savedEmotes = [],
    fetchCustomEmotes = () => {},
    emoteFrames = [],
    setEmoteFrames = () => {},
    activeFrameIdx = 0,
    setActiveFrameIdx = () => {},
    newEmoteName = "",
    setNewEmoteName = () => {},
    emoteSpeed = 1,
    setEmoteSpeed = () => {},
    emoteLoop = false,
    setEmoteLoop = () => {},
    showSaveModal = false,
    setShowSaveModal = () => {},
    playingPreset = null,
    playPresetEmote = () => {},
    loadPresetEmoteIntoMaker = () => {},
    loadSavedEmoteIntoMaker = () => {},
    playCustomEmote = () => {},
    playSavedCustomEmote = () => {},
    handleDeleteCustomEmote = () => {},
    handleSaveCustomEmote = () => {},
    addEmoteFrame = () => {},
    removeEmoteFrame = () => {},
    previewFrame = () => {},
    updateFrameDelay = () => {},
    updateFrameHold = () => {},
    PRESET_EMOTE_FRAMES = {},
    
    // Calibration Wizard State
    calibrationStep = 1,
    setCalibrationStep = () => {},
    calibJoint = "L1P",
    setCalibJoint = () => {},
    calibZero = 2048,
    setCalibZero = () => {},
    calibMin = 1000,
    setCalibMin = () => {},
    calibMax = 3000,
    setCalibMax = () => {},
    calibDirection = 1,
    setCalibDirection = () => {},
    calibSpeed = 50,
    setCalibSpeed = () => {},
    isCalibrating = false,
    setIsCalibrating = () => {},
    calibrationProgress = 0,
    setCalibrationProgress = () => {},
    handleSaveCalibration = () => {},
    handleResetCalibration = () => {},
    handleRunAutoCalibration = () => {},
    
    // CAD Mapper State
    cadMappings = {},
    setCadMappings = () => {},
    cadSearchQuery = "",
    setCadSearchQuery = () => {},
    selectedCadServo = null,
    setSelectedCadServo = () => {},
    handleAssignCadId = () => {},
    handleAutoDetectCadServos = () => {},
    handleExportCadMapping = () => {},
    handleImportCadMapping = () => {},
    
    // Vision Pipeline State
    visionStreaming = false,
    setVisionStreaming = () => {},
    visionModel = "MediaPipe Holistic",
    setVisionModel = () => {},
    confidenceThreshold = 0.75,
    setConfidenceThreshold = () => {},
    detectedKeypoints = [],
    selectedCamera = 0,
    setSelectedCamera = () => {},
    availableCameras = ["Camera 0 (Default HD)", "Camera 1 (Depth Sensor)"],
    handTrackingActive = true,
    setHandTrackingActive = () => {},
    poseTrackingActive = true,
    setPoseTrackingActive = () => {},
    
    // Live Diagnostics State
    diagFilter = "all",
    setDiagFilter = () => {},
    diagTimeRange = "5m",
    setDiagTimeRange = () => {},
    pingLatency = 4.2,
    packetLoss = 0.0,
    busVoltage = 24.1,
    busCurrent = 0.85,
    ambientTemp = 28.4,
    mcuTemp = 41.2,
    oscilloscopeData = [],
    diagnosticTestsRunning = false,
    handleRunDiagnosticSelfTest = () => {},
    connSpeedLimit = 100,
    setConnSpeedLimit = () => {},
    
    // Product Manual State
    manualSearch = "",
    setManualSearch = () => {},
    activeManualTopic = "quickstart",
    setActiveManualTopic = () => {},
    setShowShortcutHelp = () => {},
    expandedSection: propExpandedSection,
    setExpandedSection: propSetExpandedSection,
    
    // System Stats & Extra Callbacks
    systemStats = { cpu: 14, ram: 38, fps: 60, status: "NOMINAL" },
    onNavigateToSimulations = () => {},
    onNavigateToPaper = () => {},
  } = props;

  const MANUAL_TOPICS = [
    {
      id: "architecture",
      title: "1. Core API & Backend Server (main.py)",
      category: "System Core",
      summary: "Understanding the FastAPI server architecture, serial communications engine, and background telemetry daemons.",
      why: "Acts as the central nervous system connecting hardware serial pipelines to web UI sockets.",
      how: "API routes include: POST /api/connect (opens serial COM ports), POST /api/disconnect (closes COM), POST /api/motors/torque (enables/disables node torque), POST /api/calibration/tare (zeros load cells), POST /api/research/start / stop (activates active balancer loop), POST /api/research/tune (real-time PID gain updates). Telemetry broadcasts at 50Hz via WS /ws/telemetry.",
      what: "Coordinates connection state locks, updates hardware control inputs, and streams position feedback frames.",
      warning: "Only execute POST requests when the serial link is connected, otherwise endpoints report 503 Service Unavailable errors."
    },
    {
      id: "robots",
      title: "2. Actuator Platform Profiles (src/modules/robots/)",
      category: "Robot Profiles",
      summary: "Exhaustive details on humanoid, LEAP hand, and OMX manipulator profiles.",
      why: "Robot classes define joints coordinates mapping profiles, torque tables, and coordinate limits to decouple backend hardware configurations.",
      how: "Classes subclass BaseRobot: humanoid.py (coordinates 16 joints, parses offsets from calibration files), leap_hand.py (coordinates 16 biomimetic hand motors, configures profiles via osrs_config.json), omx.py (maps 5-axis manipulator joints), rover.py (skid-steer calculations for 6-wheel models).",
      what: "Verifies joint angles bounds, translates raw servo positions, and maps mechanical mirroring variables.",
      warning: "Editing physical limits inside profiles can override safety constraints; always check hardware specification bounds first."
    },
    {
      id: "perception",
      title: "3. Perception & Sensors (src/modules/perception/)",
      category: "Sensors Pipeline",
      summary: "Processing camera depth feeds, IMU orientations, and weight counts.",
      why: "Converts noisy raw hardware sensor streams into filtered coordinate telemetry used by control loop feedback engines.",
      how: "Drivers include: realsense_vision.py (captures Intel RealSense depth streams, tracks ArUco markers on fingers to mask the plate boundary box), force_sensing.py (reads counts from Arduino Uno scale processors), imu_fusion.py (calculates roll/pitch from MPU6050 gyroscope sensors), vision.py (OpenCV Hue/Saturation/Value targeting tracker).",
      what: "Filters reflection highlights, runs orientation filters, and measures target weight scales.",
      warning: "Ensure camera targets remain inside the Plate Bounding Box; coordinates calculated outside boundary limits are rejected."
    },
    {
      id: "research",
      title: "4. Control Theory & Research (src/modules/research/)",
      category: "Control Systems",
      summary: "Analyzing plate balancing PID loops, RLS modeling, and auto-tuning exploration.",
      why: "Maintains target balancing center positions using active control algorithms.",
      how: "ball_balancer.py controls active plate tilts. Select presets like Circle or Infinity paths. Tune Proportional (P), Integral (I), and Derivative (D) gains. Active Exploration generates periodic sine/cosine exploration patterns to dynamically calibrate load-cell mass maps using Recursive Least Squares (RLS).",
      what: "Computes tilt angles, logs coordinates shifts, and updates model projection matrices.",
      warning: "Set integral gains (Ki) lower to prevent integral windup, which causes large overshoot swings."
    },
    {
      id: "firmware",
      title: "5. Embedded HX711 C++ Firmware (LOAD CELL/)",
      category: "Firmware",
      summary: "Compiling and uploading load cell scale firmware to Arduino Uno processors.",
      why: "Reads high-speed weight changes directly from load cell cells and streams measurements over serial links.",
      how: "Sketch OSRS_Scale.ino (Arduino IDE) and src/main.cpp (PlatformIO) read weights from HX711 converter modules. Streams counts at 80Hz over USB serial links. Zero weight offsets upon 'tare' inputs. Use serial_monitor.py for offline testing.",
      what: "Converts analog scale load metrics to raw count bytes.",
      warning: "Compile firmware using the correct FQBN (arduino:avr:uno) to prevent sketch flash failures."
    },
    {
      id: "diagnostics",
      title: "6. Diagnostics & Safety Failsafes",
      category: "Diagnostics & Safety",
      summary: "Resolving motor faults, mock error injection, and emergency ESTOP controls.",
      why: "Halts hardware execution cycles instantly when electrical, mechanical, or signal errors occur.",
      how: "Press Reboot on individual joints to clear overload (0x20) or overheating (0x04) Dynamixel register faults. Inject mock errors to test safety recovery scripts. Press the ESTOP header button or press Alt+S to release torque globally.",
      what: "Checks error feedback registers and cuts serial loop communication signals.",
      warning: "ESTOP cuts torque instantly; support heavy mechanical components manually beforehand to prevent structural drops."
    },
    {
      id: "opensource",
      title: "7. Open-Source Governance, AI Workflows & Safety Policies",
      category: "Governance & Policies",
      summary: "Understanding the open-source license, AI-assisted development model, and hardware safety regulations.",
      why: "Ensures ethical transparency, academic citation standards, and physical operator protection across all deployed robotics hardware.",
      how: "OSRS is licensed under the permissive MIT License. AI-assisted programming workflows were used for mathematical formulations, LaTeX research paper generation, and code modularization under continuous human verification. Refer to AI_DISCLOSURE.md, DISCLAIMER.md, PRIVACY.md, and CITATION.cff in the repository root.",
      what: "Enforces local-first privacy, emergency torque shutdown procedures, and community contribution protocols.",
      warning: "Always test control algorithms in MuJoCo physics simulation or Mock Mode before commanding physical actuators."
    }
  ];

  const [localExpandedSection, setLocalExpandedSection] = useState("manual-ai-governance");
  const expandedSection = propExpandedSection !== undefined ? propExpandedSection : localExpandedSection;
  const setExpandedSection = propSetExpandedSection || setLocalExpandedSection;

  const filteredTopics = MANUAL_TOPICS.filter(topic =>
    topic.title.toLowerCase().includes((manualSearch || "").toLowerCase()) ||
    topic.category.toLowerCase().includes((manualSearch || "").toLowerCase()) ||
    topic.summary.toLowerCase().includes((manualSearch || "").toLowerCase()) ||
    topic.why.toLowerCase().includes((manualSearch || "").toLowerCase()) ||
    topic.how.toLowerCase().includes((manualSearch || "").toLowerCase()) ||
    topic.what.toLowerCase().includes((manualSearch || "").toLowerCase())
  );

  return (
              <div className="space-y-6 animate-fade-in text-white">
                {/* Header Card */}
                <div className="relative overflow-hidden rounded-[32px] bg-gradient-to-r from-[#000000] via-[#0D0F14] to-white/[0.04] p-6 md:p-8 border border-white/[0.08] shadow-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_120%,rgba(16,185,129,0.06),transparent_50%)]" />
                  <div className="relative z-10 w-full md:w-2/3">
                    <span className="text-[10px] uppercase font-black tracking-widest text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">Interactive Manual</span>
                    <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight mt-3">OSRS Operator's Guide</h2>
                    <p className="text-zinc-400 text-xs font-semibold mt-2 leading-relaxed">
                      Search, inspect, and configure every core feature of OSRS. Click a topic to expand dynamic setup tutorials, capability notes, and safety guidelines.
                    </p>
                  </div>
                  {/* Dynamic Search */}
                  <div className="relative z-10 w-full md:w-80">
                    <div className="relative">
                      <Search className="absolute left-4 top-3.5 h-4 w-4 text-zinc-500" />
                      <input
                        type="text"
                        placeholder="Search manual topics..."
                        value={manualSearch}
                        onChange={(e) => setManualSearch(e.target.value)}
                        className="w-full obsidian-card hover:obsidian-card focus:bg-[#040407] border border-white/[0.08] text-zinc-200 placeholder-[#090A0E]/40 rounded-2xl pl-11 pr-4 py-3 text-xs font-bold focus:outline-none focus:ring-2 focus:ring-[#090A0E]/30 transition-all duration-300 shadow-inner"
                      />
                      {manualSearch && (
                        <button 
                          onClick={() => setManualSearch("")} 
                          className="absolute right-4 top-3.5 text-xs text-zinc-500 hover:text-white font-bold"
                        >
                          Clear
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 gap-4">
                  {filteredTopics.length === 0 ? (
                    <div className="obsidian-card backdrop-blur-md rounded-3xl p-12 text-center border border-white/[0.06] shadow-md">
                      <HelpCircle className="h-10 w-10 text-cyan-400/40 mx-auto mb-3" />
                      <h4 className="text-base font-black text-white">No manual matches found</h4>
                      <p className="text-xs text-zinc-400 font-semibold mt-1">Try searching for keywords like "ESTOP", "COM", "Baudrate", or "Calibration".</p>
                    </div>
                  ) : (
                    filteredTopics.map((topic) => {
                      const isExpanded = expandedSection === topic.id;
                      return (
                        <div 
                          key={topic.id}
                          className="obsidian-card backdrop-blur-md rounded-3xl border border-white/[0.06] shadow-md overflow-hidden transition-all duration-300"
                        >
                          {/* Accordion Trigger */}
                          <button
                            onClick={() => setExpandedSection(isExpanded ? "" : topic.id)}
                            className="w-full text-left p-6 flex justify-between items-center hover:hover:bg-white/[0.1]/[0.04] active:active:bg-white/[0.06] transition-colors"
                          >
                            <div className="space-y-1">
                              <div className="flex items-center gap-2.5">
                                <span className="text-[10px] uppercase font-black tracking-wider text-cyan-400 bg-white/[0.08] text-zinc-300 px-2.5 py-0.5 rounded-full">
                                  {topic.category}
                                </span>
                              </div>
                              <h3 className="text-lg font-black text-white tracking-tight">{topic.title}</h3>
                              <p className="text-xs text-zinc-300 font-semibold leading-relaxed">
                                {topic.summary}
                              </p>
                            </div>
                            <span className="text-zinc-500 text-xl font-bold px-2">
                              {isExpanded ? "−" : "+"}
                            </span>
                          </button>

                          {/* Accordion Content */}
                          {isExpanded && (
                            <div className="p-6 border-t border-white/[0.06] bg-[#040407]/[0.02] grid grid-cols-1 md:grid-cols-3 gap-6 animate-slide-down">
                              
                              {/* Why Card */}
                              <div className="bg-cyan-500/20 p-5 rounded-[24px] border border-white/[0.06] flex flex-col justify-between space-y-3 shadow-inner">
                                <div>
                                  <div className="flex items-center gap-2 text-cyan-400 font-black text-xs uppercase tracking-wider mb-2">
                                    <span className="w-5 h-5 rounded-lg bg-[#12141A] text-zinc-200 flex items-center justify-center text-[10px]">?</span>
                                    <span>Why It Exists</span>
                                  </div>
                                  <p className="text-xs text-zinc-300 font-bold leading-relaxed">
                                    {topic.why}
                                  </p>
                                </div>
                              </div>

                              {/* How Card */}
                              <div className="bg-white/80 p-5 rounded-[24px] border border-white/[0.06] flex flex-col justify-between space-y-3 shadow-sm">
                                <div>
                                  <div className="flex items-center gap-2 text-white font-black text-xs uppercase tracking-wider mb-2">
                                    <span className="w-5 h-5 rounded-lg bg-[#040407] text-white flex items-center justify-center text-[10px]">✓</span>
                                    <span>How To Use</span>
                                  </div>
                                  <p className="text-xs text-zinc-300 font-semibold leading-relaxed">
                                    {topic.how}
                                  </p>
                                </div>
                              </div>

                              {/* What Card */}
                              <div className="bg-[#040407]/95 text-white p-5 rounded-[24px] border border-white/[0.06] flex flex-col justify-between space-y-3 shadow-lg">
                                <div>
                                  <div className="flex items-center gap-2 text-zinc-200 font-black text-xs uppercase tracking-wider mb-2">
                                    <span className="w-5 h-5 rounded-lg bg-white/[0.08] text-zinc-300 text-white flex items-center justify-center text-[10px]">⚡</span>
                                    <span>What It Can Do</span>
                                  </div>
                                  <p className="text-xs text-zinc-300 font-medium leading-relaxed">
                                    {topic.what}
                                  </p>
                                </div>
                              </div>

                              {/* Warning Banner */}
                              <div className="col-span-1 md:col-span-3 bg-red-50/60 border border-red-200/50 rounded-2xl p-4 flex items-start gap-3">
                                <AlertTriangle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
                                <div>
                                  <h5 className="text-xs font-black text-red-800 uppercase tracking-wider">Operational Caution</h5>
                                  <p className="text-xs text-red-700/90 font-bold mt-1 leading-relaxed">
                                    {topic.warning}
                                  </p>
                                </div>
                              </div>

                            </div>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>

              </div>
  );
}
