import CreditCardVisual from "./CreditCardVisual";
import CustomerNav from "./CustomerNav";
import React, { useState } from "react";
import { ArrowLeft, Calculator, Loader2, ShieldCheck } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { calculateCardValue } from "../api";
import { recordProductEvent } from "../productAnalytics";
import Logo from "./Logo";

const SPEND_FIELDS = [
  ["online", "Online shopping"],
  ["dining", "Dining & food delivery"],
  ["travel", "Flights, hotels & travel"],
  ["fuel", "Fuel"],
  ["utilities", "Utilities"],
  ["international", "International spends"],
  ["other", "Everything else"],
];

const EMPTY = Object.fromEntries(SPEND_FIELDS.map(([key]) => [key, ""]));
const BUDGET_PRESETS = [
  { id: "lite", name: "Lite Spender", amount: "₹25k/mo", values: { online: 10000, dining: 5000, utilities: 5000, other: 5000 } },
  { id: "balanced", name: "Balanced Optimizer", amount: "₹60k/mo", values: { online: 25000, dining: 10000, travel: 5000, fuel: 5000, utilities: 5000, other: 10000 } },
  { id: "hni", name: "HNI / Travel Spender", amount: "₹1.5L+/mo", values: { online: 50000, travel: 40000, dining: 25000, utilities: 15000, other: 20000 } },
];

export default function ValueCalculator() {
  const { search } = useLocation();
  const embedded = new URLSearchParams(search).get("embedded") === "1";
  const [form, setForm] = useState({ ...EMPTY, lounge_visits: "0", fee_preference: "worth" });
  const [activePreset, setActivePreset] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const setSpend = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    setActivePreset("");
  };
  const calculate = async (values) => {
    setLoading(true); setError("");
    try {
      const payload = Object.fromEntries(Object.entries(values).map(([key, value]) => [key, key === "fee_preference" ? value : Number(value || 0)]));
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
  const submit = (event) => {
    event.preventDefault();
    calculate(form);
  };
  const choosePreset = (preset) => {
    const next = { ...EMPTY, lounge_visits: form.lounge_visits, fee_preference: form.fee_preference, ...Object.fromEntries(Object.entries(preset.values).map(([key, value]) => [key, String(value)])) };
    setForm(next);
    setActivePreset(preset.id);
    calculate(next);
  };

  return <div className={`ciq-shell ${embedded ? "pb-4" : "min-h-screen pb-16"}`}>
    {!embedded && <header className="ciq-container ciq-container--wide flex items-center justify-between py-5">
      <Logo size="md" />
      <Link to="/" className="ciq-press inline-flex items-center gap-1.5 rounded-full border bg-white px-3 py-2 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)" }}><ArrowLeft className="h-4 w-4" /> Home</Link>
    </header>}
    {!embedded && <CustomerNav />}
    <main className="ciq-container ciq-container--reading">
      {!embedded && <section className="pt-4 text-center">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl text-white" style={{ background: "linear-gradient(145deg,#604ee8,#0e9e98)" }}><Calculator className="h-6 w-6" /></span>
        <div className="mt-4 text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>No sign-up required</div>
        <h1 className="mt-2 font-display text-3xl font-extrabold">Credit card value calculator</h1>
        <p className="mx-auto mt-2 max-w-lg text-sm leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>Enter a typical month of spending. Compare estimated annual rewards with each card’s renewal fee, then check first-year costs and the assumptions behind the estimate.</p>
      </section>}

      <form onSubmit={submit} className="mt-7 rounded-3xl border bg-white p-5" style={{ borderColor: "var(--ciq-line)" }}>
        <h2 className="font-display text-lg font-extrabold">Your monthly spending</h2>
        <p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Use approximate amounts. Do not enter card numbers, account details or transaction data.</p>
        <div className="mt-4" aria-label="Monthly spend presets">
          <p className="mb-2 text-xs font-bold" style={{ color: "var(--ciq-ink-soft)" }}>Quick presets</p>
          <div className="grid gap-2 sm:grid-cols-3">{BUDGET_PRESETS.map((preset) => <button key={preset.id} type="button" aria-pressed={activePreset === preset.id} onClick={() => choosePreset(preset)} className="ciq-press rounded-xl border px-3 py-2.5 text-left transition-colors" style={{ borderColor: activePreset === preset.id ? "var(--ciq-teal)" : "var(--ciq-line)", background: activePreset === preset.id ? "#eef9f6" : "#fff" }}><span className="block text-xs font-bold">{preset.name}</span><span className="mt-0.5 block text-[11px]" style={{ color: "var(--ciq-ink-soft)" }}>{preset.amount}</span></button>)}</div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {SPEND_FIELDS.map(([key, label]) => <label key={key} className="text-xs font-semibold">{label}<span className="mt-1 flex items-center rounded-xl border bg-white px-3" style={{ borderColor: "var(--ciq-line)" }}><span style={{ color: "var(--ciq-ink-soft)" }}>₹</span><input aria-label={label} min="0" max="2000000" inputMode="numeric" type="number" value={form[key]} onChange={(event) => setSpend(key, event.target.value)} placeholder="0" className="w-full bg-transparent px-2 py-2.5 text-sm outline-none" /></span></label>)}
          <label className="text-xs font-semibold">Airport lounge visits per year<input aria-label="Airport lounge visits per year" min="0" max="100" type="number" value={form.lounge_visits} onChange={(event) => set("lounge_visits", event.target.value)} className="mt-1 w-full rounded-xl border bg-white px-3 py-2.5 text-sm outline-none" style={{ borderColor: "var(--ciq-line)" }} /></label>
          <label className="text-xs font-semibold">Annual-fee preference<select aria-label="Annual-fee preference" value={form.fee_preference} onChange={(event) => set("fee_preference", event.target.value)} className="mt-1 w-full rounded-xl border bg-white px-3 py-2.5 text-sm outline-none" style={{ borderColor: "var(--ciq-line)" }}><option value="free">Lifetime-free only preferred</option><option value="worth">Pay a fee when value justifies it</option><option value="premium">Premium benefits are welcome</option></select></label>
        </div>
        {error && <p role="alert" className="mt-4 rounded-xl px-3 py-2 text-sm" style={{ background: "#fff3cd", color: "#7a5b00" }}>{error}</p>}
        <button disabled={loading} className="ciq-press ciq-primary-gradient mt-5 inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 font-semibold text-white disabled:opacity-60">{loading ? <Loader2 className="h-5 w-5 ciq-spin" /> : <Calculator className="h-5 w-5" />} Compare annual value</button>
      </form>

      {result && <section id="value-results" className="mt-8">
        <div className="rounded-2xl border p-4" style={{ borderColor: "#b9e4da", background: "#f2faf7" }}><div className="flex items-center gap-2 font-display font-extrabold"><ShieldCheck className="h-5 w-5" style={{ color: "var(--ciq-teal)" }} /> Your scenario</div><p className="mt-1 text-sm">₹{money(result.monthlySpend)} a month · ₹{money(result.annualSpend)} a year</p><p className="mt-2 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>Estimates use a broad CardIQ reward range, not issuer-specific transaction simulation. Merchant category, reward caps, exclusions and redemption value can change the result. Joining fees, GST on fees and interest are not included in the net range.</p></div>
        <h2 className="mt-6 font-display text-xl font-extrabold">Strongest value matches</h2>
        <div className="mt-3 grid gap-3 lg:grid-cols-2">{result.results.slice(0, 5).map((item, index) => <article key={item.card.id} className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="mb-4"><CreditCardVisual card={item.card} size="sm" /></div><div className="flex items-start justify-between gap-3"><div><div className="text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--ciq-teal)" }}>#{index + 1} value match</div><h3 className="mt-1 font-display text-base font-extrabold">{item.card.name}</h3><p className="text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{item.card.issuer}</p></div><div className="text-right"><div className="font-display text-base font-extrabold" style={{ color: "var(--ciq-teal)" }}>{money(item.valueEstimate.netLow)}–{money(item.valueEstimate.netHigh)}</div><div className="text-[10px]" style={{ color: "var(--ciq-ink-soft)" }}>estimated annual rewards after renewal fee</div></div></div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-xs"><ValueFact label="Estimated annual rewards (₹ equivalent)" value={`${money(item.valueEstimate.grossLow)}–${money(item.valueEstimate.grossHigh)}`} /><ValueFact label="Renewal fee used" value={item.valueEstimate.feeWaived ? "Waived at this spend" : money(item.valueEstimate.effectiveAnnualFee)} /><ValueFact label="First-year joining fee" value={money(item.card.joiningFeeAmount || 0)} /><ValueFact label="Explicit benefits counted" value={money((item.valueEstimate.firstYearBenefitsValue || 0) + (item.valueEstimate.loungeValue || 0))} /></div>
          <p className="mt-3 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>{item.card.rewardLine}</p>
          <div className="mt-2 flex items-center justify-between rounded-xl px-3 py-2 text-[10px]" style={{ background: item.valueEstimate.economicsQuality === "high" ? "#eef9f6" : "#fff8e8", color: "var(--ciq-ink-soft)" }}><span className="font-bold uppercase tracking-wide">Estimate quality: {item.valueEstimate.economicsQuality || "limited"}</span><span>{item.valueEstimate.economicsCoverage ?? 0}% of tracked economics valued</span></div>
          <div className="mt-3 grid grid-cols-2 gap-2"><Link to={`/cards/${encodeURIComponent(item.card.id)}`} className="rounded-xl border py-2.5 text-center text-xs font-semibold" style={{ borderColor: "var(--ciq-line)" }}>See full details</Link><a href={`/go/${encodeURIComponent(item.card.id)}/?subid=calculator_result_row&source=calculator`} rel="sponsored nofollow noopener" target="_blank" className="inline-flex items-center justify-center rounded-xl py-2.5 text-xs font-semibold text-white" style={{ background: "var(--ciq-teal-600)" }}>Apply Now →</a></div>
        </article>)}</div>
      </section>}
    </main>
  </div>;
}

function money(value) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value || 0);
}

function ValueFact({ label, value }) {
  return <div className="rounded-xl p-3" style={{ background: "#f7f8f6" }}><div className="text-[10px] uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>{label}</div><div className="mt-1 font-bold">{value}</div></div>;
}
