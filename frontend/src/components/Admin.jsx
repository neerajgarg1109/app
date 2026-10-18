import React, { useRef, useState } from "react";
import { Loader2, Lock, RefreshCw, Mail, Phone, CreditCard, Download, BarChart3, Send, Clock, Link2, Search, Save, LayoutDashboard, Users, Building2, Plus, Pencil, X, History, Archive, Upload, Activity, MessageSquare } from "lucide-react";
import Logo from "./Logo";
import { getAdminLeads, getAdminInsights, getAdminCards, createAdminCard, updateAdminCard, publishAdminCard, discardAdminCardDraft, getAdminCardHistory, rollbackAdminCard, archiveAdminCard, previewAdminCardRecommendation, exportAdminCards, importAdminCards, updateAdminCardApplyLink, leadsCsvUrl, sendReminders, getAdminCardReviews, moderateAdminCardReview, sendAdminReviewReminders, sendAdminCardAlert } from "../api";
import { catalogQualityIssues } from "../catalogQuality";

const PRESETS = [
  { key: "all", label: "All time" },
  { key: "today", label: "Today" },
  { key: "7d", label: "7 days" },
  { key: "30d", label: "30 days" },
];

const linkDraft = (card) => ({
  url: card.custom_apply_url || "", partner: card.partner_name || "", campaign: card.campaign_id || "",
  tracking: card.tracking_id || "", status: card.apply_link_status === "official" ? "testing" : (card.apply_link_status || "testing"),
  payout: card.expected_payout ?? "",
});

function rangeFor(key) {
  const today = new Date();
  const iso = (d) => d.toISOString().slice(0, 10);
  if (key === "today") return { date_from: iso(today), date_to: iso(today) };
  if (key === "7d") { const f = new Date(today); f.setDate(f.getDate() - 6); return { date_from: iso(f), date_to: iso(today) }; }
  if (key === "30d") { const f = new Date(today); f.setDate(f.getDate() - 29); return { date_from: iso(f), date_to: iso(today) }; }
  return {};
}

export default function Admin() {
  const [token, setToken] = useState(localStorage.getItem("ciq_admin") || "");
  const [authed, setAuthed] = useState(false);
  const [data, setData] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [preset, setPreset] = useState("all");
  const [reminderMsg, setReminderMsg] = useState(null);
  const [sending, setSending] = useState(false);
  const [adminCards, setAdminCards] = useState([]);
  const [cardSearch, setCardSearch] = useState("");
  const [linkDrafts, setLinkDrafts] = useState({});
  const [savingCard, setSavingCard] = useState(null);
  const [linkMsg, setLinkMsg] = useState(null);
  const [activeSection, setActiveSection] = useState("overview");
  const [editingCard, setEditingCard] = useState(null);
  const [previewCard, setPreviewCard] = useState(null);
  const [historyCard, setHistoryCard] = useState(null);
  const [versions, setVersions] = useState([]);
  const [adminRole, setAdminRole] = useState("viewer");
  const [reviews, setReviews] = useState([]);
  const [alertDraft, setAlertDraft] = useState({ card_id: "", title: "", summary: "", source_url: "", idempotency_key: "" });
  const [alertMsg, setAlertMsg] = useState(null);
  const importInput = useRef(null);

  const load = async (t, presetKey = preset) => {
    setLoading(true);
    setError(null);
    const params = rangeFor(presetKey);
    try {
      const [res, ins, catalog, reviewData] = await Promise.all([
        getAdminLeads(t, params),
        getAdminInsights(t, params),
        getAdminCards(t),
        getAdminCardReviews(t),
      ]);
      setData(res);
      setInsights(ins);
      setAdminCards(catalog.cards || []);
      setAdminRole(catalog.role || "viewer");
      setReviews(reviewData.reviews || []);
      setLinkDrafts(Object.fromEntries((catalog.cards || []).map((card) => [card.id, linkDraft(card)])));
      setAuthed(true);
      localStorage.setItem("ciq_admin", t);
    } catch (e) {
      setError("Invalid admin key.");
      setAuthed(false);
    } finally {
      setLoading(false);
    }
  };

  const applyPreset = (key) => { setPreset(key); load(token, key); };

  const downloadCsv = () => {
    const url = leadsCsvUrl(token, rangeFor(preset));
    const a = document.createElement("a");
    a.href = url; a.download = "cardiq-leads.csv";
    document.body.appendChild(a); a.click(); a.remove();
  };

  const runReminders = async () => {
    setSending(true);
    setReminderMsg(null);
    try {
      const r = await sendReminders(token);
      setReminderMsg(r.reminders_sent > 0 ? `Sent ${r.reminders_sent} reminder email(s).` : "No pending reminders to send.");
      load(token);
    } catch (e) {
      setReminderMsg("Failed to send reminders.");
    } finally {
      setSending(false);
    }
  };

  const publishAlert = async (event) => {
    event.preventDefault(); setSending(true); setAlertMsg(null);
    try { const result = await sendAdminCardAlert(token, alertDraft); setAlertMsg(`Matched ${result.matched ?? result.sent} subscriber(s); sent ${result.sent}, failed ${result.failed}.`); }
    catch (e) { setAlertMsg(e.response?.data?.detail || "Could not send this alert."); }
    finally { setSending(false); }
  };

  const saveApplyLink = async (card, value = linkDrafts[card.id]) => {
    setSavingCard(card.id);
    setLinkMsg(null);
    try {
      const updated = await updateAdminCardApplyLink(token, card.id, value);
      setAdminCards((cards) => cards.map((item) => item.id === card.id ? {
        ...item,
        custom_apply_url: updated.custom_apply_url,
        effective_apply_url: updated.effective_apply_url,
        partner_name: updated.partner_name, campaign_id: updated.campaign_id, tracking_id: updated.tracking_id,
        apply_link_status: updated.apply_link_status, expected_payout: updated.expected_payout,
      } : item));
      setLinkDrafts((drafts) => ({ ...drafts, [card.id]: linkDraft({ ...card, ...updated }) }));
      setLinkMsg({ type: "success", text: `${card.name} apply link updated.` });
    } catch (e) {
      setLinkMsg({ type: "error", text: e.response?.data?.detail || "Could not update apply link." });
    } finally {
      setSavingCard(null);
    }
  };

  const saveCatalogCard = async (payload) => {
    setSavingCard(editingCard?.id || "new");
    setLinkMsg(null);
    try {
      const saved = editingCard?.id
        ? await updateAdminCard(token, editingCard.id, payload)
        : await createAdminCard(token, payload);
      setAdminCards((cards) => editingCard?.id
        ? cards.map((card) => card.id === saved.id ? saved : card)
        : [...cards, saved].sort((a, b) => a.name.localeCompare(b.name)));
      setLinkDrafts((drafts) => ({ ...drafts, [saved.id]: linkDraft(saved) }));
      setEditingCard(null);
      setLinkMsg({ type: "success", text: `${saved.name} saved as a draft. Preview and publish it when ready.` });
    } catch (e) {
      setLinkMsg({ type: "error", text: e.response?.data?.detail || "Could not save card." });
    } finally {
      setSavingCard(null);
    }
  };

  const publishCard = async (card) => {
    setSavingCard(card.id);
    try {
      const published = await publishAdminCard(token, card.id);
      setAdminCards((cards) => cards.map((item) => item.id === card.id ? published : item));
      setPreviewCard(null);
      setLinkMsg({ type: "success", text: `${published.name} is now published.` });
    } catch (e) {
      setLinkMsg({ type: "error", text: e.response?.data?.detail || "Could not publish card." });
    } finally { setSavingCard(null); }
  };

  const discardDraft = async (card) => {
    setSavingCard(card.id);
    try {
      const result = await discardAdminCardDraft(token, card.id);
      if (result.deleted) setAdminCards((cards) => cards.filter((item) => item.id !== card.id));
      else setAdminCards((cards) => cards.map((item) => item.id === card.id ? result : item));
      setPreviewCard(null);
      setLinkMsg({ type: "success", text: "Draft discarded; the published card was not changed." });
    } catch (e) {
      setLinkMsg({ type: "error", text: e.response?.data?.detail || "Could not discard draft." });
    } finally { setSavingCard(null); }
  };

  const openHistory = async (card) => {
    setHistoryCard(card); setVersions([]);
    try { setVersions((await getAdminCardHistory(token, card.id)).versions || []); }
    catch (e) { setLinkMsg({ type: "error", text: "Could not load card history." }); }
  };

  const rollbackVersion = async (card, versionId) => {
    const updated = await rollbackAdminCard(token, card.id, versionId);
    setAdminCards((cards) => cards.map((item) => item.id === card.id ? updated : item));
    setHistoryCard(null); setLinkMsg({ type: "success", text: "Previous version restored as a draft. Preview it before publishing." });
  };

  const toggleArchive = async (card) => {
    const updated = await archiveAdminCard(token, card.id, card.publication_status === "archived");
    setAdminCards((cards) => cards.map((item) => item.id === card.id ? updated : item));
    setLinkMsg({ type: "success", text: updated.publication_status === "archived" ? `${card.name} archived.` : `${card.name} restored.` });
  };

  const downloadCatalog = async (format) => {
    const data = await exportAdminCards(token, format);
    const blob = format === "csv" ? data : new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob); const a = document.createElement("a");
    a.href = url; a.download = `cardiq-cards.${format}`; a.click(); URL.revokeObjectURL(url);
  };

  const importCatalog = async (file) => {
    try {
      const parsed = JSON.parse(await file.text()); const cards = parsed.cards || parsed;
      const check = await importAdminCards(token, cards, true);
      if (!window.confirm(`${check.cards} cards passed validation. Import them as drafts?`)) return;
      const result = await importAdminCards(token, cards, false);
      setLinkMsg({ type: "success", text: `${result.created} cards imported as drafts.` }); load(token);
    } catch (e) { setLinkMsg({ type: "error", text: e.response?.data?.detail || "Import failed. Use a valid CardIQ JSON export." }); }
  };

  const moderateReview = async (review, status) => {
    await moderateAdminCardReview(token, review.review_id, status);
    setReviews((items) => items.map((item) => item.review_id === review.review_id ? { ...item, status } : item));
  };

  const runReviewReminders = async () => {
    setSending(true);
    try { const result = await sendAdminReviewReminders(token); setReminderMsg(`Sent ${result.sent} of ${result.due} due review reminder(s).`); }
    catch (e) { setReminderMsg("Could not send review reminders."); }
    finally { setSending(false); }
  };

  if (!authed) {
    return (
      <div className="ciq-shell grid min-h-screen place-items-center">
        <div className="ciq-container">
          <div className="mx-auto max-w-sm rounded-3xl border bg-white p-6" style={{ borderColor: "var(--ciq-line)" }}>
            <div className="flex justify-center"><Logo size="lg" /></div>
            <div className="mt-5 inline-flex items-center gap-2 text-sm font-semibold" style={{ color: "var(--ciq-ink)" }}>
              <Lock className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} /> cardIQ Admin
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
  const incomplete = insights?.incomplete_sessions || 0;
  const funnel = insights?.funnel || {};
  const applicationPerformance = insights?.application_performance || {};
  const funnelStages = [
    ["Landing visitors", funnel.landing_view || 0],
    ["Quiz starts", funnel.quiz_started || 0],
    ["Results viewed", funnel.result_viewed || 0],
    ["Leads shared", funnel.lead_submitted || 0],
    ["Apply clicks", funnel.apply_clicked || 0],
  ];
  const funnelBase = Math.max(1, funnel.landing_view || 0);
  const normalizedSearch = cardSearch.trim().toLowerCase();
  const filteredCards = adminCards.filter((card) => !normalizedSearch
    || card.name.toLowerCase().includes(normalizedSearch)
    || (card.issuer || "").toLowerCase().includes(normalizedSearch));
  const issuerCoverage = Object.entries(adminCards.reduce((counts, card) => {
    const issuer = card.issuer || "Unknown issuer";
    counts[issuer] = (counts[issuer] || 0) + 1;
    return counts;
  }, {})).sort(([left], [right]) => left.localeCompare(right));
  const canEdit = ["editor", "publisher", "owner"].includes(adminRole);
  const canPublish = ["publisher", "owner"].includes(adminRole);
  const healthIssues = catalogQualityIssues(adminCards);

  return (
    <div className="ciq-shell min-h-screen pb-16">
      <header className="ciq-container flex items-center justify-between py-5" style={{ maxWidth: 1000 }}>
        <Logo size="md" />
        <div className="flex items-center gap-2">
          <button onClick={() => load(token)} className="ciq-press flex items-center gap-1.5 rounded-full border bg-white px-3 py-1.5 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        </div>
      </header>

      <div className="ciq-container" style={{ maxWidth: 1000 }}>
        <div className="mb-3 flex justify-end"><span className="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide" style={{ background: "#eef0ec", color: "var(--ciq-ink-soft)" }}>{adminRole} access</span></div>
        <nav className="mb-6 grid grid-cols-3 gap-1 rounded-2xl border bg-white p-1.5 sm:grid-cols-7" style={{ borderColor: "var(--ciq-line)" }} aria-label="Admin sections">
          {[
            { key: "overview", label: "Overview", icon: LayoutDashboard },
            { key: "issuers", label: "Issuers", icon: Building2 },
            { key: "health", label: "Health", icon: Activity },
            { key: "reviews", label: "Reviews", icon: MessageSquare },
            { key: "alerts", label: "Alerts", icon: Send },
            { key: "links", label: "Cards", icon: CreditCard },
            { key: "leads", label: "Leads", icon: Users },
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveSection(key)}
              aria-current={activeSection === key ? "page" : undefined}
              className="ciq-press flex items-center justify-center gap-1.5 rounded-xl px-2 py-2.5 text-xs font-semibold sm:text-sm"
              style={{
                background: activeSection === key ? "var(--ciq-teal-600)" : "transparent",
                color: activeSection === key ? "#fff" : "var(--ciq-ink-soft)",
              }}
            >
              <Icon className="h-4 w-4" /> <span>{label}</span>
            </button>
          ))}
        </nav>

        {/* date presets */}
        {(activeSection === "overview" || activeSection === "leads") && <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.key}
              onClick={() => applyPreset(p.key)}
              className="ciq-press rounded-full px-3.5 py-1.5 text-sm font-semibold"
              style={{
                background: preset === p.key ? "var(--ciq-teal-600)" : "#fff",
                color: preset === p.key ? "#fff" : "var(--ciq-ink)",
                border: `1px solid ${preset === p.key ? "var(--ciq-teal-600)" : "var(--ciq-line)"}`,
              }}
            >
              {p.label}
            </button>
          ))}
        </div>}

        {activeSection === "overview" && <>
        {/* stat cards */}
        <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
          <Stat label="Leads" value={data?.total || 0} />
          <Stat label="Results" value={insights?.total_results || 0} />
          <Stat label="Emails sent" value={insights?.emails_sent || 0} />
          <Stat label="Incomplete" value={incomplete} />
        </div>

        <div className="mt-4 rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="flex items-start justify-between gap-3"><div><h2 className="font-display text-base font-extrabold">Customer funnel</h2><p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Anonymous first-party counts. No form contents or session recordings.</p></div><span className="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase" style={{ background: "#e6f5f0", color: "var(--ciq-teal)" }}>v2 baseline</span></div>
          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-5">
            {funnelStages.map(([label, value]) => <div key={label} className="rounded-xl p-3" style={{ background: "#f7f8f6" }}><div className="font-display text-xl font-extrabold">{value}</div><div className="mt-1 text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>{label}</div><div className="mt-1 text-xs font-bold" style={{ color: "var(--ciq-teal)" }}>{Math.round(value * 100 / funnelBase)}%</div></div>)}
          </div>
        </div>

        <div className="mt-4 rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
          <div><h2 className="font-display text-base font-extrabold">Application revenue readiness</h2><p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Partner attribution captured at click time; expected payout is planning data until reconciled with partner reports.</p></div>
          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Stat label="Apply clicks" value={applicationPerformance.total_clicks || 0} />
            <Stat label="Partner clicks" value={applicationPerformance.partner_clicks || 0} />
            <Stat label="Monetised click rate" value={`${applicationPerformance.monetised_click_rate || 0}%`} />
            <Stat label="Expected pipeline" value={`₹${Number(applicationPerformance.expected_payout_pipeline || 0).toLocaleString("en-IN")}`} />
          </div>
          {(applicationPerformance.by_partner || []).length > 0 && <div className="mt-4 space-y-2">{applicationPerformance.by_partner.map((partner) => <Bar key={partner.label} label={partner.label} count={partner.count} pct={partner.pct} max={100} usePct />)}</div>}
        </div>

        {/* reminders */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="flex items-center gap-2 text-sm" style={{ color: "var(--ciq-ink)" }}>
            <Clock className="h-4 w-4" style={{ color: "var(--ciq-amber)" }} />
            <span><strong>{incomplete}</strong> people started but didn't finish</span>
          </div>
          <button
            onClick={runReminders}
            disabled={sending || incomplete === 0}
            className="ciq-press flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-sm font-semibold text-white"
            style={{ background: "var(--ciq-teal-600)", opacity: incomplete === 0 ? 0.5 : 1 }}
          >
            {sending ? <Loader2 className="h-4 w-4 ciq-spin" /> : <Send className="h-4 w-4" />} Send reminders
          </button>
        </div>
        {reminderMsg && <p className="mt-2 text-sm" style={{ color: "var(--ciq-teal)" }}>{reminderMsg}</p>}

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
        </>}

        {activeSection === "issuers" && <section className="rounded-3xl border bg-white p-4 md:p-5" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5" style={{ color: "var(--ciq-teal-600)" }} />
                <h2 className="font-display text-lg font-extrabold" style={{ color: "var(--ciq-ink)" }}>Issuer coverage</h2>
              </div>
              <p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Live coverage calculated from the admin card catalog.</p>
            </div>
            <div className="flex gap-2">
              <div className="rounded-xl px-3 py-2 text-center" style={{ background: "#eef9f6" }}>
                <div className="font-display text-lg font-extrabold" style={{ color: "var(--ciq-ink)" }}>{adminCards.length}</div>
                <div className="text-[10px] uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>Cards</div>
              </div>
              <div className="rounded-xl px-3 py-2 text-center" style={{ background: "#eef9f6" }}>
                <div className="font-display text-lg font-extrabold" style={{ color: "var(--ciq-ink)" }}>{issuerCoverage.length}</div>
                <div className="text-[10px] uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>Issuers</div>
              </div>
            </div>
          </div>
          <div className="mt-5 overflow-hidden rounded-2xl border" style={{ borderColor: "var(--ciq-line)" }}>
            <div className="grid grid-cols-[1fr_auto] gap-4 px-4 py-2.5 text-[10px] font-semibold uppercase tracking-wider" style={{ background: "#f7f8f6", color: "var(--ciq-ink-soft)" }}>
              <span>Card issuer</span><span>Cards</span>
            </div>
            <div className="divide-y" style={{ borderColor: "var(--ciq-line)" }}>
              {issuerCoverage.map(([issuer, count]) => (
                <div key={issuer} className="grid grid-cols-[1fr_auto] items-center gap-4 px-4 py-3 text-sm">
                  <span className="font-semibold" style={{ color: "var(--ciq-ink)" }}>{issuer}</span>
                  <span className="min-w-9 rounded-full px-2.5 py-1 text-center text-xs font-bold" style={{ background: "#e6f5f0", color: "var(--ciq-teal)" }}>{count}</span>
                </div>
              ))}
            </div>
          </div>
        </section>}

        {activeSection === "health" && <section className="rounded-3xl border bg-white p-4 md:p-5" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="flex items-start justify-between gap-3"><div><div className="flex items-center gap-2"><Activity className="h-5 w-5" style={{ color: "var(--ciq-teal-600)" }} /><h2 className="font-display text-lg font-extrabold">Catalog health</h2></div><p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Checks images, links, completeness, verification dates and duplicates.</p></div><div className="rounded-xl px-3 py-2 text-center" style={{ background: healthIssues.length ? "#fff3cd" : "#e6f5f0" }}><div className="font-display text-xl font-extrabold">{healthIssues.length}</div><div className="text-[10px] uppercase">Issues</div></div></div>
          <div className="mt-5 space-y-2">
            {healthIssues.length === 0 && <div className="rounded-2xl p-6 text-center text-sm" style={{ background: "#eef9f6", color: "var(--ciq-teal)" }}>All catalog checks passed.</div>}
            {healthIssues.map(({ card, issue }, index) => <div key={`${card.id}-${issue}-${index}`} className="flex items-center justify-between gap-3 rounded-xl border px-3 py-2.5" style={{ borderColor: "var(--ciq-line)" }}><div><div className="text-sm font-semibold">{card.name}</div><div className="text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{card.issuer}</div></div><div className="flex items-center gap-2"><span className="text-xs font-semibold" style={{ color: "#9a6700" }}>{issue}</span>{canEdit && <button onClick={() => { setEditingCard(card); }} className="rounded-lg border px-2 py-1 text-xs" style={{ borderColor: "var(--ciq-line)" }}>Fix</button>}</div></div>)}
          </div>
        </section>}

        {activeSection === "reviews" && <section className="rounded-3xl border bg-white p-4 md:p-5" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex items-center gap-2"><MessageSquare className="h-5 w-5" style={{ color: "var(--ciq-teal-600)" }} /><h2 className="font-display text-lg font-extrabold">Cardholder reviews</h2></div><p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Moderate genuine cardholder feedback before it contributes to public scores.</p></div>{canEdit && <button onClick={runReviewReminders} disabled={sending} className="rounded-xl px-3 py-2 text-sm font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>{sending ? "Sending…" : "Send due reminders"}</button>}</div>
          {reminderMsg && <p className="mt-3 text-xs" style={{ color: "var(--ciq-teal)" }}>{reminderMsg}</p>}
          <div className="mt-5 space-y-3">{reviews.length === 0 && <Empty />}{reviews.map((review) => <div key={review.review_id} className="rounded-2xl border p-4" style={{ borderColor: "var(--ciq-line)" }}><div className="flex flex-wrap items-start justify-between gap-2"><div><div className="font-display text-sm font-bold">{review.card_name}</div><div className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Overall {review.overall}/5 · Rewards {review.rewards}/5 · Service {review.service}/5</div></div><span className="rounded-full px-2 py-1 text-[10px] font-bold uppercase" style={{ background: review.status === "approved" ? "#e6f5f0" : review.status === "rejected" ? "#fdeceb" : "#fff3cd", color: "var(--ciq-ink-soft)" }}>{review.status}</span></div>{review.comments && <p className="mt-3 text-sm" style={{ color: "var(--ciq-ink)" }}>{review.comments}</p>}{review.status === "pending" && canPublish && <div className="mt-3 flex gap-2"><button onClick={() => moderateReview(review, "approved")} className="rounded-lg px-3 py-1.5 text-xs font-semibold text-white" style={{ background: "var(--ciq-teal-600)" }}>Approve</button><button onClick={() => moderateReview(review, "rejected")} className="rounded-lg border px-3 py-1.5 text-xs font-semibold" style={{ borderColor: "#e4b5b1", color: "#a33b35" }}>Reject</button></div>}</div>)}</div>
        </section>}

        {activeSection === "alerts" && <section className="rounded-3xl border bg-white p-4 md:p-5" style={{ borderColor: "var(--ciq-line)" }}><h2 className="font-display text-lg font-extrabold">Publish a card-change alert</h2><p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Publisher review is required. The source must already be attached to the card; a unique key prevents duplicate sends.</p><form onSubmit={publishAlert} className="mt-4 grid gap-3"><select required value={alertDraft.card_id} onChange={(e) => { const card = adminCards.find((item) => item.id === e.target.value); setAlertDraft({ ...alertDraft, card_id: e.target.value, source_url: card?.sourceUrls?.[0] || "" }); }} className="rounded-xl border px-3 py-2.5"><option value="">Choose card…</option>{adminCards.filter((card) => card.active !== false).map((card) => <option key={card.id} value={card.id}>{card.name} — {card.issuer}</option>)}</select><input required minLength="5" maxLength="120" placeholder="Change title" value={alertDraft.title} onChange={(e) => setAlertDraft({ ...alertDraft, title: e.target.value })} className="rounded-xl border px-3 py-2.5" /><textarea required minLength="20" maxLength="1000" rows="4" placeholder="What changed and why it matters" value={alertDraft.summary} onChange={(e) => setAlertDraft({ ...alertDraft, summary: e.target.value })} className="rounded-xl border px-3 py-2.5" /><input required type="url" placeholder="Verified issuer source" value={alertDraft.source_url} onChange={(e) => setAlertDraft({ ...alertDraft, source_url: e.target.value })} className="rounded-xl border px-3 py-2.5" /><input required minLength="8" pattern="[A-Za-z0-9._-]+" placeholder="Unique key, e.g. card-fee-2026-10" value={alertDraft.idempotency_key} onChange={(e) => setAlertDraft({ ...alertDraft, idempotency_key: e.target.value })} className="rounded-xl border px-3 py-2.5" />{alertMsg && <p className="text-sm">{alertMsg}</p>}<button disabled={!canPublish || sending} className="rounded-xl py-3 font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>{sending ? "Sending…" : "Review complete — send alert"}</button></form></section>}

        {activeSection === "links" && <section className="rounded-3xl border bg-white p-4 md:p-5" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <CreditCard className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} />
                <h2 className="font-display text-lg font-extrabold" style={{ color: "var(--ciq-ink)" }}>Card catalog</h2>
              </div>
              <p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Add cards, edit product details and manage apply-now links.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <label className="flex min-w-[220px] items-center gap-2 rounded-xl border px-3 py-2" style={{ borderColor: "var(--ciq-line)" }}>
                <Search className="h-4 w-4" style={{ color: "var(--ciq-ink-soft)" }} />
                <input value={cardSearch} onChange={(e) => setCardSearch(e.target.value)} placeholder="Search card or issuer" className="w-full bg-transparent text-sm outline-none" />
              </label>
              <button onClick={() => downloadCatalog("json")} className="ciq-press inline-flex items-center gap-1 rounded-xl border px-2.5 py-2 text-xs font-semibold" style={{ borderColor: "var(--ciq-line)" }}><Download className="h-3.5 w-3.5" /> JSON</button>
              <button onClick={() => downloadCatalog("csv")} className="ciq-press inline-flex items-center gap-1 rounded-xl border px-2.5 py-2 text-xs font-semibold" style={{ borderColor: "var(--ciq-line)" }}><Download className="h-3.5 w-3.5" /> CSV</button>
              {canEdit && <><input ref={importInput} type="file" accept="application/json,.json" className="hidden" onChange={(e) => e.target.files?.[0] && importCatalog(e.target.files[0])} /><button onClick={() => importInput.current?.click()} className="ciq-press inline-flex items-center gap-1 rounded-xl border px-2.5 py-2 text-xs font-semibold" style={{ borderColor: "var(--ciq-line)" }}><Upload className="h-3.5 w-3.5" /> Import</button></>}
              {canEdit && <button onClick={() => setEditingCard({})} className="ciq-press inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold text-white" style={{ background: "var(--ciq-teal-600)" }}>
                <Plus className="h-4 w-4" /> Add card
              </button>}
            </div>
          </div>
          {linkMsg && <p className="mt-3 text-sm" style={{ color: linkMsg.type === "error" ? "#b4433f" : "var(--ciq-teal)" }}>{linkMsg.text}</p>}
          <div className="mt-4 max-h-[560px] space-y-3 overflow-y-auto pr-1">
            {filteredCards.map((card) => {
              const draft = linkDrafts[card.id] || linkDraft(card);
              const dirty = JSON.stringify(draft) !== JSON.stringify(linkDraft(card));
              const updateDraft = (key, value) => setLinkDrafts((values) => ({ ...values, [card.id]: { ...draft, [key]: value } }));
              return (
                <div key={card.id} className="rounded-2xl border p-3.5" style={{ borderColor: "var(--ciq-line)" }}>
                  <div className="flex flex-wrap items-baseline justify-between gap-1">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-display text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>{card.name}</span>
                        {card.has_draft && <span className="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide" style={{ background: "#fff3cd", color: "#7a5b00" }}>{card.is_new_draft ? "New draft" : "Draft changes"}</span>}
                      </div>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {(card.variants || [card.network]).filter(Boolean).map((variant) => <span key={variant} className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: "#eef0ec", color: "var(--ciq-ink-soft)" }}>{variant}</span>)}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{card.issuer}</span>
                      {canEdit && <button onClick={() => setEditingCard(card)} className="ciq-press inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-xs font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}><Pencil className="h-3 w-3" /> Edit</button>}
                      <button onClick={() => openHistory(card)} className="ciq-press inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-xs font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}><History className="h-3 w-3" /> History</button>
                      {card.has_draft && <button onClick={() => setPreviewCard(card)} className="ciq-press rounded-lg px-2 py-1 text-xs font-semibold text-white" style={{ background: "var(--ciq-teal-600)" }}>Preview</button>}
                      {canPublish && !card.has_draft && <button onClick={() => toggleArchive(card)} className="ciq-press inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-xs font-semibold" style={{ borderColor: "var(--ciq-line)", color: card.publication_status === "archived" ? "var(--ciq-teal)" : "#8b4b47" }}><Archive className="h-3 w-3" /> {card.publication_status === "archived" ? "Restore" : "Archive"}</button>}
                    </div>
                  </div>
                  <div className="mt-2 flex flex-col gap-2 md:flex-row">
                    <input
                      type="url"
                      value={draft.url}
                      onChange={(e) => updateDraft("url", e.target.value)}
                      placeholder={card.official_apply_url}
                      className="min-w-0 flex-1 rounded-xl border px-3 py-2 text-sm outline-none"
                      style={{ borderColor: "var(--ciq-line)" }}
                    />
                    <button onClick={() => saveApplyLink(card)} disabled={!canEdit || !dirty || savingCard === card.id} className="ciq-press inline-flex items-center justify-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>
                      {savingCard === card.id ? <Loader2 className="h-4 w-4 ciq-spin" /> : <Save className="h-4 w-4" />} Save
                    </button>
                    {card.custom_apply_url && <button onClick={() => saveApplyLink(card, null)} disabled={savingCard === card.id} className="ciq-press rounded-xl border px-3 py-2 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>Reset</button>}
                  </div>
                  <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
                    <input value={draft.partner} onChange={(e) => updateDraft("partner", e.target.value)} placeholder="Partner name" className="rounded-xl border px-3 py-2 text-xs" style={{ borderColor: "var(--ciq-line)" }} />
                    <input value={draft.campaign} onChange={(e) => updateDraft("campaign", e.target.value)} placeholder="Campaign ID" className="rounded-xl border px-3 py-2 text-xs" style={{ borderColor: "var(--ciq-line)" }} />
                    <input value={draft.tracking} onChange={(e) => updateDraft("tracking", e.target.value)} placeholder="Tracking ID" className="rounded-xl border px-3 py-2 text-xs" style={{ borderColor: "var(--ciq-line)" }} />
                    <select value={draft.status} onChange={(e) => updateDraft("status", e.target.value)} className="rounded-xl border px-3 py-2 text-xs" style={{ borderColor: "var(--ciq-line)" }}><option value="testing">Testing</option><option value="live">Live</option><option value="paused">Paused</option></select>
                    <input min="0" step="0.01" type="number" value={draft.payout} onChange={(e) => updateDraft("payout", e.target.value)} placeholder="Expected ₹ payout" className="rounded-xl border px-3 py-2 text-xs" style={{ borderColor: "var(--ciq-line)" }} />
                  </div>
                  <p className="mt-1.5 text-[10px]" style={{ color: "var(--ciq-ink-soft)" }}>Only a <strong>Live</strong> partner link reaches customers. Testing or paused links automatically fall back to the official issuer URL.</p>
                  <a href={card.official_apply_url} target="_blank" rel="noopener noreferrer" className="mt-1.5 block truncate text-xs underline" style={{ color: "var(--ciq-ink-soft)" }}>Official: {card.official_apply_url}</a>
                </div>
              );
            })}
            {filteredCards.length === 0 && <Empty />}
          </div>
        </section>}

        {editingCard && <CardEditor key={editingCard.id || "new"} card={editingCard} saving={Boolean(savingCard)} onClose={() => setEditingCard(null)} onSave={saveCatalogCard} />}
        {previewCard && <DraftPreview card={previewCard} canEdit={canEdit} canPublish={canPublish} saving={savingCard === previewCard.id} onRecommendationPreview={(answers) => previewAdminCardRecommendation(token, previewCard.id, answers)} onClose={() => setPreviewCard(null)} onPublish={() => publishCard(previewCard)} onDiscard={() => discardDraft(previewCard)} />}
        {historyCard && <HistoryModal card={historyCard} versions={versions} canRollback={canPublish} onRollback={(versionId) => rollbackVersion(historyCard, versionId)} onClose={() => setHistoryCard(null)} />}

        {activeSection === "leads" && <section>
        <div className="mt-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="font-display text-xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>Leads</h2>
            <p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Most recent first · {data?.total || 0} total</p>
          </div>
          <button onClick={downloadCsv} className="ciq-press flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold text-white" style={{ background: "var(--ciq-teal-600)" }}>
            <Download className="h-4 w-4" /> Export CSV
          </button>
        </div>

        <div className="mt-4 space-y-3">
          {leads.length === 0 && (
            <div className="rounded-2xl border bg-white p-6 text-center text-sm" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink-soft)" }}>No leads in this period.</div>
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
        </section>}
      </div>
    </div>
  );
}

const NEW_CARD = {
  name: "", issuer: "", variants: [], productGroupId: "", variantName: "", network: "Visa", tagline: "",
  annualFee: "No annual fee", annualFeeAmount: 0, joiningFee: "No joining fee", joiningFeeAmount: 0,
  rewardLine: "", highlights: [], bestFor: [], feeType: "free", minSpend: "low",
  welcomeBenefits: [], milestoneBenefits: [], loungeBenefits: [], exclusions: [],
  rewardCurrency: "", rewardRedemption: "", forexMarkup: "", fuelBenefits: "", eligibilityNote: "", sourceUrls: [],
  editorial: { summary: "", idealFor: [], strengths: [], tradeoffs: [], verdict: "", alternatives: [] },
  editorialReviewed: false,
  creditReq: "good", rating: 4, applyUrl: "", imageUrl: "", active: true, applicationsOpen: true,
};

function HistoryModal({ card, versions, canRollback, onRollback, onClose }) {
  return <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4"><div className="w-full max-w-lg rounded-3xl bg-white p-5"><div className="flex items-start justify-between"><div><div className="text-xs font-bold uppercase tracking-wide" style={{ color: "var(--ciq-teal)" }}>Change history</div><h2 className="mt-1 font-display text-xl font-extrabold">{card.name}</h2></div><button onClick={onClose} className="rounded-full border p-2" style={{ borderColor: "var(--ciq-line)" }}><X className="h-4 w-4" /></button></div><div className="mt-4 space-y-2">{versions.length === 0 && <div className="rounded-xl p-4 text-sm" style={{ background: "#f7f8f6", color: "var(--ciq-ink-soft)" }}>No earlier published versions yet.</div>}{versions.map((version, index) => <div key={version.version_id} className="flex items-center justify-between gap-3 rounded-xl border p-3" style={{ borderColor: "var(--ciq-line)" }}><div><div className="text-sm font-semibold">Version {versions.length - index}</div><div className="text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{new Date(version.created_at).toLocaleString()}</div></div>{canRollback && <button onClick={() => onRollback(version.version_id)} className="rounded-lg border px-2.5 py-1.5 text-xs font-semibold" style={{ borderColor: "var(--ciq-line)" }}>Restore as draft</button>}</div>)}</div></div></div>;
}

const PREVIEW_PROFILES = {
  "Cashback starter": { goal: "cashback", spend: "low", fee: "free", usage: "online", priority: "cashback", creditRoute: "secured" },
  "Everyday rewards": { goal: "shopping", spend: "mid", fee: "worth", usage: "dining", priority: "rewards", creditRoute: "either" },
  "Premium traveller": { goal: "travel", spend: "high", fee: "premium", usage: "flights", priority: "lounge", creditRoute: "regular" },
};

function DraftPreview({ card, canEdit, canPublish, saving, onClose, onPublish, onDiscard, onRecommendationPreview }) {
  const [impact, setImpact] = useState(null);
  const [checking, setChecking] = useState(false);
  const checkImpact = async (answers) => { setChecking(true); try { setImpact(await onRecommendationPreview(answers)); } finally { setChecking(false); } };
  return <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
    <div className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-3xl bg-white p-5" style={{ color: "var(--ciq-ink)" }}>
      <div className="flex items-start justify-between gap-3">
        <div><div className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>Draft preview</div><h2 className="mt-1 font-display text-2xl font-extrabold">{card.name}</h2><p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{card.issuer} · {(card.variants || [card.network]).filter(Boolean).join(" · ")}</p></div>
        <button onClick={onClose} className="rounded-full border p-2" style={{ borderColor: "var(--ciq-line)" }}><X className="h-4 w-4" /></button>
      </div>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <PreviewFact label="Annual fee" value={card.annualFee} />
        <PreviewFact label="Joining fee" value={card.joiningFee} />
        <PreviewFact label="Reward summary" value={card.rewardLine} wide />
        <PreviewFact label="Rating" value={`${card.rating}/5`} />
        <PreviewFact label="Status after publishing" value={card.active && card.applicationsOpen ? "Live and recommendable" : "Not shown in recommendations"} />
        <PreviewFact label="Editorial take" value={card.editorial?.summary} wide />
        <PreviewFact label="Editorial verdict" value={card.editorial?.verdict} wide />
      </div>
      {(card.highlights || []).length > 0 && <div className="mt-4 rounded-2xl border p-4" style={{ borderColor: "var(--ciq-line)" }}><div className="text-xs font-bold uppercase tracking-wide">Highlights</div><ul className="mt-2 list-disc space-y-1 pl-5 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{card.highlights.map((item) => <li key={item}>{item}</li>)}</ul></div>}
      <div className="mt-4 rounded-2xl border p-4" style={{ borderColor: "var(--ciq-line)" }}><div className="text-xs font-bold uppercase tracking-wide">Recommendation impact</div><p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Test where this draft ranks for a representative customer.</p><div className="mt-3 flex flex-wrap gap-2">{Object.entries(PREVIEW_PROFILES).map(([label, answers]) => <button key={label} disabled={checking} onClick={() => checkImpact(answers)} className="rounded-lg border px-2.5 py-1.5 text-xs font-semibold" style={{ borderColor: "var(--ciq-line)" }}>{label}</button>)}</div>{checking && <div className="mt-3 text-xs">Calculating…</div>}{impact && <div className="mt-3 rounded-xl p-3 text-sm" style={{ background: "#eef9f6" }}><strong>Rank #{impact.rank || "—"}</strong> of {impact.total} · {impact.confidence ?? "—"}% match<div className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Top card: {impact.top_card}</div></div>}</div>
      <p className="mt-4 rounded-xl px-3 py-2 text-xs" style={{ background: "#eef9f6", color: "var(--ciq-ink-soft)" }}>Publishing makes this version available to the customer catalog and recommendation engine. Discarding leaves the current published card unchanged.</p>
      <div className="mt-5 flex flex-wrap justify-end gap-2">
        {canEdit && <button disabled={saving} onClick={onDiscard} className="rounded-xl border px-4 py-2.5 text-sm font-semibold" style={{ borderColor: "#e4b5b1", color: "#a33b35" }}>Discard draft</button>}
        {canPublish && <button disabled={saving} onClick={onPublish} className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60" style={{ background: "var(--ciq-teal-600)" }}>{saving ? <Loader2 className="h-4 w-4 ciq-spin" /> : <CheckPublishIcon />} Publish card</button>}
      </div>
    </div>
  </div>;
}

function PreviewFact({ label, value, wide }) {
  return <div className={`rounded-xl p-3 ${wide ? "col-span-2" : ""}`} style={{ background: "#f7f8f6" }}><div className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>{label}</div><div className="mt-1 text-sm font-bold">{value || "Not specified"}</div></div>;
}

function CheckPublishIcon() { return <Save className="h-4 w-4" />; }

function CardEditor({ card, saving, onClose, onSave }) {
  const [form, setForm] = useState({ ...NEW_CARD, ...card, editorial: { ...NEW_CARD.editorial, ...(card.editorial || {}) }, applyUrl: card.applyUrl || card.official_apply_url || "" });
  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const setEditorial = (key, value) => setForm((current) => ({ ...current, editorial: { ...current.editorial, [key]: value } }));
  const submit = (e) => {
    e.preventDefault();
    onSave({
      ...form,
      variants: Array.isArray(form.variants) ? form.variants : String(form.variants || "").split(",").map((v) => v.trim()).filter(Boolean),
      highlights: Array.isArray(form.highlights) ? form.highlights : String(form.highlights || "").split("\n").map((v) => v.trim()).filter(Boolean),
      welcomeBenefits: lines(form.welcomeBenefits), milestoneBenefits: lines(form.milestoneBenefits),
      loungeBenefits: lines(form.loungeBenefits), exclusions: lines(form.exclusions), sourceUrls: lines(form.sourceUrls),
      bestFor: Array.isArray(form.bestFor) ? form.bestFor : String(form.bestFor || "").split(",").map((v) => v.trim()).filter(Boolean),
      editorial: form.editorial.summary || form.editorial.verdict ? {
        ...form.editorial,
        idealFor: lines(form.editorial.idealFor), strengths: lines(form.editorial.strengths), tradeoffs: lines(form.editorial.tradeoffs),
        alternatives: parseAlternatives(form.editorial.alternatives),
      } : null,
      annualFeeAmount: Number(form.annualFeeAmount), joiningFeeAmount: Number(form.joiningFeeAmount), rating: Number(form.rating),
    });
  };
  const inputClass = "w-full rounded-xl border bg-white px-3 py-2 text-sm outline-none";
  const labelClass = "space-y-1 text-xs font-semibold";
  return <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4">
    <form onSubmit={submit} className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-t-3xl bg-white p-5 sm:rounded-3xl" style={{ color: "var(--ciq-ink)" }}>
      <div className="flex items-start justify-between gap-3">
        <div><h2 className="font-display text-xl font-extrabold">{card.id ? "Edit card draft" : "Create a card draft"}</h2><p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Nothing reaches customers until you preview and publish it. Variants can be separated by commas.</p></div>
        <button type="button" onClick={onClose} className="rounded-full border p-2" style={{ borderColor: "var(--ciq-line)" }} aria-label="Close"><X className="h-4 w-4" /></button>
      </div>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <label className={labelClass}>Card name<input required className={inputClass} value={form.name} onChange={(e) => set("name", e.target.value)} /></label>
        <label className={labelClass}>Issuer<input required className={inputClass} value={form.issuer} onChange={(e) => set("issuer", e.target.value)} /></label>
        <label className={labelClass}>Card variants<input className={inputClass} value={Array.isArray(form.variants) ? form.variants.join(", ") : form.variants} onChange={(e) => set("variants", e.target.value)} placeholder="Visa, Mastercard, RuPay" /></label>
        <label className={labelClass}>Primary network<input className={inputClass} value={form.network} onChange={(e) => set("network", e.target.value)} /></label>
        <label className={labelClass}>Product family ID<input className={inputClass} value={form.productGroupId || ""} onChange={(e) => set("productGroupId", e.target.value)} placeholder="tata-neu-hdfc" /></label>
        <label className={labelClass}>Variant name<input className={inputClass} value={form.variantName || ""} onChange={(e) => set("variantName", e.target.value)} placeholder="Infinity RuPay" /></label>
        <label className={`${labelClass} sm:col-span-2`}>Tagline<input className={inputClass} value={form.tagline} onChange={(e) => set("tagline", e.target.value)} /></label>
        <label className={`${labelClass} sm:col-span-2`}>Reward summary<input required className={inputClass} value={form.rewardLine} onChange={(e) => set("rewardLine", e.target.value)} /></label>
        <label className={labelClass}>Annual fee<input className={inputClass} value={form.annualFee} onChange={(e) => set("annualFee", e.target.value)} /></label>
        <label className={labelClass}>Annual fee amount<input min="0" type="number" className={inputClass} value={form.annualFeeAmount} onChange={(e) => set("annualFeeAmount", e.target.value)} /></label>
        <label className={labelClass}>Joining fee<input className={inputClass} value={form.joiningFee} onChange={(e) => set("joiningFee", e.target.value)} /></label>
        <label className={labelClass}>Joining fee amount<input min="0" type="number" className={inputClass} value={form.joiningFeeAmount} onChange={(e) => set("joiningFeeAmount", e.target.value)} /></label>
        <label className={labelClass}>Fee tier<select className={inputClass} value={form.feeType} onChange={(e) => set("feeType", e.target.value)}>{["free", "worth", "premium"].map((v) => <option key={v}>{v}</option>)}</select></label>
        <label className={labelClass}>Minimum spend<select className={inputClass} value={form.minSpend} onChange={(e) => set("minSpend", e.target.value)}>{["low", "mid", "high", "vhigh"].map((v) => <option key={v}>{v}</option>)}</select></label>
        <label className={labelClass}>Credit requirement<select className={inputClass} value={form.creditReq} onChange={(e) => set("creditReq", e.target.value)}>{["new", "fair", "good", "excellent"].map((v) => <option key={v}>{v}</option>)}</select></label>
        <label className={labelClass}>CardIQ rating<input min="0" max="5" step="0.1" type="number" className={inputClass} value={form.rating} onChange={(e) => set("rating", e.target.value)} /></label>
        <label className={`${labelClass} sm:col-span-2`}>Best for <span className="font-normal">(comma-separated)</span><input className={inputClass} value={Array.isArray(form.bestFor) ? form.bestFor.join(", ") : form.bestFor} onChange={(e) => set("bestFor", e.target.value)} placeholder="cashback, shopping, online" /></label>
        <label className={`${labelClass} sm:col-span-2`}>Highlights <span className="font-normal">(one per line)</span><textarea rows="4" className={inputClass} value={Array.isArray(form.highlights) ? form.highlights.join("\n") : form.highlights} onChange={(e) => set("highlights", e.target.value)} /></label>
        <label className={labelClass}>Reward currency<input className={inputClass} value={form.rewardCurrency || ""} onChange={(e) => set("rewardCurrency", e.target.value)} placeholder="Cashback, Reward Points, Air Miles" /></label>
        <label className={labelClass}>Forex markup<input className={inputClass} value={form.forexMarkup || ""} onChange={(e) => set("forexMarkup", e.target.value)} placeholder="3.5% + GST" /></label>
        <label className={`${labelClass} sm:col-span-2`}>Reward redemption<textarea rows="2" className={inputClass} value={form.rewardRedemption || ""} onChange={(e) => set("rewardRedemption", e.target.value)} /></label>
        <label className={`${labelClass} sm:col-span-2`}>Welcome benefits <span className="font-normal">(one per line)</span><textarea rows="3" className={inputClass} value={listText(form.welcomeBenefits)} onChange={(e) => set("welcomeBenefits", e.target.value)} /></label>
        <label className={`${labelClass} sm:col-span-2`}>Milestone benefits <span className="font-normal">(one per line)</span><textarea rows="3" className={inputClass} value={listText(form.milestoneBenefits)} onChange={(e) => set("milestoneBenefits", e.target.value)} /></label>
        <label className={`${labelClass} sm:col-span-2`}>Lounge benefits <span className="font-normal">(one per line)</span><textarea rows="3" className={inputClass} value={listText(form.loungeBenefits)} onChange={(e) => set("loungeBenefits", e.target.value)} /></label>
        <label className={`${labelClass} sm:col-span-2`}>Reward exclusions <span className="font-normal">(one per line)</span><textarea rows="3" className={inputClass} value={listText(form.exclusions)} onChange={(e) => set("exclusions", e.target.value)} /></label>
        <label className={`${labelClass} sm:col-span-2`}>Fuel benefit<textarea rows="2" className={inputClass} value={form.fuelBenefits || ""} onChange={(e) => set("fuelBenefits", e.target.value)} /></label>
        <label className={`${labelClass} sm:col-span-2`}>Eligibility note<textarea rows="2" className={inputClass} value={form.eligibilityNote || ""} onChange={(e) => set("eligibilityNote", e.target.value)} /></label>
        <div className="sm:col-span-2 rounded-2xl border p-4" style={{ borderColor: "var(--ciq-line)", background: "#f7fbfa" }}>
          <div className="font-display text-sm font-extrabold">CardIQ editorial</div>
          <p className="mt-1 text-xs font-normal" style={{ color: "var(--ciq-ink-soft)" }}>Independent analysis shown on the card page. Edit this separately from issuer-sourced facts.</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <label className={`${labelClass} sm:col-span-2`}>Our take<textarea rows="3" className={inputClass} value={form.editorial.summary} onChange={(e) => setEditorial("summary", e.target.value)} /></label>
            <label className={labelClass}>Who it suits <span className="font-normal">(one per line)</span><textarea rows="5" className={inputClass} value={listText(form.editorial.idealFor)} onChange={(e) => setEditorial("idealFor", e.target.value)} /></label>
            <label className={labelClass}>Key strengths <span className="font-normal">(one per line)</span><textarea rows="5" className={inputClass} value={listText(form.editorial.strengths)} onChange={(e) => setEditorial("strengths", e.target.value)} /></label>
            <label className={`${labelClass} sm:col-span-2`}>Trade-offs <span className="font-normal">(one per line)</span><textarea rows="4" className={inputClass} value={listText(form.editorial.tradeoffs)} onChange={(e) => setEditorial("tradeoffs", e.target.value)} /></label>
            <label className={`${labelClass} sm:col-span-2`}>Verdict<textarea rows="3" className={inputClass} value={form.editorial.verdict} onChange={(e) => setEditorial("verdict", e.target.value)} /></label>
            <label className={`${labelClass} sm:col-span-2`}>Alternatives <span className="font-normal">(one per line: card-id | name | reason)</span><textarea rows="4" className={inputClass} value={alternativesText(form.editorial.alternatives)} onChange={(e) => setEditorial("alternatives", e.target.value)} /></label>
          </div>
          {card.id && <label className="mt-4 flex items-start gap-2 text-xs font-semibold"><input type="checkbox" checked={Boolean(form.editorialReviewed)} onChange={(e) => set("editorialReviewed", e.target.checked)} /><span>I reviewed this editorial against any fee, reward, benefit or availability changes in this draft.</span></label>}
        </div>
        <label className={`${labelClass} sm:col-span-2`}>Issuer source URLs <span className="font-normal">(one HTTPS URL per line)</span><textarea rows="3" className={inputClass} value={listText(form.sourceUrls)} onChange={(e) => set("sourceUrls", e.target.value)} /></label>
        <label className={`${labelClass} sm:col-span-2`}>Official apply URL<input required type="url" className={inputClass} value={form.applyUrl} onChange={(e) => set("applyUrl", e.target.value)} placeholder="https://issuer.example/card" /></label>
        <label className={`${labelClass} sm:col-span-2`}>Card image URL<input className={inputClass} value={form.imageUrl || ""} onChange={(e) => set("imageUrl", e.target.value)} placeholder="/cards/card.png or https://…" /></label>
      </div>
      <div className="mt-4 flex flex-wrap gap-5 text-sm">
        <label className="flex items-center gap-2"><input type="checkbox" checked={form.active} onChange={(e) => set("active", e.target.checked)} /> Active</label>
        <label className="flex items-center gap-2"><input type="checkbox" checked={form.applicationsOpen} onChange={(e) => set("applicationsOpen", e.target.checked)} /> Applications open</label>
      </div>
      <div className="mt-6 flex justify-end gap-2">
        <button type="button" onClick={onClose} className="rounded-xl border px-4 py-2.5 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)" }}>Cancel</button>
        <button disabled={saving} className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60" style={{ background: "var(--ciq-teal-600)" }}>{saving ? <Loader2 className="h-4 w-4 ciq-spin" /> : <Save className="h-4 w-4" />} Save draft</button>
      </div>
    </form>
  </div>;
}

function lines(value) { return Array.isArray(value) ? value : String(value || "").split("\n").map((item) => item.trim()).filter(Boolean); }
function listText(value) { return Array.isArray(value) ? value.join("\n") : value || ""; }
function alternativesText(value) { return Array.isArray(value) ? value.map((item) => `${item.id} | ${item.name} | ${item.reason}`).join("\n") : value || ""; }
function parseAlternatives(value) {
  if (Array.isArray(value)) return value;
  return lines(value).map((line) => { const [id, name, ...reason] = line.split("|").map((item) => item.trim()); return { id, name, reason: reason.join(" | ") }; }).filter((item) => item.id && item.name && item.reason);
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
