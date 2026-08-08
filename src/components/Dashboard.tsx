"use client";

import React, { useState } from "react";
import type { Node } from "@prisma/client";
import Sidebar from "./Sidebar";
import NodeView from "./NodeView";
import Navigation from "./Navigation";
import SearchPanel from "./SearchPanel";
import JobsPanel from "./JobsPanel";

interface DashboardProps {
  initialNodes: Node[];
}

export default function Dashboard({ initialNodes }: DashboardProps) {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [currentView, setCurrentView] = useState("osint");

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", position: "relative", width: "100vw" }}>
      <div className="scanline" />
      <Navigation currentView={currentView} onViewChange={setCurrentView} />
      
      {currentView === "osint" && (
        <>
          <Sidebar initialNodes={initialNodes} onSelectNode={setSelectedNode} selectedNodeId={selectedNode?.id} />
          <NodeView node={selectedNode} />
        </>
      )}

      {currentView === "overview" && (
        <div style={{ padding: "40px", color: "var(--text-primary)", flex: 1, overflowY: "auto" }}>
          <h1 style={{ fontFamily: "var(--font-mono)", color: "var(--text-accent)" }}>MERAGLYM SYSTEM OVERVIEW</h1>
          <p style={{ marginTop: "20px", color: "var(--text-secondary)" }}>
            Welcome to the Meraglym OSINT Intelligence Platform. Select a module from the left navigation array to begin.
          </p>
        </div>
      )}

      {currentView === "search" && (
        <SearchPanel />
      )}

      {currentView === "jobs" && (
        <JobsPanel />
      )}
    </div>
  );
}
