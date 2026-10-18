import React, { useState } from "react";
import { ArrowLeft, Calculator, ExternalLink, Loader2, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { calculateCardValue, trackApplyClick } from "../api";
import { recordProductEvent } from "../productAnalytics";
import Logo from "./Logo";

const SPEND_FIELDS = [
  ["online", "Online shopping"],
  ["dining", "Dining & food delivery"],
  ["travel", "Flights, hotels & travel"],
  ["fuel", "Fuel"],
  ["international", "International spends"],
  ["other", "Everything else"],
];

const EMPTY = Object.fromEntries(SPEND_FIELDS.map(([key]) => [key, ""]));

export default function ValueCalculator() {
  const [form, setForm] = useState({ ...EMPTY, lounge_visits: "0", fee_preference: "worth" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const submit = async (event) => {
    event.preventDefault();
    setLoading(true); setError("");
    try {
      const payload = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, key === "fee_preference" ? value : Number(value || 0)]));
      setResult(await calculateCardValue(payload));
      recordProductEvent("calculator_completed");
      window.setTimeout(() => {
        const results = document.getElementById("value-results");
        if (typeof results?.scrollIntoView === "function") results.scrollIntoView({ behavior: "smooth" });
      }, 0);
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || "We couldn’t calculate this scenario. Please try again.");
    } finally { setLoading(false); }
  };

  const apply = (card) => {
    if (!card.applyUrl) return;
    trackApplyClick(card.id, null).catch(() => {});
    window.open(card.applyUrl, "_blank", "noopener,noreferrer");
  };

  return <div className="ciq-shell min-h-screen pb-16">
    <header className="ciq-container ciq-container--wide flex items-center justify-between py-5">
      <Logo size="md" />
      <Link to="/" className="ciq-press inline-flex items-center gap-1.5 rounded-full border bg-white px-3 py-2 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)" }}><ArrowLeft className="h-4 w-4" /> Home</Link>
    </header>
    <main className="ciq-container ciq-container--reading">
      <section className="pt-4 text-center">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl text-white" style={{ background: "linear-gradient(145deg,#604ee8,#0e9e98)" }}><Calculator className="h-6 w-6" /></span>
        <div className="mt-4 text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>No sign-up required</div>
        <h1 className="mt-2 font-display text-3xl font-extrabold">Credit card value calculator</h1>
        <p className="mx-auto mt-2 max-w-lg text-sm leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>Enter a typical month of spending. CardIQ will compare the live catalogue and show an honest annual-value range after published annual fees.</p>
      </section>

      <form onSubmit={submit} className="mt-7 rounded-3xl border bg-white p-5" style={{ borderColor: "var(--ciq-line)" }}>
        <h2 className="font-display text-lg font-extrabold">Your monthly spending</h2>
        <p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Use approximate amounts. Do not enter card numbers, account details or transaction data.</p>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {SPEND_FIELDS.map(([key, label]) => <label key={key} className="text-xs font-semibold">{label}<span className="mt-1 flex items-center rounded-xl border bg-white px-3" style={{ borderColor: "var(--ciq-line)" }}><span style={{ color: "var(--ciq-ink-soft)" }}>₹</span><input aria-label={label} min="0" max="2000000" inputMode="numeric" type="number" value={form[key]} onChange={(event) => set(key, event.target.value)} placeholder="0" className="w-full bg-transparent px-2 py-2.5 text-sm outline-none" /></span></label>)}
          <label className="text-xs font-semibold">Airport lounge visits per year<input aria-label="Airport lounge visits per year" min="0" max="100" type="number" value={form.lounge_visits} onChange={(event) => set("lounge_visits", event.target.value)} className="mt-1 w-full rounded-xl border bg-white px-3 py-2.5 text-sm outline-none" style={{ borderColor: "var(--ciq-line)" }} /></label>
          <label className="text-xs font-semibold">Annual-fee preference<select aria-label="Annual-fee preference" value={form.fee_preference} onChange={(event) => set("fee_preference", event.target.value)} className="mt-1 w-full rounded-xl border bg-white px-3 py-2.5 text-sm outline-none" style={{ borderColor: "var(--ciq-line)" }}><option value="free">Lifetime-free only preferred</option><option value="worth">Pay a fee when value justifies it</option><option value="premium">Premium benefits are welcome</option></select></label>
        </div>
        {error && <p role="alert" className="mt-4 rounded-xl px-3 py-2 text-sm" style={{ background: "#fff3cd", color: "#7a5b00" }}>{error}</p>}
        <button disabled={loading} className="ciq-press ciq-primary-gradient mt-5 inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 font-semibold text-white disabled:opacity-60">{loading ? <Loader2 className="h-5 w-5 ciq-spin" /> : <Calculator className="h-5 w-5" />} Compare annual value</button>
      </form>

      {result && <section id="value-results" className="mt-8">
        <div className="rounded-2xl border p-4" style={{ borderColor: "#b9e4da", background: "#f2faf7" }}><div className="flex items-center gap-2 font-display font-extrabold"><ShieldCheck className="h-5 w-5" style={{ color: "var(--ciq-teal)" }} /> Your scenario</div><p className="mt-1 text-sm">₹{result.monthlySpend.toLocaleString("en-IN")} a month · ₹{result.annualSpend.toLocaleString("en-IN")} a year</p><p className="mt-2 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>These are editorial ranges, not guaranteed returns. CardIQ uses your spending, catalogue categories, published fees and explicitly priced benefits. Actual rewards depend on merchant classification, caps, exclusions and redemption choices.</p></div>
        <h2 className="mt-6 font-display text-xl font-extrabold">Strongest value matches</h2>
        <div className="mt-3 grid gap-3 lg:grid-cols-2">{result.results.slice(0, 5).map((item, index) => <article key={item.card.id} className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="flex items-start justify-between gap-3"><div><div className="text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--ciq-teal)" }}>#{index + 1} value match</div><h3 className="mt-1 font-display text-base font-extrabold">{item.card.name}</h3><p className="text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{item.card.issuer}</p></div><div className="text-right"><div className="font-display text-base font-extrabold" style={{ color: "var(--ciq-teal)" }}>₹{item.valueEstimate.netLow.toLocaleString("en-IN")}–₹{item.valueEstimate.netHigh.toLocaleString("en-IN")}</div><div className="text-[10px]" style={{ color: "var(--ciq-ink-soft)" }}>estimated yearly net value</div></div></div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-xs"><ValueFact label="Rewards range" value={`₹${item.valueEstimate.grossLow.toLocaleString("en-IN")}–₹${item.valueEstimate.grossHigh.toLocaleString("en-IN")}`} /><ValueFact label="Annual fee used" value={item.valueEstimate.feeWaived ? "Waived" : `₹${item.valueEstimate.effectiveAnnualFee.toLocaleString("en-IN")}`} /></div>
          <p className="mt-3 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>{item.card.rewardLine}</p>
          <div className="mt-2 flex items-center justify-between rounded-xl px-3 py-2 text-[10px]" style={{ background: item.valueEstimate.economicsQuality === "high" ? "#eef9f6" : "#fff8e8", color: "var(--ciq-ink-soft)" }}><span className="font-bold uppercase tracking-wide">{item.valueEstimate.economicsQuality || "limited"} data confidence</span><span>{item.valueEstimate.economicsCoverage ?? 0}% economics structured</span></div>
          <div className="mt-3 grid grid-cols-2 gap-2"><Link to={`/cards/${encodeURIComponent(item.card.id)}`} className="rounded-xl border py-2.5 text-center text-xs font-semibold" style={{ borderColor: "var(--ciq-line)" }}>See full details</Link><button type="button" disabled={!item.card.applyUrl} onClick={() => apply(item.card)} className="inline-flex items-center justify-center gap-1 rounded-xl py-2.5 text-xs font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>Apply on bank <ExternalLink className="h-3.5 w-3.5" /></button></div>
        </article>)}</div>
      </section>}
    </main>
  </div>;
}

function ValueFact({ label, value }) {
  return <div className="rounded-xl p-3" style={{ background: "#f7f8f6" }}><div className="text-[10px] uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>{label}</div><div className="mt-1 font-bold">{value}</div></div>;
}
