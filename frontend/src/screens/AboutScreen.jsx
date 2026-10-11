import React, { useState, useEffect } from "react";
import { Globe, Bot, FileText, Shield } from "lucide-react";

/**
 * About Screen - System specs, open-source architecture, team and project credits
 */
export default function AboutScreen(props) {
  // Destructure shared state and actions with safe defaults
  const {
    // Hardware & Connection
    connected = false,
    connPort = "COM9",
    setConnPort = () => { },
    connBaud = 1000000,
    setConnBaud = () => { },
    connMock = false,
    setConnMock = () => { },
    triggerConnect = () => { },
    triggerDisconnect = () => { },
    toggleEstop = () => { },
    estopActive = false,
    handVersion = "Humanoid V1",
    setHandVersion = () => { },
    BAUDRATE_OPTIONS = [
      { value: 4000000, label: "4M bps" },
      { value: 1000000, label: "1M bps" },
      { value: 115200, label: "115200 bps" },
      { value: 57600, label: "57600 bps" }
    ],
    showBaudDropdownDashboard = false,
    setShowBaudDropdownDashboard = () => { },

    // UI Routing & Banners
    activeTab = "",
    setActiveTab = () => { },
    alertBanner = null,
    setAlertBanner = () => { },

    // Telemetry & Logs
    telemetry = {},
    limits = {},
    logs = [],
    clearOffset = 0,
    setClearOffset = () => { },
    pauseLogs = false,
    setPauseLogs = () => { },
    handleCopyLogs = () => { },
    handleClearLogs = () => { },
    rebootMotor = () => { },
    toggleTorqueGlobal = () => { },
    toggleTorqueIndividual = () => { },
    isAnyTorqueActive = false,

    // Positions & Joints
    positions = {},
    handlePositionChange = () => { },
    sendZeroPose = () => { },
    selectedJoint = null,
    setSelectedJoint = () => { },
    handleJointClick = () => { },
    handleSendCommand = () => { },
    rotateJointByDeg = () => { },
    expandedSections = { leftArm: true, rightArm: true, head: true },
    setExpandedSections = () => { },

    // Emotes
    savedEmotes = [],
    fetchCustomEmotes = () => { },
    emoteFrames = [],
    setEmoteFrames = () => { },
    activeFrameIdx = 0,
    setActiveFrameIdx = () => { },
    newEmoteName = "",
    setNewEmoteName = () => { },
    emoteSpeed = 1,
    setEmoteSpeed = () => { },
    emoteLoop = false,
    setEmoteLoop = () => { },
    showSaveModal = false,
    setShowSaveModal = () => { },
    playingPreset = null,
    playPresetEmote = () => { },
    loadPresetEmoteIntoMaker = () => { },
    loadSavedEmoteIntoMaker = () => { },
    playCustomEmote = () => { },
    playSavedCustomEmote = () => { },
    handleDeleteCustomEmote = () => { },
    handleSaveCustomEmote = () => { },
    addEmoteFrame = () => { },
    removeEmoteFrame = () => { },
    previewFrame = () => { },
    updateFrameDelay = () => { },
    updateFrameHold = () => { },
    PRESET_EMOTE_FRAMES = {},

    // Calibration Wizard State
    calibrationStep = 1,
    setCalibrationStep = () => { },
    calibJoint = "L1P",
    setCalibJoint = () => { },
    calibZero = 2048,
    setCalibZero = () => { },
    calibMin = 1000,
    setCalibMin = () => { },
    calibMax = 3000,
    setCalibMax = () => { },
    calibDirection = 1,
    setCalibDirection = () => { },
    calibSpeed = 50,
    setCalibSpeed = () => { },
    isCalibrating = false,
    setIsCalibrating = () => { },
    calibrationProgress = 0,
    setCalibrationProgress = () => { },
    handleSaveCalibration = () => { },
    handleResetCalibration = () => { },
    handleRunAutoCalibration = () => { },

    // CAD Mapper State
    cadMappings = {},
    setCadMappings = () => { },
    cadSearchQuery = "",
    setCadSearchQuery = () => { },
    selectedCadServo = null,
    setSelectedCadServo = () => { },
    handleAssignCadId = () => { },
    handleAutoDetectCadServos = () => { },
    handleExportCadMapping = () => { },
    handleImportCadMapping = () => { },

    // Vision Pipeline State
    visionStreaming = false,
    setVisionStreaming = () => { },
    visionModel = "MediaPipe Holistic",
    setVisionModel = () => { },
    confidenceThreshold = 0.75,
    setConfidenceThreshold = () => { },
    detectedKeypoints = [],
    selectedCamera = 0,
    setSelectedCamera = () => { },
    availableCameras = ["Camera 0 (Default HD)", "Camera 1 (Depth Sensor)"],
    handTrackingActive = true,
    setHandTrackingActive = () => { },
    poseTrackingActive = true,
    setPoseTrackingActive = () => { },

    // Live Diagnostics State
    diagFilter = "all",
    setDiagFilter = () => { },
    diagTimeRange = "5m",
    setDiagTimeRange = () => { },
    pingLatency = 4.2,
    packetLoss = 0.0,
    busVoltage = 24.1,
    busCurrent = 0.85,
    ambientTemp = 28.4,
    mcuTemp = 41.2,
    oscilloscopeData = [],
    diagnosticTestsRunning = false,
    handleRunDiagnosticSelfTest = () => { },
    connSpeedLimit = 100,
    setConnSpeedLimit = () => { },

    // Product Manual State
    manualSearch = "",
    setManualSearch = () => { },
    activeManualTopic = "quickstart",
    setActiveManualTopic = () => { },
    setShowShortcutHelp = () => { },

    // System Stats & Extra Callbacks
    systemStats = { cpu: 14, ram: 38, fps: 60, status: "NOMINAL" },
    onNavigateToSimulations = () => { },
    onNavigateToPaper = () => { },
  } = props;


  return (
    <div className="space-y-6 animate-fade-in">
      {/* About Us Hero Banner */}
      <div className="relative overflow-hidden rounded-[32px] bg-gradient-to-r from-[#000000] via-[#0D0F14] to-white/[0.04] p-6 md:p-8 border border-white/[0.08] shadow-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_120%,rgba(16,185,129,0.06),transparent_50%)]" />
        <div className="relative z-10">
          <span className="text-[10px] uppercase font-black tracking-widest text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">OSRS Team</span>
          <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight mt-3">About OSRS</h2>
          <p className="text-zinc-400 text-xs font-semibold mt-2 max-w-xl leading-relaxed">
            Open Source Robotics System (OSRS) is an advanced web-integrated dashboard designed for controlling, visualising, and calibrating high-degree-of-freedom robotic systems. Built as a modular workspace, it bridges kinematics simulation, serial bus telemetry, custom emote making, and computer vision hand tracking.
          </p>
        </div>
      </div>

      {/* The Builders Grid */}
      <div className="space-y-4">
        <h3 className="text-base font-black text-white uppercase tracking-wider px-2">Project Builders</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          {/* Aditya Jadav */}
          <div className="obsidian-card backdrop-blur-md rounded-3xl p-6 border border-white/[0.06] shadow-md flex flex-col justify-between hover:scale-[1.02] active:scale-[0.99] transition-all duration-300">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-[#040407] text-zinc-200 flex items-center justify-center font-black text-base shadow-md mb-4">
                AJ
              </div>
              <h4 className="text-lg font-black text-white">Aditya Jadav</h4>
            </div>
            <a
              href="https://github.com/adityajadav203-cpu"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-[#040407] hover:bg-[#12141A] text-zinc-200 font-bold text-[11px] uppercase tracking-wider py-3 px-4 rounded-full inline-flex items-center justify-center gap-2 mt-6 transition-colors shadow-sm"
            >
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
              <span>GitHub Profile</span>
            </a>
          </div>

          {/* Archie Veera */}
          <div className="obsidian-card backdrop-blur-md rounded-3xl p-6 border border-white/[0.06] shadow-md flex flex-col justify-between hover:scale-[1.02] active:scale-[0.99] transition-all duration-300">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-[#040407] text-zinc-200 flex items-center justify-center font-black text-base shadow-md mb-4">
                AV
              </div>
              <h4 className="text-lg font-black text-white">Archie Veera</h4>
            </div>
            <a
              href="https://github.com/archieveera04-del"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-[#040407] hover:bg-[#12141A] text-zinc-200 font-bold text-[11px] uppercase tracking-wider py-3 px-4 rounded-full inline-flex items-center justify-center gap-2 mt-6 transition-colors shadow-sm"
            >
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
              <span>GitHub Profile</span>
            </a>
          </div>

          {/* Bilal Sabugar */}
          <div className="obsidian-card backdrop-blur-md rounded-3xl p-6 border border-white/[0.06] shadow-md flex flex-col justify-between hover:scale-[1.02] active:scale-[0.99] transition-all duration-300">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-[#040407] text-zinc-200 flex items-center justify-center font-black text-base shadow-md mb-4">
                BS
              </div>
              <h4 className="text-lg font-black text-white">Bilal Sabugar</h4>
            </div>
            <a
              href="https://github.com/BilalSabugar"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-[#040407] hover:bg-[#12141A] text-zinc-200 font-bold text-[11px] uppercase tracking-wider py-3 px-4 rounded-full inline-flex items-center justify-center gap-2 mt-6 transition-colors shadow-sm"
            >
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
              <span>GitHub Profile</span>
            </a>
          </div>

        </div>
      </div>

      {/* AI-Assisted Development & Open Source Card */}
      <div className="relative overflow-hidden bg-gradient-to-r from-[#000000] via-[#0D0F14] to-white/[0.04] p-6 md:p-8 border border-white/[0.08] shadow-2xl rounded-3xl flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 mt-6">
        <div className="relative z-10">
          <div className="flex items-center gap-2 text-zinc-200 font-bold text-xs uppercase tracking-widest">
            <Bot className="h-4 w-4 text-sky-400" />
            <span>AI-Assisted Engineering Workflow</span>
          </div>
          <h3 className="text-xl font-black text-white mt-1.5">AI Collaboration & Research Notice</h3>
          <p className="text-zinc-400 mt-1 text-xs font-semibold max-w-2xl leading-relaxed">
            This project was built using AI-assisted programming workflows. Artificial Intelligence was leveraged to accelerate theoretical modeling, state-space derivations, component modularization, physics MJCF definitions, and automated verification, under continuous human engineering direction and hardware safety validation.
          </p>
        </div>
        <div className="relative z-10 w-full lg:w-auto flex flex-wrap items-center gap-3">
          <a
            href="https://github.com/BilalSabugar/OSRS/blob/main/AI_DISCLOSURE.md"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white/10 hover:bg-white/[0.1]/20 text-zinc-200 px-5 py-3 rounded-xl text-xs font-bold tracking-wider transition-all uppercase border border-white/10 inline-flex items-center gap-2"
          >
            <FileText className="w-4 h-4" />
            <span>AI Disclosure</span>
          </a>
          <a
            href="https://github.com/BilalSabugar/OSRS/blob/main/LICENSE"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white/10 hover:bg-white/[0.1]/20 text-zinc-200 px-5 py-3 rounded-xl text-xs font-bold tracking-wider transition-all uppercase border border-white/10 inline-flex items-center gap-2"
          >
            <Shield className="w-4 h-4" />
            <span>MIT License</span>
          </a>
        </div>
      </div>

      {/* Project Repo Card */}
      <div className="relative overflow-hidden bg-gradient-to-r from-[#090A0E] via-[#0E1017] to-[#12151E] p-6 md:p-8 border border-white/[0.08] shadow-2xl rounded-3xl flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 mt-8">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-emerald-500/5 to-transparent animate-pulse" />
        <div className="relative z-10">
          <div className="flex items-center gap-2 text-zinc-200 font-bold text-xs uppercase tracking-widest">
            <Globe className="h-4 w-4" />
            <span>Open Source Source Code</span>
          </div>
          <h3 className="text-xl font-black text-white mt-1.5">Official Repository</h3>
          <p className="text-zinc-400 mt-1 text-xs font-semibold">Explore the source files, submit issues, propose pull requests, and deploy custom instances of OSRS.</p>
        </div>
        <div className="relative z-10 w-full lg:w-auto flex items-center gap-3">
          <a
            href="https://github.com/BilalSabugar/OSRS"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full lg:w-auto bg-black text-black hover:bg-white/[0.1] text-black/90 active:scale-[0.98] text-white px-6 py-3.5 rounded-xl text-xs font-extrabold tracking-wider transition-all uppercase shadow-lg inline-flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            <span>Go To Repository</span>
          </a>
        </div>
      </div>
    </div>
  );
}
