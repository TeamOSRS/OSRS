import React from "react";
import BallBalancerResearch from "../components/BallBalancerResearch";

export default function ResearchBalancerScreen(props) {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-2">
        <h2 className="text-2xl md:text-3xl font-semibold text-white tracking-tight">Ball Balancer Research</h2>
        <p className="text-xs text-zinc-400 font-normal mt-0.5">Tune and monitor the closed-loop plate balancing algorithm.</p>
      </div>
      <BallBalancerResearch {...props} />
    </div>
  );
}
