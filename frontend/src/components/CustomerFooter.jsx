import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import Logo from "./Logo";
import { getSiteContent } from "../api";

const GROUPS = [
  {
    title: "Discover cards",
    links: [
      ["Browse all cards", "/cards"],
      ["Card comparisons", "/cards?mode=compare"],
      ["New and updated cards", "/updates"],
      ["Invite-only cards", "/restricted-cards"],
    ],
  },
  {
    title: "Tools",
    links: [
      ["Find my best card", "/"],
      ["Annual value calculator", "/calculator"],
      ["Which card should I use?", "/wallet-optimizer"],
      ["Card change alerts", "/alerts"],
    ],
  },
  {
    title: "Help & research",
    links: [
      ["Reviews and editorials", `${process.env.PUBLIC_URL}/guides/`, "external"],
      ["Issuer contacts", "/help/issuers"],
      ["How to close a card", "/help/issuers"],
      ["Credit card guides", `${process.env.PUBLIC_URL}/guides/`, "external"],
    ],
  },
  {
    title: "About CardIQ",
    links: [
      ["How recommendations work", `${process.env.PUBLIC_URL}/methodology/`, "external"],
      ["How CardIQ makes money", `${process.env.PUBLIC_URL}/methodology/`, "external"],
      ["Card catalogue", `${process.env.PUBLIC_URL}/catalog/`, "external"],
    ],
  },
];

export default function CustomerFooter() {
  const { pathname, search } = useLocation();
  const [groups, setGroups] = useState(GROUPS);
  useEffect(() => {
    let active = true;
    getSiteContent().then((data) => {
      if (!active || !Array.isArray(data?.footer_groups)) return;
      setGroups(data.footer_groups.map((group) => ({ title: group.title, links: group.links.map((link) => [link.label, link.url]) })));
    }).catch(() => {});
    return () => { active = false; };
  }, []);
  if (pathname.startsWith("/admin") || pathname.startsWith("/review/") || new URLSearchParams(search).get("embedded") === "1") return null;

  return (
    <footer className="border-t bg-white" style={{ borderColor: "var(--ciq-line)" }}>
      <div className="ciq-container ciq-container--wide py-10">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-[1.2fr_repeat(4,1fr)]">
          <div>
            <Logo size="md" />
            <p className="mt-3 max-w-xs text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>Clear credit-card information for India, including fees, benefits, trade-offs, comparisons and official issuer sources.</p>
          </div>
          {groups.map((group) => (
            <section key={group.title} aria-labelledby={`footer-${group.title.replace(/\W+/g, "-").toLowerCase()}`}>
              <h2 id={`footer-${group.title.replace(/\W+/g, "-").toLowerCase()}`} className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ciq-ink)" }}>{group.title}</h2>
              <ul className="mt-3 space-y-2.5">
                {group.links.map(([label, destination, kind]) => (
                  <li key={`${label}-${destination}`}>
                    {kind === "external" || !isSpaDestination(destination)
                      ? <a href={publicDestination(destination)} className="text-xs hover:underline" style={{ color: "var(--ciq-ink-soft)" }}>{label}</a>
                      : <Link to={destination} className="text-xs hover:underline" style={{ color: "var(--ciq-ink-soft)" }}>{label}</Link>}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
        <div className="mt-8 border-t pt-5 text-[11px] leading-relaxed" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink-soft)" }}>
          © {new Date().getFullYear()} CardIQ. Card names, images and trademarks belong to their respective owners. Always verify current fees, eligibility and benefits on the issuer’s website before applying.
        </div>
      </div>
    </footer>
  );
}

function isSpaDestination(url) {
  return url === "/" || ["/cards", "/updates", "/restricted-cards", "/calculator", "/wallet-optimizer", "/alerts", "/help/issuers"].some((path) => url.startsWith(path));
}

function publicDestination(url) {
  if (/^https:\/\//.test(url)) return url;
  const publicUrl = process.env.PUBLIC_URL || "";
  if (publicUrl && (url === publicUrl || url.startsWith(`${publicUrl}/`))) return url;
  return `${publicUrl}${url}`;
}
