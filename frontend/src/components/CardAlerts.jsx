import React, { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Bell, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { getCards, subscribeCardAlerts } from "../api";
import { contactEmailError } from "../contactValidation";
import Logo from "./Logo";

export default function CardAlerts() {
  const [cards, setCards] = useState([]);
  const [form, setForm] = useState({ email: "", scope_type: "all", scope_value: "", alert_consent: false });
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  useEffect(() => { getCards().then((data) => setCards(Array.isArray(data) ? data : [])).catch(() => setCards([])); }, []);
  const issuers = useMemo(() => [...new Set(cards.map((card) => card.issuer))].sort(), [cards]);
  const options = form.scope_type === "issuer" ? issuers.map((value) => [value, value]) : form.scope_type === "card" ? cards.map((card) => [card.id, `${card.name} — ${card.issuer}`]) : [];
  const submit = async (event) => {
    event.preventDefault();
    const validation = contactEmailError(form.email);
    if (validation || !form.alert_consent || (form.scope_type !== "all" && !form.scope_value)) { setError(validation || "Choose an alert and confirm your consent."); return; }
    setStatus("sending"); setError("");
    try { await subscribeCardAlerts(form); setStatus("sent"); } catch (requestError) { setError(requestError?.response?.data?.detail || "We couldn’t save this alert."); setStatus("idle"); }
  };
  return <div className="ciq-shell min-h-screen pb-16"><header className="ciq-container flex items-center justify-between py-5"><Logo size="md" /><Link to="/" className="rounded-full border bg-white px-3 py-2 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)" }}><ArrowLeft className="mr-1 inline h-4 w-4" /> Home</Link></header><main className="ciq-container max-w-xl"><section className="pt-4 text-center"><span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl text-white" style={{ background: "var(--ciq-teal-600)" }}><Bell className="h-6 w-6" /></span><h1 className="mt-4 font-display text-3xl font-extrabold">Card change alerts</h1><p className="mt-2 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Follow the cards or issuers you care about. We’ll use this address only for the alerts you choose.</p></section>{status === "sent" ? <section className="mt-7 rounded-3xl border bg-white p-6 text-center" style={{ borderColor: "#b9e4da" }}><h2 className="font-display text-xl font-extrabold">Your alert is active</h2><p className="mt-2 text-sm">We saved this preference independently from marketing consent. Every alert email will include an unsubscribe option.</p></section> : <form onSubmit={submit} className="mt-7 space-y-4 rounded-3xl border bg-white p-5" style={{ borderColor: "var(--ciq-line)" }}><label className="block text-sm font-semibold">Email<input aria-label="Alert email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-1 w-full rounded-xl border px-3 py-2.5" /></label><label className="block text-sm font-semibold">Alert me about<select aria-label="Alert scope" value={form.scope_type} onChange={(e) => setForm({ ...form, scope_type: e.target.value, scope_value: "" })} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="all">Important changes across CardIQ</option><option value="issuer">One issuer</option><option value="card">One card</option></select></label>{options.length > 0 && <label className="block text-sm font-semibold">Choose {form.scope_type}<select aria-label="Alert choice" value={form.scope_value} onChange={(e) => setForm({ ...form, scope_value: e.target.value })} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="">Select…</option>{options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>}<label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={form.alert_consent} onChange={(e) => setForm({ ...form, alert_consent: e.target.checked })} className="mt-1" /><span>I agree to receive the card-change alerts selected above. This does not consent to marketing.</span></label>{error && <p role="alert" className="text-sm" style={{ color: "#a63e38" }}>{error}</p>}<button disabled={status === "sending"} className="ciq-primary-gradient flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 font-semibold text-white">{status === "sending" && <Loader2 className="h-4 w-4 ciq-spin" />}Create alert</button></form>}</main></div>;
}
