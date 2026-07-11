import React, { useEffect, useState, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { Cpu, Activity } from "lucide-react";

export default function DigitalTwinViewer({ joints, activeRobot, syncMode, onSyncModeChange }) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const robotGroupRef = useRef(null);
  const parsedJointsRef = useRef({});
  const [robotDesc, setRobotDesc] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState("Initializing...");

  // 1. Fetch Robot Description when active profile changes
  useEffect(() => {
    setLoadingStatus("Fetching description...");
    const origin = window.location.origin.includes("3000") || window.location.origin.includes("5173")
      ? "http://localhost:8000"
      : window.location.origin;

    fetch(`${origin}/api/robot/description`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load robot description");
        return res.json();
      })
      .then((data) => {
        setRobotDesc(data);
        setLoadingStatus("Ready");
      })
      .catch((err) => {
        console.error(err);
        setLoadingStatus(`Error: ${err.message}`);
      });
  }, [activeRobot]);

  // 2. Initialize Three.js Scene, Camera, Lights, OrbitControls
  useEffect(() => {
    if (!mountRef.current) return;
    
    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x131416); // Match UI theme
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0.9, 0.8, 1.3);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    mountRef.current.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.1; // Stay above grid
    controls.minDistance = 0.1;
    controls.maxDistance = 5;

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.25);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.85);
    dirLight1.position.set(2, 4, 3);
    dirLight1.castShadow = true;
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xb5acf3, 0.35);
    dirLight2.position.set(-2, 2, -3);
    scene.add(dirLight2);

    // Neon Ground Grid
    const gridHelper = new THREE.GridHelper(4, 40, 0xcfff3e, 0x222427);
    gridHelper.position.y = -0.3;
    scene.add(gridHelper);

    // Robot parent group (Z-up orientation offset helper)
    const robotGroup = new THREE.Group();
    // Rotate to match MuJoCo coordinates (+Z is up, +X is forward)
    robotGroup.rotation.x = -Math.PI / 2; 
    robotGroup.position.y = -0.3; // Offset to sit on grid
    scene.add(robotGroup);
    robotGroupRef.current = robotGroup;

    let animationFrameId;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!mountRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
    };
  }, []);

  // 3. Dynamic XML Asset Loader
  useEffect(() => {
    if (!robotGroupRef.current || !sceneRef.current) return;

    // Clear existing meshes
    while (robotGroupRef.current.children.length > 0) {
      robotGroupRef.current.remove(robotGroupRef.current.children[0]);
    }
    parsedJointsRef.current = {};

    if (!robotDesc) return;

    const visual = robotDesc.visual_model;
    if (visual.asset_type === "MJCF" && visual.path) {
      setLoadingStatus("Loading MJCF Asset...");
      const origin = window.location.origin.includes("3000") || window.location.origin.includes("5173")
        ? "http://localhost:8000"
        : window.location.origin;

      fetch(`${origin}/api/robot/asset?path=${visual.path}`)
        .then((res) => {
          if (!res.ok) throw new Error(`Failed to load asset file: ${visual.path}`);
          return res.text();
        })
        .then((xmlText) => {
          setLoadingStatus("Parsing MJCF structure...");
          const parser = new DOMParser();
          const xmlDoc = parser.parseFromString(xmlText, "text/xml");
          const worldbody = xmlDoc.getElementsByTagName("worldbody")[0];
          
          if (!worldbody) {
            throw new Error("No <worldbody> tag found in MJCF scene.");
          }

          const jointMap = {};
          // Recursively traverse child bodies of worldbody
          const firstBodies = worldbody.children;
          Array.from(firstBodies).forEach((node) => {
            if (node.nodeName === "body") {
              parseMjcfBody(node, robotGroupRef.current, jointMap);
            }
          });

          parsedJointsRef.current = jointMap;
          setLoadingStatus("Ready");
        })
        .catch((err) => {
          console.error(err);
          setLoadingStatus(`Error: ${err.message}`);
          // Load fallback placeholder
          renderFallbackPlaceholder();
        });
    } else {
      // Fallback procedural visual representations for other profiles
      renderFallbackPlaceholder();
    }
  }, [robotDesc]);

  // Recursively parses MJCF xml body tags
  function parseMjcfBody(bodyNode, parentTHREEGroup, jointMap) {
    const name = bodyNode.getAttribute("name") || "";
    const group = new THREE.Group();
    group.name = name;

    // Translation pos
    const posStr = bodyNode.getAttribute("pos");
    if (posStr) {
      const [x, y, z] = posStr.split(" ").map(Number);
      group.position.set(x, y, z);
    }

    // Rotation quat (w, x, y, z)
    const quatStr = bodyNode.getAttribute("quat");
    if (quatStr) {
      const [qw, qx, qy, qz] = quatStr.split(" ").map(Number);
      // Three.js Quaternion is constructed (x, y, z, w)
      group.quaternion.set(qx, qy, qz, qw);
    }

    // Direct geoms
    Array.from(bodyNode.children).forEach((child) => {
      if (child.nodeName !== "geom") return;
      
      const type = child.getAttribute("type") || "sphere";
      const sizeStr = child.getAttribute("size") || "0.05";
      const size = sizeStr.split(" ").map(Number);
      const geomPosStr = child.getAttribute("pos");
      const geomQuatStr = child.getAttribute("quat");
      const material = child.getAttribute("material") || "";

      // Map materials to standard color presets
      let color = 0x6e7681;
      let opacity = 1.0;
      let transparent = false;
      let roughness = 0.5;
      let metalness = 0.0;

      if (material.includes("white")) {
        color = 0xf6f8fa;
        roughness = 0.3;
      } else if (material.includes("metal") || material.includes("silver")) {
        color = 0xd0d7de;
        metalness = 0.85;
        roughness = 0.2;
      } else if (material.includes("motor") || material.includes("black")) {
        color = 0x21262d;
        roughness = 0.65;
      } else if (material.includes("rubber")) {
        color = 0x161b22;
        roughness = 0.9;
      } else if (material.includes("glass") || material.includes("acrylic")) {
        color = 0xc9d1d9;
        opacity = 0.3;
        transparent = true;
        roughness = 0.1;
      } else if (material.includes("face") || material.includes("screen")) {
        color = 0x090c10;
        roughness = 0.1;
      }

      const mat = new THREE.MeshStandardMaterial({
        color,
        roughness,
        metalness,
        opacity,
        transparent
      });

      let mesh;
      if (type === "box") {
        // MuJoCo uses half-sizes
        const w = (size[0] || 0.05) * 2;
        const h = (size[1] || 0.05) * 2;
        const d = (size[2] || 0.05) * 2;
        mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
      } else if (type === "cylinder") {
        const r = size[0] || 0.05;
        const halfH = size[1] || 0.05;
        // In Three.js, Cylinder is along Y. In MuJoCo, cylinder defaults to Z-aligned.
        mesh = new THREE.Mesh(new THREE.CylinderGeometry(r, r, halfH * 2, 16), mat);
        mesh.rotation.x = Math.PI / 2; // Align to MuJoCo coordinate frame orientation
      } else if (type === "sphere") {
        const r = size[0] || 0.05;
        mesh = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 16), mat);
      } else if (type === "ellipsoid") {
        mesh = new THREE.Mesh(new THREE.SphereGeometry(1.0, 16, 16), mat);
        mesh.scale.set(size[0] || 0.05, size[1] || 0.05, size[2] || 0.05);
      } else {
        // Fallback Sphere
        const r = size[0] || 0.05;
        mesh = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 16), mat);
      }

      if (mesh) {
        if (geomPosStr) {
          const [gx, gy, gz] = geomPosStr.split(" ").map(Number);
          mesh.position.set(gx, gy, gz);
        }
        if (geomQuatStr) {
          const [gqw, gqx, gqy, gqz] = geomQuatStr.split(" ").map(Number);
          const q = new THREE.Quaternion(gqx, gqy, gqz, gqw);
          mesh.quaternion.premultiply(q);
        }
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        group.add(mesh);
      }
    });

    // Extract joint definitions
    Array.from(bodyNode.children).forEach((child) => {
      if (child.nodeName !== "joint") return;
      
      const jointName = child.getAttribute("name");
      const axisStr = child.getAttribute("axis") || "0 0 1";
      const axis = axisStr.split(" ").map(Number);
      
      if (jointName) {
        jointMap[jointName] = {
          group: group,
          axis: new THREE.Vector3(...axis).normalize(),
          initialQuaternion: group.quaternion.clone()
        };
      }
    });

    parentTHREEGroup.add(group);

    // Recursively parse child bodies
    Array.from(bodyNode.children).forEach((child) => {
      if (child.nodeName === "body") {
        parseMjcfBody(child, group, jointMap);
      }
    });
  }

  // Renders a generic visual representation for the robots that are not loaded via asset files
  function renderFallbackPlaceholder() {
    const parent = robotGroupRef.current;
    const bodyMat = new THREE.MeshStandardMaterial({ color: 0x1f2226, roughness: 0.5 });
    const accentMat = new THREE.MeshStandardMaterial({ color: 0xcfff3e });

    if (activeRobot === "Open Manipulator X") {
      const base = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.07, 0.05, 16), bodyMat);
      parent.add(base);

      const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.3, 16), bodyMat);
      arm.position.set(0, 0, 0.15);
      arm.rotation.x = Math.PI / 2;
      parent.add(arm);

      const claw = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.02, 0.06), accentMat);
      claw.position.set(0, 0, 0.32);
      parent.add(claw);
    } else if (activeRobot === "Rover Bot") {
      const chassis = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.06, 0.3), bodyMat);
      chassis.position.set(0, 0, 0.08);
      parent.add(chassis);

      // Wheels
      for (let side = -1; side <= 1; side += 2) {
        for (let idx = -1; idx <= 1; idx++) {
          const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.03, 16), accentMat);
          wheel.position.set(side * 0.12, idx * 0.11, 0.05);
          wheel.rotation.z = Math.PI / 2;
          parent.add(wheel);
        }
      }
    } else {
      // Leap Hand / generic
      const palm = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.02, 0.1), bodyMat);
      palm.position.set(0, 0, 0.01);
      parent.add(palm);

      for (let i = 0; i < 4; i++) {
        const finger = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.08, 12), accentMat);
        finger.position.set(-0.045 + i * 0.03, 0.04, 0.02);
        finger.rotation.x = Math.PI / 2;
        parent.add(finger);
      }
    }
  }

  // 4. Update joint rotations in real time from joints telemetry data
  useEffect(() => {
    if (Object.keys(joints).length === 0) return;

    if (robotDesc && robotDesc.visual_model.asset_type === "MJCF") {
      Object.entries(parsedJointsRef.current).forEach(([jointName, jointInfo]) => {
        let rad = 0.0;

        // Try direct lookup (simulation/hybrid mode serves jointNames directly)
        if (joints[jointName] !== undefined) {
          const rawVal = joints[jointName];
          rad = typeof rawVal === "object" ? (rawVal.present ?? 0) : rawVal;
        } 
        // Fallback: look up by Dynamixel motor ID using RobotDescription joints map
        else if (robotDesc.joints) {
          const jMeta = robotDesc.joints.find((j) => j.name === jointName);
          if (jMeta) {
            const motorIdStr = String(jMeta.id);
            const valObj = joints[motorIdStr];
            if (valObj !== undefined) {
              const tick = typeof valObj === "object" ? (valObj.present ?? jMeta.default_val) : valObj;
              // Conversion: (ticks - default) / 2048 * PI
              const defaultTick = jMeta.default_val;
              rad = ((tick - defaultTick) / 2048.0) * Math.PI;
            }
          }
        }

        // Apply relative rotation along rotation axis
        const targetQuat = jointInfo.initialQuaternion.clone();
        const axisRotation = new THREE.Quaternion().setFromAxisAngle(jointInfo.axis, rad);
        targetQuat.multiply(axisRotation);
        jointInfo.group.quaternion.copy(targetQuat);
      });
    }
  }, [joints, robotDesc]);

  return (
    <div className="relative w-full h-full min-h-[350px] bg-[#131416] rounded-xl border border-slate-800 overflow-hidden flex flex-col">
      {/* 3D Canvas */}
      <div ref={mountRef} className="w-full h-full flex-grow" />

      {/* Asset Loading Status & Info Overlay */}
      <div className="absolute top-3 left-3 bg-[#191a1b]/85 backdrop-blur-md px-3.5 py-2.5 rounded-lg border border-slate-700/50 flex flex-col gap-1.5 z-10 text-[10px] text-slate-300 font-sans shadow-md">
        <div className="flex items-center gap-1.5 text-[#CFFF3E] font-semibold tracking-wider uppercase">
          <Cpu className="h-3.5 w-3.5" />
          <span>Digital Twin Viewer</span>
        </div>
        <div className="flex flex-col gap-0.5 mt-1">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Target Model:</span>
            <span className="text-white font-medium">{activeRobot}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Loading State:</span>
            <span className={`font-semibold ${loadingStatus.includes("Error") ? "text-red-400" : "text-[#CFFF3E]"}`}>
              {loadingStatus}
            </span>
          </div>
        </div>
      </div>

      {/* Sync Mode Switcher */}
      <div className="absolute bottom-3 right-3 bg-[#191a1b]/85 backdrop-blur-md p-1.5 rounded-lg border border-slate-700/50 flex items-center gap-1.5 z-10 shadow-md">
        {["hardware", "simulation", "hybrid"].map((mode) => (
          <button
            key={mode}
            onClick={() => onSyncModeChange(mode)}
            className={`px-3 py-1 rounded text-[9px] font-bold uppercase tracking-wider transition ${
              syncMode === mode
                ? "bg-[#CFFF3E] text-slate-900 shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {mode}
          </button>
        ))}
      </div>
    </div>
  );
}
