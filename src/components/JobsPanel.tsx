"use client";

import React, { useState, useEffect, useCallback } from "react";
import type { Job } from "@prisma/client";
import { useI18n } from "@/lib/i18nContext";
import { JOB_ADAPTERS, findAdapter } from "@/lib/jobAdapters";

type JobRow = Omit<Job, "payload" | "result"> & {
  payload: unknown;
  result: unknown;
  redacted?: boolean;
};

const TOKEN_KEY = "meraglym.jobsAdminToken";

const mono: React.CSSProperties = { fontFamily: "var(--font-mono)" };
const inputStyle: React.CSSProperties = {
  ...mono,
  background: "var(--bg-panel)",
  border: "1px solid var(--border-primary)",
  color: "var(--text-primary)",
  padding: "6px 8px",
  fontSize: "12px",
};
const buttonStyle: React.CSSProperties = {
  ...mono,
  background: "transparent",
  border: "1px solid var(--border-highlight)",
  color: "var(--text-accent)",
  padding: "6px 12px",
  fontSize: "12px",
  cursor: "pointer",
};

function describeTarget(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;
  const p = payload as { value?: unknown; objects?: unknown[] };
  if (typeof p.value === "string") return p.value;
  if (Array.isArray(p.objects)) return `${p.objects.length} STIX object(s)`;
  return null;
}

function resultSummary(result: unknown): { count: number | null; observations: unknown[] } {
  if (!result || typeof result !== "object") return { count: null, observations: [] };
  const r = result as { count?: number; observations?: unknown[] };
  const observations = Array.isArray(r.observations) ? r.observations : [];
  return { count: typeof r.count === "number" ? r.count : observations.length, observations };
}

export default function JobsPanel() {
  const { t } = useI18n();
  const [jobs, setJobs] = useState<JobRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState("");
  const [tokenInvalid, setTokenInvalid] = useState(false);
  const [adapterId, setAdapterId] = useState<string>(JOB_ADAPTERS[0].id);
  const [target, setTarget] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  const adapter = findAdapter(adapterId) ?? JOB_ADAPTERS[0];

  const fetchJobs = useCallback(async () => {
    try {
      const stored = typeof window !== "undefined" ? window.sessionStorage.getItem(TOKEN_KEY) : null;
      const res = await fetch("/api/jobs", {
        headers: stored ? { "x-admin-token": stored } : undefined,
        cache: "no-store",
      });
      if (res.ok) {
        setTokenInvalid(Boolean(stored) && res.headers.get("x-admin-auth") === "invalid");
        const data = await res.json();
        setJobs(data);
      }
    } catch (err) {
      console.error("Failed to fetch jobs", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Defer the initial work to a timer callback so state updates never
    // happen synchronously inside the effect body (react-hooks/set-state-in-effect).
    const initial = setTimeout(() => {
      const stored = window.sessionStorage.getItem(TOKEN_KEY);
      if (stored) setToken(stored);
      void fetchJobs();
    }, 0);
    const interval = setInterval(() => {
      void fetchJobs();
    }, 5000); // Poll every 5 seconds
    return () => {
      clearTimeout(initial);
      clearInterval(interval);
    };
  }, [fetchJobs]);

  const saveToken = (value: string) => {
    setToken(value);
    if (value) window.sessionStorage.setItem(TOKEN_KEY, value);
    else window.sessionStorage.removeItem(TOKEN_KEY);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      const res = await fetch("/api/jobs", {
        method: "POST",
        headers: { "content-type": "application/json", "x-admin-token": token },
        body: JSON.stringify({ adapter: adapterId, target }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setMessage({ ok: true, text: `${t("jobsPanel.queued")} #${data.id}` });
        setTarget("");
        void fetchJobs();
      } else {
        setMessage({ ok: false, text: `${res.status}: ${data.error ?? "error"}` });
      }
    } catch (err) {
      setMessage({ ok: false, text: String(err) });
    } finally {
      setSubmitting(false);
    }
  };

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
      <form
        onSubmit={submit}
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          padding: "16px",
          marginBottom: "24px",
          border: "1px solid var(--border-primary)",
          background: "var(--bg-panel)",
        }}
      >
        <div style={{ ...mono, color: "var(--text-accent)", fontSize: "14px" }}>{t("jobsPanel.newJob")}</div>
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
          <select
            value={adapterId}
            onChange={(e) => setAdapterId(e.target.value)}
            style={{ ...inputStyle, minWidth: "280px" }}
            aria-label={t("jobsPanel.adapter")}
          >
            {JOB_ADAPTERS.map((a) => (
              <option key={a.id} value={a.id}>
                [{a.region}] {a.label}
              </option>
            ))}
          </select>
          <input
            type="password"
            value={token}
            onChange={(e) => saveToken(e.target.value)}
            placeholder={t("jobsPanel.token")}
            autoComplete="off"
            style={{ ...inputStyle, width: "220px" }}
            aria-label={t("jobsPanel.token")}
            aria-invalid={tokenInvalid}
            title={tokenInvalid ? t("jobsPanel.tokenInvalid") : undefined}
          />
          {tokenInvalid && <span style={{ color: "#ff5555", fontSize: "0.75rem" }}>{t("jobsPanel.tokenInvalid")}</span>}
        </div>
        {adapter.input === "stix" ? (
          <textarea
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder={adapter.placeholder}
            rows={4}
            style={{ ...inputStyle, resize: "vertical" }}
            aria-label={t("jobsPanel.target")}
          />
        ) : (
          <input
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder={adapter.placeholder}
            style={inputStyle}
            aria-label={t("jobsPanel.target")}
          />
        )}
        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <button type="submit" disabled={submitting || !target || !token} style={buttonStyle}>
            {submitting ? t("jobsPanel.submitting") : t("jobsPanel.submit")}
          </button>
          {adapter.requires && (
            <span style={{ ...mono, fontSize: "11px", color: "var(--text-secondary)" }}>
              {t("jobsPanel.requires")} {adapter.requires}
            </span>
          )}
          {message && (
            <span style={{ ...mono, fontSize: "12px", color: message.ok ? "var(--text-accent)" : "#ff5555" }}>
              {message.text}
            </span>
          )}
        </div>
      </form>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h2 style={{ fontFamily: "var(--font-mono)", color: "var(--text-accent)", fontSize: "16px" }}>
          {t("jobsPanel.title")} {jobs.length} {t("jobsPanel.recent")}
        </h2>
        <button
          onClick={() => { setLoading(true); fetchJobs(); }}
          style={buttonStyle}
        >
          {t("jobsPanel.refresh")}
        </button>
      </div>

      <div style={{ flex: 1 }}>
        {loading && jobs.length === 0 && (
          <div style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>{t("jobsPanel.loading")}</div>
        )}

        {!loading && jobs.length === 0 && (
          <div style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>{t("jobsPanel.noJobs")}</div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {jobs.map((job) => {
            const adapterName = (job.payload as { adapter_identifier?: string } | null)?.adapter_identifier;
            const targetText = describeTarget(job.payload);
            const summary = resultSummary(job.result);
            const isOpen = expanded === job.id;
            return (
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
                  <div style={{ display: "flex", gap: "16px", alignItems: "center", flexWrap: "wrap" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontWeight: "bold", color: "var(--text-primary)" }}>
                      {adapterName ?? job.type}
                    </span>
                    {targetText && (
                      <span style={{ ...mono, fontSize: "12px", color: "var(--text-primary)" }}>{targetText}</span>
                    )}
                    <span style={{ fontSize: "12px", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
                      {t("jobsPanel.id")} {job.id}
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

                <div style={{ fontSize: "12px", color: "var(--text-secondary)", fontFamily: "var(--font-mono)", display: "flex", gap: "24px", flexWrap: "wrap" }}>
                  <div>{t("jobsPanel.created")} {new Date(job.createdAt).toLocaleString()}</div>
                  {job.startedAt && <div>{t("jobsPanel.started")} {new Date(job.startedAt).toLocaleString()}</div>}
                  {job.completedAt && <div>{t("jobsPanel.completed")} {new Date(job.completedAt).toLocaleString()}</div>}
                  {job.status === "COMPLETED" && summary.count !== null && (
                    <div>{t("jobsPanel.results")} {summary.count}</div>
                  )}
                </div>

                {job.status === "COMPLETED" && summary.observations.length > 0 && (
                  <div style={{ marginTop: "10px" }}>
                    <button onClick={() => setExpanded(isOpen ? null : job.id)} style={{ ...buttonStyle, padding: "3px 8px" }}>
                      {isOpen ? t("jobsPanel.hide") : t("jobsPanel.show")}
                    </button>
                    {isOpen && (
                      <pre style={{
                        ...mono,
                        marginTop: "8px",
                        maxHeight: "360px",
                        overflow: "auto",
                        fontSize: "11px",
                        color: "var(--text-primary)",
                        whiteSpace: "pre-wrap",
                        wordBreak: "break-all",
                      }}>
                        {JSON.stringify(summary.observations, null, 2)}
                      </pre>
                    )}
                  </div>
                )}

                {job.redacted && (
                  <div style={{ ...mono, marginTop: "8px", fontSize: "11px", color: "var(--text-secondary)" }}>
                    {t("jobsPanel.redacted")}
                  </div>
                )}

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
            );
          })}
        </div>
      </div>
    </div>
  );
}
