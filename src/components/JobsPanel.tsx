"use client";

import React, { useState, useEffect } from "react";
import type { Job } from "@prisma/client";

export default function JobsPanel() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchJobs = async () => {
    try {
      const res = await fetch("/api/jobs");
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch (err) {
      console.error("Failed to fetch jobs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "COMPLETED": return "var(--text-accent)";
      case "RUNNING": return "#e2b714"; // Yellow/orange
      case "FAILED": return "#ff5555";
      case "RETRY": return "#ffb86c";
      default: return "var(--text-secondary)";
    }
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: "40px", overflowY: "auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h2 style={{ fontFamily: "var(--font-mono)", color: "var(--text-accent)", fontSize: "16px" }}>
          SYSTEM WORKER JOBS // {jobs.length} RECENT
        </h2>
        <button 
          onClick={() => { setLoading(true); fetchJobs(); }}
          style={{
            background: "transparent",
            border: "1px solid var(--border-highlight)",
            color: "var(--text-accent)",
            padding: "6px 12px",
            fontFamily: "var(--font-mono)",
            fontSize: "12px",
            cursor: "pointer"
          }}
        >
          REFRESH
        </button>
      </div>

      <div style={{ flex: 1 }}>
        {loading && jobs.length === 0 && (
          <div style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>[LOADING JOB SCHEDULER...]</div>
        )}

        {!loading && jobs.length === 0 && (
          <div style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>[NO JOBS FOUND IN DATABASE]</div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {jobs.map((job) => (
            <div
              key={job.id}
              style={{
                padding: "16px",
                background: "var(--bg-panel)",
                borderLeft: `3px solid ${getStatusColor(job.status)}`,
                borderTop: "1px solid var(--border-primary)",
                borderRight: "1px solid var(--border-primary)",
                borderBottom: "1px solid var(--border-primary)",
                borderRadius: "2px"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
                <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontWeight: "bold", color: "var(--text-primary)" }}>
                    {job.type}
                  </span>
                  <span style={{ fontSize: "12px", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
                    ID: {job.id}
                  </span>
                </div>
                <div style={{ 
                  color: getStatusColor(job.status), 
                  fontFamily: "var(--font-mono)", 
                  fontSize: "12px",
                  fontWeight: "bold"
                }}>
                  [{job.status}]
                </div>
              </div>

              <div style={{ fontSize: "12px", color: "var(--text-secondary)", fontFamily: "var(--font-mono)", display: "flex", gap: "24px" }}>
                <div>CREATED: {new Date(job.createdAt).toLocaleString()}</div>
                {job.startedAt && <div>STARTED: {new Date(job.startedAt).toLocaleString()}</div>}
                {job.completedAt && <div>COMPLETED: {new Date(job.completedAt).toLocaleString()}</div>}
              </div>

              {job.error && (
                <div style={{ 
                  marginTop: "12px", 
                  padding: "8px", 
                  background: "rgba(255, 85, 85, 0.1)", 
                  border: "1px solid rgba(255, 85, 85, 0.3)",
                  color: "#ff5555",
                  fontSize: "12px",
                  fontFamily: "var(--font-mono)",
                  whiteSpace: "pre-wrap"
                }}>
                  {job.error}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
