import React, { useEffect, useState } from "react";
import { ArrowRight, ShieldCheck, Timer, BellOff, List, TrendingUp, Database, PhoneCall, Sparkles, Check, Search, GitCompare, Newspaper, Building2, Calculator } from "lucide-react";
import Logo from "./Logo";
import { TRUST_POINTS, PROBLEMS } from "../mock/mock";
import { getCards, getResult } from "../api";
import { Link } from "react-router-dom";
import CARD_CATEGORIES from "../data/cardCategories.json";

const ICONS = { ShieldCheck, Timer, BellOff, List, TrendingUp, Database, PhoneCall };

const INTENTS = [
  { title: "Help me choose", text: "Get a recommendation based on how you spend.", icon: Sparkles, action: "quiz" },
  { title: "Calculate my annual value", text: "Rank cards using your monthly spending and annual fees.", icon: Calculator, to: "/calculator" },
  { title: "Research a card", text: "Search fees, rewards, exclusions and our verdict.", icon: Search, to: "/cards" },
  { title: "Compare with my card", text: "Mark a card you own and compare alternatives.", icon: GitCompare, to: "/cards?mode=compare" },
  { title: "See recent card updates", text: "Start with the most recently verified cards.", icon: Newspaper, to: "/cards?sort=recent" },
  { title: "Browse by issuer", text: "See every catalogued card from each issuer.", icon: Building2, to: "/cards?browse=issuers" },
  { title: "Issuer help & card closure", text: "Use verified official support and closure channels.", icon: PhoneCall, to: "/help/issuers" },
];

export default function Landing({ onStart, onResume, resumeStep, savedResult }) {
  const [catalogStats, setCatalogStats] = useState({ cards: null, issuers: null });
  const [savedCardName, setSavedCardName] = useState(null);

  useEffect(() => {
    let active = true;
    getCards()
      .then((cards) => {
        if (!active || !Array.isArray(cards)) return;
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
      <header className="ciq-container flex items-center justify-between py-5">
        <Logo size="md" />
        <div className="flex items-center gap-2">
          <Link to="/cards" className="ciq-press rounded-full border bg-white px-3 py-2 text-xs font-semibold sm:text-sm" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>Browse cards</Link>
          <button
            onClick={onStart}
            className="ciq-press ciq-primary-gradient ciq-soft-glow rounded-full px-4 py-2 text-sm font-semibold text-white"
          >
            Get started
          </button>
        </div>
      </header>

      {/* Hero */}
      <section className="ciq-container pt-6 text-center ciq-fade-up">
        <div
          className="mx-auto mb-5 inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold"
          style={{ background: "linear-gradient(90deg,#eeeaff,#e4faf6)", color: "var(--ciq-teal)" }}
        >
          <Sparkles className="h-3.5 w-3.5" /> Independent. Evidence-led. Built around you.
        </div>
        <h1 className="font-display text-[34px] leading-[1.1] font-extrabold" style={{ color: "var(--ciq-ink)" }}>
          Your clearest path to the <span className="ciq-gradient-text">right credit card</span>
        </h1>
        <p className="mx-auto mt-4 max-w-sm text-[15px]" style={{ color: "var(--ciq-ink-soft)" }}>
          CardIQ checks {catalogStats.cards == null ? "the live card catalogue" : `${catalogStats.cards} cards across ${catalogStats.issuers} issuers`}, weighs the fees and fine print against how you spend, and explains its strongest recommendation.
        </p>

        <div className="ciq-soft-glow mt-5 grid grid-cols-3 overflow-hidden rounded-2xl border bg-white/90 text-center backdrop-blur" style={{ borderColor: "var(--ciq-line)" }}>
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

        <div className="mt-6 flex flex-col gap-2">
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

        <button
          onClick={onStart}
          className="ciq-press ciq-primary-gradient ciq-soft-glow mt-8 inline-flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-base font-semibold text-white"
        >
          Find my strongest match <ArrowRight className="h-5 w-5" />
        </button>
        <Link to="/cards" className="ciq-press mt-3 inline-flex w-full items-center justify-center gap-2 rounded-2xl border bg-white py-3 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>
          Search and explore all cards
        </Link>
        {resumeStep && (
          <button
            onClick={onResume}
            className="ciq-press mt-3 inline-flex w-full items-center justify-center gap-2 rounded-2xl border bg-white py-3 text-sm font-semibold"
            style={{ borderColor: "var(--ciq-teal-600)", color: "var(--ciq-teal)" }}
          >
            Resume where you left off · Question {resumeStep}
          </button>
        )}
        {savedResult?.resultId && (
          <a href={`${process.env.PUBLIC_URL}/#/r/${savedResult.resultId}`} className="ciq-press mt-3 inline-flex w-full items-center justify-center gap-2 rounded-2xl border bg-white py-3 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>
            Open saved result{savedCardName ? ` · ${savedCardName}` : ""}
          </a>
        )}
      </section>

      <section className="ciq-container mt-12">
        <div className="text-center">
          <div className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>Start with what you need</div>
          <h2 className="mt-2 font-display text-2xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>More than a card quiz</h2>
          <p className="mx-auto mt-2 max-w-md text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Choose a card, research one you have heard about, or compare it with a card already in your wallet.</p>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {INTENTS.map((intent) => {
            const Icon = intent.icon;
            const content = <><span className="grid h-10 w-10 flex-shrink-0 place-items-center rounded-xl" style={{ background: "#eeeaff", color: "#5142d8" }}><Icon className="h-5 w-5" /></span><span><span className="block text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>{intent.title}</span><span className="mt-0.5 block text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>{intent.text}</span></span><ArrowRight className="ml-auto h-4 w-4 flex-shrink-0" style={{ color: "var(--ciq-teal)" }} /></>;
            return intent.action === "quiz"
              ? <button key={intent.title} type="button" onClick={onStart} className="ciq-press flex w-full items-center gap-3 rounded-2xl border bg-white p-4 text-left" style={{ borderColor: "var(--ciq-line)" }}>{content}</button>
              : <Link key={intent.title} to={intent.to} className="ciq-press flex items-center gap-3 rounded-2xl border bg-white p-4 text-left" style={{ borderColor: "var(--ciq-line)" }}>{content}</Link>;
          })}
        </div>
      </section>

      {/* Problem section */}
      <section className="ciq-container mt-16">
        <h2 className="font-display text-2xl font-extrabold text-center" style={{ color: "var(--ciq-ink)" }}>
          A recommendation you can verify
        </h2>
        <p className="mt-2 text-center text-sm" style={{ color: "var(--ciq-ink-soft)" }}>
          See why a card fits, what it costs and what could reduce its value—before you leave for the issuer’s site.
        </p>
        <div className="mt-6 grid grid-cols-2 gap-3">
          {PROBLEMS.map((p) => {
            const Icon = ICONS[p.icon];
            return (
              <div
                key={p.title}
                className="ciq-feature-card rounded-2xl border bg-white p-4"
                style={{ borderColor: "var(--ciq-line)" }}
              >
                <div
                  className="grid h-9 w-9 place-items-center rounded-xl"
                  style={{ background: "linear-gradient(145deg,#fff0ed,#ffe8f2)", color: "var(--ciq-coral)" }}
                >
                  <Icon className="h-4.5 w-4.5" />
                </div>
                <div className="mt-3 font-display font-bold text-sm" style={{ color: "var(--ciq-ink)" }}>{p.title}</div>
                <div className="mt-1 text-xs leading-snug" style={{ color: "var(--ciq-ink-soft)" }}>{p.text}</div>
              </div>
            );
          })}
        </div>
      </section>

      {/* How cardIQ is different */}
      <section className="ciq-container" style={{ marginTop: 32 }}>
        <div
          className="ciq-trust-panel rounded-3xl p-6 text-white"
          style={{ background: "linear-gradient(145deg,#33268f 0%,#604ee8 55%,#0e9e98 130%)", boxShadow: "0 24px 55px -30px rgba(61,45,184,.8)" }}
        >
          <h2 className="font-display text-2xl font-extrabold">Built to earn your trust.</h2>
          <p className="mt-2 text-sm text-white/85">
            We turn {catalogStats.cards == null ? "the live card catalogue" : `a catalogue of ${catalogStats.cards} cards`} into one reasoned recommendation, using your priorities—not a sponsored leaderboard.
          </p>
          <ul className="mt-5 space-y-3">
            {["Card facts traced to issuer and official partner sources", "Fees, exclusions and trade-offs shown clearly", "No bank can pay to improve its match score"].map((x) => (
              <li key={x} className="flex items-start gap-2 text-sm">
                <span className="mt-0.5 grid h-5 w-5 flex-shrink-0 place-items-center rounded-full bg-white/20">
                  <Check className="h-3 w-3" />
                </span>
                {x}
              </li>
            ))}
          </ul>
          <a href={`${process.env.PUBLIC_URL}/methodology/`} className="mt-5 inline-block text-xs font-semibold text-white underline underline-offset-4">Read our methodology and revenue disclosure</a>
        </div>
      </section>

      {/* sticky CTA */}
      <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-white/90 backdrop-blur" style={{ borderColor: "var(--ciq-line)" }}>
        <div className="ciq-container py-3">
          <button
            onClick={onStart}
            className="ciq-press ciq-primary-gradient inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-base font-semibold text-white"
          >
            Get my evidence-backed match <ArrowRight className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
