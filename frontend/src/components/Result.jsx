import React, { useState } from "react";
import { Check, RotateCcw, Star, ArrowRight, Sparkles, ChevronRight, Mail, Loader2, GitCompare, Share2, ExternalLink, Image as ImageIcon } from "lucide-react";
import Logo from "./Logo";
import CreditCardVisual from "./CreditCardVisual";
import Compare from "./Compare";
import { emailResult } from "../api";

export default function Result({ scored, resultId, onRestart, shared = false }) {
  const best = scored[0];
  const alternates = scored.slice(1, 3);
  const card = best.card;

  const [emailState, setEmailState] = useState("idle"); // idle | sending | sent | error
  const [sentTo, setSentTo] = useState("");
  const [showCompare, setShowCompare] = useState(false);
  const [copied, setCopied] = useState(false);

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

  const handleShare = async () => {
    const url = `${window.location.origin}/r/${resultId}`;
    const shareData = { title: "My cardIQ match", text: `My best credit card match is ${card.name}`, url };
    try {
      if (navigator.share) {
        await navigator.share(shareData);
        return;
      }
    } catch (e) { /* fall through to copy */ }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2200);
    } catch (e) { /* noop */ }
  };

  const handleApply = () => {
    if (card.applyUrl) window.open(card.applyUrl, "_blank", "noopener,noreferrer");
  };

  const [imgState, setImgState] = useState("idle"); // idle | working | done

  const generateShareImage = async () => {
    setImgState("working");
    try {
      const W = 1080, H = 1080;
      const canvas = document.createElement("canvas");
      canvas.width = W; canvas.height = H;
      const ctx = canvas.getContext("2d");

      // background
      ctx.fillStyle = "#f6f7f5";
      ctx.fillRect(0, 0, W, H);

      // card panel gradient
      const grad = ctx.createLinearGradient(90, 170, 990, 640);
      grad.addColorStop(0, card.palette[0]);
      grad.addColorStop(1, card.palette[1]);
      roundRect(ctx, 90, 170, 900, 470, 40);
      ctx.fillStyle = grad;
      ctx.fill();

      // brand on card
      ctx.fillStyle = "#ffffff";
      ctx.font = "800 46px 'Plus Jakarta Sans', sans-serif";
      ctx.fillText("card", 140, 250);
      const cw = ctx.measureText("card").width;
      ctx.fillStyle = card.accent;
      ctx.fillText("IQ", 140 + cw, 250);

      // chip
      ctx.fillStyle = "#e9c766";
      roundRect(ctx, 140, 300, 90, 64, 12); ctx.fill();

      // card name on card
      ctx.fillStyle = "#ffffff";
      ctx.font = "800 64px 'Plus Jakarta Sans', sans-serif";
      ctx.fillText(card.name, 140, 500);
      ctx.font = "500 32px Inter, sans-serif";
      ctx.fillStyle = "rgba(255,255,255,0.85)";
      ctx.fillText(card.rewardLine, 140, 560);

      // heading
      ctx.fillStyle = "#0f1a17";
      ctx.font = "800 54px 'Plus Jakarta Sans', sans-serif";
      ctx.fillText("My cardIQ match", 90, 740);

      // confidence pill
      ctx.fillStyle = "#0d9488";
      roundRect(ctx, 90, 770, 300, 70, 35); ctx.fill();
      ctx.fillStyle = "#ffffff";
      ctx.font = "700 36px Inter, sans-serif";
      ctx.fillText(`${best.confidence}% match`, 120, 816);

      // benefits
      ctx.fillStyle = "#55615c";
      ctx.font = "500 32px Inter, sans-serif";
      card.highlights.slice(0, 3).forEach((h, i) => {
        ctx.fillStyle = "#0d9488";
        ctx.fillText("\u2713", 92, 910 + i * 54);
        ctx.fillStyle = "#334039";
        ctx.fillText(truncate(h, 46), 140, 910 + i * 54);
      });

      // footer
      ctx.fillStyle = "#9aa39e";
      ctx.font = "500 26px Inter, sans-serif";
      ctx.fillText("Find your perfect credit card \u00b7 cardIQ", 90, 1030);

      const blob = await new Promise((res) => canvas.toBlob(res, "image/png"));
      const file = new File([blob], "cardiq-match.png", { type: "image/png" });

      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({ files: [file], title: "My cardIQ match", text: `My best card match is ${card.name}` });
      } else {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = "cardiq-match.png";
        document.body.appendChild(a); a.click(); a.remove();
        URL.revokeObjectURL(url);
      }
      setImgState("done");
      setTimeout(() => setImgState("idle"), 2200);
    } catch (e) {
      setImgState("idle");
    }
  };

  return (
    <div className="ciq-shell pb-28">
      <header className="ciq-container flex items-center justify-between py-5">
        <Logo size="md" onClick={onRestart} />
        <button onClick={onRestart} className="ciq-press flex items-center gap-1.5 rounded-full border bg-white px-3 py-1.5 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>
          <RotateCcw className="h-3.5 w-3.5" /> {shared ? "Take quiz" : "Retake"}
        </button>
      </header>

      <section className="ciq-container text-center ciq-fade-up">
        <div className="mx-auto inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold" style={{ background: "#e6f5f0", color: "var(--ciq-teal)" }}>
          <Sparkles className="h-3.5 w-3.5" /> Your best match
        </div>
        <h1 className="mt-3 font-display text-3xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>{card.name}</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{card.tagline}</p>
        {typeof best.confidence === "number" && (
          <div className="mt-3 inline-flex items-center gap-2 rounded-full border px-3 py-1.5" style={{ borderColor: "var(--ciq-line)", background: "#fff" }}>
            <span className="relative grid h-6 w-6 place-items-center">
              <svg viewBox="0 0 36 36" className="h-6 w-6 -rotate-90">
                <circle cx="18" cy="18" r="15" fill="none" stroke="#eef0ec" strokeWidth="5" />
                <circle cx="18" cy="18" r="15" fill="none" stroke="#0d9488" strokeWidth="5" strokeLinecap="round"
                  strokeDasharray={`${(best.confidence / 100) * 94.2} 94.2`} />
              </svg>
            </span>
            <span className="text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>{best.confidence}% match</span>
          </div>
        )}
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
        <div className="mt-4 grid grid-cols-3 gap-2.5">
          <button
            onClick={handleEmail}
            disabled={emailState === "sending" || emailState === "sent"}
            className="ciq-press flex items-center justify-center gap-1.5 rounded-2xl border bg-white py-3 text-sm font-semibold"
            style={{ borderColor: emailState === "sent" ? "var(--ciq-teal-600)" : "var(--ciq-line)", color: "var(--ciq-ink)" }}
          >
            {emailState === "sending" && <Loader2 className="h-4 w-4 ciq-spin" />}
            {emailState === "sent" ? (<><Check className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} /> Emailed</>) :
             emailState === "sending" ? "Sending…" : (<><Mail className="h-4 w-4" /> Email</>)}
          </button>
          <button
            onClick={handleShare}
            className="ciq-press flex items-center justify-center gap-1.5 rounded-2xl border bg-white py-3 text-sm font-semibold"
            style={{ borderColor: copied ? "var(--ciq-teal-600)" : "var(--ciq-line)", color: "var(--ciq-ink)" }}
          >
            {copied ? (<><Check className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} /> Copied</>) : (<><Share2 className="h-4 w-4" /> Share</>)}
          </button>
          <button
            onClick={() => setShowCompare(true)}
            className="ciq-press flex items-center justify-center gap-1.5 rounded-2xl border bg-white py-3 text-sm font-semibold"
            style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}
          >
            <GitCompare className="h-4 w-4" /> Compare
          </button>
        </div>
        <button
          onClick={generateShareImage}
          disabled={imgState === "working"}
          className="ciq-press mt-2.5 flex w-full items-center justify-center gap-2 rounded-2xl border bg-white py-3 text-sm font-semibold"
          style={{ borderColor: imgState === "done" ? "var(--ciq-teal-600)" : "var(--ciq-line)", color: "var(--ciq-ink)" }}
        >
          {imgState === "working" ? (<><Loader2 className="h-4 w-4 ciq-spin" /> Creating image…</>) :
           imgState === "done" ? (<><Check className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} /> Image ready</>) :
           (<><ImageIcon className="h-4 w-4" /> Share as image</>)}
        </button>
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
                {typeof alt.confidence === "number" && (
                  <span className="flex-shrink-0 rounded-full px-2 py-0.5 text-xs font-bold" style={{ background: "#e6f5f0", color: "var(--ciq-teal)" }}>{alt.confidence}%</span>
                )}
                <ChevronRight className="h-4 w-4 flex-shrink-0" style={{ color: "var(--ciq-ink-soft)" }} />
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-white/90 backdrop-blur" style={{ borderColor: "var(--ciq-line)" }}>
        <div className="ciq-container py-3">
          <button onClick={handleApply} className="ciq-press inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-base font-semibold text-white" style={{ background: "var(--ciq-teal-600)", boxShadow: "0 16px 30px -14px rgba(13,148,136,0.7)" }}>
            Apply for {card.name} <ExternalLink className="h-5 w-5" />
          </button>
        </div>
      </div>

      {showCompare && <Compare cards={compareCards} onClose={() => setShowCompare(false)} />}
    </div>
  );
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function truncate(str, n) {
  return str.length > n ? str.slice(0, n - 1) + "…" : str;
}

