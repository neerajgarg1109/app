import React, { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ExternalLink, Loader2, Search, X } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { getCards, trackApplyClick } from "../api";
import { recordProductEvent } from "../productAnalytics";
import Logo from "./Logo";
import CardDetails from "./CardDetails";

const PAGE_SIZE = 24;

export default function CardExplorer() {
  const { cardId } = useParams();
  const [cards, setCards] = useState([]);
  const [query, setQuery] = useState("");
  const [issuer, setIssuer] = useState("all");
  const [visible, setVisible] = useState(PAGE_SIZE);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    getCards().then((data) => { if (active) setCards(Array.isArray(data) ? data : []); }).catch(() => { if (active) setError(true); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const issuers = useMemo(() => [...new Set(cards.map((card) => card.issuer).filter(Boolean))].sort(), [cards]);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return cards.filter((card) => {
      if (issuer !== "all" && card.issuer !== issuer) return false;
      if (!needle) return true;
      const searchable = [card.name, card.issuer, card.network, card.rewardLine, ...(card.bestFor || []), ...(card.highlights || [])].join(" ").toLowerCase();
      return searchable.includes(needle);
    });
  }, [cards, issuer, query]);
  const selected = cardId ? cards.find((card) => card.id === cardId) : null;

  useEffect(() => { setVisible(PAGE_SIZE); }, [query, issuer]);

  const apply = (card) => {
    if (!card?.applyUrl || card.active === false || card.applicationsOpen === false) return;
    trackApplyClick(card.id, null).catch(() => {});
    recordProductEvent("apply_clicked");
    window.open(card.applyUrl, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="ciq-shell min-h-screen pb-16">
      <header className="ciq-container flex items-center justify-between py-5">
        <Logo size="md" />
        <Link to="/" className="ciq-press inline-flex items-center gap-1.5 rounded-full border bg-white px-3 py-2 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}><ArrowLeft className="h-4 w-4" /> Home</Link>
      </header>

      <main className="ciq-container">
        <section className="pt-4 text-center">
          <div className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>Explore without the quiz</div>
          <h1 className="mt-2 font-display text-3xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>Find any credit card</h1>
          <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>Search CardIQ’s sourced catalogue by card, issuer, benefit or network and inspect the full details we have verified.</p>
        </section>

        <section className="sticky top-0 z-20 -mx-2 mt-6 rounded-2xl bg-[var(--ciq-bg)]/95 p-2 backdrop-blur">
          <label className="flex items-center gap-2 rounded-2xl border bg-white px-4 py-3" style={{ borderColor: "var(--ciq-line)" }}>
            <Search className="h-5 w-5" style={{ color: "var(--ciq-ink-soft)" }} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search card, issuer, cashback, lounge…" className="min-w-0 flex-1 bg-transparent text-sm outline-none" aria-label="Search cards" />
            {query && <button type="button" onClick={() => setQuery("")} aria-label="Clear search"><X className="h-4 w-4" /></button>}
          </label>
          <select value={issuer} onChange={(event) => setIssuer(event.target.value)} className="mt-2 w-full rounded-xl border bg-white px-3 py-2.5 text-sm font-semibold outline-none" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }} aria-label="Filter by issuer">
            <option value="all">All issuers</option>
            {issuers.map((name) => <option key={name} value={name}>{name}</option>)}
          </select>
        </section>

        {loading && <div className="grid min-h-[40vh] place-items-center"><Loader2 className="h-7 w-7 ciq-spin" style={{ color: "var(--ciq-teal)" }} /></div>}
        {error && <div className="mt-8 rounded-2xl border bg-white p-5 text-center text-sm" style={{ borderColor: "var(--ciq-line)" }}>We couldn’t load the catalogue. Please try again.</div>}
        {!loading && !error && <>
          <div className="mt-4 flex items-center justify-between text-xs" style={{ color: "var(--ciq-ink-soft)" }}><span>{filtered.length} card{filtered.length === 1 ? "" : "s"} found</span><span>Details checked by CardIQ</span></div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {filtered.slice(0, visible).map((card) => (
              <Link key={card.id} to={`/cards/${encodeURIComponent(card.id)}`} className="ciq-press rounded-2xl border bg-white p-4 text-left" style={{ borderColor: "var(--ciq-line)" }}>
                <div className="flex items-start gap-3">
                  <div className="h-12 w-20 flex-shrink-0 rounded-xl" style={{ background: `linear-gradient(135deg, ${card.palette?.[0] || "#172554"}, ${card.palette?.[1] || "#1e40af"})` }} />
                  <div className="min-w-0 flex-1"><div className="font-display text-sm font-extrabold" style={{ color: "var(--ciq-ink)" }}>{card.name}</div><div className="mt-0.5 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{card.issuer}</div></div>
                </div>
                <p className="mt-3 text-xs font-semibold leading-relaxed" style={{ color: "var(--ciq-ink)" }}>{card.rewardLine}</p>
                <div className="mt-3 flex items-center justify-between gap-3 border-t pt-3 text-xs" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink-soft)" }}><span>{card.annualFee || "Fee not specified"}</span><span className="flex-shrink-0 font-bold" style={{ color: "var(--ciq-teal)" }}>Full details</span></div>
              </Link>
            ))}
          </div>
          {filtered.length === 0 && <div className="mt-8 rounded-2xl border bg-white p-6 text-center"><div className="font-display font-bold">No matching cards</div><p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Try a card name, issuer, benefit or a broader search.</p></div>}
          {visible < filtered.length && <button type="button" onClick={() => setVisible((count) => count + PAGE_SIZE)} className="ciq-press mt-5 w-full rounded-2xl border bg-white py-3 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>Show more cards</button>}
        </>}
      </main>

      {cardId && !loading && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center sm:p-5" role="dialog" aria-modal="true" aria-label="Card details">
          <div className="max-h-[94vh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-white p-5 sm:rounded-3xl">
            <div className="sticky top-0 z-10 -mx-1 mb-4 flex items-start justify-between bg-white px-1 pb-2">
              <div><div className="font-display text-xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>{selected?.name || "Card not found"}</div>{selected && <div className="mt-0.5 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{selected.issuer}</div>}</div>
              <Link to="/cards" className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full border" style={{ borderColor: "var(--ciq-line)" }} aria-label="Close card details"><X className="h-4 w-4" /></Link>
            </div>
            {selected ? <CardDetails card={selected} heading="Everything we know about this card" onApply={() => apply(selected)} /> : <div className="rounded-2xl p-5 text-sm" style={{ background: "#f7f8f6" }}>This card is not in the current public catalogue.</div>}
          </div>
        </div>
      )}
    </div>
  );
}
