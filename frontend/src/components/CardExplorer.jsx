import React, { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Check, GitCompare, Loader2, Search, Share2, X } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { getCards, trackApplyClick } from "../api";
import { recordProductEvent } from "../productAnalytics";
import Logo from "./Logo";
import CardDetails from "./CardDetails";
import Compare from "./Compare";
import CARD_CATEGORIES from "../data/cardCategories.json";

const PAGE_SIZE = 24;
const POPULAR_CATEGORIES = [
  ["cashback", "Cashback"], ["travel", "Travel"], ["domestic-lounge", "Lounge"], ["lifetime-free", "Lifetime free"],
  ["fuel", "Fuel"], ["rupay-upi", "UPI / RuPay"], ["secured", "Secured"], ["premium", "Premium"],
];

export default function CardExplorer() {
  const { cardId } = useParams();
  const [cards, setCards] = useState([]);
  const [query, setQuery] = useState("");
  const initialFilters = hashFilters();
  const [issuer, setIssuer] = useState(initialFilters.issuer || "all");
  const [category, setCategory] = useState(initialFilters.category || "all");
  const [visible, setVisible] = useState(PAGE_SIZE);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [compareIds, setCompareIds] = useState(() => {
    const linked = String(initialFilters.compare || "").split(",").map((id) => id.trim()).filter(Boolean).slice(0, 3);
    if (linked.length >= 2) return linked;
    try { return JSON.parse(localStorage.getItem("ciq_compare_cards") || "[]").slice(0, 3); } catch (error) { return []; }
  });
  const [showCompare, setShowCompare] = useState(() => String(initialFilters.compare || "").split(",").filter(Boolean).length >= 2);
  const [ownedCardId, setOwnedCardId] = useState(() => localStorage.getItem("ciq_owned_card") || "");

  useEffect(() => {
    let active = true;
    getCards().then((data) => { if (active) setCards(Array.isArray(data) ? data : []); }).catch(() => { if (active) setError(true); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const issuers = useMemo(() => [...new Set(cards.map((card) => card.issuer).filter(Boolean))].sort(), [cards]);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const matches = cards.filter((card) => {
      if (issuer !== "all" && card.issuer !== issuer) return false;
      if (category !== "all" && !matchesCategory(card, category)) return false;
      if (!needle) return true;
      const editorial = card.editorial || {};
      const searchable = [card.name, card.issuer, card.network, card.rewardLine, editorial.summary, editorial.verdict, ...(editorial.idealFor || []), ...(card.bestFor || []), ...(card.highlights || [])].join(" ").toLowerCase();
      return searchable.includes(needle);
    });
    return initialFilters.sort === "recent" ? matches.sort((a, b) => String(b.verifiedOn || "").localeCompare(String(a.verifiedOn || ""))) : matches;
  }, [cards, issuer, category, query]);
  const selected = cardId ? cards.find((card) => card.id === cardId) : null;
  const compareCards = compareIds.map((id) => cards.find((card) => card.id === id)).filter(Boolean);
  const availableCategories = useMemo(() => CARD_CATEGORIES.map((item) => ({ ...item, count: cards.filter((card) => matchesCategory(card, item.id)).length })).filter((item) => item.count >= 3), [cards]);

  useEffect(() => { setVisible(PAGE_SIZE); }, [query, issuer, category]);
  useEffect(() => { localStorage.setItem("ciq_compare_cards", JSON.stringify(compareIds)); }, [compareIds]);
  useEffect(() => { if (ownedCardId) localStorage.setItem("ciq_owned_card", ownedCardId); else localStorage.removeItem("ciq_owned_card"); }, [ownedCardId]);

  useEffect(() => {
    if (!ownedCardId || compareIds.includes(ownedCardId)) return;
    setCompareIds((current) => [ownedCardId, ...current].slice(0, 3));
  }, [ownedCardId, compareIds]);

  const toggleCompare = (cardIdToToggle) => {
    setCompareIds((current) => current.includes(cardIdToToggle)
      ? current.filter((id) => id !== cardIdToToggle)
      : current.length < 3 ? [...current, cardIdToToggle] : current);
  };

  const apply = (card) => {
    if (!card?.applyUrl || card.active === false || card.applicationsOpen === false) return;
    trackApplyClick(card.id, null).catch(() => {});
    recordProductEvent("apply_clicked");
    window.open(card.applyUrl, "_blank", "noopener,noreferrer");
  };

  const shareComparison = async () => {
    const url = `${window.location.origin}${window.location.pathname}#/cards?compare=${compareIds.map(encodeURIComponent).join(",")}`;
    if (navigator.share) await navigator.share({ title: "CardIQ comparison", url });
    else await navigator.clipboard.writeText(url);
  };

  return (
    <div className="ciq-shell min-h-screen pb-32">
      <header className="ciq-container ciq-container--wide flex items-center justify-between py-5">
        <Logo size="md" />
        <Link to="/" className="ciq-press inline-flex items-center gap-1.5 rounded-full border bg-white px-3 py-2 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}><ArrowLeft className="h-4 w-4" /> Home</Link>
      </header>

      <main className="ciq-container ciq-container--wide">
        <section className="pt-4 text-center">
          <div className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>Explore without the quiz</div>
          <h1 className="mt-2 font-display text-3xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>Find any credit card</h1>
          <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>Search CardIQ’s sourced catalogue by card, issuer, benefit or network and inspect the full details we have verified.</p>
        </section>

        {initialFilters.mode === "compare" && <section className="mt-5 rounded-2xl border p-4" style={{ borderColor: "#b9e4da", background: "#f2faf7" }}><div className="font-display text-base font-extrabold">Compare against a card you already have</div><p className="mt-1 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>Search for your existing card and choose “I have this card”, then add up to two alternatives.</p></section>}

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

        {!loading && !error && <>
          <section className="mt-4">
            <div className="text-xs font-bold uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>Browse by category</div>
            <div className="mt-2 flex gap-2 overflow-x-auto pb-1 no-scrollbar">
              <button type="button" onClick={() => setCategory("all")} className="flex-shrink-0 rounded-full border px-3 py-1.5 text-xs font-semibold" style={{ borderColor: category === "all" ? "var(--ciq-teal-600)" : "var(--ciq-line)", background: category === "all" ? "var(--ciq-teal-600)" : "#fff", color: category === "all" ? "#fff" : "var(--ciq-ink)" }}>All cards</button>
              {POPULAR_CATEGORIES.map(([value, label]) => <button type="button" key={value} onClick={() => setCategory(value)} className="flex-shrink-0 rounded-full border px-3 py-1.5 text-xs font-semibold" style={{ borderColor: category === value ? "var(--ciq-teal-600)" : "var(--ciq-line)", background: category === value ? "var(--ciq-teal-600)" : "#fff", color: category === value ? "#fff" : "var(--ciq-ink)" }}>{label}</button>)}
            </div>
          </section>
          <details className="mt-4 rounded-2xl border bg-white p-3" style={{ borderColor: "var(--ciq-line)" }}>
            <summary className="cursor-pointer text-sm font-bold">Browse {issuers.length} issuers</summary>
            <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
              <button type="button" onClick={() => setIssuer("all")} className="rounded-xl border px-3 py-2 text-left text-xs font-semibold" style={{ borderColor: issuer === "all" ? "var(--ciq-teal-600)" : "var(--ciq-line)" }}>All issuers <span className="block font-normal" style={{ color: "var(--ciq-ink-soft)" }}>{cards.length} cards</span></button>
              {issuers.map((name) => { const count = cards.filter((card) => card.issuer === name).length; return <button type="button" key={name} onClick={() => setIssuer(name)} className="rounded-xl border px-3 py-2 text-left text-xs font-semibold" style={{ borderColor: issuer === name ? "var(--ciq-teal-600)" : "var(--ciq-line)" }}>{name}<span className="block font-normal" style={{ color: "var(--ciq-ink-soft)" }}>{count} card{count === 1 ? "" : "s"}</span></button>; })}
            </div>
          </details>
          <details className="mt-3 rounded-2xl border bg-white p-3" style={{ borderColor: "var(--ciq-line)" }}>
            <summary className="cursor-pointer text-sm font-bold">Explore {availableCategories.length} useful card categories</summary>
            <p className="mt-2 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>Only categories with at least three matching cards are published.</p>
            <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
              {availableCategories.map((item) => <button type="button" key={item.id} onClick={() => setCategory(item.id)} className="rounded-xl border px-3 py-2 text-left text-xs font-semibold" style={{ borderColor: category === item.id ? "var(--ciq-teal-600)" : "var(--ciq-line)" }}>{item.label}<span className="block font-normal" style={{ color: "var(--ciq-ink-soft)" }}>{item.count} cards</span></button>)}
            </div>
          </details>
        </>}

        {loading && <div className="grid min-h-[40vh] place-items-center"><Loader2 className="h-7 w-7 ciq-spin" style={{ color: "var(--ciq-teal)" }} /></div>}
        {error && <div className="mt-8 rounded-2xl border bg-white p-5 text-center text-sm" style={{ borderColor: "var(--ciq-line)" }}>We couldn’t load the catalogue. Please try again.</div>}
        {!loading && !error && <>
          <div className="mt-4 flex items-center justify-between text-xs" style={{ color: "var(--ciq-ink-soft)" }}><span>{filtered.length} card{filtered.length === 1 ? "" : "s"} found</span><span>Details checked by CardIQ</span></div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {filtered.slice(0, visible).map((card) => {
              const comparing = compareIds.includes(card.id);
              const compareFull = compareIds.length >= 3 && !comparing;
              return <article key={card.id} className="rounded-2xl border bg-white p-4 text-left" style={{ borderColor: comparing ? "var(--ciq-teal-600)" : "var(--ciq-line)" }}>
              <Link to={`/cards/${encodeURIComponent(card.id)}`} className="ciq-press block">
                <div className="flex items-start gap-3">
                  <div className="h-12 w-20 flex-shrink-0 rounded-xl" style={{ background: `linear-gradient(135deg, ${card.palette?.[0] || "#172554"}, ${card.palette?.[1] || "#1e40af"})` }} />
                  <div className="min-w-0 flex-1"><div className="font-display text-sm font-extrabold" style={{ color: "var(--ciq-ink)" }}>{card.name}</div><div className="mt-0.5 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{card.issuer}</div></div>
                </div>
                <p className="mt-3 text-xs font-semibold leading-relaxed" style={{ color: "var(--ciq-ink)" }}>{card.rewardLine}</p>
                {card.editorial?.summary && <p className="mt-2 line-clamp-3 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}><span className="font-bold" style={{ color: "var(--ciq-teal)" }}>CardIQ take: </span>{card.editorial.summary}</p>}
                <div className="mt-3 flex items-center justify-between gap-3 border-t pt-3 text-xs" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink-soft)" }}><span>{card.annualFee || "Fee not specified"}</span><span className="flex-shrink-0 font-bold" style={{ color: "var(--ciq-teal)" }}>Full details</span></div>
              </Link>
              <button type="button" onClick={() => setOwnedCardId(ownedCardId === card.id ? "" : card.id)} className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-xl border py-2 text-xs font-semibold" style={{ borderColor: ownedCardId === card.id ? "var(--ciq-teal-600)" : "var(--ciq-line)", background: ownedCardId === card.id ? "#f2faf7" : "#fff", color: ownedCardId === card.id ? "var(--ciq-teal)" : "var(--ciq-ink)" }}>{ownedCardId === card.id ? <><Check className="h-3.5 w-3.5" /> This is my card</> : "I have this card"}</button>
              <button type="button" disabled={compareFull} onClick={() => toggleCompare(card.id)} className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-xl border py-2 text-xs font-semibold disabled:opacity-40" style={{ borderColor: comparing ? "var(--ciq-teal-600)" : "var(--ciq-line)", color: comparing ? "var(--ciq-teal)" : "var(--ciq-ink)" }}>{comparing ? <><Check className="h-3.5 w-3.5" /> Added to compare</> : <><GitCompare className="h-3.5 w-3.5" /> {compareFull ? "Compare tray full" : "Add to compare"}</>}</button>
              </article>;
            })}
          </div>
          {filtered.length === 0 && <div className="mt-8 rounded-2xl border bg-white p-6 text-center"><div className="font-display font-bold">No matching cards</div><p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Try a card name, issuer, benefit or a broader search.</p></div>}
          {visible < filtered.length && <button type="button" onClick={() => setVisible((count) => count + PAGE_SIZE)} className="ciq-press mt-5 w-full rounded-2xl border bg-white py-3 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>Show more cards</button>}
        </>}
      </main>

      {cardId && !loading && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center sm:p-5" role="dialog" aria-modal="true" aria-label="Card details">
          <div className="max-h-[94vh] w-full max-w-3xl overflow-y-auto rounded-t-3xl bg-white p-5 sm:rounded-3xl lg:p-7">
            <div className="sticky top-0 z-10 -mx-1 mb-4 flex items-start justify-between bg-white px-1 pb-2">
              <div><div className="font-display text-xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>{selected?.name || "Card not found"}</div>{selected && <div className="mt-0.5 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{selected.issuer}</div>}</div>
              <Link to="/cards" className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full border" style={{ borderColor: "var(--ciq-line)" }} aria-label="Close card details"><X className="h-4 w-4" /></Link>
            </div>
            {selected ? <CardDetails card={selected} heading="Everything we know about this card" onApply={() => apply(selected)} /> : <div className="rounded-2xl p-5 text-sm" style={{ background: "#f7f8f6" }}>This card is not in the current public catalogue.</div>}
          </div>
        </div>
      )}
      {compareCards.length > 0 && <div className="fixed inset-x-0 bottom-0 z-40 border-t bg-white/95 backdrop-blur" style={{ borderColor: "var(--ciq-line)" }}><div className="ciq-container flex items-center gap-3 py-3"><div className="min-w-0 flex-1"><div className="text-xs font-bold">{ownedCardId ? "Compare with your card" : `Compare ${compareCards.length} of 3 cards`}</div><div className="truncate text-[10px]" style={{ color: "var(--ciq-ink-soft)" }}>{compareCards.map((card) => `${card.id === ownedCardId ? "Your card: " : ""}${card.name}`).join(" · ")}</div></div><button type="button" onClick={() => { setCompareIds([]); setOwnedCardId(""); }} className="text-xs font-semibold underline" style={{ color: "var(--ciq-ink-soft)" }}>Clear</button><button type="button" disabled={compareCards.length < 2} onClick={shareComparison} aria-label="Share comparison" className="rounded-xl border p-2.5 disabled:opacity-40" style={{ borderColor: "var(--ciq-line)" }}><Share2 className="h-4 w-4" /></button><button type="button" disabled={compareCards.length < 2} onClick={() => setShowCompare(true)} className="rounded-xl px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-40" style={{ background: "var(--ciq-teal-600)" }}>Compare</button></div></div>}
      {showCompare && <Compare cards={compareCards} onClose={() => setShowCompare(false)} />}
    </div>
  );
}

function matchesCategory(card, category) {
  const definition = CARD_CATEGORIES.find((item) => item.id === category);
  if (!definition) return true;
  const text = [card.name, card.rewardLine, card.feeType, card.network, ...(card.bestFor || []), ...(card.highlights || [])].join(" ").toLowerCase();
  const checks = [];
  if (definition.keywords?.length) checks.push(definition.keywords.some((keyword) => text.includes(keyword)));
  if (typeof definition.annualFeeMax === "number") checks.push(Number(card.annualFeeAmount) <= definition.annualFeeMax);
  if (typeof definition.annualFeeMin === "number") checks.push(Number(card.annualFeeAmount) >= definition.annualFeeMin);
  if (definition.secured) checks.push(card.secured === true);
  if (definition.creditReq) checks.push(card.creditReq === definition.creditReq);
  if (definition.coBranded) checks.push(Boolean(card.coBrandPartner) || /co-brand|co brand/.test(text));
  if (definition.fintech) checks.push(Boolean(card.coBrandPartner) || /fintech|kredit|salaryse|zaggle|onecard|scapia|super\.money/.test(text));
  return checks.some(Boolean);
}

function hashFilters() {
  try {
    const query = window.location.hash.split("?")[1] || "";
    return Object.fromEntries(new URLSearchParams(query));
  } catch (error) { return {}; }
}
