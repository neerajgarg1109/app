import React from "react";
import { ArrowRight, ShieldCheck, Timer, BellOff, List, TrendingUp, Database, PhoneCall, Sparkles, Check } from "lucide-react";
import Logo from "./Logo";
import { TRUST_POINTS, PROBLEMS } from "../mock/mock";

const ICONS = { ShieldCheck, Timer, BellOff, List, TrendingUp, Database, PhoneCall };

export default function Landing({ onStart }) {
  return (
    <div className="ciq-shell pb-28">
      <header className="ciq-container flex items-center justify-between py-5">
        <Logo size="md" />
        <button
          onClick={onStart}
          className="ciq-press rounded-full px-4 py-2 text-sm font-semibold text-white"
          style={{ background: "var(--ciq-teal-600)" }}
        >
          Get started
        </button>
      </header>

      {/* Hero */}
      <section className="ciq-container pt-6 text-center ciq-fade-up">
        <div
          className="mx-auto mb-5 inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold"
          style={{ background: "#e6f5f0", color: "var(--ciq-teal)" }}
        >
          <Sparkles className="h-3.5 w-3.5" /> Unbiased, AI-matched picks
        </div>
        <h1 className="font-display text-[34px] leading-[1.1] font-extrabold" style={{ color: "var(--ciq-ink)" }}>
          Find the <span style={{ color: "var(--ciq-teal-600)" }}>one</span> credit card that fits your life
        </h1>
        <p className="mx-auto mt-4 max-w-sm text-[15px]" style={{ color: "var(--ciq-ink-soft)" }}>
          No endless lists. No paid rankings. Answer a few smart questions and get a single recommendation that's actually right for you.
        </p>

        <div className="mt-6 flex flex-col gap-2">
          {TRUST_POINTS.map((t) => {
            const Icon = ICONS[t.icon];
            return (
              <div key={t.text} className="flex items-center justify-center gap-2 text-sm font-medium" style={{ color: "var(--ciq-ink)" }}>
                <Icon className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} />
                {t.text}
              </div>
            );
          })}
        </div>

        <button
          onClick={onStart}
          className="ciq-press mt-8 inline-flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-base font-semibold text-white"
          style={{ background: "var(--ciq-teal-600)", boxShadow: "0 16px 30px -14px rgba(13,148,136,0.7)" }}
        >
          Find my best card <ArrowRight className="h-5 w-5" />
        </button>
      </section>

      {/* Problem section */}
      <section className="ciq-container mt-16">
        <h2 className="font-display text-2xl font-extrabold text-center" style={{ color: "var(--ciq-ink)" }}>
          Every card site looks the same
        </h2>
        <p className="mt-2 text-center text-sm" style={{ color: "var(--ciq-ink-soft)" }}>
          And somehow the “best” card is always the one they get paid to show you.
        </p>
        <div className="mt-6 grid grid-cols-2 gap-3">
          {PROBLEMS.map((p) => {
            const Icon = ICONS[p.icon];
            return (
              <div
                key={p.title}
                className="rounded-2xl border bg-white p-4"
                style={{ borderColor: "var(--ciq-line)" }}
              >
                <div
                  className="grid h-9 w-9 place-items-center rounded-xl"
                  style={{ background: "#fdecec", color: "#d9534f" }}
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
      <section className="ciq-container mt-12">
        <div
          className="rounded-3xl p-6 text-white"
          style={{ background: "linear-gradient(160deg,#0f766e,#0d9488)" }}
        >
          <h2 className="font-display text-2xl font-extrabold">cardIQ flips the model.</h2>
          <p className="mt-2 text-sm text-white/85">
            Instead of showing you 100 cards, we ask a few smart questions and give you the one card that actually fits your life.
          </p>
          <ul className="mt-5 space-y-3">
            {["One honest recommendation, not a sponsored list", "We never sell your data to banks", "Zero spam calls — your details stay yours"].map((x) => (
              <li key={x} className="flex items-start gap-2 text-sm">
                <span className="mt-0.5 grid h-5 w-5 flex-shrink-0 place-items-center rounded-full bg-white/20">
                  <Check className="h-3 w-3" />
                </span>
                {x}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* sticky CTA */}
      <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-white/90 backdrop-blur" style={{ borderColor: "var(--ciq-line)" }}>
        <div className="ciq-container py-3">
          <button
            onClick={onStart}
            className="ciq-press inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-base font-semibold text-white"
            style={{ background: "var(--ciq-teal-600)" }}
          >
            Find my best card <ArrowRight className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
