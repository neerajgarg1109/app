import React from "react";
import { ExternalLink, Newspaper } from "lucide-react";
import { formatCustomerDate } from "../formatDate";

export default function LatestNews({ items = [] }) {
  const news = items.filter((item) => item.active && ["upcoming", "announcement"].includes(item.status));
  if (!news.length) return null;

  return <section aria-labelledby="latest-card-news-title" className="min-w-0">
    <div className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ciq-teal)" }}>On the horizon</div>
    <h2 id="latest-card-news-title" className="mt-1 font-display text-2xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>Latest news</h2>
    <p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Upcoming cards and issuer announcements, with availability clearly marked.</p>
    <div className="mt-5 space-y-4">
      {news.map((item) => <article key={item.id} className="rounded-3xl border bg-white p-5" style={{ borderColor: "#d9d2f5" }}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider" style={{ background: "#f1edff", color: "#5142d8" }}><Newspaper className="h-3.5 w-3.5" />{item.statusLabel}</span>
          <span className="text-xs font-semibold" style={{ color: "var(--ciq-teal)" }}>{item.issuer}</span>
        </div>
        <h3 className="mt-4 font-display text-lg font-extrabold" style={{ color: "var(--ciq-ink)" }}>{item.headline}</h3>
        <p className="mt-1 text-xs font-semibold" style={{ color: "var(--ciq-teal)" }}>{item.cardName}</p>
        <p className="mt-3 text-sm leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>{item.summary}</p>
        <p className="mt-3 rounded-xl px-3 py-2 text-xs leading-relaxed" style={{ background: "#f7f6fb", color: "var(--ciq-ink-soft)" }}>{item.availabilityNote}</p>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" className="ciq-press inline-flex items-center gap-1.5 rounded-full border px-4 py-2 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>Read issuer announcement <ExternalLink className="h-4 w-4" /></a>
          <span className="text-[11px]" style={{ color: "var(--ciq-ink-soft)" }}>Checked <time dateTime={item.verifiedOn}>{formatCustomerDate(item.verifiedOn)}</time></span>
        </div>
      </article>)}
    </div>
  </section>;
}
