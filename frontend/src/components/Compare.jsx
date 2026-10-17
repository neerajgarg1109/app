import React from "react";
import { X, Check, Star } from "lucide-react";

export default function Compare({ cards, onClose }) {
  if (!cards || cards.length === 0) return null;
  const rows = [
    cards.some((c) => typeof c._confidence === "number") && { label: "Match", get: (c) => typeof c._confidence === "number" ? `${c._confidence}%` : "—" },
    cards.some((c) => c._valueEstimate) && { label: "First-year potential", get: (c) => c._valueEstimate ? `Up to ${money(c._valueEstimate.headlinePotential)}` : "Not available" },
    cards.some((c) => c._valueEstimate) && { label: "Estimated net value", get: (c) => c._valueEstimate ? `${money(c._valueEstimate.netLow)}–${money(c._valueEstimate.netHigh)}` : "Not available" },
    { label: "Best for", get: (c) => (c.rewardLine || "") },
    { label: "Annual fee", get: (c) => c.annualFee },
    { label: "Joining fee", get: (c) => c.joiningFee || "See issuer" },
    { label: "Network", get: (c) => c.network },
    { label: "Forex / travel", get: (c) => (c.highlights || []).find((h) => /forex|foreign|international|lounge/i.test(h)) || "No highlighted benefit" },
    { label: "Important limit", get: (c) => (c.highlights || []).find((h) => /cap|limit|exclude|minimum|waiv/i.test(h)) || "See issuer terms" },
    { label: "cardIQ rating", get: (c) => `${c.rating} / 5`, star: true },
  ].filter(Boolean);

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/40" onClick={onClose}>
      <div
        className="mt-auto max-h-[88vh] overflow-y-auto rounded-t-3xl bg-white no-scrollbar ciq-pop"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b bg-white px-5 py-4" style={{ borderColor: "var(--ciq-line)" }}>
          <h3 className="font-display text-lg font-extrabold" style={{ color: "var(--ciq-ink)" }}>Compare cards</h3>
          <button onClick={onClose} className="ciq-press grid h-9 w-9 place-items-center rounded-full border" style={{ borderColor: "var(--ciq-line)" }}>
            <X className="h-4 w-4" style={{ color: "var(--ciq-ink)" }} />
          </button>
        </div>

        <div className="p-5">
          {/* header row of card names */}
          <div className="grid gap-2" style={{ gridTemplateColumns: `110px repeat(${cards.length}, minmax(0,1fr))` }}>
            <div />
            {cards.map((c) => (
              <div key={c.id} className="text-center">
                <div className="mx-auto mb-2 h-10 w-16 rounded-lg" style={{ background: `linear-gradient(135deg, ${c.palette[0]}, ${c.palette[1]})` }} />
                <div className="font-display text-xs font-bold leading-tight" style={{ color: "var(--ciq-ink)" }}>{c.name}</div>
              </div>
            ))}
          </div>

          <div className="mt-4 space-y-0">
            {rows.map((row, i) => (
              <div
                key={row.label}
                className="grid items-center gap-2 py-3"
                style={{ gridTemplateColumns: `110px repeat(${cards.length}, minmax(0,1fr))`, borderTop: i === 0 ? "none" : "1px solid var(--ciq-line)" }}
              >
                <div className="text-xs font-semibold" style={{ color: "var(--ciq-ink-soft)" }}>{row.label}</div>
                {cards.map((c) => (
                  <div key={c.id} className="text-center text-xs font-medium" style={{ color: "var(--ciq-ink)" }}>
                    {row.star ? (
                      <span className="inline-flex items-center gap-1">
                        <Star className="h-3 w-3 fill-current" style={{ color: "var(--ciq-amber)" }} /> {row.get(c)}
                      </span>
                    ) : row.get(c)}
                  </div>
                ))}
              </div>
            ))}

            {/* highlights */}
            <div className="grid gap-2 py-3" style={{ gridTemplateColumns: `110px repeat(${cards.length}, minmax(0,1fr))`, borderTop: "1px solid var(--ciq-line)" }}>
              <div className="text-xs font-semibold" style={{ color: "var(--ciq-ink-soft)" }}>Top perks</div>
              {cards.map((c) => (
                <ul key={c.id} className="space-y-1.5">
                  {c.highlights.slice(0, 3).map((h) => (
                    <li key={h} className="flex items-start gap-1 text-[11px] leading-snug" style={{ color: "var(--ciq-ink)" }}>
                      <Check className="mt-0.5 h-3 w-3 flex-shrink-0" style={{ color: "var(--ciq-teal-600)" }} /> {h}
                    </li>
                  ))}
                </ul>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function money(value) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value); }
