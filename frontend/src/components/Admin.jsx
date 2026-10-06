import React, { useState } from "react";
import { Loader2, Lock, RefreshCw, Mail, Phone, CreditCard } from "lucide-react";
import Logo from "./Logo";
import { getAdminLeads } from "../api";

export default function Admin() {
  const [token, setToken] = useState(localStorage.getItem("ciq_admin") || "");
  const [authed, setAuthed] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = async (t) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getAdminLeads(t);
      setData(res);
      setAuthed(true);
      localStorage.setItem("ciq_admin", t);
    } catch (e) {
      setError("Invalid admin key.");
      setAuthed(false);
    } finally {
      setLoading(false);
    }
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
  return (
    <div className="ciq-shell min-h-screen pb-16">
      <header className="ciq-container flex items-center justify-between py-5" style={{ maxWidth: 1000 }}>
        <Logo size="md" />
        <button onClick={() => load(token)} className="ciq-press flex items-center gap-1.5 rounded-full border bg-white px-3 py-1.5 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </header>

      <div className="ciq-container" style={{ maxWidth: 1000 }}>
        <h1 className="font-display text-2xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>Leads</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{data?.total || 0} total · most recent first</p>

        <div className="mt-5 space-y-3">
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

function formatDate(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  } catch (e) {
    return iso;
  }
}
