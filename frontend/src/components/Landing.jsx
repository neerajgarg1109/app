import React, { useEffect, useState } from "react";
import { ArrowRight, ShieldCheck, Timer, BellOff, PhoneCall, Sparkles, Search, GitCompare, Newspaper, Building2, Calculator, LockKeyhole, BookOpen } from "lucide-react";
import Logo from "./Logo";
import { TRUST_POINTS } from "../mock/mock";
import { getCards, getCardUpdates, getResult, getSiteContent } from "../api";
import { Link } from "react-router-dom";
import CARD_CATEGORIES from "../data/cardCategories.json";
import CustomerNav from "./CustomerNav";
import FeaturedCards from "./FeaturedCards";
import CARD_NEWS from "../data/cardNews.json";

const ICONS = { ShieldCheck, Timer, BellOff };

const PRIMARY_INTENTS = [
  { title: "Find my best card", text: "Get a recommendation based on how you spend.", icon: Sparkles, action: "quiz" },
  { title: "Search cards", text: "Check fees, rewards, exclusions and our review.", icon: Search, to: "/cards" },
  { title: "Compare cards", text: "Compare a card you own with other options.", icon: GitCompare, to: "/cards?mode=compare" },
  { title: "New card launches", text: "See new cards and important benefit changes.", icon: Newspaper, to: "/updates" },
];

const MORE_INTENTS = [
  { title: "Calculate my annual value", text: "Rank cards using your monthly spending and annual fees.", icon: Calculator, to: "/calculator" },
  { title: "Pick a card from my wallet", text: "See which card best fits a planned purchase.", icon: Calculator, to: "/wallet-optimizer" },
  { title: "Explore restricted-access cards", text: "Understand invite-only, relationship and special-channel cards.", icon: LockKeyhole, to: "/restricted-cards" },
  { title: "Browse by issuer", text: "See every catalogued card from each issuer.", icon: Building2, to: "/cards?browse=issuers" },
  { title: "Issuer help & card closure", text: "Use verified official support and closure channels.", icon: PhoneCall, to: "/help/issuers" },
  { title: "Track card changes", text: "Get opt-in alerts for a card, issuer or major update.", icon: Newspaper, to: "/alerts" },
  { title: "Read credit card guides", text: "Explore sourced shortlists, comparisons and practical card guidance.", icon: BookOpen, href: `${process.env.PUBLIC_URL}/guides/` },
];
const ALL_INTENTS = [...PRIMARY_INTENTS, ...MORE_INTENTS];

export default function Landing({ onStart, onResume, resumeStep, savedResult }) {
  const [catalogStats, setCatalogStats] = useState({ cards: null, issuers: null });
  const [catalogCards, setCatalogCards] = useState([]);
  const [cardUpdates, setCardUpdates] = useState([]);
  const [featuredPlacements, setFeaturedPlacements] = useState(null);
  const [savedCardName, setSavedCardName] = useState(null);

  useEffect(() => {
    let active = true;
    getCards()
      .then((cards) => {
        if (!active || !Array.isArray(cards)) return;
        setCatalogCards(cards);
        setCatalogStats({
          cards: cards.length,
          issuers: new Set(cards.map((card) => card.issuer).filter(Boolean)).size,
        });
      })
      .catch(() => {});
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    getSiteContent().then((data) => { if (active) setFeaturedPlacements(Array.isArray(data?.featured_cards) ? data.featured_cards : null); }).catch(() => {});
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    getCardUpdates().then((data) => { if (active) setCardUpdates(Array.isArray(data?.updates) ? data.updates : []); }).catch(() => {});
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    setSavedCardName(null);
    if (savedResult?.resultId) {
      getResult(savedResult.resultId)
        .then((result) => { if (active) setSavedCardName(result?.scored?.[0]?.card?.name || null); })
        .catch(() => {});
    }
    return () => { active = false; };
  }, [savedResult?.resultId]);

  return (
    <div className="ciq-shell pb-40">
      <header className="ciq-container ciq-container--wide py-5">
        <Logo size="md" />
      </header>
      <CustomerNav />

      {/* Hero */}
      <section className="ciq-container ciq-container--reading pt-6 text-center ciq-fade-up lg:pt-12">
        <div
          className="mx-auto mb-5 inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold"
          style={{ background: "linear-gradient(90deg,#eeeaff,#e4faf6)", color: "var(--ciq-teal)" }}
        >
          <Sparkles className="h-3.5 w-3.5" /> Clear comparisons. Honest trade-offs. Built around you.
        </div>
        <h1 className="font-display text-[34px] leading-[1.1] font-extrabold sm:text-5xl lg:text-6xl" style={{ color: "var(--ciq-ink)" }}>
          Your clearest path to the <span className="ciq-gradient-text">right credit card</span>
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-[15px] leading-relaxed sm:text-base" style={{ color: "var(--ciq-ink-soft)" }}>
          CardIQ checks {catalogStats.cards == null ? "the cards we track" : `${catalogStats.cards} cards from ${catalogStats.issuers} banks and issuers`}, weighs the fees and fine print against how you spend, and helps you find the best card for your needs.
        </p>

        <div className="ciq-soft-glow mx-auto mt-6 grid max-w-2xl grid-cols-3 overflow-hidden rounded-2xl border bg-white/90 text-center backdrop-blur" style={{ borderColor: "var(--ciq-line)" }}>
          {[
            [catalogStats.cards == null ? "—" : String(catalogStats.cards), "cards catalogued"],
            [catalogStats.issuers == null ? "—" : String(catalogStats.issuers), "issuers covered"],
            [String(CARD_CATEGORIES.length), "card categories"],
          ].map(([value, label], index) => (
            <div key={label} className="ciq-stat px-2 py-3" style={{ borderLeft: index ? "1px solid var(--ciq-line)" : "none" }}>
              <div className="font-display text-base font-extrabold" style={{ color: "var(--ciq-ink)" }}>{value}</div>
              <div className="mt-0.5 text-[10px] leading-tight" style={{ color: "var(--ciq-ink-soft)" }}>{label}</div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex flex-col justify-center gap-2 sm:flex-row sm:flex-wrap sm:gap-x-6">
          {TRUST_POINTS.map((t) => {
            const Icon = ICONS[t.icon];
            return (
              <div key={t.text} className="ciq-trust-point flex items-center justify-center gap-2 text-sm font-medium" style={{ color: "var(--ciq-ink)" }}>
                <Icon className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} />
                {t.text}
              </div>
            );
          })}
        </div>

        {resumeStep && (
          <button
            onClick={onResume}
            className="ciq-press mx-auto mt-3 flex w-full max-w-xl items-center justify-center gap-2 rounded-2xl border bg-white py-3 text-sm font-semibold"
            style={{ borderColor: "var(--ciq-teal-600)", color: "var(--ciq-teal)" }}
          >
            Resume where you left off · Question {resumeStep}
          </button>
        )}
        {savedResult?.resultId && (
          <a href={`${process.env.PUBLIC_URL}/#/r/${savedResult.resultId}`} className="ciq-press mx-auto mt-3 flex w-full max-w-xl items-center justify-center gap-2 rounded-2xl border bg-white py-3 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>
            Open saved result{savedCardName ? ` · ${savedCardName}` : ""}
          </a>
        )}
      </section>

      <FeaturedCards cards={catalogCards} updates={cardUpdates} placements={featuredPlacements} news={CARD_NEWS} />

      <section className="ciq-container ciq-container--wide mt-20 pt-2 lg:mt-28 lg:pt-4">
        <div className="text-center">
          <div className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>Start with what you need</div>
          <h2 className="mt-2 font-display text-2xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>What would you like to do?</h2>
          <p className="mx-auto mt-2 max-w-md text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Find a card, check one you have heard about, compare options or see what is new.</p>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {ALL_INTENTS.map((intent) => {
            const Icon = intent.icon;
            const content = <><span className="grid h-10 w-10 flex-shrink-0 place-items-center rounded-xl" style={{ background: "#eeeaff", color: "#5142d8" }}><Icon className="h-5 w-5" /></span><span><span className="block text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>{intent.title}</span><span className="mt-0.5 block text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>{intent.text}</span></span><ArrowRight className="ml-auto h-4 w-4 flex-shrink-0" style={{ color: "var(--ciq-teal)" }} /></>;
            if (intent.action === "quiz") return <button key={intent.title} type="button" onClick={onStart} className="ciq-press flex w-full items-center gap-3 rounded-2xl border bg-white p-4 text-left" style={{ borderColor: "var(--ciq-line)" }}>{content}</button>;
            if (intent.href) return <a key={intent.title} href={intent.href} className="ciq-press flex items-center gap-3 rounded-2xl border bg-white p-4 text-left" style={{ borderColor: "var(--ciq-line)" }}>{content}</a>;
            return <Link key={intent.title} to={intent.to} className="ciq-press flex items-center gap-3 rounded-2xl border bg-white p-4 text-left" style={{ borderColor: "var(--ciq-line)" }}>{content}</Link>;
          })}
        </div>
      </section>

      {/* sticky CTA */}
      <div className="fixed bottom-4 right-4 z-30 sm:bottom-6 sm:right-6">
        <button
          onClick={onStart}
          className="ciq-press ciq-primary-gradient ciq-soft-glow inline-flex items-center justify-center gap-2 rounded-full px-5 py-3.5 text-sm font-semibold text-white sm:px-6 sm:text-base"
          aria-label="Find my best card"
        >
          Find my best card <ArrowRight className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
