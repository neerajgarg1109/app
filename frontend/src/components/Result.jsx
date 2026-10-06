import React, { useState } from "react";
import { Check, RotateCcw, Star, ArrowRight, Sparkles, ChevronRight, Mail, Loader2, GitCompare } from "lucide-react";
import Logo from "./Logo";
import CreditCardVisual from "./CreditCardVisual";
import Compare from "./Compare";
import { emailResult } from "../api";

export default function Result({ scored, resultId, onRestart }) {
  const best = scored[0];
  const alternates = scored.slice(1, 3);
  const card = best.card;

  const [emailState, setEmailState] = useState("idle"); // idle | sending | sent | error
  const [sentTo, setSentTo] = useState("");
  const [showCompare, setShowCompare] = useState(false);

  const compareCards = scored.slice(0, 3).map((s) => s.card);

  const handleEmail = async () => {
    if (emailState === "sending" || !resultId) return;
    setEmailState("sending");
    try {
      const data = await emailResult(resultId);
      setSentTo(data.sent_to || "");
      setEmailState("sent");
    } catch (e) {
      setEmailState("error");
    }
  };

  return (
    <div className="ciq-shell pb-28">
      <header className="ciq-container flex items-center justify-between py-5">
        <Logo size="md" onClick={onRestart} />
        <button onClick={onRestart} className="ciq-press flex items-center gap-1.5 rounded-full border bg-white px-3 py-1.5 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>
          <RotateCcw className="h-3.5 w-3.5" /> Retake
        </button>
      </header>

      <section className="ciq-container text-center ciq-fade-up">
        <div className="mx-auto inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold" style={{ background: "#e6f5f0", color: "var(--ciq-teal)" }}>
          <Sparkles className="h-3.5 w-3.5" /> Your best match
        </div>
        <h1 className="mt-3 font-display text-3xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>{card.name}</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{card.tagline}</p>
      </section>

      <section className="ciq-container mt-6 ciq-pop">
        <CreditCardVisual card={card} />
      </section>

      <section className="ciq-container mt-5">
        <div className="flex items-center justify-center gap-1 text-sm">
          <Star className="h-4 w-4 fill-current" style={{ color: "var(--ciq-amber)" }} />
          <span className="font-bold" style={{ color: "var(--ciq-ink)" }}>{card.rating}</span>
          <span style={{ color: "var(--ciq-ink-soft)" }}>· {card.annualFee}</span>
        </div>

        {/* action row */}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <button
            onClick={handleEmail}
            disabled={emailState === "sending" || emailState === "sent"}
            className="ciq-press flex items-center justify-center gap-2 rounded-2xl border bg-white py-3 text-sm font-semibold"
            style={{ borderColor: emailState === "sent" ? "var(--ciq-teal-600)" : "var(--ciq-line)", color: "var(--ciq-ink)" }}
          >
            {emailState === "sending" && <Loader2 className="h-4 w-4 ciq-spin" />}
            {emailState === "sent" ? (<><Check className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} /> Emailed</>) :
             emailState === "sending" ? "Sending…" : (<><Mail className="h-4 w-4" /> Email me this</>)}
          </button>
          <button
            onClick={() => setShowCompare(true)}
            className="ciq-press flex items-center justify-center gap-2 rounded-2xl border bg-white py-3 text-sm font-semibold"
            style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}
          >
            <GitCompare className="h-4 w-4" /> Compare
          </button>
        </div>
        {emailState === "sent" && sentTo && (
          <p className="mt-2 text-center text-xs" style={{ color: "var(--ciq-teal)" }}>Sent to {sentTo}</p>
        )}
        {emailState === "error" && (
          <p className="mt-2 text-center text-xs" style={{ color: "#b4433f" }}>Couldn't send email. Try again.</p>
        )}

        {best.reasons.length > 0 && (
          <div className="mt-4 rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
            <div className="font-display text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>Why this fits you</div>
            <ul className="mt-2 space-y-1.5">
              {best.reasons.map((r) => (
                <li key={r} className="flex items-start gap-2 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>
                  <Check className="mt-0.5 h-4 w-4 flex-shrink-0" style={{ color: "var(--ciq-teal-600)" }} /> {r}
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="ciq-container mt-4">
        <div className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="font-display text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>Key benefits</div>
          <ul className="mt-3 space-y-2.5">
            {card.highlights.map((h) => (
              <li key={h} className="flex items-start gap-2 text-sm" style={{ color: "var(--ciq-ink)" }}>
                <span className="mt-0.5 grid h-5 w-5 flex-shrink-0 place-items-center rounded-full" style={{ background: "#e6f5f0" }}>
                  <Check className="h-3 w-3" style={{ color: "var(--ciq-teal-600)" }} />
                </span>
                {h}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {alternates.length > 0 && (
        <section className="ciq-container mt-6">
          <div className="font-display text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>Runner-ups worth a look</div>
          <div className="mt-3 space-y-3">
            {alternates.map((alt) => (
              <div key={alt.card.id} className="flex items-center gap-3 rounded-2xl border bg-white p-3" style={{ borderColor: "var(--ciq-line)" }}>
                <div className="h-11 w-16 flex-shrink-0 rounded-lg" style={{ background: `linear-gradient(135deg, ${alt.card.palette[0]}, ${alt.card.palette[1]})` }} />
                <div className="min-w-0 flex-1">
                  <div className="truncate font-display text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>{alt.card.name}</div>
                  <div className="truncate text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{alt.card.rewardLine}</div>
                </div>
                <ChevronRight className="h-4 w-4 flex-shrink-0" style={{ color: "var(--ciq-ink-soft)" }} />
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-white/90 backdrop-blur" style={{ borderColor: "var(--ciq-line)" }}>
        <div className="ciq-container py-3">
          <button className="ciq-press inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-base font-semibold text-white" style={{ background: "var(--ciq-teal-600)", boxShadow: "0 16px 30px -14px rgba(13,148,136,0.7)" }}>
            Apply for {card.name} <ArrowRight className="h-5 w-5" />
          </button>
        </div>
      </div>

      {showCompare && <Compare cards={compareCards} onClose={() => setShowCompare(false)} />}
    </div>
  );
}
