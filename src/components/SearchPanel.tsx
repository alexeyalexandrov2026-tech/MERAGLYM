"use client";

import React, { useState, useEffect } from "react";
import type { NodeModel as Node } from "@/generated/prisma/models";
import { useI18n } from "@/lib/i18nContext";

export default function SearchPanel() {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Node[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (query.trim().length > 2) {
        performSearch(query);
      } else {
        setResults([]);
        setSearched(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  const performSearch = async (q: string) => {
    setLoading(true);
    setSearched(true);
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      if (res.ok) {
        const data = await res.json();
        setResults(data);
      }
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: "40px" }}>
      <h2 style={{ fontFamily: "var(--font-mono)", color: "var(--text-accent)", marginBottom: "20px", fontSize: "16px" }}>
        {t("searchPanel.title")}
      </h2>
      
      <div style={{ marginBottom: "20px" }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("searchPanel.placeholder")}
          style={{
            width: "100%",
            maxWidth: "600px",
            background: "rgba(100, 255, 218, 0.05)",
            border: "1px solid var(--border-highlight)",
            color: "var(--text-primary)",
            padding: "12px 16px",
            fontFamily: "var(--font-mono)",
            fontSize: "14px",
            outline: "none"
          }}
        />
      </div>

      <div style={{ flex: 1, overflowY: "auto", borderTop: "1px solid var(--border-primary)", paddingTop: "20px" }}>
        {loading && <div style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>{t("searchPanel.searching")}</div>}
        
        {!loading && searched && results.length === 0 && (
          <div style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>{t("searchPanel.noResults")}</div>
        )}

        {!loading && results.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", fontFamily: "var(--font-mono)", marginBottom: "8px" }}>
              {results.length} {t("searchPanel.matches")}
            </div>
            {results.map((node) => (
              <div
                key={node.id}
                style={{
                  padding: "16px",
                  background: "var(--bg-panel)",
                  border: "1px solid var(--border-primary)",
                  borderRadius: "4px"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                  <div style={{ color: "var(--text-accent)", fontWeight: "bold", fontSize: "16px", fontFamily: "var(--font-mono)" }}>
                    {node.name}
                  </div>
                  <div style={{ fontSize: "10px", color: "var(--text-secondary)", background: "rgba(255,255,255,0.05)", padding: "2px 6px", borderRadius: "2px" }}>
                    {node.type.toUpperCase()}
                  </div>
                </div>
                
                {node.description && (
                  <div style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: "12px" }}>
                    {node.description}
                  </div>
                )}
                
                {node.url && (
                  <a
                    href={node.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: "inline-block",
                      fontSize: "12px",
                      color: "var(--text-accent)",
                      textDecoration: "none",
                      borderBottom: "1px solid rgba(100, 255, 218, 0.3)",
                      paddingBottom: "2px"
                    }}
                  >
                    {node.url}
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
