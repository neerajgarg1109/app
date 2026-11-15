import React from "react";
import { ArrowUpRight, Newspaper } from "lucide-react";
import { formatCustomerDate } from "../formatDate";
import "./HomeHighlights.css";

export default function LatestNews({ items = [] }) {
  const news = items.filter((item) => item.active && ["upcoming", "announcement"].includes(item.status));
  if (!news.length) return null;

  return <section aria-labelledby="latest-card-news-title" className="ciq-highlight-panel">
    <header className="ciq-highlight-header">
      <span className="ciq-highlight-icon"><Newspaper className="h-5 w-5" /></span>
      <div><h2 id="latest-card-news-title" className="font-display">News &amp; rule updates</h2><p>Issuer changes that may affect your card.</p></div>
    </header>
    <div className="ciq-highlight-list">
      {news.map((item) => <article key={item.id} className="ciq-highlight-article">
        <div className="ciq-highlight-meta"><span className="ciq-highlight-badge">{item.statusLabel}</span><span>{item.issuer}</span></div>
        <h3 className="font-display">{item.headline || item.cardName}</h3>
        <p className="ciq-highlight-summary">{item.summary}</p>
        <p className="ciq-highlight-note">{item.availabilityNote}</p>
        <div className="ciq-highlight-footer">
          <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" className="ciq-press ciq-highlight-action">Read official source <ArrowUpRight className="h-3.5 w-3.5" /></a>
          <span className="ciq-highlight-date">Checked <time dateTime={item.verifiedOn}>{formatCustomerDate(item.verifiedOn)}</time></span>
        </div>
      </article>)}
    </div>
    <p className="ciq-news-editorial">CardIQ editorial desk · <a href="mailto:hi@findmybest.cards">hi@findmybest.cards</a> for corrections. Always confirm current terms with the issuer.</p>
  </section>;
}
