import React from "react";
import { X, Check } from "lucide-react";

export default function Compare({ cards, onClose, inline = false, showHeading = true }) {
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
  ].filter(Boolean);

  return (
    <div className={inline ? "rounded-3xl border bg-white overflow-hidden" : "fixed inset-0 z-50 flex flex-col bg-black/40"} onClick={inline ? undefined : onClose}>
      <div
        className={inline ? "overflow-x-auto bg-white" : "mt-auto max-h-[88vh] overflow-y-auto rounded-t-3xl bg-white no-scrollbar ciq-pop"}
        onClick={(e) => e.stopPropagation()}
      >
        {showHeading && <div className="sticky top-0 flex items-center justify-between border-b bg-white px-5 py-4" style={{ borderColor: "var(--ciq-line)" }}>
          <h3 className="font-display text-lg font-extrabold" style={{ color: "var(--ciq-ink)" }}>Compare cards</h3>
          {!inline && <button aria-label="Close comparison" onClick={onClose} className="ciq-press grid h-9 w-9 place-items-center rounded-full border" style={{ borderColor: "var(--ciq-line)" }}>
            <X className="h-4 w-4" style={{ color: "var(--ciq-ink)" }} />
          </button>}
        </div>}

        <div className="p-5" style={inline ? { minWidth: cards.length === 3 ? 720 : 520 } : undefined}>
          {/* header row of card names */}
          <div className="grid gap-2" style={{ gridTemplateColumns: `110px repeat(${cards.length}, minmax(0,1fr))` }}>
            <div />
            {cards.map((c) => (
              <div key={c.id} className="text-center">
                <div className="mx-auto mb-2 h-10 w-16 rounded-lg" style={{ background: `linear-gradient(135deg, ${c.palette?.[0] || "#312e81"}, ${c.palette?.[1] || "#6366f1"})` }} />
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
                    {row.get(c)}
                  </div>
                ))}
              </div>
            ))}

            {/* highlights */}
            <div className="grid gap-2 py-3" style={{ gridTemplateColumns: `110px repeat(${cards.length}, minmax(0,1fr))`, borderTop: "1px solid var(--ciq-line)" }}>
              <div className="text-xs font-semibold" style={{ color: "var(--ciq-ink-soft)" }}>Top perks</div>
              {cards.map((c) => (
                <ul key={c.id} className="space-y-1.5">
                  {(c.highlights || []).slice(0, 3).map((h) => (
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
