import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import CONTENT from "../data/footerContent.json";
import "./CustomerFooter.css";
import { getSiteContent } from "../api";


export default function CustomerFooter() {
  const { pathname, search } = useLocation();
  const [groups, setGroups] = useState(CONTENT.groups);
  useEffect(() => {
    let active = true;
    getSiteContent().then((data) => {
      if (!active || !Array.isArray(data?.footer_groups)) return;
      setGroups(data.footer_groups);
    }).catch(() => {});
    return () => { active = false; };
  }, []);
  if (pathname.startsWith("/admin") || new URLSearchParams(search).get("embedded") === "1") return null;

  return (
    <>
    <section className="editorial-transparency" aria-label="Editorial and financial transparency"><h2>{CONTENT.transparency.heading}</h2><p>{CONTENT.transparency.body}</p></section>
    <footer className="customer-footer" aria-label="Site footer">
      <div className="customer-footer-inner">
        <div className="customer-footer-grid">
          <div className="customer-footer-about">
            <Link to="/" className="customer-footer-brand" aria-label="CardIQ home"><span className="customer-footer-mark" aria-hidden="true"><span /></span><span>card<span className="customer-footer-iq">IQ</span></span></Link>
            <p>{CONTENT.description}</p>
          </div>
          {groups.map((group, index) => (
            <section key={group.title} aria-labelledby={`footer-group-${index}`}>
              <h2 id={`footer-group-${index}`}>{group.title}</h2>
              <ul>{group.links.map(({ label, url: storedUrl }) => <li key={`${label}-${storedUrl}`}>
                {localSpaRoute(footerRoute(storedUrl)) ? <Link to={localSpaRoute(footerRoute(storedUrl))}>{label}</Link> : isSpaDestination(footerRoute(storedUrl)) ? <Link to={footerRoute(storedUrl)}>{label}</Link> : <a href={publicDestination(footerRoute(storedUrl))}>{label}</a>}
              </li>)}</ul>
            </section>
          ))}
        </div>
        <div className="customer-footer-notice">© {new Date().getFullYear()} CardIQ. {CONTENT.notice}</div>
        <div className="footer-contact-note"><p>Found an outdated fee or reward cap? For editorial feedback, corrections, or affiliate network correspondence, reach out to our editorial team at <a href="mailto:hi@findmybest.cards">hi@findmybest.cards</a>.</p></div>
      </div>
    </footer>
    </>
  );
}

function isSpaDestination(url) {
  return url === "/reward-calculator" || [ "/wallet-optimizer", "/alerts", "/help/issuers", "/cards", "/calculator", "/updates", "/restricted-cards"].some((path) => url.startsWith(path));
}

function localSpaRoute(url) {
  if (process.env.NODE_ENV !== "development") return null;
  if (url === "/compare/") return "/cards?mode=compare";
  if (url === "/catalog/") return "/cards";
  if (url === "/calculator/") return "/calculator";
  if (url === "/reward-calculator/") return "/reward-calculator";
  if (url === "/lounges/") return "/cards?category=travel";
  if (url === "/guides/" || url.startsWith("/guides/new-credit-cards/")) return "/updates";
  if (url.startsWith("/guides/invite-only-credit-cards/")) return "/restricted-cards";
  if (url.startsWith("/guides/how-to-close-a-credit-card/")) return "/help/issuers";
  return null;
}

function publicDestination(url) {
  if (/^https:\/\//.test(url)) return url;
  const publicUrl = process.env.PUBLIC_URL || "";
  if (publicUrl && (url === publicUrl || url.startsWith(`${publicUrl}/`))) return url;
  return `${publicUrl}${url}`;
}

function footerRoute(url) {
  return ({"/": "/", "/cards": "/catalog/", "/cards?mode=compare": "/compare/", "/calculator": "/calculator/", "/reward-calculator": "/reward-calculator/", "/updates": "/guides/new-credit-cards/", "/restricted-cards": "/guides/invite-only-credit-cards/"})[url] || url;
}
