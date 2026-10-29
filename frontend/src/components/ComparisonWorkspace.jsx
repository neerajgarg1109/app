import CreditCardVisual from "./CreditCardVisual";
import React, { useEffect, useState } from "react";
import { GitCompare, Plus, Search, Share2, X } from "lucide-react";
import Compare from "./Compare";
import { getCard } from "../api";

export default function ComparisonWorkspace({ cards, selected, loading, error, ownedCardId, onToggle, onOwned, onShare, resultsFirst = false }) {
  const [editing, setEditing] = useState(false);
  const compact = resultsFirst && !editing && selected.length >= 2;
  useEffect(() => { if (resultsFirst) window.scrollTo(0, 0); }, [resultsFirst]);
  const [query, setQuery] = useState("");
  const [details, setDetails] = useState({});
  const [detailError, setDetailError] = useState(false);
  const [retry, setRetry] = useState(0);
  const selectedKey = selected.map(card => card.id).join(",");
  useEffect(() => {
    let active = true;
    setDetailError(false);
    if (selectedKey) Promise.all(selectedKey.split(",").map(id => getCard(id))).then(results => {
      if (active) setDetails(Object.fromEntries(results.map(card => [card.id, card])));
    }).catch(() => { if (active) setDetailError(true); });
    return () => { active = false; };
  }, [selectedKey, retry]);
  const fullCards = selected.map(card => details[card.id]).filter(Boolean);
  const matches = query.trim() ? cards.filter(card => !selected.some(item => item.id === card.id) && `${card.name} ${card.issuer}`.toLowerCase().includes(query.trim().toLowerCase())).slice(0, 8) : [];
  const remove = card => { if (card.id === ownedCardId) onOwned(""); onToggle(card.id); };
  return <div className={compact ? "py-4" : "py-8 sm:py-12"}>
    {!compact && <div className="mx-auto max-w-2xl text-center">
      <div className="text-xs font-bold uppercase tracking-widest" style={{ color: "var(--ciq-teal)" }}>The side-by-side view</div>
      <h1 className="mt-3 font-display text-3xl font-extrabold sm:text-4xl">Which card comes out ahead?</h1>
      <p className="mt-3 text-sm leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>Choose two or three cards. Compare their fees, rewards and limits in one place, or see how an alternative stacks up against your current card.</p>
    </div>}
    {loading ? <p className="py-12 text-center" role="status">Loading cards…</p> : error ? <p className="py-12 text-center" role="alert">We couldn’t load the catalogue. Please try again.</p> : <>
      {!compact && <>
      <section aria-label="Cards selected for comparison" className="mt-8 grid gap-3 md:grid-cols-3">
        {[0, 1, 2].map(index => { const card = selected[index]; return <div key={index} className="relative flex min-h-40 flex-col rounded-2xl border p-5" style={{ borderColor: card ? "var(--ciq-teal)" : "var(--ciq-line)", background: card ? "white" : "rgba(255,255,255,.45)", borderStyle: card ? "solid" : "dashed" }}>
          {card ? <><button type="button" aria-label={`Remove ${card.name}`} onClick={() => remove(card)} className="absolute right-3 top-3 rounded-full p-2"><X className="h-4 w-4" /></button><div className="mb-3 w-full max-w-[180px]"><CreditCardVisual card={card} size="sm" /></div><h2 className="pr-6 text-base font-bold">{card.name}</h2><p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{card.issuer}</p><button type="button" onClick={() => onOwned(ownedCardId === card.id ? "" : card.id)} className="mt-4 self-start text-xs font-semibold underline">{ownedCardId === card.id ? "Your current card ✓" : "Set as my current card"}</button></> : <div className="m-auto text-center" style={{ color: "var(--ciq-ink-soft)" }}><Plus className="mx-auto mb-2 h-5 w-5" /><div className="text-sm font-semibold">{index === 2 ? "Add a third card" : `Choose card ${index + 1}`}</div><div className="mt-1 text-xs">{index === 2 ? "Optional" : "Use the search below"}</div></div>}
        </div>; })}
      </section>
      {selected.length < 3 && <section className="relative mx-auto mt-5 max-w-2xl">
        <label className="flex items-center gap-3 rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}><Search className="h-5 w-5 shrink-0" /><input aria-label="Find a card to compare" className="min-w-0 flex-1 bg-transparent text-sm outline-none" placeholder="Type a card name or bank to add it…" value={query} onChange={event => setQuery(event.target.value)} /></label>
        {query.trim() && <div className="mt-2 overflow-hidden rounded-2xl border bg-white" style={{ borderColor: "var(--ciq-line)" }}>{matches.length ? matches.map(card => <button type="button" key={card.id} onClick={() => { onToggle(card.id); setQuery(""); }} className="flex w-full items-center justify-between gap-4 border-b p-4 text-left hover:bg-violet-50"><span className="w-16 shrink-0"><CreditCardVisual card={card} size="thumbnail" /></span><span className="flex-1"><span className="block text-sm font-bold">{card.name}</span><span className="text-xs">{card.issuer}</span></span><Plus className="h-4 w-4 shrink-0" /></button>) : <p className="p-4 text-sm">No matching cards. Try another card name or bank.</p>}</div>}
      </section>}
      </>}
      {selected.length >= 2 ? <section className={compact ? "" : "mt-8"}><div className="mb-4 flex flex-wrap items-center justify-between gap-3">{compact ? <h1 className="text-lg font-bold">Compare cards</h1> : <h2 className="text-lg font-bold">Your comparison</h2>}{resultsFirst && <button type="button" onClick={() => { setEditing(!editing); window.scrollTo(0, 0); }} className="ml-auto rounded-full border bg-white px-4 py-2 text-sm font-semibold">{compact ? "Change cards" : "Show comparison"}</button>}<button type="button" onClick={onShare} aria-label="Share comparison" className="flex items-center gap-2 rounded-full border bg-white px-4 py-2 text-sm font-semibold"><Share2 className="h-4 w-4" /> Share comparison</button></div>{detailError ? <div role="alert" className="rounded-2xl border bg-white p-6">We couldn’t load the full card details. <button type="button" className="font-bold underline" onClick={() => setRetry(value => value + 1)}>Try again</button></div> : fullCards.length === selected.length ? <Compare cards={fullCards} inline showHeading={!compact} /> : <p role="status" className="p-8 text-center">Loading full comparison…</p>}</section> : <div className="mt-8 rounded-3xl border bg-white px-6 py-12 text-center" style={{ borderColor: "var(--ciq-line)" }}><GitCompare className="mx-auto mb-4 h-8 w-8" style={{ color: "var(--ciq-teal)" }} /><h2 className="text-lg font-bold">{selected.length ? "Add one more card to see the differences" : "Your comparison starts here"}</h2><p className="mt-2 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Annual fees · Joining fees · Rewards · Travel benefits · Important limits</p></div>}
    </>}
  </div>;
}
