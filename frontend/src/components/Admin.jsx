import React, { useState } from "react";
import { Loader2, Lock, RefreshCw, Mail, Phone, CreditCard, Download, BarChart3 } from "lucide-react";
import Logo from "./Logo";
import { getAdminLeads, getAdminInsights, leadsCsvUrl } from "../api";

export default function Admin() {
  const [token, setToken] = useState(localStorage.getItem("ciq_admin") || "");
  const [authed, setAuthed] = useState(false);
  const [data, setData] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = async (t) => {
    setLoading(true);
    setError(null);
    try {
      const [res, ins] = await Promise.all([getAdminLeads(t), getAdminInsights(t)]);
      setData(res);
      setInsights(ins);
      setAuthed(true);
      localStorage.setItem("ciq_admin", t);
    } catch (e) {
      setError("Invalid admin key.");
      setAuthed(false);
    } finally {
      setLoading(false);
    }
  };

  const downloadCsv = () => {
    const url = leadsCsvUrl(token);
    const a = document.createElement("a");
    a.href = url;
    a.download = "cardiq-leads.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  if (!authed) {
    return (
      <div className="ciq-shell grid min-h-screen place-items-center">
        <div className="ciq-container">
          <div className="mx-auto max-w-sm rounded-3xl border bg-white p-6" style={{ borderColor: "var(--ciq-line)" }}>
            <div className="flex justify-center"><Logo size="lg" /></div>
            <div className="mt-5 inline-flex items-center gap-2 text-sm font-semibold" style={{ color: "var(--ciq-ink)" }}>
              <Lock className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} /> Admin — Leads
            </div>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && token && load(token)}
              placeholder="Enter admin key"
              className="mt-3 w-full rounded-2xl border bg-white px-3.5 py-3 text-[15px] outline-none"
              style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}
            />
            {error && <p className="mt-2 text-xs" style={{ color: "#b4433f" }}>{error}</p>}
            <button
              onClick={() => token && load(token)}
              disabled={loading || !token}
              className="ciq-press mt-4 inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3 text-sm font-semibold text-white"
              style={{ background: "var(--ciq-teal-600)", opacity: token && !loading ? 1 : 0.55 }}
            >
              {loading ? <Loader2 className="h-4 w-4 ciq-spin" /> : "Unlock dashboard"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const leads = data?.leads || [];
  const maxGoal = Math.max(1, ...((insights?.by_goal || []).map((g) => g.count)));

  return (
    <div className="ciq-shell min-h-screen pb-16">
      <header className="ciq-container flex items-center justify-between py-5" style={{ maxWidth: 1000 }}>
        <Logo size="md" />
        <div className="flex items-center gap-2">
          <button onClick={downloadCsv} className="ciq-press flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold text-white" style={{ background: "var(--ciq-teal-600)" }}>
            <Download className="h-3.5 w-3.5" /> CSV
          </button>
          <button onClick={() => load(token)} className="ciq-press flex items-center gap-1.5 rounded-full border bg-white px-3 py-1.5 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        </div>
      </header>

      <div className="ciq-container" style={{ maxWidth: 1000 }}>
        {/* stat cards */}
        <div className="grid grid-cols-3 gap-3">
          <Stat label="Total leads" value={data?.total || 0} />
          <Stat label="Results" value={insights?.total_results || 0} />
          <Stat label="Emails sent" value={insights?.emails_sent || 0} />
        </div>

        {/* Insights */}
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <InsightCard title="Top matched cards" icon={CreditCard}>
            {(insights?.by_card || []).length === 0 && <Empty />}
            <div className="space-y-3">
              {(insights?.by_card || []).map((c) => (
                <Bar key={c.label} label={c.label} count={c.count} pct={c.pct} max={100} usePct />
              ))}
            </div>
          </InsightCard>

          <InsightCard title="What people want most" icon={BarChart3}>
            {(insights?.by_goal || []).length === 0 && <Empty />}
            <div className="space-y-3">
              {(insights?.by_goal || []).map((g) => (
                <Bar key={g.label} label={g.label} count={g.count} pct={g.pct} max={maxGoal} />
              ))}
            </div>
          </InsightCard>
        </div>

        <h2 className="mt-8 font-display text-xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>Leads</h2>
        <p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>most recent first</p>

        <div className="mt-4 space-y-3">
          {leads.length === 0 && (
            <div className="rounded-2xl border bg-white p-6 text-center text-sm" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink-soft)" }}>No leads yet.</div>
          )}
          {leads.map((l, i) => (
            <div key={i} className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="font-display font-bold" style={{ color: "var(--ciq-ink)" }}>{l.name}</div>
                <span className="rounded-full px-2.5 py-1 text-xs font-semibold" style={{ background: l.email_sent ? "#e6f5f0" : "#f1f2ef", color: l.email_sent ? "var(--ciq-teal)" : "var(--ciq-ink-soft)" }}>
                  {l.email_sent ? "Email sent" : "Not emailed"}
                </span>
              </div>
              <div className="mt-2 grid gap-1.5 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>
                <span className="flex items-center gap-2"><Mail className="h-3.5 w-3.5" /> {l.email}</span>
                {l.phone && <span className="flex items-center gap-2"><Phone className="h-3.5 w-3.5" /> {l.phone}</span>}
                <span className="flex items-center gap-2" style={{ color: "var(--ciq-ink)" }}><CreditCard className="h-3.5 w-3.5" style={{ color: "var(--ciq-teal-600)" }} /> {l.recommended_card}</span>
              </div>
              <div className="mt-2 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{formatDate(l.created_at)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
      <div className="font-display text-2xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>{value}</div>
      <div className="mt-0.5 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{label}</div>
    </div>
  );
}

function InsightCard({ title, icon: Icon, children }) {
  return (
    <div className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
      <div className="mb-3 flex items-center gap-2">
        <Icon className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} />
        <span className="font-display text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>{title}</span>
      </div>
      {children}
    </div>
  );
}

function Bar({ label, count, pct, max, usePct }) {
  const width = usePct ? pct : Math.round((count / max) * 100);
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="font-medium" style={{ color: "var(--ciq-ink)" }}>{label}</span>
        <span style={{ color: "var(--ciq-ink-soft)" }}>{count} · {pct}%</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full" style={{ background: "#eef0ec" }}>
        <div className="h-full rounded-full" style={{ width: `${width}%`, background: "linear-gradient(90deg,#0d9488,#2dd4bf)" }} />
      </div>
    </div>
  );
}

function Empty() {
  return <div className="text-xs" style={{ color: "var(--ciq-ink-soft)" }}>No data yet.</div>;
}

function formatDate(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  } catch (e) {
    return iso;
  }
}
