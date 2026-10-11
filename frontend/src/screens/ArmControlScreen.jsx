import React, { useState, useEffect, useRef } from "react";
import { RefreshCw } from "lucide-react";

/**
 * Arm Control Screen - Visual joint dials, limits, 3D/2D skeleton representation
 */
export default function ArmControlScreen(props) {
  // Destructure shared state and actions with safe defaults
  const {
    // Hardware & Connection
    connected = false,
    connPort = "COM14",
    setConnPort = () => {},
    connBaud = 4000000,
    setConnBaud = () => {},
    connMock = false,
    setConnMock = () => {},
    connCurrentLimit = 250,
    setConnCurrentLimit = () => {},
    connSpeedLimit = 150,
    setConnSpeedLimit = () => {},
    triggerConnect = () => {},
    triggerDisconnect = () => {},
    toggleEstop = () => {},
    estopActive = false,
    handVersion = "Humanoid V1",
    setHandVersion = () => {},
    mirrorSyncActive = false,
    handleToggleMirrorSync = () => {},
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
    systemStats = { health: 100, cpu: 14, ram: 38, fps: 60, status: "NOMINAL", latency: 2.1 },
    
    // Telemetry & Logs
    telemetry = {},
    limits = {},
    activeMotorIds = [],
    setActiveMotorIds = () => {},
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
    
    // Arm Control & Visual Dials
    positions = {},
    localDrags = {},
    setLocalDrags = () => {},
    inputValues = {},
    setInputValues = () => {},
    handleInputChange = () => {},
    handleSliderDrag = () => {},
    handleSliderRelease = () => {},
    handleInputBlur = () => {},
    handlePositionChange = () => {},
    sendZeroPose = () => {},
    resetAllToDefault = () => {},
    selectedJoint = null,
    setSelectedJoint = () => {},
    handleJointClick = () => {},
    handleSendCommand = () => {},
    rotateJointByDeg = () => {},
    expandedSections = { leftArm: true, rightArm: true, head: true },
    setExpandedSections = () => {},
    
    // Emote Maker Studio
    savedEmotes = {},
    fetchCustomEmotes = () => {},
    emoteFrames = [],
    setEmoteFrames = () => {},
    activeFrameIdx = 0,
    setActiveFrameIdx = () => {},
    newEmoteName = "",
    setNewEmoteName = () => {},
    saveName = "",
    setSaveName = () => {},
    emoteSpeed = 1,
    setEmoteSpeed = () => {},
    emoteLoop = 1,
    setEmoteLoop = () => {},
    showSaveModal = false,
    setShowSaveModal = () => {},
    playingPreset = null,
    playingEmote = false,
    playPresetEmote = () => {},
    loadPresetEmoteIntoMaker = () => {},
    loadSavedEmoteIntoMaker = () => {},
    playCustomEmote = () => {},
    playSavedCustomEmote = () => {},
    handleDeleteCustomEmote = () => {},
    handleSaveCustomEmote = () => {},
    handleSaveEmote = () => {},
    addEmoteFrame = () => {},
    removeEmoteFrame = () => {},
    previewFrame = () => {},
    updateFrameDelay = () => {},
    updateFrameHold = () => {},
    updateFrameJoint = () => {},
    emoteInputValues = {},
    setEmoteInputValues = () => {},
    PRESET_EMOTE_FRAMES = {},
    
    // Calibration Wizard State
    calibration = { calib_left: {}, calib_right: {} },
    setCalibration = () => {},
    calib_left = {},
    calib_right = {},
    calibBaseInputs = {},
    setCalibBaseInputs = () => {},
    calibInputValues = {},
    setCalibInputValues = () => {},
    calibrationState = {
      calib_running: false,
      calib_progress: 0,
      calib_status_msg: "Ready",
      calib_fault_reason: "",
      calib_paused: false,
      calib_retry: false,
      calib_aborted: false
    },
    controlCalibration = () => {},
    handleTorqueArm = () => {},
    handleCaptureCalibration = () => {},
    handleGoToBase = () => {},
    handleSaveCalibration = () => {},
    handleSetZeroCalibration = () => {},
    handleSaveBaseFrame = () => {},
    
    // CAD Mapper State
    mapperId = "",
    setMapperId = () => {},
    mapperNewId = "",
    setMapperNewId = () => {},
    mapperName = "",
    setMapperName = () => {},
    mapperDefault = 0,
    setMapperDefault = () => {},
    mapperMin = -4096,
    setMapperMin = () => {},
    mapperMax = 4096,
    setMapperMax = () => {},
    mapperInverted = false,
    setMapperInverted = () => {},
    editingMapper = false,
    startEditMapper = () => {},
    resetMapperForm = () => {},
    handleSaveMapper = () => {},
    handleDeleteMapper = () => {},
    
    // Perception Vision
    cameraIdx = 0,
    setCameraIdx = () => {},
    cameraActive = false,
    toggleVisionSystem = () => {},
    trackingEnabled = false,
    toggleTracking = () => {},
    toggleHandTracking = () => {},
    videoFrame = null,
    
    // Live Diagnostics & Mock Errors
    mockErrorId = "",
    setMockErrorId = () => {},
    mockErrorByte = "32",
    setMockErrorByte = () => {},
    triggerMockError = () => {},
    
    // Ball Balancer Research
    balancerData = {},
    handleTune = () => {},
    handleResearchToggle = () => {},
    handleGoToStart = () => {},
    handleInitializeArms = () => {},
    handleBalancerCommand = () => {},
    backendState = {},
    
    // Product Manual State
    manualSearch = "",
    setManualSearch = () => {},
    setShowShortcutHelp = () => {},
    
    // Navigation Callback
    onNavigate = () => {},
    onNavigateToSimulations = () => {},
    onNavigateToPaper = () => {},
  } = props;


  const sliderRefs = useRef({});

  return (
            <div className="obsidian-card p-6 md:p-8 animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 border-b border-white/[0.06] pb-4 gap-4">
                <div>
                  <h3 className="text-2xl font-black text-white">Visual Structure Control</h3>
                  <p className="text-xs text-zinc-400 font-bold mt-0.5">Highlight joints in the map to filter. Slide parameters or click direct values to override coordinates.</p>
                </div>
                <div className="bg-[#B5ACF3]/10 border border-[#B5ACF3]/30 rounded-2xl p-4 text-[11px] text-zinc-300 font-medium font-bold max-w-sm">
                  <span className="block font-black text-white">Horn Convention:</span>
                  <span className="block mt-0.5">● (+) values move Counter-Clockwise (CCW).</span>
                  <span className="block">● (-) values move Clockwise (CW).</span>
                  <span className="block">● Reference baseline offset is mapped at 0.</span>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* SVG Skeleton Map (Center) */}
                <div className="obsidian-inset rounded-3xl p-6 border border-white/[0.06] flex flex-col items-center justify-center min-h-[460px]">
                  <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-6">Joint Wireframe Mapper</h4>
                  
                  {handVersion === "Humanoid V1" || handVersion === "V1" || handVersion === "V2" ? (
                    <svg viewBox="0 0 340 380" className="w-full max-w-[280px] h-auto">
                      {/* Neck & Head trunk */}
                      <line x1="170" y1="20" x2="170" y2="48" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="170" y1="48" x2="170" y2="75" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      
                      {/* Shoulders */}
                      <line x1="170" y1="75" x2="120" y2="90" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="170" y1="75" x2="220" y2="90" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      
                      {/* Left Arm Links */}
                      <line x1="120" y1="90" x2="105" y2="130" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="105" y1="130" x2="90" y2="170" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="90" y1="170" x2="75" y2="210" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="75" y1="210" x2="60" y2="250" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="60" y1="250" x2="45" y2="290" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="45" y1="290" x2="30" y2="330" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="30" y1="330" x2="18" y2="365" stroke="rgba(255,255,255,0.15)" strokeWidth="3" strokeDasharray="3,3" />

                      {/* Right Arm Links */}
                      <line x1="220" y1="90" x2="235" y2="130" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="235" y1="130" x2="250" y2="170" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="250" y1="170" x2="265" y2="210" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="265" y1="210" x2="280" y2="250" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="280" y1="250" x2="295" y2="290" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="295" y1="290" x2="310" y2="330" stroke="rgba(255,255,255,0.15)" strokeWidth="4" />
                      <line x1="310" y1="330" x2="322" y2="365" stroke="rgba(255,255,255,0.15)" strokeWidth="3" strokeDasharray="3,3" />

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
                    <div className="flex flex-col items-center justify-center flex-1 text-zinc-500 italic text-xs">
                      <span>No skeleton mapping view available for {handVersion}</span>
                    </div>
                  )}
                  
                  {selectedJoint && (
                    <div className="mt-4 text-xs bg-[#B5ACF3]/20 text-white px-4 py-2 rounded-full font-black">
                      Selected Joint ID: {selectedJoint}
                    </div>
                  )}

                  {/* Dual-Arm Mirroring & Pose Presets Card */}
                  <div className="mt-6 w-full obsidian-inset rounded-2xl border border-white/[0.06] p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-black text-zinc-200 uppercase tracking-wide">Dual-Arm Mirroring</span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={mirrorSyncActive} 
                          onChange={(e) => handleToggleMirrorSync(e.target.checked)} 
                          className="sr-only peer" 
                        />
                        <div className="w-9 h-5 bg-white/[0.08] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-350 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#CFFF3E]"></div>
                      </label>
                    </div>
                    
                    <div className="border-t border-white/[0.06] pt-3">
                      <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest block mb-2.5">Calibrated Pose Presets</span>
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
                          className="py-2 bg-white/[0.04] hover:bg-white/[0.1]/[0.08] text-white border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Left Arm Pose
                        </button>
                        <button 
                          onClick={() => handleSendCommand("right_pose")}
                          disabled={!connected}
                          className="py-2 bg-white/[0.04] hover:bg-white/[0.1]/[0.08] text-white border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Right Arm Pose
                        </button>
                        <button 
                          onClick={() => handleSendCommand("tilt_up")}
                          disabled={!connected}
                          className="py-2 bg-white/[0.04] hover:bg-white/[0.1]/[0.08] text-white border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Both Arms Up
                        </button>
                        <button 
                          onClick={() => handleSendCommand("tilt_center")}
                          disabled={!connected}
                          className="py-2 bg-white/[0.04] hover:bg-white/[0.1]/[0.08] text-white border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Both Arms Center
                        </button>
                        <button 
                          onClick={() => handleSendCommand("tilt_down")}
                          disabled={!connected}
                          className="py-2 bg-white/[0.04] hover:bg-white/[0.1]/[0.08] text-white border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Both Arms Down
                        </button>
                        <button 
                          onClick={() => handleSendCommand("left_hand_open")}
                          disabled={!connected}
                          className="py-2 bg-white/[0.04] hover:bg-white/[0.1]/[0.08] text-white border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
                        >
                          Left Hand Open
                        </button>
                        <button 
                          onClick={() => handleSendCommand("left_hand_closed")}
                          disabled={!connected}
                          className="py-2 bg-white/[0.04] hover:bg-white/[0.1]/[0.08] text-white border border-slate-250/30 text-[10px] font-black uppercase rounded-xl transition disabled:opacity-45"
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
                          <div key={catKey} className="obsidian-inset rounded-2xl border border-white/[0.06] p-4 space-y-3 transition-all duration-300">
                            <button
                              onClick={() => setExpandedSections(prev => ({ ...prev, [catKey]: !prev[catKey] }))}
                              className="w-full flex items-center justify-between font-bold text-xs uppercase tracking-wider text-zinc-400 hover:text-zinc-200 px-2 py-1 transition focus:outline-none"
                            >
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-black text-zinc-200">{catData.title}</span>
                                <span className="bg-white/[0.08] text-zinc-300 text-[10px] px-2.5 py-0.5 rounded-full font-extrabold">{catData.joints.length} Node{catData.joints.length > 1 ? 's' : ''}</span>
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
                                          : "bg-[#040407] border-white/[0.06] hover:border-white/[0.12] text-zinc-300"
                                      }`}
                                    >
                                      <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                          <span className="font-extrabold text-base text-white">{info.name}</span>
                                          <span className="text-[9px] bg-white/[0.04] text-zinc-400 font-bold px-2 py-0.5 rounded-full">ID {mid}</span>
                                          <button 
                                            onClick={() => toggleTorqueIndividual(mid, true)}
                                            className="text-[9px] bg-white/[0.04] hover:bg-[#CFFF3E] text-white font-black px-2.5 py-0.5 rounded-full transition"
                                          >
                                            TORQUE ON
                                          </button>
                                          <button 
                                            onClick={() => toggleTorqueIndividual(mid, false)}
                                            className="text-[9px] bg-white/[0.04] hover:bg-red-500 hover:text-white text-zinc-400 font-black px-2.5 py-0.5 rounded-full transition"
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
                                            className="w-16 text-center text-xs font-mono font-bold text-white bg-black/60 border border-white/[0.06] rounded-lg py-1 focus:outline-none focus:ring-2 focus:ring-[#B5ACF3]"
                                            title="Click to manually edit angle value"
                                          />
                                        )}
                                      </div>

                                      {/* Quick Rotate & Value readout row */}
                                      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 bg-white/[0.02] p-3 rounded-2xl border border-white/[0.06] text-xs">
                                        <div className="flex items-center gap-2">
                                          <span className="text-zinc-400 font-bold">Quick Rotate:</span>
                                          <button
                                            onClick={() => rotateJointByDeg(mid, -90)}
                                            disabled={hasError}
                                            className="px-3 py-1.5 bg-white/[0.05] hover:bg-white/[0.1]/[0.1] text-zinc-200 font-bold rounded-xl border border-white/[0.08] transition-colors transition text-[10px] uppercase tracking-wider flex items-center gap-1 disabled:opacity-40"
                                          >
                                            -90° (CW)
                                          </button>
                                          <button
                                            onClick={() => rotateJointByDeg(mid, 90)}
                                            disabled={hasError}
                                            className="px-3 py-1.5 bg-white/[0.05] hover:bg-white/[0.1]/[0.1] text-zinc-200 font-bold rounded-xl border border-white/[0.08] transition-colors transition text-[10px] uppercase tracking-wider flex items-center gap-1 disabled:opacity-40"
                                          >
                                            +90° (CCW)
                                          </button>
                                        </div>
                                        <div className="flex items-center gap-3 text-zinc-400 font-bold font-mono text-[10px]">
                                          <span>OFFSET: <span className="text-blue-600 font-black">{displayValue} ticks</span> ({(displayValue * 360 / 4096).toFixed(1)}°)</span>
                                          <span className="text-slate-350">|</span>
                                          <span>ABS: <span className="text-white font-black">{currentPhysical} ticks</span></span>
                                        </div>
                                      </div>
                                      
                                      <div className="flex items-center gap-4">
                                        <span className="text-[10px] text-zinc-400 font-bold">{minVal}</span>
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
                                          <div className="flex justify-between text-[8px] text-zinc-400 font-bold mt-1 px-1">
                                            <span>(-) Clockwise (CW)</span>
                                            <span>(+) Counter-Clockwise (CCW)</span>
                                          </div>
                                        </div>
                                        <span className="text-[10px] text-zinc-400 font-bold">{maxVal}</span>
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
                    <div className="text-zinc-500 text-center py-20 italic">Please establish device bus connection first.</div>
                  )}
                </div>

              </div>
            </div>
  );
}
