import React from "react";
import { Link } from "react-router-dom";

const NAV_ITEMS = [
  { label: "Browse cards", to: "/cards" },
  { label: "Card comparisons", to: "/cards?mode=compare" },
  { label: "Reviews & editorials", href: `${process.env.PUBLIC_URL}/guides/` },
  { label: "Value calculator", to: "/calculator" },
  { label: "New & updated", to: "/updates" },
  { label: "Invite-only cards", to: "/restricted-cards" },
  { label: "Close a card", to: "/help/issuers", important: true },
];

export default function CustomerNav() {
  return (
    <nav className="ciq-container ciq-container--wide" aria-label="Explore CardIQ">
      <div className="mb-2 text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ciq-ink-soft)" }}>Explore CardIQ</div>
      <div className="grid grid-cols-2 gap-2 pb-2 sm:flex sm:flex-wrap">
        {NAV_ITEMS.map((item) => {
          const className = "ciq-press rounded-xl border bg-white px-3 py-2 text-center text-xs font-semibold sm:rounded-full sm:text-sm";
          const style = {
            borderColor: item.important ? "var(--ciq-teal-600)" : "var(--ciq-line)",
            color: item.important ? "var(--ciq-teal)" : "var(--ciq-ink)",
          };
          if (item.href) return <a key={item.label} href={item.href} className={className} style={style}>{item.label}</a>;
          return <Link key={item.label} to={item.to} className={className} style={style}>{item.label}</Link>;
        })}
      </div>
    </nav>
  );
}
