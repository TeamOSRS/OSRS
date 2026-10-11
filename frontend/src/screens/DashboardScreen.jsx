import React, { useState, useEffect, useRef } from "react";
import { Activity, Cpu, Terminal, Wifi, WifiOff } from "lucide-react";

/**
 * Dashboard Screen - High-level telemetry, link status, logs and quick actions
 */
export default function DashboardScreen(props) {
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

  const terminalRef = useRef(null);
  const logEndRef = useRef(null);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const visibleLogs = (logs || []).slice(clearOffset || 0);

  return (
              <div className="space-y-6 animate-fade-in">
                
                {/* Futuristic Welcome Hero Banner */}
                <div className="relative overflow-hidden rounded-[32px] bg-gradient-to-r from-[#000000] via-[#0D0F14] to-white/[0.04] p-6 md:p-8 border border-white/[0.08] shadow-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                  <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(16,185,129,0.08),transparent_50%)]" />
                  <div className="relative z-10">
                    <span className="text-[10px] uppercase font-black tracking-widest text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">OSRS Command Center</span>
                    <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight mt-3">Robot System Control</h2>
                    <p className="text-zinc-400 text-xs font-semibold mt-1 max-w-lg">Monitor kinematics, fine-tune PID active balancers, track telemetry pipelines, and command multiple degrees-of-freedom from a single interface.</p>
                  </div>
                  <div className="relative z-10 flex gap-3">
                    <div className="bg-[#090A0E] border border-white/[0.08] rounded-2xl p-4 flex flex-col gap-0.5 items-center justify-center min-w-[90px] shadow-lg">
                      <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Active Rig</span>
                      <span className="text-sm font-extrabold text-zinc-200 mt-0.5">{handVersion}</span>
                    </div>
                    <div className="bg-[#090A0E] border border-white/[0.08] rounded-2xl p-4 flex flex-col gap-0.5 items-center justify-center min-w-[90px] shadow-lg">
                      <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Bus Link</span>
                      <span className={`text-sm font-extrabold mt-0.5 ${connected ? "text-emerald-400" : "text-rose-400"}`}>{connected ? "ONLINE" : "OFFLINE"}</span>
                    </div>
                  </div>
                </div>

                {/* Startup Connection Station if offline */}
                {!connected && (
                  <div className="bg-[#090A0E] border border-white/[0.08] rounded-2xl p-6 shadow-xl flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-emerald-500/5 to-transparent animate-pulse" />
                    <div className="relative z-10">
                      <div className="flex items-center gap-2 text-rose-400 font-bold text-xs uppercase tracking-widest">
                        <WifiOff className="h-4 w-4" />
                        <span>Link Offline</span>
                      </div>
                      <h3 className="text-lg font-black text-white mt-1.5">Configure Communications Link</h3>
                      <p className="text-zinc-400 mt-1 text-xs font-semibold">Enter the serial port ID and serial bus baudrate speed parameters to initialize joint feedback.</p>
                    </div>
                    
                    <div className="relative z-10 flex flex-wrap gap-3 items-end bg-[#040407] p-3 rounded-xl border border-white/[0.06] w-full lg:w-auto">
                      <div className="flex flex-col gap-1 w-full sm:w-28">
                        <label className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest px-1">Serial Port</label>
                        <input 
                          type="text" 
                          value={connPort}
                          onChange={(e) => setConnPort(e.target.value)}
                          placeholder="COM14"
                          className="bg-[#040407] border border-white/[0.08] focus:border-cyan-500/50 rounded-xl px-3 py-2 text-xs font-bold text-white focus:outline-none w-full transition-colors"
                        />
                      </div>
                      
                      <div className="flex flex-col gap-1 w-full sm:w-36 relative">
                        <label className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest px-1">Baudrate Speed</label>
                        <button
                          type="button"
                          onClick={() => setShowBaudDropdownDashboard(!showBaudDropdownDashboard)}
                          className="bg-[#040407] border border-white/[0.08] hover:border-white/[0.15] focus:border-cyan-500/50 rounded-xl px-3 py-2 text-xs font-bold text-white flex items-center justify-between cursor-pointer w-full transition-colors h-[34px]"
                        >
                          <span>{BAUDRATE_OPTIONS.find(o => o.value === connBaud)?.label || "Select speed"}</span>
                          <svg className={`w-3.5 h-3.5 text-zinc-400 transition-transform duration-200 ${showBaudDropdownDashboard ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        
                        {showBaudDropdownDashboard && (
                          <>
                            <div 
                              className="fixed inset-0 z-40" 
                              onClick={() => setShowBaudDropdownDashboard(false)} 
                            />
                            <div className="absolute left-0 right-0 mt-12 bg-[#040407] rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.5)] border border-white/[0.08] p-1 z-50 flex flex-col gap-0.5 text-white font-sans animate-in fade-in slide-in-from-top-2 duration-150">
                              {BAUDRATE_OPTIONS.map((opt) => (
                                <button
                                  key={opt.value}
                                  type="button"
                                  onClick={() => {
                                    setConnBaud(opt.value);
                                    setShowBaudDropdownDashboard(false);
                                  }}
                                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-bold transition-all duration-150 ${
                                    connBaud === opt.value 
                                      ? "pill-btn-white text-zinc-900" 
                                      : "hover:bg-[#12141A]/65 text-zinc-300 hover:text-white"
                                  }`}
                                >
                                  {opt.label}
                                </button>
                              ))}
                            </div>
                          </>
                        )}
                      </div>
                      
                      <label className="flex items-center gap-2 text-xs font-bold text-zinc-400 hover:text-white cursor-pointer px-3 py-2 rounded-xl bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.15] transition-colors w-full sm:w-auto justify-center">
                        <input 
                          type="checkbox"
                          checked={connMock}
                          onChange={(e) => setConnMock(e.target.checked)}
                          className="rounded text-zinc-200 bg-[#040407] border-white/[0.08] w-4 h-4 cursor-pointer focus:ring-0 focus:ring-offset-0 focus:outline-none"
                        />
                        <span>Mock Mode</span>
                      </label>
                      
                      <button
                        onClick={triggerConnect}
                        className="w-full sm:w-auto bg-white hover:bg-zinc-100 active:scale-[0.98] text-black px-6 py-2.5 rounded-xl text-xs font-bold tracking-wider transition-all uppercase shadow-md flex items-center justify-center gap-2 cursor-pointer"
                      >
                        Connect Link
                      </button>
                    </div>
                  </div>
                )}

                {/* Main Overhaul Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  
                  {/* Column 1: Stats cards & Signal Activity */}
                  <div className="space-y-6 flex flex-col justify-between">
                    {/* Small card 1: Temp / CPU */}
                    <div className="bg-[#090A0E] hover:bg-[#0D0F14] rounded-2xl p-6 shadow-lg border border-white/[0.07] flex justify-between items-center transition-all duration-200">
                      <div>
                        <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block">System CPU Load</span>
                        <h4 className="text-3xl font-black text-zinc-200 mt-2">{systemStats.cpu}%</h4>
                        <span className="text-[9px] text-zinc-200/55 font-bold mt-1 block">Utilization Nominal</span>
                      </div>
                      <div className="w-12 h-12 rounded-full bg-white/[0.05] flex items-center justify-center border border-white/[0.08] shadow-inner">
                        <Cpu className="w-5 h-5 text-zinc-200" />
                      </div>
                    </div>

                    {/* Small card 2: Telemetry latency */}
                    <div className="bg-[#090A0E] hover:bg-[#0D0F14] rounded-2xl p-6 shadow-lg border border-white/[0.07] flex justify-between items-center transition-all duration-200">
                      <div>
                        <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block">Bus Network Latency</span>
                        <h4 className="text-3xl font-black text-zinc-200 mt-2">{systemStats.latency} ms</h4>
                        <span className="text-[9px] text-zinc-200/55 font-bold mt-1 block">Frame Speed: {systemStats.fps} Hz</span>
                      </div>
                      <div className="w-12 h-12 rounded-full bg-white/[0.05] flex items-center justify-center border border-white/[0.08] shadow-inner">
                        <Activity className="w-5 h-5 text-zinc-200" />
                      </div>
                    </div>

                    {/* Live Telemetry Terminal */}
                    <div className="bg-[#090A0E] rounded-2xl p-6 shadow-lg border border-white/[0.07] text-white flex-1 flex flex-col justify-between min-h-[260px]">
                      <div className="flex justify-between items-center mb-4 pb-2 border-b border-white/[0.06]">
                        <div className="flex items-center gap-2">
                          <Terminal className="h-4 w-4 text-zinc-200" />
                          <span className="font-bold text-xs uppercase tracking-widest text-zinc-200">Live Telemetry Terminal</span>
                        </div>
                        
                        {/* Terminal Action Deck */}
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setPauseLogs(!pauseLogs)}
                            className={`px-2.5 py-1 rounded-md text-[9px] font-bold uppercase tracking-wider transition ${
                              pauseLogs 
                                ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" 
                                : "bg-white/[0.05] text-zinc-400 hover:text-white border border-white/[0.08]"
                            }`}
                            title={pauseLogs ? "Resume Log Stream" : "Pause Log Stream"}
                          >
                            {pauseLogs ? "Paused" : "Pause"}
                          </button>
                          
                          <button
                            onClick={handleCopyLogs}
                            className="px-2.5 py-1 rounded-md text-[9px] font-bold uppercase tracking-wider bg-white/[0.05] text-zinc-400 hover:text-white border border-white/[0.08] transition"
                            title="Copy Logs to Clipboard"
                          >
                            Copy
                          </button>
                          
                          <button
                            onClick={handleClearLogs}
                            className="px-2.5 py-1 rounded-md text-[9px] font-bold uppercase tracking-wider bg-white/[0.05] text-rose-400 hover:text-rose-300 border border-white/[0.08] hover:bg-rose-500/10 transition"
                            title="Clear Terminal Display"
                          >
                            Clear
                          </button>
                        </div>
                      </div>
                      
                      <div ref={terminalRef} className="bg-[#000000]/60 font-mono text-[10px] p-4 rounded-2xl overflow-y-auto border border-white/[0.06] flex flex-col gap-1 text-zinc-300 h-40 terminal-scrollbar">
                        {visibleLogs.length > 0 ? (
                          visibleLogs.map((log, index) => {
                            let textColor = "text-zinc-300";
                            if (log.includes("ERROR")) textColor = "text-rose-300 font-bold";
                            else if (log.includes("WARNING")) textColor = "text-amber-300";
                            else if (log.includes("AUTO-RESTART")) textColor = "text-zinc-200 font-medium";
                            
                            const lineNum = String(index + 1).padStart(2, "0");
                            return (
                              <div key={index} className="flex gap-2.5 leading-relaxed hover:bg-white/[0.1]/[0.03] px-1 py-0.5 rounded transition-colors duration-150">
                                <span className="text-zinc-600 select-none font-bold">[{lineNum}]</span>
                                <span className={textColor}>{log}</span>
                              </div>
                            );
                          })
                        ) : (
                          <div className="text-zinc-600 text-center py-12 italic text-xs">Terminal display empty or cleared.</div>
                        )}
                        <div ref={logEndRef} />
                      </div>
                    </div>
                  </div>

                  {/* Column 2: Wellness Index / Node Integrity Matrix */}
                  <div className="bg-[#090A0E] rounded-2xl p-6 shadow-lg border border-white/[0.07] flex flex-col justify-between min-h-[460px]">
                    <div>
                      <div className="flex justify-between items-center mb-4 pb-2 border-b border-white/[0.06]">
                        <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Actuator Bus Status</span>
                        <span className="text-[9px] font-extrabold text-zinc-200 bg-white/[0.05] border border-white/[0.08] px-2.5 py-0.5 rounded-full">{systemStats.health}% Good</span>
                      </div>
                      <h3 className="text-2xl font-black text-white tracking-tight">{activeMotorIds.length} <span className="text-xs font-bold text-zinc-400 block mt-0.5">Active Nodes Mapped on Serial Loop</span></h3>
                    </div>

                    <div className="flex-1 flex flex-col justify-center my-6">
                      <div className="grid grid-cols-4 gap-2.5 p-4 bg-[#040407] rounded-xl border border-white/[0.05] p-4">
                        {activeMotorIds.map((mid) => {
                          const telemData = telemetry[mid] || { error: 0, torque: false };
                          const hasError = telemData.error !== 0;
                          const isTorqued = telemData.torque === true;
                          
                          let dotBg = "bg-[#040407] border-white/[0.06] text-zinc-600";
                          if (connected) {
                            if (hasError) dotBg = "bg-red-500/20 border-red-500/40 text-red-300 animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.15)]";
                            else if (isTorqued) dotBg = "bg-cyan-500/20 border-cyan-500/40 text-zinc-200 shadow-[0_0_10px_rgba(56,189,248,0.2)]";
                            else dotBg = "bg-white/[0.03] border-white/[0.06] text-zinc-400";
                          }

                          return (
                            <div 
                              key={mid}
                              onClick={() => {
                                setSelectedJoint(parseInt(mid));
                                setActiveTab("control");
                              }}
                              title={`Joint ID ${mid}: ${limits[mid]?.name || "Actuator"}`}
                              className={`h-12 rounded-xl ${dotBg} border flex flex-col items-center justify-center text-[10px] font-black shadow-sm cursor-pointer hover:scale-105 transition-all active:scale-95 duration-200`}
                            >
                              <span className="opacity-50 text-[7px] tracking-wider font-extrabold uppercase">ID</span>
                              <span className="text-xs mt-0.5">{mid}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="flex flex-wrap justify-between items-center text-[8px] font-bold uppercase tracking-widest text-zinc-500 border-t border-white/[0.06] pt-4 gap-2">
                      <span className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-cyan-500/20 border border-cyan-500/40" /> Active Torque</span>
                      <span className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-white/[0.03] border border-white/[0.06]" /> Standby/Hold</span>
                      <span className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-red-500/20 border border-red-500/40 animate-pulse" /> Register Fault</span>
                    </div>
                  </div>

                </div>

              </div>
  );
}
