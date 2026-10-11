import React, { useState, useEffect } from "react";
import { Activity, AlertTriangle, Settings } from "lucide-react";

/**
 * Diagnostics Screen - Live bus oscilloscope, temperature profiling, packet health
 */
export default function DiagnosticsScreen(props) {
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


  return (
            <div className="space-y-6 animate-fade-in">
              <div className="obsidian-card p-6 md:p-8 animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
                <div className="flex items-center gap-3 border-b border-white/[0.06] pb-4 mb-6">
                  <Activity className="h-6 w-6 text-white" />
                  <h3 className="text-2xl font-black text-white">Health Diagnostics & Telemetry Bus</h3>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-white/[0.06] text-zinc-500 font-bold uppercase tracking-wider text-[10px]">
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
                          <tr key={mid} className="border-b border-white/[0.06] hover:bg-white/[0.1]/[0.02]">
                            <td className="py-3 px-4 font-mono font-bold">{mid}</td>
                            <td className="py-3 px-4 font-bold text-zinc-200">{info.name}</td>
                            <td className="py-3 px-4 font-mono text-zinc-400">{telemData.goal}</td>
                            <td className="py-3 px-4 font-mono text-zinc-400">{telemData.present}</td>
                            <td className="py-3 px-4 font-mono text-zinc-400">{telemData.current}</td>
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
                                className="bg-[#B5ACF3]/10 hover:bg-[#B5ACF3]/25 text-white font-bold px-3 py-1.5 rounded-xl transition text-[11px]"
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
                <div className="obsidian-card p-6 animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
                  <h3 className="text-lg font-extrabold text-white mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-red-500" /> Error Injection Simulator
                  </h3>
                  <p className="text-xs text-zinc-400 font-bold mb-5 leading-relaxed">
                    Inject artificial register errors into individual servos to simulate hardware faults (e.g. Overload 0x20 / 32).
                  </p>
                  
                  <div className="flex gap-4 items-center">
                    <input 
                      type="number"
                      placeholder="ID"
                      value={mockErrorId}
                      onChange={(e) => setMockErrorId(e.target.value)}
                      className="bg-black/60 border border-white/[0.06] rounded-xl px-4 py-2 text-xs font-bold w-20 focus:outline-none focus:ring-2 focus:ring-[#B5ACF3]"
                    />
                    <select
                      value={mockErrorByte}
                      onChange={(e) => setMockErrorByte(e.target.value)}
                      className="bg-black/60 border border-white/[0.06] rounded-xl px-4 py-2 text-xs font-bold focus:outline-none cursor-pointer"
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
                <div className="obsidian-card p-6 animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
                  <h3 className="text-lg font-extrabold text-white mb-3 flex items-center gap-2">
                    <Settings className="h-5 w-5 text-[#B5ACF3]" /> Global Safety Limits
                  </h3>
                  <p className="text-xs text-zinc-400 font-bold mb-5 leading-relaxed">
                    Configure thresholds for maximum velocity and maximum current draw (mA). Adjustments apply during serial bus connections.
                  </p>
                  
                  <div className="space-y-4">
                    <div className="flex justify-between items-center obsidian-inset p-3 rounded-xl border border-slate-150">
                      <span className="text-xs font-bold text-zinc-300">Peak Current Limit</span>
                      <input 
                        type="number"
                        value={connCurrentLimit}
                        onChange={(e) => setConnCurrentLimit(parseInt(e.target.value) || 0)}
                        className="bg-[#040407] border border-white/[0.08] focus:border-cyan-500/50 rounded-lg px-2 py-1 text-center font-mono font-semibold text-white focus:outline-none text-xs w-20 focus:outline-none focus:border-[#B5ACF3]"
                      />
                      <span className="text-[10px] text-zinc-500 font-bold">mA</span>
                    </div>

                    <div className="flex justify-between items-center obsidian-inset p-3 rounded-xl border border-slate-150">
                      <span className="text-xs font-bold text-zinc-300">Peak Speed Limit</span>
                      <input 
                        type="number"
                        value={connSpeedLimit}
                        onChange={(e) => setConnSpeedLimit(parseInt(e.target.value) || 0)}
                        className="bg-[#040407] border border-white/[0.08] focus:border-cyan-500/50 rounded-lg px-2 py-1 text-center font-mono font-semibold text-white focus:outline-none text-xs w-20 focus:outline-none focus:border-[#B5ACF3]"
                      />
                      <span className="text-[10px] text-zinc-500 font-bold">RPM</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
  );
}
