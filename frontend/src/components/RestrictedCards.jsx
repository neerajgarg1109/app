import CustomerNav from "./CustomerNav";
import React, { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ExternalLink, LockKeyhole, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { getRestrictedCards } from "../api";
import Logo from "./Logo";

const FILTERS = [
  ["invite-only", "Invitation only"], ["all", "All restricted access"],
  ["existing-relationship", "Existing relationship"], ["segment-restricted", "Customer segment"],
  ["partner-channel", "Partner or branch"], ["issuer-discretion", "Issuer selected"],
];

export default function RestrictedCards() {
  const [cards, setCards] = useState([]);
  const [filter, setFilter] = useState("invite-only");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getRestrictedCards().then((data) => setCards(data.cards || [])).catch(() => setError("Restricted-access cards could not be loaded."));
  }, []);
  const visible = useMemo(() => cards.filter((card) => {
    const matchesFilter = filter === "all" || card.accessType === filter;
    const haystack = `${card.name} ${card.issuer} ${card.accessExplanation}`.toLowerCase();
    return matchesFilter && haystack.includes(query.trim().toLowerCase());
  }), [cards, filter, query]);

  return <div className="ciq-shell min-h-screen pb-20">
    <header className="ciq-container ciq-container--wide flex items-center justify-between py-5"><Logo size="md" /><Link to="/" className="flex items-center gap-1 text-sm font-semibold" style={{ color: "var(--ciq-teal)" }}><ArrowLeft className="h-4 w-4" /> Home</Link></header>
      <CustomerNav />
    <main className="ciq-container ciq-container--wide">
      <section className="rounded-3xl p-6 text-white" style={{ background: "linear-gradient(145deg,#33268f,#604ee8 60%,#0e9e98 130%)" }}>
        <LockKeyhole className="h-8 w-8" /><h1 className="mt-4 font-display text-3xl font-extrabold">{filter === "invite-only" ? "Invite-only credit cards in India" : "Restricted-access credit cards in India"}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-white/85">Invitation-only cards are shown by default. Use the filters to explore other access requirements, such as an existing banking relationship, a defined customer segment, or a partner channel. These other restrictions do not mean a card is invite-only. These cards are excluded from the CardIQ quiz because we cannot verify that you can access them.</p>
      </section>

      <div className="mt-6 flex items-center gap-2 rounded-2xl border bg-white px-4 py-3" style={{ borderColor: "var(--ciq-line)" }}><Search className="h-4 w-4" style={{ color: "var(--ciq-ink-soft)" }} /><input aria-label="Search restricted cards" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search card or issuer" className="w-full bg-transparent text-sm outline-none" /></div>
      <div className="mt-4 flex gap-2 overflow-x-auto pb-2">{FILTERS.map(([value, label]) => <button key={value} type="button" onClick={() => setFilter(value)} aria-pressed={filter === value} className="whitespace-nowrap rounded-full border px-3 py-2 text-xs font-semibold" style={{ borderColor: filter === value ? "var(--ciq-teal)" : "var(--ciq-line)", background: filter === value ? "#e4faf6" : "white", color: "var(--ciq-ink)" }}>{label}</button>)}</div>
      {error && <p role="alert" className="mt-6 text-sm text-red-700">{error}</p>}
      <p className="mt-4 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{visible.length} card{visible.length === 1 ? "" : "s"} shown</p>
      <div className="mt-3 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{visible.map((card) => <article key={card.id} className="rounded-2xl border bg-white p-5" style={{ borderColor: "var(--ciq-line)" }}>
        <div className="text-xs font-bold uppercase tracking-wide" style={{ color: "var(--ciq-teal)" }}>{card.accessLabel}</div>
        <h2 className="mt-2 font-display text-xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>{card.name}</h2><p className="text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{card.issuer}</p>
        <p className="mt-4 text-sm font-semibold" style={{ color: "var(--ciq-ink)" }}>{card.rewardLine}</p><p className="mt-2 text-sm leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>{card.accessExplanation}</p>
        <p className="mt-3 text-xs" style={{ color: "var(--ciq-ink-soft)" }}><strong>Annual fee:</strong> {card.annualFee}</p>
        <div className="mt-4 flex flex-wrap gap-3"><Link to={`/cards/${card.id}`} className="text-sm font-bold" style={{ color: "var(--ciq-teal)" }}>See full card details</Link>{card.sourceUrls?.[0] && <a href={card.sourceUrls[0]} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-sm font-semibold" style={{ color: "var(--ciq-ink-soft)" }}>Check official access route <ExternalLink className="h-3.5 w-3.5" /></a>}</div>
      </article>)}</div>
      <aside className="mt-8 rounded-2xl border bg-white p-5 text-sm leading-relaxed" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink-soft)" }}><strong style={{ color: "var(--ciq-ink)" }}>Access is not guaranteed.</strong> Invitations, upgrades and eligibility are controlled by the issuer. CardIQ does not treat restricted access as an approval signal, and the issuer’s current terms remain authoritative.</aside>
    </main>
  </div>;
}
