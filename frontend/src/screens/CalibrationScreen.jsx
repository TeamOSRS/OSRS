import React, { useState, useEffect } from "react";
import { AlertTriangle, Settings, Wrench } from "lucide-react";

/**
 * Calibration Screen - Guided joint zero-point and limits calibration wizard
 */
export default function CalibrationScreen(props) {
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
            <div className="space-y-8 max-w-3xl mx-auto animate-fade-in">
              {/* Wizard Card */}
              <div className="obsidian-card p-6 md:p-8 animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
                <div className="flex items-center gap-3 border-b border-white/[0.06] pb-4 mb-6">
                  <Wrench className="h-6 w-6 text-white" />
                  <h3 className="text-2xl font-black text-white">Calibration Wizard</h3>
                </div>
                
                <p className="text-xs text-zinc-400 font-bold mb-8 leading-relaxed">
                  Calibration calculates individual actuator endpoints and maps absolute zero coordinates. The wizard uses quintic polynomial path generation to smoothly shift joints, detecting mechanical cable binding or thermal obstructions.
                </p>

                <div className="obsidian-inset p-6 border border-white/[0.06] rounded-2xl mb-8 space-y-6">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black text-zinc-400 uppercase">Operational Status</span>
                    <span className={`text-xs font-black px-3 py-1 rounded-full ${
                      calibrationState.running 
                        ? (calibrationState.paused ? "bg-amber-100 text-amber-700 animate-pulse" : "bg-blue-100 text-blue-750 animate-pulse") 
                        : "bg-white/[0.08] text-zinc-300"
                    }`}>
                      {calibrationState.status_msg}
                    </span>
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs font-bold text-zinc-500">
                      <span>Task Progress</span>
                      <span>{Math.round(calibrationState.progress * 100)}%</span>
                    </div>
                    <div className="w-full bg-white/[0.08] rounded-full h-3 overflow-hidden shadow-inner">
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
                        className="bg-[#CFFF3E] hover:bg-[#bce634] text-white font-black text-xs px-8 py-3.5 rounded-full transition disabled:opacity-40"
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
                        className="bg-white/[0.04] hover:bg-white/[0.1]/[0.08] text-zinc-300 font-bold text-xs px-6 py-2.5 rounded-full border border-white/[0.06] transition"
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
              <div className="obsidian-card p-6 md:p-8 animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-white/[0.06] pb-4 mb-6 gap-4">
                  <div className="flex items-center gap-3">
                    <Wrench className="h-6 w-6 text-white" />
                    <h3 className="text-2xl font-black text-white">Physical Arm Calibration Wizard</h3>
                  </div>
                  
                  <button
                    onClick={handleSaveCalibration}
                    disabled={!connected}
                    className="bg-[#CFFF3E] hover:bg-[#bce634] text-white font-black text-xs px-6 py-2.5 rounded-full transition disabled:opacity-40 self-start sm:self-auto"
                  >
                    SAVE CALIBRATION TO FILE
                  </button>
                </div>

                <p className="text-xs text-zinc-400 font-bold mb-8 leading-relaxed">
                  Power on torques, physically position the arms to their neutral straight poses, capture calibration offsets, and click "Save Calibration to File".
                </p>

                {/* Arm Panels Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Left Arm Calibration Card */}
                  <div className="bg-white/[0.02] p-5 rounded-[24px] border border-white/[0.06] flex flex-col gap-4">
                    <div className="flex justify-between items-center border-b border-white/[0.06]/65 pb-3">
                      <span className="text-white font-black text-sm uppercase tracking-wide">Left Arm Calibration</span>
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
                          className="px-2.5 py-1 bg-white/[0.08] text-white border border-slate-350 rounded-lg text-[9px] font-black uppercase hover:bg-slate-300 transition disabled:opacity-40"
                        >
                          Capture
                        </button>
                      </div>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-white/[0.06] text-zinc-500 font-bold uppercase tracking-wider text-[9px]">
                            <th className="py-2 font-semibold">Joint</th>
                            <th className="py-2 font-semibold text-center">ID</th>
                            <th className="py-2 font-semibold text-center">Live Position</th>
                            <th className="py-2 font-semibold text-center">Calibrated Center</th>
                            <th className="py-2 font-semibold text-center">Torque</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200/60 text-zinc-300">
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
                              <tr key={mid} className="hover:bg-white/[0.1]/[0.04]/40">
                                <td className="py-2 text-white font-extrabold">{jointName}</td>
                                <td className="py-2 text-center text-zinc-500 font-mono">{mid}</td>
                                <td className={`py-2 text-center font-mono font-bold ${livePos === "--" ? "text-zinc-500" : "text-white"}`}>
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
                                    className="w-16 text-center font-mono font-bold text-blue-605 bg-slate-150/40 border border-white/[0.06] rounded py-0.5 focus:outline-none focus:ring-1 focus:ring-[#B5ACF3]"
                                  />
                                </td>
                                <td className="py-2 text-center">
                                  <button
                                    onClick={() => toggleTorqueIndividual(mid, !isTorqueOn)}
                                    disabled={!connected}
                                    className={`px-2 py-0.5 text-[9px] font-bold uppercase rounded border transition ${
                                      isTorqueOn
                                        ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                                        : "bg-white/[0.04] text-zinc-500 border-white/[0.06]"
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
                  <div className="bg-white/[0.02] p-5 rounded-[24px] border border-white/[0.06] flex flex-col gap-4">
                    <div className="flex justify-between items-center border-b border-white/[0.06]/65 pb-3">
                      <span className="text-white font-black text-sm uppercase tracking-wide">Right Arm Calibration</span>
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
                          className="px-2.5 py-1 bg-white/[0.08] text-white border border-slate-350 rounded-lg text-[9px] font-black uppercase hover:bg-slate-300 transition disabled:opacity-40"
                        >
                          Capture
                        </button>
                      </div>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-white/[0.06] text-zinc-500 font-bold uppercase tracking-wider text-[9px]">
                            <th className="py-2 font-semibold">Joint</th>
                            <th className="py-2 font-semibold text-center">ID</th>
                            <th className="py-2 font-semibold text-center">Live Position</th>
                            <th className="py-2 font-semibold text-center">Calibrated Center</th>
                            <th className="py-2 font-semibold text-center">Torque</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200/60 text-zinc-300">
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
                              <tr key={mid} className="hover:bg-white/[0.1]/[0.04]/40">
                                <td className="py-2 text-white font-extrabold">{jointName}</td>
                                <td className="py-2 text-center text-zinc-500 font-mono">{mid}</td>
                                <td className={`py-2 text-center font-mono font-bold ${livePos === "--" ? "text-zinc-500" : "text-white"}`}>
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
                                    className="w-16 text-center font-mono font-bold text-blue-605 bg-slate-150/40 border border-white/[0.06] rounded py-0.5 focus:outline-none focus:ring-1 focus:ring-[#B5ACF3]"
                                  />
                                </td>
                                <td className="py-2 text-center">
                                  <button
                                    onClick={() => toggleTorqueIndividual(mid, !isTorqueOn)}
                                    disabled={!connected}
                                    className={`px-2 py-0.5 text-[9px] font-bold uppercase rounded border transition ${
                                      isTorqueOn
                                        ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                                        : "bg-white/[0.04] text-zinc-500 border-white/[0.06]"
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
              <div className="obsidian-card p-6 md:p-8 animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-white/[0.06] pb-4 mb-6 gap-4">
                  <div className="flex items-center gap-3">
                    <Settings className="h-6 w-6 text-white" />
                    <h3 className="text-2xl font-black text-white">Base Frame Configurator</h3>
                  </div>
                  
                  <button
                    onClick={handleGoToBase}
                    disabled={!connected}
                    className="bg-[#1E2022] hover:bg-black text-white font-bold text-xs px-6 py-2.5 rounded-full transition disabled:opacity-40 self-start sm:self-auto"
                  >
                    GO TO BASE FRAME
                  </button>
                </div>

                <p className="text-xs text-zinc-400 font-bold mb-6 leading-relaxed">
                  Set the absolute tick values for your calibrated base frame. Read the live servo tick values, enter your custom baseline targets, and click "Save Base Frame Configurations" to persist them.
                </p>

                {Object.keys(limits).length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-white/[0.06] text-zinc-400 text-[10px] font-black uppercase tracking-wider">
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
                            <tr key={mid} className="hover:bg-white/[0.1]/[0.02]">
                              <td className="py-3.5 px-4 font-bold text-white">{info.name}</td>
                              <td className="py-3.5 px-4 font-mono text-zinc-400">ID {mid}</td>
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
                                  className="w-24 obsidian-inset border border-white/[0.06] rounded-lg px-2.5 py-1 font-mono font-bold text-white focus:outline-none focus:border-[#1E2022]"
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
                                  className="text-[10px] bg-white/[0.04] hover:bg-white/[0.1]/[0.08] text-zinc-300 font-bold px-3 py-1 rounded transition disabled:opacity-40"
                                >
                                  Use Live Position
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>

                    <div className="flex justify-end mt-6 pt-4 border-t border-white/[0.06]">
                      <button
                        onClick={handleSaveBaseFrame}
                        className="bg-[#CFFF3E] hover:bg-[#bce634] text-white font-black text-xs px-8 py-3.5 rounded-full transition"
                      >
                        SAVE BASE FRAME CONFIGURATIONS
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-zinc-500 italic text-xs">
                    Please connect robot/simulator to load motor mapping.
                  </div>
                )}
              </div>
            </div>
  );
}
