import React from "react";
import { ArrowUpRight, Newspaper } from "lucide-react";
import { formatCustomerDate } from "../formatDate";
import "./HomeHighlights.css";

export default function LatestNews({ items = [] }) {
  const news = items
    .filter((item) => item.active && ["upcoming", "announcement"].includes(item.status))
    .sort((a, b) => (b.verifiedOn || "").localeCompare(a.verifiedOn || ""))
    .slice(0, 1);
  if (!news.length) return null;

  return <section aria-labelledby="latest-card-news-title" className="ciq-highlight-panel ciq-news-panel">
    <header className="ciq-highlight-header ciq-news-header">
      <span className="ciq-highlight-icon"><Newspaper className="h-5 w-5" /></span>
      <div><h2 id="latest-card-news-title" className="font-display">News &amp; rule updates</h2><p>Issuer changes that may affect your card.</p></div>
      <a href="/guides/news/" className="ciq-highlight-updates">All updates →</a>
    </header>
    <div className="ciq-highlight-list">
      {news.map((item) => <article key={item.id} className="ciq-highlight-article ciq-news-article">
        <div className="ciq-highlight-meta"><span className="ciq-highlight-badge">{item.statusLabel}</span><span>{item.issuer}</span></div>
        <h3 className="font-display"><a href={item.sourceUrl} target="_blank" rel="noopener noreferrer">{item.headline || item.cardName}</a></h3>
        <p className="ciq-highlight-summary">{item.summary}</p>
        <div className="ciq-highlight-footer">
          <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" className="ciq-highlight-action">Official source <ArrowUpRight className="h-3.5 w-3.5" /></a>
          <span className="ciq-highlight-date">Checked <time dateTime={item.verifiedOn}>{formatCustomerDate(item.verifiedOn)}</time></span>
        </div>
      </article>)}
    </div>
  </section>;
}
