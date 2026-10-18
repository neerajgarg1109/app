import React from "react";
import { Check, ExternalLink, ShieldCheck } from "lucide-react";
import CreditCardVisual from "./CreditCardVisual";
import { editorialInsights } from "../editorialInsights";
import SharePanel from "./SharePanel";

export default function CardDetails({ card, heading = "Card details", compact = false, onApply }) {
  if (!card) return null;
  const unavailable = card.active === false || card.applicationsOpen === false;
  const editorial = editorialInsights(card);
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
          The key costs, benefits and catches—followed by full details if you need them.
        </p>
      </div>

      {!compact && <CreditCardVisual card={card} size="sm" />}

      <section className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
        <div className="text-[10px] font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>At a glance</div>
        <div className="mt-2 text-sm font-bold leading-relaxed" style={{ color: "var(--ciq-ink)" }}>{card.rewardLine || "See issuer terms for the current rewards programme."}</div>
        <div className="mt-4 grid grid-cols-2 gap-2">
          {facts.map(([label, value]) => (
            <div key={label} className="rounded-xl p-3" style={{ background: "#f7f8f6" }}>
              <div className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>{label}</div>
              <div className="mt-1 text-xs font-bold leading-relaxed" style={{ color: "var(--ciq-ink)" }}>{value}</div>
            </div>
          ))}
        </div>
        {(card.bestFor || []).length > 0 && <div className="mt-3 flex flex-wrap gap-2">{card.bestFor.slice(0, 5).map((tag) => <span key={tag} className="rounded-full px-2.5 py-1 text-xs font-semibold capitalize" style={{ background: "#eeeaff", color: "#4538c8" }}>{tag}</span>)}</div>}
      </section>

      <section className="rounded-2xl border p-4" style={{ borderColor: "#b9e4da", background: "linear-gradient(145deg,#f2faf7,#ffffff)" }}>
        <div className="text-[10px] font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>Quick decision</div>
        <h3 className="mt-1 font-display text-lg font-extrabold" style={{ color: "var(--ciq-ink)" }}>Is this card right for you?</h3>
        <p className="mt-2 text-sm leading-relaxed" style={{ color: "var(--ciq-ink)" }}>{editorial.summary}</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <DecisionPoint title="Best for" text={editorial.idealFor[0]} />
          <DecisionPoint title="Why consider it" text={editorial.strengths[0]} />
          <DecisionPoint title="Main catch" text={editorial.tradeoffs[0]} />
        </div>
        <div className="mt-4 rounded-xl border-l-4 bg-white p-3" style={{ borderColor: "var(--ciq-teal-600)" }}><div className="text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--ciq-teal)" }}>Bottom line</div><p className="mt-1.5 text-sm font-semibold leading-relaxed">{editorial.verdict}</p></div>
      </section>

      {onApply && (
        <div><button type="button" onClick={onApply} disabled={unavailable || !card.applyUrl} className="ciq-press inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>
          {unavailable ? "Applications unavailable" : `Check eligibility on ${card.issuer}`} <ExternalLink className="h-4 w-4" />
        </button>{card.affiliateDisclosureRequired && <p className="mt-2 text-center text-[10px] leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>CardIQ may earn a commission if you apply through this link. This does not affect our match score or editorial view.</p>}</div>
      )}

      <section className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
        <h3 className="font-display text-base font-extrabold" style={{ color: "var(--ciq-ink)" }}>Key benefits and conditions</h3>
        <ul className="mt-3 space-y-2.5">
          {(card.highlights || []).slice(0, 5).map((item) => (
            <li key={item} className="flex items-start gap-2 text-sm leading-relaxed" style={{ color: "var(--ciq-ink)" }}>
              <span className="mt-0.5 grid h-5 w-5 flex-shrink-0 place-items-center rounded-full" style={{ background: "#e6f5f0" }}>
                <Check className="h-3 w-3" style={{ color: "var(--ciq-teal-600)" }} />
              </span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </section>

      <details className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
        <summary className="cursor-pointer font-display text-sm font-extrabold">See all benefits, rewards and exclusions</summary>
        <div className="mt-4"><StructuredBenefits card={card} plain /></div>
      </details>

      <details className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
        <summary className="cursor-pointer font-display text-sm font-extrabold">Eligibility and documents to check</summary>
        <div className="mt-4"><EligibilityChecklist card={card} plain /></div>
      </details>

      <details className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
        <summary className="cursor-pointer font-display text-sm font-extrabold">Detailed analysis and alternatives</summary>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <EditorialList title="Who it suits" items={editorial.idealFor} />
          <EditorialList title="Key strengths" items={editorial.strengths} />
        </div>
        <div className="mt-4"><EditorialList title="Trade-offs to understand" items={editorial.tradeoffs} /></div>
        {editorial.alternatives.length > 0 && <div className="mt-4"><div className="text-xs font-bold">Compare before deciding</div><div className="mt-2 space-y-2">{editorial.alternatives.map((alternative) => <a key={alternative.id} href={`${process.env.PUBLIC_URL}/#/cards/${encodeURIComponent(alternative.id)}`} className="block rounded-xl border p-3" style={{ borderColor: "var(--ciq-line)" }}><div className="text-sm font-bold" style={{ color: "var(--ciq-teal)" }}>{alternative.name}</div><div className="mt-1 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>{alternative.reason}</div></a>)}</div></div>}
        <p className="mt-4 border-t pt-3 text-[11px] leading-relaxed" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink-soft)" }}>CardIQ editorial analysis is maintained separately from commercial links. Verify current terms before applying.</p>
      </details>

      <SharePanel card={card} />

      <div className="rounded-xl border p-3 text-xs leading-relaxed" style={{ borderColor: "var(--ciq-line)", background: "#f7f8f6", color: "var(--ciq-ink-soft)" }}>
        <div className="flex items-center gap-1.5 font-bold" style={{ color: "var(--ciq-ink)" }}><ShieldCheck className="h-4 w-4" /> Checked against issuer information</div>
        <p className="mt-1.5">Last checked {card.verifiedOn || "date not recorded"}. {card.availabilityNote || "Availability and approval are decided by the issuer."}</p>
        {card.termsNote && <p className="mt-1.5">Worth knowing: {card.termsNote}</p>}
        {(card.sourceUrls || []).length > 0 && (
          <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
            {card.sourceUrls.map((url, index) => <a key={url} href={url} target="_blank" rel="noopener noreferrer" className="font-semibold underline" style={{ color: "var(--ciq-teal)" }}>Official source {index + 1}</a>)}
          </div>
        )}
      </div>
    </div>
  );
}

function DecisionPoint({ title, text }) {
  if (!text) return null;
  return <div className="rounded-xl border bg-white/80 p-3" style={{ borderColor: "var(--ciq-line)" }}><div className="text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--ciq-teal)" }}>{title}</div><div className="mt-1 text-xs font-semibold leading-relaxed" style={{ color: "var(--ciq-ink)" }}>{text}</div></div>;
}

function EditorialList({ title, items }) {
  return <div><div className="text-xs font-bold" style={{ color: "var(--ciq-ink)" }}>{title}</div><ul className="mt-2 list-disc space-y-1.5 pl-5 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>{items.map((item) => <li key={item}>{item}</li>)}</ul></div>;
}

function StructuredBenefits({ card, plain = false }) {
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
  return <div className={plain ? "" : "rounded-2xl border bg-white p-4"} style={plain ? undefined : { borderColor: "var(--ciq-line)" }}>
    <div className="font-display text-sm font-bold">Complete benefit details</div>
    {facts.map(([label, value]) => <div key={label} className="mt-3 border-t pt-3 text-sm" style={{ borderColor: "var(--ciq-line)" }}><div className="text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>{label}</div><div className="mt-1 leading-relaxed">{value}</div></div>)}
    {sections.map(([label, items]) => <div key={label} className="mt-3 border-t pt-3" style={{ borderColor: "var(--ciq-line)" }}><div className="text-xs font-bold">{label}</div><ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{items.map((item) => <li key={item}>{item}</li>)}</ul></div>)}
  </div>;
}

function creditLabel(value) {
  return ({ good: "Good credit profile", excellent: "Excellent credit profile", fair: "Fair credit profile", starter: "Starter / building credit" })[value] || "Issuer eligibility applies";
}

function EligibilityChecklist({ card, plain = false }) {
  const checks = [
    card.eligibilityNote || null,
    card.secured ? "A fixed deposit or other issuer-approved security may be required." : `The issuer may assess the ${creditLabel(card.creditReq).toLowerCase()} indicated for this product.`,
    card.availabilityNote || "Confirm that applications are open for your city and customer profile.",
    "Check the issuer’s current income, age, residency and documentation requirements before applying.",
  ].filter(Boolean);
  return <section className={plain ? "" : "rounded-2xl border bg-white p-4"} style={plain ? undefined : { borderColor: "var(--ciq-line)" }}><div className="text-[10px] font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>Eligibility checklist</div><h3 className="mt-1 font-display text-base font-extrabold">Check access before you apply</h3><ul className="mt-3 space-y-2">{checks.map((item) => <li key={item} className="flex items-start gap-2 text-sm leading-relaxed"><Check className="mt-0.5 h-4 w-4 flex-shrink-0" style={{ color: "var(--ciq-teal-600)" }} /><span>{item}</span></li>)}</ul><p className="mt-3 text-[11px] leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>This is a practical pre-application check, not an approval prediction. The issuing bank makes the final decision.</p></section>;
}
