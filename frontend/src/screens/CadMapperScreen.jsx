import React, { useState, useEffect } from "react";
import { Settings } from "lucide-react";

/**
 * CAD Mapper Screen - Servo ID remapping and bus auto-addressing
 */
export default function CadMapperScreen(props) {
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
            <div className="obsidian-card p-6 md:p-8 animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
              <div className="flex items-center gap-3 border-b border-white/[0.06] pb-4 mb-6">
                <Settings className="h-6 w-6 text-white" />
                <h3 className="text-2xl font-black text-white">CAD ID Joint Mapping Editor</h3>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Form Editor */}
                <div className="obsidian-inset p-5 border border-white/[0.06] rounded-2xl h-fit space-y-4">
                  <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-2">
                    {editingMapper ? `Edit Joint ID ${mapperId}` : "Register New Joint Mapping"}
                  </h4>
                  
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase block">Active Actuator ID</label>
                    <input 
                      type="number"
                      value={mapperId}
                      onChange={(e) => setMapperId(e.target.value)}
                      disabled={editingMapper}
                      placeholder="e.g. 21"
                      className="w-full bg-[#040407] border border-white/[0.08] focus:border-cyan-500/50 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-white focus:outline-none transition-colors"
                    />
                  </div>

                  {editingMapper && (
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase block">Map to New ID</label>
                      <input 
                        type="number"
                        value={mapperNewId}
                        onChange={(e) => setMapperNewId(e.target.value)}
                        placeholder="New ID key"
                        className="w-full bg-[#040407] border border-white/[0.08] focus:border-cyan-500/50 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-white focus:outline-none transition-colors"
                      />
                    </div>
                  )}

                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase block">Acronym / Name Label</label>
                    <input 
                      type="text"
                      value={mapperName}
                      onChange={(e) => setMapperName(e.target.value)}
                      placeholder="e.g. L1P"
                      className="w-full bg-[#040407] border border-white/[0.08] focus:border-cyan-500/50 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-white focus:outline-none transition-colors"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase block">Min Raw Tick</label>
                      <input 
                        type="number"
                        value={mapperMin}
                        onChange={(e) => setMapperMin(parseInt(e.target.value) || 0)}
                        className="w-full bg-[#040407] border border-white/[0.08] focus:border-cyan-500/50 rounded-xl px-3.5 py-2.5 text-xs font-mono font-semibold text-white focus:outline-none transition-colors"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase block">Max Raw Tick</label>
                      <input 
                        type="number"
                        value={mapperMax}
                        onChange={(e) => setMapperMax(parseInt(e.target.value) || 0)}
                        className="w-full bg-[#040407] border border-white/[0.08] focus:border-cyan-500/50 rounded-xl px-3.5 py-2.5 text-xs font-mono font-semibold text-white focus:outline-none transition-colors"
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
                        className="bg-white/[0.08] hover:bg-slate-300 text-zinc-300 font-bold text-xs px-4 py-3 rounded-full flex-1 transition"
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
                      <tr className="border-b border-white/[0.06] text-zinc-500 font-bold uppercase tracking-wider text-[10px]">
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
                          <tr key={mid} className="border-b border-white/[0.06] hover:bg-white/[0.1]/[0.02]">
                            <td className="py-3 px-4 font-mono font-bold">{mid}</td>
                            <td className="py-3 px-4 font-bold text-zinc-200">{info.name}</td>
                            <td className="py-3 px-4 font-mono text-zinc-400">{info.min}</td>
                            <td className="py-3 px-4 font-mono text-zinc-400">{info.max}</td>
                            <td className="py-3 px-4 font-mono text-zinc-400">{info.default}</td>
                            <td className="py-3 px-4 text-center flex justify-center gap-2">
                              <button
                                onClick={() => startEditMapper(mid, info)}
                                className="bg-[#B5ACF3]/10 hover:bg-[#B5ACF3]/25 text-white font-bold px-3 py-1.5 rounded-xl transition"
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
  );
}
