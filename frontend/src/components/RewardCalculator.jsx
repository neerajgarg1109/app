import React, { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowLeftRight, Search } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { calculateCardRewards, getCards } from "../api";
import CustomerNav from "./CustomerNav";
import Logo from "./Logo";

const CATEGORIES = [
  ["dining", "Dining"], ["travel", "Travel"], ["shopping", "Shopping"],
  ["utility", "Utilities"], ["fuel", "Fuel"], ["international", "International"],
  ["upi", "UPI"], ["grocery", "Groceries"], ["other", "Other"],
];
const REDEMPTIONS = [
  ["transfer_partner", "Airline / hotel transfer"],
  ["statement_credit", "Statement credit"], ["voucher", "Voucher"],
];
const money = (value) => value == null ? "—" : `₹${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;

export default function RewardCalculator() {
  const { search } = useLocation();
  const embedded = new URLSearchParams(search).get("embedded") === "1";
  const [cards, setCards] = useState([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState([]);
  const [category, setCategory] = useState("dining");
  const [amount, setAmount] = useState("");
  const [preference, setPreference] = useState("transfer_partner");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getCards().then(setCards).catch(() => setError("We couldn’t load the card catalogue. Please try again."));
  }, []);
  const matches = useMemo(() => cards.filter((card) => `${card.name} ${card.issuer}`.toLowerCase().includes(query.toLowerCase())).slice(0, 20), [cards, query]);
  const toggle = (id) => setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : current.length < 10 ? [...current, id] : current);

  const submit = async (event) => {
    event.preventDefault();
    const spend = Number(amount);
    if (!selected.length) { setError("Select at least one card from your wallet."); return; }
    if (!Number.isFinite(spend) || spend <= 0 || spend > 10_000_000) { setError("Enter a valid transaction amount greater than ₹0 and no more than ₹1 crore."); return; }
    setError(""); setLoading(true);
    try {
      setResult(await calculateCardRewards({ card_ids: selected, category, amount: spend, redemption_preference: preference }));
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || "We couldn’t calculate these rewards. Please try again.");
    } finally { setLoading(false); }
  };

  return <div className="ciq-shell min-h-screen pb-16">
    {!embedded && <header className="ciq-container ciq-container--wide flex items-center justify-between py-5"><Logo size="md" /><Link to="/" className="rounded-full border bg-white px-3 py-2 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)" }}><ArrowLeft className="mr-1 inline h-4 w-4" /> Home</Link></header>}
    {!embedded && <CustomerNav />}
    <main className="ciq-container max-w-3xl">
      <section className="pt-4 text-center"><ArrowLeftRight className="mx-auto h-10 w-10" style={{ color: "var(--ciq-teal)" }} /><h1 className="mt-3 font-display text-3xl font-extrabold">Reward &amp; transfer partner calculator</h1><p className="mt-2 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Compare estimated rewards for cards you already hold.</p></section>
      <form onSubmit={submit} className="mt-6 space-y-4 rounded-3xl border bg-white p-5" style={{ borderColor: "var(--ciq-line)" }}>
        <label className="flex items-center gap-2 rounded-xl border px-3 py-2.5"><Search className="h-4 w-4" /><input aria-label="Search cards" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search your cards" className="min-w-0 flex-1 outline-none" /></label>
        <fieldset><legend className="mb-2 text-sm font-semibold">Cards in your wallet (up to 10)</legend><div className="max-h-56 space-y-2 overflow-y-auto">{matches.map((card) => <label key={card.id} className="flex items-center gap-3 rounded-xl border p-3 text-sm"><input type="checkbox" checked={selected.includes(card.id)} onChange={() => toggle(card.id)} disabled={!selected.includes(card.id) && selected.length >= 10} /><span><strong>{card.name}</strong><span className="block text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{card.issuer}</span></span></label>)}{!matches.length && <p className="p-3 text-sm">No matching cards found.</p>}</div></fieldset>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm font-semibold">Transaction category<select value={category} onChange={(event) => setCategory(event.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2.5">{CATEGORIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label className="block text-sm font-semibold">Transaction amount<span className="mt-1 flex rounded-xl border px-3"><span className="py-2.5">₹</span><input aria-label="Transaction amount" type="number" min="0.01" max="10000000" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} className="w-full px-2 py-2.5 outline-none" placeholder="e.g. 5000" /></span></label>
        </div>
        <label className="block text-sm font-semibold">Compare point redemption as<select value={preference} onChange={(event) => setPreference(event.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2.5">{REDEMPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        {error && <p role="alert" className="text-sm" style={{ color: "#a63e38" }}>{error}</p>}
        <button disabled={loading} className="ciq-primary-gradient w-full rounded-2xl py-3.5 font-semibold text-white disabled:opacity-60">{loading ? "Calculating…" : "Compare rewards"}</button>
      </form>
      {result && <section className="mt-6" aria-live="polite"><h2 className="font-display text-xl font-extrabold">Estimated reward comparison</h2><p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{result.assumptions.note} Exact issuer caps, exclusions and redemption terms apply.</p>
        <div className="mt-3 space-y-3">{result.results.map((item, index) => <article key={item.card_id} className="rounded-2xl border bg-white p-4" style={{ borderColor: index === 0 && item.effective_value_inr != null ? "var(--ciq-teal-600)" : "var(--ciq-line)" }}>
          <div className="flex flex-wrap items-start justify-between gap-2"><div><h3 className="font-display font-extrabold">{item.card_name}</h3><p className="text-xs">{item.issuer}{item.reward_currency ? ` · ${item.reward_currency}` : ""}</p></div><strong>{item.effective_value_inr == null ? "Rate unavailable" : `${money(item.effective_value_inr)} estimated`}</strong></div>
          <p className="mt-2 text-sm">{item.reward_type === "points" ? `${Number(item.points_earned).toLocaleString("en-IN")} points estimated` : item.reward_type === "cashback" ? "Direct cashback estimate" : "No estimate available"}</p>
          <div className="mt-3 grid gap-2 text-xs sm:grid-cols-3"><p className="rounded-lg bg-slate-50 p-2"><span className="block font-semibold">Transfer partner*</span>{item.reward_type === "cashback" ? "Cashback" : money(item.valuations.transfer_partner)}</p><p className="rounded-lg bg-slate-50 p-2"><span className="block font-semibold">Statement credit*</span>{item.reward_type === "cashback" ? "Cashback" : money(item.valuations.statement_credit)}</p><p className="rounded-lg bg-slate-50 p-2"><span className="block font-semibold">Voucher*</span>{item.reward_type === "cashback" ? "Cashback" : money(item.valuations.voucher)}</p></div>
          <p className="mt-2 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{item.rationale}</p>
        </article>)}</div>
        <p className="mt-3 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>*Illustrative values use ₹0.80, ₹0.25 and ₹0.40 per point respectively. Cashback is shown directly. Estimates are unavailable when catalog terms are unclear.</p>
      </section>}
    </main>
  </div>;
}
