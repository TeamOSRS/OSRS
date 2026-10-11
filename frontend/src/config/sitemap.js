/**
 * OSRS Platform Sitemap & Route Architecture
 * Defines the hierarchical navigation, metadata, and routing structure for the entire application.
 */

export const SITEMAP = [
  // 1. OPERATIONS & SIMULATIONS
  {
    id: "dashboard",
    title: "Operations Dashboard",
    shortTitle: "Dashboard",
    category: "Operations & Simulations",
    path: "/dashboard",
    iconName: "LayoutDashboard",
    description: "Central command center with real-time hardware telemetry, CPU load, actuator statuses, and execution log bus.",
    badge: "Primary Hub",
    breadcrumbs: ["OSRS Command Center", "Dashboard"],
    keywords: ["telemetry", "vitals", "status", "logs", "actuators", "motors", "cpu", "system"],
    status: "online"
  },
  {
    id: "simulations",
    title: "Physics Simulations (MuJoCo)",
    shortTitle: "Simulations",
    category: "Operations & Simulations",
    path: "/simulations",
    iconName: "Atom",
    description: "High-fidelity MuJoCo physics engine lab featuring dual-arm plate balancing, PID benchmarks, and humanoid OP3 manipulation.",
    badge: "MuJoCo 3.0",
    breadcrumbs: ["OSRS Command Center", "Simulations"],
    keywords: ["physics", "mujoco", "simulation", "plate", "benchmark", "op3", "franka", "digital twin"],
    status: "active"
  },
  {
    id: "paper",
    title: "Research Paper & Genesis",
    shortTitle: "Research Paper",
    category: "Operations & Simulations",
    path: "/paper",
    iconName: "FileText",
    description: "Official publication, interactive PDF reader, academic mathematical equations, and origin engineering chronicle.",
    badge: "Academic Paper",
    breadcrumbs: ["OSRS Command Center", "Research Paper"],
    keywords: ["paper", "pdf", "research", "academic", "theory", "genesis", "equations"],
    status: "verified"
  },
  {
    id: "sitemap",
    title: "System Sitemap & Directory",
    shortTitle: "Sitemap",
    category: "Operations & Simulations",
    path: "/sitemap",
    iconName: "Map",
    description: "Architectural overview and visual sitemap of all screens, navigation pathways, APIs, and robotic control modules.",
    badge: "Full Tree",
    breadcrumbs: ["OSRS Command Center", "Sitemap"],
    keywords: ["sitemap", "directory", "navigation", "routes", "index", "structure", "architecture"],
    status: "index"
  },

  // 2. KINEMATICS & CONTROL
  {
    id: "control",
    title: "Visual Structure & Arm Control",
    shortTitle: "Arm Control",
    category: "Kinematics & Control",
    path: "/control",
    iconName: "SlidersHorizontal",
    description: "3D digital twin visualization, wireframe joint coordinate inspection, torque management, and manual angular overrides.",
    badge: "Joint Space",
    breadcrumbs: ["OSRS Command Center", "Arm Control"],
    keywords: ["joints", "digital twin", "kinematics", "torque", "motors", "wireframe", "override", "angles"],
    status: "live"
  },
  {
    id: "emotemaker",
    title: "Emotes & Motion Studio",
    shortTitle: "Emotes & Maker",
    category: "Kinematics & Control",
    path: "/emotemaker",
    iconName: "PlayCircle",
    description: "Preset robot choreography, expressive gesture library, frame-by-frame joint timeline animator, and motion compilation.",
    badge: "Choreography",
    breadcrumbs: ["OSRS Command Center", "Emotes & Maker"],
    keywords: ["emotes", "gestures", "namaste", "animation", "timeline", "choreography", "motion", "maker"],
    status: "ready"
  },
  {
    id: "dataflow",
    title: "ROS Dataflow Node Graph",
    shortTitle: "Dataflow Graph",
    category: "Kinematics & Control",
    path: "/dataflow",
    iconName: "Network",
    description: "Visual node graph mapping active perception, estimation filters, motor drivers, and websocket event buses.",
    badge: "Pipelines",
    breadcrumbs: ["OSRS Command Center", "Dataflow Graph"],
    keywords: ["dataflow", "graph", "nodes", "ros", "events", "bus", "pipeline", "reactive"],
    status: "streaming"
  },

  // 3. RESEARCH & PERCEPTION
  {
    id: "research",
    title: "Ball Balancer Research Suite",
    shortTitle: "Research Balancer",
    category: "Research & Perception",
    path: "/research",
    iconName: "TrendingUp",
    description: "Closed-loop tactile plate balancing laboratory with RealSense optical tracking, HX711 force sensing, and adaptive learning.",
    badge: "Closed-Loop",
    breadcrumbs: ["OSRS Command Center", "Research Balancer"],
    keywords: ["balancer", "pid", "plate", "ball", "realsense", "closed-loop", "loadcell", "force", "tactile"],
    status: "online"
  },
  {
    id: "recording",
    title: "Telemetry Replay & Record",
    shortTitle: "Replay & Record",
    category: "Research & Perception",
    path: "/recording",
    iconName: "History",
    description: "Frame-accurate sensor recording, dataset generation, trajectory exports (JSON/CSV), and physics flight playback.",
    badge: "Telemetry Bus",
    breadcrumbs: ["OSRS Command Center", "Replay & Record"],
    keywords: ["recording", "replay", "telemetry", "datasets", "trajectory", "export", "playback", "log"],
    status: "ready"
  },
  {
    id: "vision",
    title: "Perception & Vision System",
    shortTitle: "Vision System",
    category: "Research & Perception",
    path: "/vision",
    iconName: "Video",
    description: "Multi-camera triangulation, RealSense D415 stream, solvePnP optical calibration, and HSV color thresholding.",
    badge: "RealSense RGB-D",
    breadcrumbs: ["OSRS Command Center", "Vision System"],
    keywords: ["vision", "camera", "realsense", "hsv", "solvepnp", "triangulation", "optical", "tracking"],
    status: "online"
  },

  // 4. DIAGNOSTICS & HARDWARE
  {
    id: "calibration",
    title: "Hardware Calibration Wizard",
    shortTitle: "Calibration",
    category: "Diagnostics & Hardware",
    path: "/calibration",
    iconName: "Wrench",
    description: "Step-by-step actuator zeroing, physical mechanical limits verification, quintic spline path execution, and EEPROM offsets.",
    badge: "Wizard",
    breadcrumbs: ["OSRS Command Center", "Calibration"],
    keywords: ["calibration", "zeroing", "wizard", "offsets", "homing", "limits", "servos"],
    status: "ready"
  },
  {
    id: "mapper",
    title: "CAD ID Joint Mapping Editor",
    shortTitle: "CAD ID Mapper",
    category: "Diagnostics & Hardware",
    path: "/mapper",
    iconName: "Settings",
    description: "Associates CAD SolidWorks mechanical joint definitions with Dynamixel motor IDs, inversion flags, and gear ratios.",
    badge: "Topology",
    breadcrumbs: ["OSRS Command Center", "CAD ID Mapper"],
    keywords: ["cad", "mapping", "topology", "ids", "motors", "solidworks", "joints", "inversion"],
    status: "active"
  },
  {
    id: "diagnostics",
    title: "Hardware Diagnostics & Bus",
    shortTitle: "Diagnostics",
    category: "Diagnostics & Hardware",
    path: "/diagnostics",
    iconName: "Activity",
    description: "Live serial bus bus health, individual servo temperature, input voltage monitoring, packet drop detection, and ping tests.",
    badge: "Health Telemetry",
    breadcrumbs: ["OSRS Command Center", "Diagnostics"],
    keywords: ["diagnostics", "voltage", "temperature", "packets", "health", "ping", "errors", "servos"],
    status: "monitoring"
  },
  {
    id: "manual",
    title: "Product Manual & Guides",
    shortTitle: "Product Manual",
    category: "Diagnostics & Hardware",
    path: "/manual",
    iconName: "BookOpen",
    description: "Complete developer manual, FastAPI backend architecture, MuJoCo physics theory, hotkey index, and troubleshooting.",
    badge: "Documentation",
    breadcrumbs: ["OSRS Command Center", "Product Manual"],
    keywords: ["manual", "docs", "documentation", "guide", "api", "shortcuts", "troubleshooting", "setup"],
    status: "reference"
  },
  {
    id: "about",
    title: "About OSRS Robotics Lab",
    shortTitle: "About Us",
    category: "Diagnostics & Hardware",
    path: "/about",
    iconName: "Info",
    description: "Mission manifesto, hardware compatibility matrix, research laboratory roadmap, and open-source contribution guidelines.",
    badge: "Open Source",
    breadcrumbs: ["OSRS Command Center", "About Us"],
    keywords: ["about", "mission", "team", "license", "open source", "hardware", "contributors"],
    status: "info"
  }
];

export const SITEMAP_CATEGORIES = [
  "Operations & Simulations",
  "Kinematics & Control",
  "Research & Perception",
  "Diagnostics & Hardware"
];

export function getSitemapByCategory() {
  const grouped = {};
  SITEMAP_CATEGORIES.forEach(cat => {
    grouped[cat] = SITEMAP.filter(item => item.category === cat);
  });
  return grouped;
}

export function getScreenMetadata(id) {
  return SITEMAP.find(item => item.id === id) || {
    id,
    title: id ? id.toUpperCase() : "Unknown",
    shortTitle: id,
    category: "General",
    path: `/${id}`,
    iconName: "LayoutDashboard",
    description: "",
    badge: "",
    breadcrumbs: ["OSRS Command Center", id]
  };
}

export function searchSitemap(query) {
  if (!query || !query.trim()) return SITEMAP;
  const q = query.toLowerCase().trim();
  return SITEMAP.filter(item => {
    return (
      item.title.toLowerCase().includes(q) ||
      item.shortTitle.toLowerCase().includes(q) ||
      item.description.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q) ||
      (item.keywords && item.keywords.some(k => k.toLowerCase().includes(q)))
    );
  });
}
