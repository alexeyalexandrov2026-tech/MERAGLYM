"use client";

import React, { useState } from "react";
import type { Node } from "@prisma/client";
import Sidebar from "./Sidebar";
import NodeView from "./NodeView";
import Navigation from "./Navigation";
import SearchPanel from "./SearchPanel";
import JobsPanel from "./JobsPanel";
import { useI18n } from "@/lib/i18nContext";

interface DashboardProps {
  initialNodes: Node[];
}

export default function Dashboard({ initialNodes }: DashboardProps) {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [currentView, setCurrentView] = useState("osint");
  const { t, locale, setLocale } = useI18n();

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
        <div style={{ padding: "40px", color: "var(--text-primary)", flex: 1, overflowY: "auto", position: "relative" }}>
          
          <div style={{ position: "absolute", top: "40px", right: "40px", display: "flex", gap: "10px", alignItems: "center" }}>
            <span style={{ fontSize: "12px", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>{t("common.language")}:</span>
            <select 
              value={locale} 
              onChange={(e) => setLocale(e.target.value as any)}
              style={{ background: "transparent", color: "var(--text-accent)", border: "1px solid var(--border-highlight)", padding: "4px" }}
            >
              <option value="en">EN</option>
              <option value="ru">RU</option>
            </select>
          </div>

          <h1 style={{ fontFamily: "var(--font-mono)", color: "var(--text-accent)" }}>{t("dashboard.title")}</h1>
          <p style={{ marginTop: "20px", color: "var(--text-secondary)" }}>
            {t("dashboard.welcome")}
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
