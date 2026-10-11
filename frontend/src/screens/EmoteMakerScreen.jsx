import React, { useState, useEffect } from "react";
import { Eye, Play, Plus, Repeat, Save, Sliders, StopCircle, Trash } from "lucide-react";

/**
 * Emote Maker Screen - Keyframe sequencing, preset library, timeline player
 */
export default function EmoteMakerScreen(props) {
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
              
              {/* Presets Motions card */}
              <div className="obsidian-card p-6 animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
                <h3 className="text-xl font-black text-white mb-4">Preset Robot Expressive Motions</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                  {[
                    { name: "HI Left", color: "text-purple-700 bg-purple-50/50 hover:bg-purple-100 border border-purple-200" },
                    { name: "HI Right", color: "text-purple-700 bg-purple-50/50 hover:bg-purple-100 border border-purple-200" },
                    { name: "Namaste", color: "text-green-800 bg-green-50/50 hover:bg-green-100 border border-green-200" },
                    { name: "Clap", color: "text-fuchsia-800 bg-fuchsia-50/50 hover:bg-fuchsia-100 border border-fuchsia-200" },
                    { name: "Victory", color: "text-amber-800 bg-amber-50/50 hover:bg-amber-100 border border-amber-200" },
                    { name: "Heart", color: "text-red-800 bg-red-50/50 hover:bg-red-100 border border-red-200" },
                    { name: "67", color: "text-zinc-200 bg-white/[0.02] hover:bg-white/[0.1]/[0.04] border border-white/[0.06]" }
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
                            className="p-2 bg-white/[0.04] text-white hover:bg-white/[0.1] border border-white/[0.06] rounded-xl text-[10px] font-black flex items-center justify-center transition"
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
              <div className="obsidian-card p-6 md:p-8 animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 border-b border-white/[0.06] pb-4 gap-4">
                  <div>
                    <h3 className="text-2xl font-black text-white">Custom Emote Maker Sequence</h3>
                    <p className="text-xs text-zinc-400 font-bold mt-0.5">Define poses and steps to create a custom loop. Edits broadcast live frames to the physical arm.</p>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-3">
                    <label className="flex items-center gap-2 obsidian-inset px-4 py-2 rounded-full border border-white/[0.06]">
                      <Repeat className="w-4 h-4 text-zinc-400" />
                      <span className="text-xs font-bold text-zinc-300">Loops</span>
                      <input 
                        type="number" 
                        min="1" 
                        max="100" 
                        value={emoteLoop} 
                        onChange={(e) => setEmoteLoop(parseInt(e.target.value) || 1)}
                        className="w-12 bg-[#040407] border border-white/[0.08] rounded-lg py-1 text-center font-semibold text-white focus:outline-none text-xs"
                      />
                    </label>
                    <label className="flex items-center gap-2 obsidian-inset px-4 py-2 rounded-full border border-white/[0.06]">
                      <Sliders className="w-4 h-4 text-zinc-400" />
                      <span className="text-xs font-bold text-zinc-300">Speed</span>
                      <select 
                        value={emoteSpeed} 
                        onChange={(e) => setEmoteSpeed(parseFloat(e.target.value))}
                        className="bg-[#040407] border border-white/[0.08] rounded-lg py-1 px-2 font-semibold text-white focus:outline-none text-xs cursor-pointer hover:border-slate-350"
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
                      className="px-6 py-2.5 rounded-full text-xs font-bold bg-[#CFFF3E] text-white hover:bg-[#bce634] shadow-md transition flex items-center gap-2"
                    >
                      <Save className="w-4 h-4" /> SAVE EMOTE
                    </button>
                  </div>
                </div>

                <div className="space-y-6">
                  {emoteFrames.map((frame, fidx) => (
                    <div key={fidx} className="obsidian-inset rounded-[28px] p-6 border border-slate-250/50 relative group">
                      <div className="absolute -left-4 -top-4 w-8 h-8 bg-[#0D0E14] border-2 border-white/[0.1] rounded-full text-cyan-400 flex items-center justify-center font-black text-zinc-500 text-xs shadow-md">
                        {fidx + 1}
                      </div>
                      
                      <div className="flex justify-between items-center mb-4 border-b border-white/[0.06] pb-3">
                        <div className="flex items-center gap-6">
                          <div className="flex items-center gap-3">
                            <span className="text-xs font-bold text-zinc-400">Transition Frames:</span>
                            <input 
                              type="number" 
                              value={frame.delay} 
                              onChange={(e) => updateFrameDelay(fidx, e.target.value)}
                              className="w-16 px-3 py-1 rounded-lg border border-slate-350 focus:outline-none font-bold text-xs"
                            />
                          </div>

                          <div className="flex items-center gap-3">
                            <span className="text-xs font-bold text-zinc-400">Hold Frames:</span>
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
                            className="bg-[#B5ACF3]/10 text-white hover:bg-[#B5ACF3]/20 border border-[#B5ACF3]/30 px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition disabled:opacity-40"
                            title="Move robot to this frame pose for layout alignment"
                          >
                            <Eye className="w-3.5 h-3.5" /> PREVIEW ON ROBOT
                          </button>
                        </div>
                        <button 
                          onClick={() => removeEmoteFrame(fidx)}
                          className="p-1.5 rounded-full hover:bg-red-50 text-zinc-500 hover:text-red-500 transition"
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
                            <div key={mid} className="obsidian-inset px-4 py-3 rounded-2xl border border-white/[0.06] shadow-sm">
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-xs font-bold text-zinc-400">{info.name}</span>
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
                                  className="w-14 text-center text-[10px] font-mono font-bold text-white obsidian-inset border border-white/[0.06] rounded-lg py-0.5 focus:outline-none"
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
                    className="w-full py-4 rounded-[24px] border-2 border-dashed border-white/[0.1] text-zinc-400 font-bold hover:border-[#B5ACF3] hover:text-white hover:obsidian-inset transition flex justify-center items-center gap-2"
                  >
                    <Plus className="w-4 h-4" /> ADD SEQUENCE FRAME
                  </button>
                </div>
              </div>

              {/* Saved Custom Emotes List */}
              <div className="obsidian-card p-6 md:p-8 animate-fluid space-y-6 border border-white/[0.08] shadow-2xl">
                <h3 className="text-xl font-black text-white mb-4">Saved Custom Emotes</h3>
                {Object.keys(savedEmotes).length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(savedEmotes).map(([name, frames]) => {
                      const isPlaying = playingPreset === name;
                      return (
                        <div key={name} className="obsidian-inset p-5 rounded-[24px] border border-white/[0.06] flex flex-col justify-between gap-4">
                          <div>
                            <span className="font-extrabold text-base text-white block truncate">{name}</span>
                            <span className="text-[10px] bg-slate-250 text-zinc-400 font-bold px-2 py-0.5 rounded-full inline-block mt-1">
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
                              className="px-3 py-2 bg-white/[0.04] text-zinc-300 hover:bg-white/[0.1]/[0.08] rounded-xl transition font-bold text-xs flex items-center justify-center gap-1"
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
                  <div className="text-zinc-500 text-center py-12 italic text-xs">
                    No custom emotes saved yet. Build a sequence above and click "Save Emote".
                  </div>
                )}
              </div>
            </div>
  );
}
