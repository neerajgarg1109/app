import React from "react";
import { Link } from "react-router-dom";

const NAV_ITEMS = [
  { label: "Home", to: "/" },
  { label: "Browse cards", to: "/cards" },
  { label: "Card comparisons", to: "/cards?mode=compare" },
  { label: "Reviews & editorials", href: `${process.env.PUBLIC_URL}/guides/` },
  { label: "Value calculator", to: "/calculator" },
  { label: "New & updated", to: "/updates" },
  { label: "Invite-only cards", to: "/restricted-cards" },
  { label: "Close a card", to: "/help/issuers" },
];

export default function CustomerNav() {
  const location = currentHashLocation();
  return (
    <nav className="ciq-container ciq-container--wide" aria-label="Main navigation">
      <div className="grid grid-cols-2 gap-2 pb-2 sm:flex sm:flex-wrap">
        {NAV_ITEMS.map((item) => {
          const active = item.to ? isActive(item.to, location.pathname, location.search) : false;
          const className = "ciq-press rounded-xl border bg-white px-3 py-2 text-center text-xs font-semibold sm:rounded-full sm:text-sm";
          const style = {
            borderColor: active ? "var(--ciq-teal-600)" : "var(--ciq-line)",
            background: active ? "#f2faf7" : "#fff",
            color: active ? "var(--ciq-teal)" : "var(--ciq-ink)",
          };
          if (item.href) return <a key={item.label} href={item.href} className={className} style={style}>{item.label}</a>;
          return <Link key={item.label} to={item.to} aria-current={active ? "page" : undefined} className={className} style={style}>{item.label}</Link>;
        })}
      </div>
    </nav>
  );
}

function currentHashLocation() {
  const raw = typeof window === "undefined" ? "/" : (window.location.hash.replace(/^#/, "") || "/");
  const [pathname, query = ""] = raw.split("?");
  return { pathname, search: query ? `?${query}` : "" };
}

function isActive(destination, pathname, search) {
  const [path, query = ""] = destination.split("?");
  if (path === "/cards" && pathname.startsWith("/cards/")) return !query;
  if (pathname !== path) return false;
  return query ? search === `?${query}` : !(path === "/cards" && search.includes("mode=compare"));
}
