import React, { useState, useEffect } from "react";
import { RefreshCw, Video } from "lucide-react";

/**
 * Vision Screen - Computer vision pipeline, camera feeds, pose estimation
 */
export default function VisionScreen(props) {
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
            <div className="obsidian-card p-6 md:p-8 max-w-4xl mx-auto animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
              <div className="flex items-center gap-3 border-b border-white/[0.06] pb-4 mb-6">
                <Video className="h-6 w-6 text-white" />
                <h3 className="text-2xl font-black text-white">Perception Vision Pipeline</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Control settings */}
                <div className="obsidian-inset p-5 border border-white/[0.06] rounded-2xl h-fit space-y-5">
                  <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Camera Settings</h4>
                  
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase block">Select Device Index</label>
                    <select
                      value={cameraIdx}
                      onChange={(e) => setCameraIdx(parseInt(e.target.value))}
                      disabled={cameraActive}
                      className="w-full bg-[#040407] border border-white/[0.08] focus:border-cyan-500/50 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-white focus:outline-none cursor-pointer"
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
                      trackingEnabled ? "bg-[#CFFF3E]/20 border-[#CFFF3E] text-white" : "bg-[#040407] border-white/[0.06] text-zinc-400"
                    }`}>
                      <span>Hand-Tracking Autopilot</span>
                      <div className={`w-8 h-5 rounded-full p-0.5 flex-shrink-0 transition-colors ${trackingEnabled ? "bg-[#CFFF3E] border-[#1E2022]/10" : "bg-slate-300"}`}>
                        <div className={`w-4 h-4 bg-zinc-200 rounded-full shadow-sm transform transition-transform ${trackingEnabled ? "translate-x-3" : "translate-x-0"}`} />
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
                        <div className="flex flex-col items-center gap-2 text-zinc-400 font-mono text-xs">
                          <RefreshCw className="w-5 h-5 animate-spin text-[#B5ACF3]" />
                          <span>Streaming perception canvas pipeline...</span>
                        </div>
                      )
                    ) : (
                      <div className="text-zinc-400 text-xs font-mono text-center px-4">
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
  );
}
