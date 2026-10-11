import React from "react";
import SimulationLauncher from "../components/SimulationLauncher";

export default function SimulationsScreen({ onNavigateToPaper }) {
  return (
    <SimulationLauncher onNavigateToPaper={onNavigateToPaper} />
  );
}
