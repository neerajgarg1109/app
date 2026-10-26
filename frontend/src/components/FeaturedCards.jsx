import React from "react";
import { ArrowRight, BadgeIndianRupee, ExternalLink, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import CreditCardVisual from "./CreditCardVisual";
import { trackApplyClick } from "../api";
import { recordProductEvent } from "../productAnalytics";
import LatestNews from "./LatestNews";
import { formatCustomerDate } from "../formatDate";
import "./HomeHighlights.css";

export default function FeaturedCards({ cards = [], updates = [], placements = null, news = [] }) {
  const byId = new Map(cards.map((card) => [card.id, card]));
  const configured = Array.isArray(placements)
    ? placements.filter((item) => item.active).map((item) => {
        const card = byId.get(item.card_id);
        return card && { card, placement: { type: item.placement_type, label: item.label, summary: item.summary } };
      }).filter(Boolean)
    : cards.filter((card) => card.homepagePlacement?.active && card.active !== false && card.applicationsOpen !== false)
        .sort((a, b) => Number(b.homepagePlacement.priority || 0) - Number(a.homepagePlacement.priority || 0))
        .map((card) => ({ card, placement: card.homepagePlacement }));
  const partnerCard = cards.find((card) => card.applicationLinkType === "partner" && card.active !== false && card.applicationsOpen !== false);
  const launch = updates.find((item) => item.change_type === "launch" && byId.has(item.card_id));
  const launchCard = launch ? byId.get(launch.card_id) : null;
  const features = [];
  configured.forEach(({ card, placement }) => features.push({
    card,
    label: placement.label || (placement.type === "partner" ? "Partner feature" : "New launch"),
    commercial: placement.type === "partner",
    summary: placement.summary || card.editorial?.summary || card.rewardLine,
  }));
  if (partnerCard && !features.some((item) => item.card.id === partnerCard.id)) features.push({ card: partnerCard, label: "Partner feature", commercial: true, summary: partnerCard.editorial?.summary || partnerCard.rewardLine });
  if (launchCard && !features.some((item) => item.card.id === launchCard.id)) features.push({ card: launchCard, label: "New launch", commercial: false, summary: launch.summary || launchCard.editorial?.summary || launchCard.rewardLine });
  const hasNews = news.some((item) => item.active && ["upcoming", "announcement"].includes(item.status));
  if (!features.length && !hasNews) return null;
  const launches = features.filter((item) => !item.commercial).slice(0, 2);
  const promotions = features.filter((item) => item.commercial).slice(0, 2);

  return (
    <div className="ciq-home-highlights">
      {(launches.length > 0 || hasNews) && <div className={`ciq-container ciq-container--wide ciq-highlights-grid ${launches.length > 0 && hasNews ? "ciq-highlights-grid--paired" : ""}`}>
      {launches.length > 0 && <FeatureSection
        id="new-card-launches"
        eyebrow="Newly launched"
        title="New launches"
        description="Recently released cards, at a glance."
        features={launches}
        updatesLink
        embedded
      />}
      {hasNews && <LatestNews items={news} />}
      </div>}
      {promotions.length > 0 && <FeatureSection
        id="promoted-cards"
        eyebrow="Promoted cards"
        title="Offers from CardIQ partners"
        description="Clearly labelled paid placements from issuers or partners working with CardIQ. Promotion never changes match scores, ratings or editorial conclusions."
        features={promotions}
      />}
    </div>
  );
}

function FeatureSection({ id, eyebrow, title, description, features, updatesLink = false, embedded = false }) {
  const trackApplication = (card) => {
    Promise.resolve(trackApplyClick(card.id, null)).catch(() => {});
    recordProductEvent("apply_clicked");
  };
  if (embedded) return <section className="ciq-highlight-panel" aria-labelledby={`${id}-title`}>
    <header className="ciq-highlight-header">
      <span className="ciq-highlight-icon"><Sparkles className="h-5 w-5" /></span>
      <div><h2 id={`${id}-title`} className="font-display">{title}</h2><p>{description}</p></div>
      {updatesLink && <Link to="/updates" aria-label="See all card updates" className="ciq-highlight-updates">All updates →</Link>}
    </header>
    <div className="ciq-highlight-list">{features.map(({ card, label, summary }) => <article key={card.id} className="ciq-highlight-article">
      <div className="ciq-highlight-meta"><span className="ciq-highlight-badge">{label}</span><span>{card.issuer}</span></div>
      <h3 className="font-display">{card.name}</h3>
      <p className="ciq-highlight-summary">{summary}</p>
      <div className="ciq-highlight-footer">
        <Link to={`/cards/${encodeURIComponent(card.id)}`} className="ciq-press ciq-highlight-action">View details <ArrowRight className="h-3.5 w-3.5" /></Link>
        {card.applyUrl && card.active !== false && card.applicationsOpen !== false && <a href={card.applyUrl} target="_blank" rel="noopener noreferrer" onClick={() => trackApplication(card)} className="ciq-highlight-secondary">Apply now <ExternalLink className="h-3 w-3" /></a>}
        {card.verifiedOn && <span className="ciq-highlight-date">Checked <time dateTime={card.verifiedOn}>{formatCustomerDate(card.verifiedOn)}</time></span>}
      </div>
    </article>)}</div>
  </section>;
  return <section className={embedded ? "min-w-0" : "ciq-container ciq-container--wide mt-12"} aria-labelledby={`${id}-title`}>
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <div className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>{eyebrow}</div>
        <h2 id={`${id}-title`} className="mt-1 font-display text-2xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>{title}</h2>
        <p className="mt-1 max-w-2xl text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{description}</p>
      </div>
      {updatesLink && !embedded && <Link to="/updates" className="text-sm font-semibold underline" style={{ color: "var(--ciq-teal)" }}>See all card updates</Link>}
    </div>
    <div className={`mt-5 grid gap-4 ${embedded ? "" : "lg:grid-cols-2"}`}>
        {features.map(({ card, label, commercial, summary }) => (
          <article key={`${label}-${card.id}`} className="rounded-3xl border bg-white p-5" style={{ borderColor: commercial ? "#c9c1ff" : "#b9e4da" }}>
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider" style={{ color: commercial ? "#5142d8" : "var(--ciq-teal)" }}>
              {commercial ? <BadgeIndianRupee className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />} {label}
            </div>
            <div className="mt-4 grid items-center gap-4 sm:grid-cols-[150px_1fr]">
              <CreditCardVisual card={card} size="sm" />
              <div>
                <h3 className="font-display text-lg font-extrabold" style={{ color: "var(--ciq-ink)" }}>{card.name}</h3>
                <p className="mt-0.5 text-xs font-semibold" style={{ color: "var(--ciq-teal)" }}>{card.issuer}</p>
                <p className="mt-2 text-sm leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>{summary}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {card.applyUrl && card.active !== false && card.applicationsOpen !== false && <a href={card.applyUrl} target="_blank" rel="noopener noreferrer" onClick={() => trackApplication(card)} className="ciq-press inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold text-white" style={{ background: "var(--ciq-teal-600)" }}>Apply now <ExternalLink className="h-4 w-4" /></a>}
                  <Link to={`/cards/${encodeURIComponent(card.id)}`} className="ciq-press inline-flex items-center gap-1.5 rounded-full border px-4 py-2 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>View details <ArrowRight className="h-4 w-4" /></Link>
                </div>
              </div>
            </div>
            {commercial && <p className="mt-4 border-t pt-3 text-[11px] leading-relaxed" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink-soft)" }}>Promoted placement. CardIQ may earn a commission if you apply. This placement does not affect recommendations, ratings or editorial conclusions.</p>}
          </article>
        ))}
      </div>
      {updatesLink && embedded && <Link to="/updates" className="mt-4 inline-block text-sm font-semibold underline" style={{ color: "var(--ciq-teal)" }}>See all card updates</Link>}
    </section>;
}
