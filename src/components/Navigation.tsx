import React from "react";
import { useI18n } from "@/lib/i18nContext";

interface NavigationProps {
  currentView: string;
  onViewChange: (view: string) => void;
}

export default function Navigation({ currentView, onViewChange }: NavigationProps) {
  const { t } = useI18n();

  const navItems = [
    { id: "overview", label: t("nav.overview") },
    { id: "osint", label: t("nav.osint") },
    { id: "search", label: t("nav.search") },
    { id: "jobs", label: t("nav.jobs") },
  ];

  return (
    <div
      className="gotham-panel"
      style={{
        width: "60px",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        borderRight: "1px solid var(--border-highlight)",
        borderTop: "none",
        borderBottom: "none",
        borderLeft: "none",
        paddingTop: "20px",
        gap: "20px",
      }}
    >
      {/* Brand logo / icon */}
      <div
        style={{
          width: "40px",
          height: "40px",
          borderRadius: "4px",
          background: "rgba(100, 255, 218, 0.1)",
          border: "1px solid var(--border-highlight)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--text-accent)",
          fontWeight: "bold",
          fontSize: "12px",
          marginBottom: "20px",
          cursor: "pointer",
        }}
        onClick={() => onViewChange("overview")}
      >
        MX
      </div>

      {navItems.map((item) => {
        const isActive = currentView === item.id;
        return (
          <div
            key={item.id}
            title={item.label}
            onClick={() => onViewChange(item.id)}
            style={{
              width: "40px",
              height: "40px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              borderRadius: "4px",
              background: isActive ? "var(--bg-accent)" : "transparent",
              color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
              border: isActive ? "1px solid var(--border-highlight)" : "1px solid transparent",
              transition: "all 0.2s ease",
            }}
          >
            <span style={{ fontSize: "10px", writingMode: "vertical-rl", transform: "rotate(180deg)", fontFamily: "var(--font-mono)", letterSpacing: "1px" }}>
              {item.label.split(" ")[0]}
            </span>
          </div>
        );
      })}
    </div>
  );
}
