"use client";

import React, { useState, useEffect } from "react";
import type { Node } from "@prisma/client";
import { useI18n } from "@/lib/i18nContext";

interface SidebarProps {
  initialNodes: Node[];
  onSelectNode: (node: Node) => void;
  selectedNodeId?: number | null;
}

const TreeNode = ({
  node,
  level,
  onSelectNode,
  selectedNodeId,
}: {
  node: Node;
  level: number;
  onSelectNode: (node: Node) => void;
  selectedNodeId?: number | null;
}) => {
  const [expanded, setExpanded] = useState(false);
  const [children, setChildren] = useState<Node[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);
  
  // Predict if it has children based on type, otherwise wait for fetch.
  // arf.json folders usually have children.
  const mightHaveChildren = node.type === "folder";
  const isSelected = selectedNodeId === node.id;

  const handleToggle = async () => {
    if (!expanded && !hasFetched && mightHaveChildren) {
      setLoading(true);
      try {
        const res = await fetch(`/api/nodes?parentId=${node.id}`);
        if (res.ok) {
          const data = await res.json();
          setChildren(data);
        }
      } catch (err) {
        console.error("Failed to load children", err);
      } finally {
        setLoading(false);
        setHasFetched(true);
      }
    }
    setExpanded(!expanded);
  };

  return (
    <div style={{ marginLeft: level > 0 ? "16px" : "0" }}>
      <div
        className={`node-item ${isSelected ? "node-active" : ""}`}
        style={{
          display: "flex",
          alignItems: "center",
          padding: "8px 12px",
          borderLeft: "2px solid transparent",
          color: isSelected ? "var(--text-accent)" : "var(--text-primary)",
          fontSize: "14px",
          userSelect: "none",
          cursor: "pointer",
        }}
        onClick={() => {
          if (mightHaveChildren) handleToggle();
          onSelectNode(node);
        }}
      >
        <span
          style={{
            marginRight: "8px",
            fontFamily: "var(--font-mono)",
            opacity: 0.7,
            width: "20px",
            display: "inline-block",
            textAlign: "center"
          }}
        >
          {loading ? "..." : (mightHaveChildren ? (expanded ? "[-]" : "[+]") : "›")}
        </span>
        <span style={{ 
          fontFamily: node.type === "folder" ? "var(--font-mono)" : "var(--font-inter)",
          fontWeight: node.type === "folder" ? "bold" : "normal",
          letterSpacing: node.type === "folder" ? "0.5px" : "normal"
        }}>
          {node.name}
        </span>
      </div>
      {expanded && children.length > 0 && (
        <div style={{ borderLeft: "1px dashed var(--border-muted)" }}>
          {children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onSelectNode={onSelectNode}
              selectedNodeId={selectedNodeId}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default function Sidebar({ initialNodes, onSelectNode, selectedNodeId }: SidebarProps) {
  const { t } = useI18n();

  return (
    <div
      className="gotham-panel"
      style={{
        width: "350px",
        height: "100%",
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
        borderRight: "1px solid var(--border-highlight)",
        borderTop: "none",
        borderBottom: "none",
        borderLeft: "none"
      }}
    >
      <div style={{
        padding: "20px",
        borderBottom: "1px solid var(--border-primary)",
        position: "sticky",
        top: 0,
        background: "var(--bg-panel)",
        zIndex: 10,
        backdropFilter: "blur(12px)"
      }}>
        <h2 style={{ color: "var(--text-accent)", fontSize: "16px", marginBottom: "4px" }}>
          {t("sidebar.sysIndex")}
        </h2>
        <div style={{ fontSize: "11px", color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>
          {t("sidebar.rootCategories")} // {initialNodes.length} {t("sidebar.entries")}
        </div>
      </div>
      
      <div style={{ padding: "10px 0" }}>
        {initialNodes.map((node) => (
          <TreeNode
            key={node.id}
            node={node}
            level={0}
            onSelectNode={onSelectNode}
            selectedNodeId={selectedNodeId}
          />
        ))}
      </div>
    </div>
  );
}
