#!/usr/bin/env python3
"""Generate crawlable GitHub Pages entry documents for public catalog routes."""
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "frontend" / "build"
CARDS = json.loads((ROOT / "backend" / "cards_catalog.json").read_text())
CATEGORIES = json.loads((ROOT / "frontend" / "src" / "data" / "cardCategories.json").read_text())
ORIGIN = "https://neerajgarg1109.github.io/app"


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def page(title, description, canonical, destination, body):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(description, quote=True)}">
<link rel="canonical" href="{html.escape(canonical, quote=True)}">
<meta property="og:title" content="{html.escape(title, quote=True)}"><meta property="og:description" content="{html.escape(description, quote=True)}">
<style>body{{margin:0;background:#f8f7ff;color:#172033;font:16px/1.55 Inter,Arial,sans-serif}}header,main,footer{{max-width:960px;margin:auto;padding:24px}}header{{display:flex;justify-content:space-between;align-items:center}}a{{color:#4538c8}}.brand{{font-size:22px;font-weight:800;text-decoration:none}}h1{{font-size:38px;line-height:1.15}}.cta{{display:inline-block;background:#5b4ff0;color:white;text-decoration:none;padding:12px 18px;border-radius:12px;font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}.card{{background:white;border:1px solid #e4e2f1;border-radius:16px;padding:16px}}.muted{{color:#5d6478}}li{{margin:7px 0}}</style></head>
<body><header><a class="brand" href="{ORIGIN}/">cardIQ</a><a href="{ORIGIN}/#/cards">Browse all cards</a></header><main>{body}<p><a class="cta" href="{html.escape(destination, quote=True)}">Explore and compare in CardIQ</a></p></main><footer class="muted">Card facts are dated and linked to issuer sources. Eligibility and approval are decided by the issuing bank.</footer></body></html>'''


def write(relative, contents):
    target = BUILD / relative / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(contents)


def clean_generated_routes():
    """Remove stale generated routes while preserving CRA assets such as card images."""
    shutil.rmtree(BUILD / "categories", ignore_errors=True)
    shutil.rmtree(BUILD / "issuers", ignore_errors=True)
    cards_directory = BUILD / "cards"
    if cards_directory.exists():
        for child in cards_directory.iterdir():
            if child.is_dir():
                shutil.rmtree(child)


def category_match(card, definition):
    text = " ".join(str(value) for value in [card.get("name"), card.get("rewardLine"), card.get("feeType"), card.get("network"), *(card.get("bestFor") or []), *(card.get("highlights") or [])]).lower()
    checks = []
    if definition.get("keywords"):
        checks.append(any(keyword.lower() in text for keyword in definition["keywords"]))
    if "annualFeeMax" in definition:
        checks.append(card.get("annualFeeAmount", 0) <= definition["annualFeeMax"])
    if "annualFeeMin" in definition:
        checks.append(card.get("annualFeeAmount", 0) >= definition["annualFeeMin"])
    if definition.get("secured"):
        checks.append(card.get("secured") is True)
    if definition.get("creditReq"):
        checks.append(card.get("creditReq") == definition["creditReq"])
    if definition.get("coBranded"):
        checks.append(bool(card.get("coBrandPartner")) or "co-brand" in text or "co brand" in text)
    if definition.get("fintech"):
        checks.append(bool(card.get("coBrandPartner")) or any(term in text for term in ("fintech", "kredit", "salaryse", "zaggle", "onecard", "scapia", "super.money")))
    return any(checks)


def card_links(cards):
    return '<div class="grid">' + "".join(
        f'<article class="card"><h2><a href="{ORIGIN}/cards/{html.escape(card["id"])}/">{html.escape(card["name"])}</a></h2>'
        f'<p class="muted">{html.escape(card["issuer"])}</p><p>{html.escape(card.get("rewardLine", ""))}</p>'
        f'<p><strong>Annual fee:</strong> {html.escape(card.get("annualFee", "Not specified"))}</p></article>'
        for card in cards
    ) + "</div>"


clean_generated_routes()

for card in CARDS:
    name, issuer = card["name"], card["issuer"]
    description = f'{card.get("rewardLine", "")} Annual fee: {card.get("annualFee", "Not specified")}. Verified card details from CardIQ.'
    route = f'{ORIGIN}/#/cards/{quote(card["id"])}'
    facts = "".join(f"<li>{html.escape(item)}</li>" for item in card.get("highlights", []))
    sources = "".join(f'<li><a href="{html.escape(url, quote=True)}" rel="nofollow">Issuer source {index + 1}</a></li>' for index, url in enumerate(card.get("sourceUrls", [])))
    body = f'<h1>{html.escape(name)}</h1><p class="muted">{html.escape(issuer)} · Checked {html.escape(card.get("verifiedOn", "date unavailable"))}</p><p>{html.escape(description)}</p><h2>Benefits, limits and conditions</h2><ul>{facts}</ul><h2>Sources</h2><ul>{sources}</ul>'
    write(Path("cards") / card["id"], page(f"{name} — fees, rewards and benefits | CardIQ", description, f'{ORIGIN}/cards/{card["id"]}/', route, body))

issuers = sorted({card["issuer"] for card in CARDS})
for issuer in issuers:
    matches = [card for card in CARDS if card["issuer"] == issuer]
    count = len(matches)
    description = f"Compare {count} currently catalogued {issuer} credit cards, fees, rewards and verified benefits on CardIQ."
    destination = f'{ORIGIN}/#/cards?issuer={quote(issuer)}'
    body = f'<h1>{html.escape(issuer)} credit cards</h1><p>{html.escape(description)}</p>{card_links(matches)}'
    write(Path("issuers") / slug(issuer), page(f"{issuer} credit cards | CardIQ", description, f'{ORIGIN}/issuers/{slug(issuer)}/', destination, body))

published_categories = []
for category in CATEGORIES:
    matches = [card for card in CARDS if category_match(card, category)]
    if len(matches) < 3:
        continue
    published_categories.append(category)
    description = category["description"]
    destination = f'{ORIGIN}/#/cards?category={category["id"]}'
    body = f'<h1>{html.escape(category["label"])} credit cards in India</h1><p>{html.escape(description)}</p><p class="muted">{len(matches)} matching cards · Details checked against issuer or official partner sources.</p>{card_links(matches)}'
    write(Path("categories") / category["id"], page(f'{category["label"]} credit cards in India | CardIQ', description, f'{ORIGIN}/categories/{category["id"]}/', destination, body))

sitemap_urls = [f"{ORIGIN}/"]
sitemap_urls += [f'{ORIGIN}/cards/{card["id"]}/' for card in CARDS]
sitemap_urls += [f'{ORIGIN}/issuers/{slug(issuer)}/' for issuer in issuers]
sitemap_urls += [f'{ORIGIN}/categories/{category["id"]}/' for category in published_categories]
(BUILD / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in sitemap_urls) + "\n</urlset>\n")
(BUILD / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n")

print(f"Generated {len(CARDS)} card, {len(issuers)} issuer and {len(published_categories)} useful category pages")
