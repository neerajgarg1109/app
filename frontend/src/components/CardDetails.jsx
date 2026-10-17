import React from "react";
import { Check, ExternalLink, ShieldCheck } from "lucide-react";
import CreditCardVisual from "./CreditCardVisual";

export default function CardDetails({ card, heading = "Card details", compact = false, onApply }) {
  if (!card) return null;
  const unavailable = card.active === false || card.applicationsOpen === false;
  const facts = [
    ["Annual fee", card.annualFee || "Not specified"],
    ["Joining fee", card.joiningFee || "Not specified"],
    ["Network", card.network || "Not specified"],
    ["Credit profile", creditLabel(card.creditReq)],
  ];

  return (
    <div className="space-y-4">
      <div>
        <div className="font-display text-lg font-extrabold" style={{ color: "var(--ciq-ink)" }}>{heading}</div>
        <p className="mt-1 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>
          All benefits and conditions currently verified in the CardIQ catalogue.
        </p>
      </div>

      <StructuredBenefits card={card} />

      {!compact && <CreditCardVisual card={card} />}

      <div className="rounded-2xl p-4" style={{ background: "#f2faf7" }}>
        <div className="text-[10px] font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>Core reward proposition</div>
        <div className="mt-1.5 text-sm font-bold leading-relaxed" style={{ color: "var(--ciq-ink)" }}>{card.rewardLine || "See issuer terms for the current rewards programme."}</div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {facts.map(([label, value]) => (
          <div key={label} className="rounded-xl border bg-white p-3" style={{ borderColor: "var(--ciq-line)" }}>
            <div className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>{label}</div>
            <div className="mt-1 text-xs font-bold leading-relaxed" style={{ color: "var(--ciq-ink)" }}>{value}</div>
          </div>
        ))}
      </div>

      <div>
        <div className="font-display text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>Benefits, limits and conditions</div>
        <ul className="mt-3 space-y-2.5">
          {(card.highlights || []).map((item) => (
            <li key={item} className="flex items-start gap-2 text-sm leading-relaxed" style={{ color: "var(--ciq-ink)" }}>
              <span className="mt-0.5 grid h-5 w-5 flex-shrink-0 place-items-center rounded-full" style={{ background: "#e6f5f0" }}>
                <Check className="h-3 w-3" style={{ color: "var(--ciq-teal-600)" }} />
              </span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {(card.bestFor || []).length > 0 && (
        <div>
          <div className="text-xs font-semibold" style={{ color: "var(--ciq-ink-soft)" }}>Best suited for</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {card.bestFor.map((tag) => <span key={tag} className="rounded-full px-2.5 py-1 text-xs font-semibold capitalize" style={{ background: "#eeeaff", color: "#4538c8" }}>{tag}</span>)}
          </div>
        </div>
      )}

      <div className="rounded-xl border p-3 text-xs leading-relaxed" style={{ borderColor: "var(--ciq-line)", background: "#f7f8f6", color: "var(--ciq-ink-soft)" }}>
        <div className="flex items-center gap-1.5 font-bold" style={{ color: "var(--ciq-ink)" }}><ShieldCheck className="h-4 w-4" /> Verified information</div>
        <p className="mt-1.5">Details checked {card.verifiedOn || "date not recorded"}. {card.availabilityNote || "Availability and approval are decided by the issuer."}</p>
        {card.termsNote && <p className="mt-1.5">{card.termsNote}</p>}
        {(card.sourceUrls || []).length > 0 && (
          <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
            {card.sourceUrls.map((url, index) => <a key={url} href={url} target="_blank" rel="noopener noreferrer" className="font-semibold underline" style={{ color: "var(--ciq-teal)" }}>Issuer source {index + 1}</a>)}
          </div>
        )}
      </div>

      {onApply && (
        <button type="button" onClick={onApply} disabled={unavailable || !card.applyUrl} className="ciq-press inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>
          {unavailable ? "Applications unavailable" : `Apply on ${card.issuer}`} <ExternalLink className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

function StructuredBenefits({ card }) {
  const sections = [
    ["Welcome benefits", card.welcomeBenefits],
    ["Milestone benefits", card.milestoneBenefits],
    ["Lounge access", card.loungeBenefits],
    ["Reward exclusions", card.exclusions],
  ].filter(([, items]) => Array.isArray(items) && items.length);
  const facts = [
    ["Reward currency", card.rewardCurrency],
    ["Reward redemption", card.rewardRedemption],
    ["Forex markup", card.forexMarkup || (typeof card.forexMarkupPercent === "number" ? `${card.forexMarkupPercent}% + applicable taxes` : null)],
    ["Fuel benefit", card.fuelBenefits],
    ["Eligibility note", card.eligibilityNote],
  ].filter(([, value]) => value);
  if (!sections.length && !facts.length) return null;
  return <div className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
    <div className="font-display text-sm font-bold">Structured benefit details</div>
    {facts.map(([label, value]) => <div key={label} className="mt-3 border-t pt-3 text-sm" style={{ borderColor: "var(--ciq-line)" }}><div className="text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>{label}</div><div className="mt-1 leading-relaxed">{value}</div></div>)}
    {sections.map(([label, items]) => <div key={label} className="mt-3 border-t pt-3" style={{ borderColor: "var(--ciq-line)" }}><div className="text-xs font-bold">{label}</div><ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{items.map((item) => <li key={item}>{item}</li>)}</ul></div>)}
  </div>;
}

function creditLabel(value) {
  return ({ good: "Good credit profile", excellent: "Excellent credit profile", fair: "Fair credit profile", starter: "Starter / building credit" })[value] || "Issuer eligibility applies";
}
