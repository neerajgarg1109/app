import React from "react";
import { ArrowRight, BadgeIndianRupee, BellRing, ExternalLink, Newspaper, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { trackApplyClick } from "../api";
import { recordProductEvent } from "../productAnalytics";
import { formatCustomerDate } from "../formatDate";
import "./HomeHighlights.css";

export default function FeaturedCards({ cards = [], updates = [], placements = null, news = [] }) {
  const byId = new Map(cards.map((card) => [card.id, card]));
  const activeCards = cards.filter((card) => card.active !== false);
  const partnerCard = (placements || []).filter((item) => item.active && item.placement_type === "partner")
    .map((item) => byId.get(item.card_id)).find((card) => card && card.active !== false && card.applicationsOpen !== false)
    || activeCards.find((card) => card.applicationLinkType === "partner" && card.applicationsOpen !== false);
  const promotedCard = partnerCard || activeCards.find((card) => card.id === "sbi-cashback-sbi");
  const liveLaunch = activeCards.find((card) => card.id === "hdfc-swiggy-ornge-hdfc-bank-credit-card" && card.applicationsOpen !== false)
    || updates.filter((item) => item.change_type === "launch").map((item) => byId.get(item.card_id)).find((card) => card && card.applicationsOpen !== false);
  const activeNews = news.filter((item) => item.active && ["announcement", "upcoming"].includes(item.status));
  const announcement = activeNews.find((item) => item.status === "announcement");
  const ruleUpdate = activeNews.find((item) => item.id.includes("sbi")) || activeNews.find((item) => item.status === "upcoming");
  const trackApplication = (card) => {
    Promise.resolve(trackApplyClick(card.id, null)).catch(() => {});
    recordProductEvent("apply_clicked");
  };
  const cardSummary = (card) => card.editorial?.summary || card.rewardLine || "Review the card’s current fees, benefits and eligibility.";
  const liveLaunchLabel = liveLaunch?.homepagePlacement?.label || "Live launch";
  const liveLaunchSummary = liveLaunch?.homepagePlacement?.summary || (liveLaunch ? cardSummary(liveLaunch) : "");
  const renderNews = (item, label, variant) => item ? <article className="ciq-highlight-article">
    <div className="ciq-highlight-meta"><span className={`ciq-highlight-badge ciq-highlight-badge--${variant}`}>{label}</span><span>{item.issuer}</span></div>
    <h3 className="font-display">{item.headline || item.cardName}</h3>
    <p className="ciq-highlight-summary">{item.summary}</p>
    <p className="ciq-highlight-note">{item.availabilityNote}</p>
    <div className="ciq-highlight-footer"><a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" className="ciq-highlight-action">Read issuer source <ArrowRight className="h-3.5 w-3.5" /></a><span className="ciq-highlight-date">Checked <time dateTime={item.verifiedOn}>{formatCustomerDate(item.verifiedOn)}</time></span></div>
  </article> : <article className="ciq-highlight-article"><p className="ciq-highlight-summary">No active update to feature today.</p><a href="/guides/news/" className="ciq-highlight-secondary">Browse the archive <ArrowRight className="h-3 w-3" /></a></article>;

  if (!promotedCard && !liveLaunch && !announcement && !ruleUpdate) return null;
  return <section className="ciq-home-highlights" aria-labelledby="ciq-home-highlights-title">
    <div className="ciq-container ciq-container--wide">
      <header className="ciq-highlights-heading"><div><p className="ciq-highlights-eyebrow">THE CARDIQ DESK</p><h2 id="ciq-home-highlights-title">Cards &amp; updates</h2><p>New cards, useful highlights and issuer changes worth knowing.</p></div></header>
      <div className="ciq-highlights-grid ciq-highlights-grid--four">
        <section className="ciq-highlight-panel" aria-labelledby="ciq-highlight-promoted">
          <header className="ciq-highlight-header"><span className="ciq-highlight-icon"><BadgeIndianRupee className="h-5 w-5" /></span><div><h2 id="ciq-highlight-promoted">Featured card</h2><p>{partnerCard ? "Partner placement" : "Editor’s pick"}</p></div></header>
          {promotedCard ? <article className="ciq-highlight-article"><div className="ciq-highlight-meta"><span className={`ciq-highlight-badge ${partnerCard ? "ciq-highlight-badge--launch" : ""}`}>{partnerCard ? "Promoted" : "Cashback"}</span><span>{promotedCard.issuer}</span></div><h3 className="font-display">{promotedCard.name}</h3><p className="ciq-highlight-summary">{cardSummary(promotedCard)}</p><div className="ciq-highlight-footer">{promotedCard.applyUrl && promotedCard.active !== false && promotedCard.applicationsOpen !== false && <a href={promotedCard.applyUrl} target="_blank" rel="noopener noreferrer" onClick={() => trackApplication(promotedCard)} className="ciq-highlight-action">Apply now <ExternalLink className="h-3.5 w-3.5" /></a>}<Link to={`/cards/${encodeURIComponent(promotedCard.id)}`} className="ciq-highlight-secondary">View card <ArrowRight className="h-3 w-3" /></Link></div>{partnerCard && <p className="ciq-highlight-note">Promoted placement. CardIQ may earn a commission; this does not affect recommendations or editorial conclusions.</p>}</article> : <article className="ciq-highlight-article"><p className="ciq-highlight-summary">Browse cards and compare issuer-sourced fees, rewards and benefits.</p><Link to="/cards" className="ciq-highlight-action">Browse cards <ArrowRight className="h-3.5 w-3.5" /></Link></article>}
        </section>
        <section className="ciq-highlight-panel" aria-labelledby="ciq-highlight-launch"><header className="ciq-highlight-header"><span className="ciq-highlight-icon"><Sparkles className="h-5 w-5" /></span><div><h2 id="ciq-highlight-launch">Latest live launch</h2><p>Open for public applications</p></div></header>
          {liveLaunch ? <article className="ciq-highlight-article"><div className="ciq-highlight-meta"><span className="ciq-highlight-badge ciq-highlight-badge--launch">{liveLaunchLabel}</span><span>{liveLaunch.issuer}</span></div><h3 className="font-display">{liveLaunch.name}</h3><p className="ciq-highlight-summary">{liveLaunchSummary}</p><div className="ciq-highlight-footer"><Link to={`/cards/${encodeURIComponent(liveLaunch.id)}`} className="ciq-highlight-action">View details <ArrowRight className="h-3.5 w-3.5" /></Link>{liveLaunch.applyUrl && <a href={liveLaunch.applyUrl} target="_blank" rel="noopener noreferrer" onClick={() => trackApplication(liveLaunch)} className="ciq-highlight-secondary">Apply now <ExternalLink className="h-3 w-3" /></a>}</div></article> : <article className="ciq-highlight-article"><p className="ciq-highlight-summary">No recently verified public launch is featured today.</p><a href="/guides/news/" className="ciq-highlight-action">Browse card news <ArrowRight className="h-3.5 w-3.5" /></a></article>}
        </section>
        <section className="ciq-highlight-panel" aria-labelledby="ciq-highlight-announced"><header className="ciq-highlight-header"><span className="ciq-highlight-icon"><Newspaper className="h-5 w-5" /></span><div><h2 id="ciq-highlight-announced">Announced / upcoming</h2><p>Announcements are not necessarily open to apply.</p></div></header>{renderNews(announcement, "Announced", "announcement")}</section>
        <section className="ciq-highlight-panel" aria-labelledby="ciq-highlight-rules"><header className="ciq-highlight-header"><span className="ciq-highlight-icon"><BellRing className="h-5 w-5" /></span><div><h2 id="ciq-highlight-rules">Existing card updates</h2><p>Fees, rewards and benefit changes.</p></div></header>{renderNews(ruleUpdate, "Rule update", "rule")}</section>
      </div>
      <div className="ciq-highlights-more"><span>More issuer notices, earlier changes and archived updates.</span><a href="/guides/news/">Show more updates &amp; archives <ArrowRight className="h-4 w-4" /></a></div>
      <p className="ciq-news-editorial">CardIQ editorial desk · <a href="mailto:hi@findmybest.cards">hi@findmybest.cards</a> for corrections. Confirm current terms with the issuer.</p>
    </div>
  </section>;
}

