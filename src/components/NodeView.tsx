import React from "react";
import type { Node } from "@prisma/client";

interface NodeViewProps {
  node: Node | null;
}

export default function NodeView({ node }: NodeViewProps) {
  if (!node) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-muted)", flexDirection: "column" }}>
        <div style={{ fontSize: "48px", marginBottom: "16px", opacity: 0.2 }}>◇</div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "14px", letterSpacing: "1px" }}>AWAITING_TARGET_SELECTION</div>
      </div>
    );
  }

  return (
    <div className="gotham-panel" style={{ margin: "24px", padding: "32px", borderRadius: "8px", flex: 1, display: "flex", flexDirection: "column", animation: "pulseGlow 4s infinite" }}>
      <div style={{ borderBottom: "1px solid var(--border-primary)", paddingBottom: "20px", marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ color: "var(--accent-electric)", fontSize: "12px", fontFamily: "var(--font-mono)", marginBottom: "8px", letterSpacing: "2px" }}>
            [ID: {node.id.toString().padStart(4, "0")}] // {node.type.toUpperCase()}
          </div>
          <h1 style={{ color: "var(--text-primary)", fontSize: "28px", letterSpacing: "1px" }}>{node.name}</h1>
        </div>
        {node.url && (
          <a
            href={node.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              padding: "8px 16px",
              background: "rgba(0, 136, 255, 0.1)",
              border: "1px solid var(--accent-electric)",
              color: "var(--accent-electric)",
              textDecoration: "none",
              fontFamily: "var(--font-mono)",
              fontSize: "12px",
              cursor: "pointer",
              transition: "all 0.2s"
            }}
            onMouseOver={(e) => (e.currentTarget.style.background = "rgba(0, 136, 255, 0.2)")}
            onMouseOut={(e) => (e.currentTarget.style.background = "rgba(0, 136, 255, 0.1)")}
          >
            INITIATE_UPLINK ↗
          </a>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <Field label="DESCRIPTION" value={node.description} />
          <Field label="STATUS" value={node.status} />
          <Field label="BEST FOR" value={node.bestFor} />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <Field label="PRICING" value={node.pricing} />
          <Field label="INPUT" value={node.input} />
          <Field label="OUTPUT" value={node.output} />
          <Field label="OPSEC" value={node.opsec} isWarning={node.opsec?.toLowerCase().includes("high") || node.opsec?.toLowerCase().includes("warning")} />
          <Field label="OPSEC NOTE" value={node.opsecNote} />
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, isWarning }: { label: string; value?: string | null; isWarning?: boolean }) {
  if (!value) return null;
  
  return (
    <div>
      <div style={{ color: "var(--text-secondary)", fontSize: "11px", fontFamily: "var(--font-mono)", marginBottom: "4px" }}>
        {label}
      </div>
      <div style={{ 
        color: isWarning ? "var(--accent-warning)" : "var(--text-primary)", 
        fontSize: "14px",
        lineHeight: "1.5",
        padding: "8px 12px",
        background: "rgba(255,255,255,0.02)",
        borderLeft: `2px solid ${isWarning ? "var(--accent-warning)" : "var(--border-muted)"}`
      }}>
        {value}
      </div>
    </div>
  );
}
