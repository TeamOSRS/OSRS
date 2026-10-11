import React from "react";
import ResearchPaperViewer from "../components/ResearchPaperViewer";

export default function ResearchPaperScreen({ onNavigateToSimulations }) {
  return (
    <ResearchPaperViewer onNavigateToSimulations={onNavigateToSimulations} />
  );
}
