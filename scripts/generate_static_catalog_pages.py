#!/usr/bin/env python3
"""Generate crawlable GitHub Pages entry documents for public catalog routes."""
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "frontend" / "build"
CATEGORIES = json.loads((ROOT / "frontend" / "src" / "data" / "cardCategories.json").read_text())
DEFAULT_ORIGIN = json.loads((ROOT / "frontend" / "package.json").read_text())["homepage"]
ORIGIN = os.environ.get("CARDIQ_PUBLIC_ORIGIN", DEFAULT_ORIGIN).rstrip("/")


def load_cards():
    catalog_url = os.environ.get("CARDIQ_CATALOG_API_URL")
    if catalog_url:
        try:
            with urlopen(catalog_url, timeout=30) as response:
                cards = json.load(response)
            if not isinstance(cards, list) or not cards:
                raise RuntimeError("The configured CardIQ catalog API returned no cards")
            return cards, catalog_url
        except Exception as error:
            print(f"Live catalog unavailable ({error}); using the repository fallback.", file=sys.stderr)
    path = ROOT / "backend" / "cards_catalog.json"
    return json.loads(path.read_text()), str(path.relative_to(ROOT))


CARDS, CATALOG_SOURCE = load_cards()


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def social_links(title, canonical):
    text = quote(f"{title} — CardIQ", safe="")
    url = quote(canonical, safe="")
    return f'''<section class="share"><h2>Share this page</h2><p>Send these sourced details to someone comparing cards.</p><div class="share-links">
<a href="https://wa.me/?text={text}%20{url}" target="_blank" rel="noopener noreferrer">WhatsApp</a>
<a href="https://twitter.com/intent/tweet?text={text}&amp;url={url}" target="_blank" rel="noopener noreferrer">X</a>
<a href="https://www.facebook.com/sharer/sharer.php?u={url}" target="_blank" rel="noopener noreferrer">Facebook</a>
<button type="button" onclick="navigator.clipboard.writeText('{html.escape(canonical, quote=True)}').then(()=>this.textContent='Copied')">Copy link</button>
</div></section>'''


def page(title, description, canonical, destination, body, image_url=None):
    image_meta = f'<meta property="og:image" content="{html.escape(image_url, quote=True)}"><meta name="twitter:card" content="summary_large_image">' if image_url else '<meta name="twitter:card" content="summary">'
    return f'''<!doctype html><html lang="en-IN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(description, quote=True)}">
<link rel="canonical" href="{html.escape(canonical, quote=True)}">
<meta property="og:title" content="{html.escape(title, quote=True)}"><meta property="og:description" content="{html.escape(description, quote=True)}"><meta property="og:url" content="{html.escape(canonical, quote=True)}"><meta property="og:type" content="website">{image_meta}
<style>body{{margin:0;background:#f8f7ff;color:#172033;font:16px/1.55 Inter,Arial,sans-serif}}header,main,footer{{max-width:960px;margin:auto;padding:24px}}header{{display:flex;justify-content:space-between;align-items:center}}a{{color:#4538c8}}.brand{{font-size:22px;font-weight:800;text-decoration:none}}h1{{font-size:38px;line-height:1.15}}.cta{{display:inline-block;background:#5b4ff0;color:white;text-decoration:none;padding:12px 18px;border-radius:12px;font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}.card,.share{{background:white;border:1px solid #e4e2f1;border-radius:16px;padding:16px}}.share{{margin-top:24px}}.share-links{{display:flex;flex-wrap:wrap;gap:8px}}.share-links a,.share-links button{{border:1px solid #d8d5e8;border-radius:10px;background:white;color:#4538c8;padding:9px 12px;font:600 14px Inter,Arial,sans-serif;text-decoration:none;cursor:pointer}}.muted{{color:#5d6478}}li{{margin:7px 0}}</style></head>
<body><header><a class="brand" href="{ORIGIN}/">cardIQ</a><a href="{ORIGIN}/catalog/">Browse the catalogue</a></header><main>{body}{social_links(title, canonical)}<p><a class="cta" href="{html.escape(destination, quote=True)}">Explore and compare in CardIQ</a></p></main><footer class="muted">Card facts are dated and linked to issuer sources. Eligibility and approval are decided by the issuing bank. <a href="{ORIGIN}/methodology/">How CardIQ researches and ranks cards</a>.</footer></body></html>'''


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


def editorial_analysis(card):
    stored = card.get("editorial") or {}
    if stored.get("summary") and stored.get("verdict"):
        list_html = lambda items: "".join(f"<li>{html.escape(item)}</li>" for item in items)
        alternatives = "".join(
            f'<li><a href="{ORIGIN}/cards/{html.escape(item["id"])}/">{html.escape(item["name"])}</a> — {html.escape(item["reason"])}</li>'
            for item in stored.get("alternatives", [])
        )
        alternatives_section = f'<h3>Compare before deciding</h3><ul>{alternatives}</ul>' if alternatives else ""
        return (
            f'<section><h2>CardIQ editorial view</h2><h3>Our take</h3><p>{html.escape(stored["summary"])}</p>'
            f'<div class="grid"><div class="card"><h3>Who it suits</h3><ul>{list_html(stored.get("idealFor", []))}</ul></div>'
            f'<div class="card"><h3>Key strengths</h3><ul>{list_html(stored.get("strengths", []))}</ul></div></div>'
            f'<h3>Trade-offs to understand</h3><ul>{list_html(stored.get("tradeoffs", []))}</ul>'
            f'<h3>CardIQ verdict</h3><p>{html.escape(stored["verdict"])}</p>{alternatives_section}'
            '<p class="muted">This independent editorial assessment is maintained separately from issuer facts and paid placement. Verify current terms before applying.</p></section>'
        )
    labels = {"cashback": "cashback", "shopping": "shopping", "online": "online purchases", "travel": "travel", "dining": "dining", "lounge": "airport lounge access", "rewards": "reward points", "forex": "international spending", "fuel": "fuel", "grocery": "groceries", "upi": "UPI payments", "secured": "building credit"}
    interests = [labels.get(tag, tag.replace("-", " ")) for tag in (card.get("bestFor") or [])[:3]]
    audience = (", ".join(interests[:-1]) + " and " + interests[-1]) if len(interests) > 1 else (interests[0] if interests else "its published reward proposition")
    fee = card.get("annualFeeAmount") or 0
    if card.get("secured"):
        verdict = f'{card["name"]} is primarily worth considering for building credit through a secured or fixed-deposit-backed card.'
    elif fee == 0:
        verdict = f'{card["name"]} is a practical option for people who prioritise {audience}. Its no-annual-fee structure lowers the cost of keeping it long term.'
    elif fee >= 5000:
        verdict = f'{card["name"]} is a practical option for people who prioritise {audience}. The premium fee makes sense only if you will consistently use its higher-value benefits.'
    else:
        verdict = f'{card["name"]} is a practical option for people who prioritise {audience}. The decision should come down to whether your expected rewards comfortably exceed the annual fee.'
    limitation = next((item for item in card.get("highlights", []) if re.search(r"cap|exclu|limit|markup|not cash|condition|eligible", item, re.I)), None)
    good_fit = [f"Your priorities include {audience}.", "The benefits you will actually use are worth more to you than the annual fee." if fee else "You want to avoid an annual membership charge."]
    think_twice = [limitation] if limitation else []
    if fee:
        think_twice.append("You would not use the card enough to offset its annual fee and applicable GST.")
    if not think_twice:
        think_twice.append("Most of your spending falls outside the card's eligible reward categories.")
    list_html = lambda items: "".join(f"<li>{html.escape(item)}</li>" for item in items)
    return f'<section><h2>CardIQ editorial view</h2><p>{html.escape(verdict)}</p><div class="grid"><div class="card"><h3>A good fit when</h3><ul>{list_html(good_fit)}</ul></div><div class="card"><h3>Think twice when</h3><ul>{list_html(think_twice[:2])}</ul></div></div><p class="muted">This analysis is derived from the sourced fees, rewards and conditions on this page. It is not approval advice or a paid ranking.</p></section>'


clean_generated_routes()

for card in CARDS:
    name, issuer = card["name"], card["issuer"]
    description = f'{name}: {card.get("rewardLine", "")}. Annual fee: {card.get("annualFee", "Not specified")}. Sourced card details from CardIQ.'
    route = f'{ORIGIN}/#/cards/{quote(card["id"])}'
    facts = "".join(f"<li>{html.escape(item)}</li>" for item in card.get("highlights", []))
    sources = "".join(f'<li><a href="{html.escape(url, quote=True)}">Issuer source {index + 1}</a></li>' for index, url in enumerate(card.get("sourceUrls", [])))
    body = f'<h1>{html.escape(name)}</h1><p class="muted">{html.escape(issuer)} · Checked {html.escape(card.get("verifiedOn", "date unavailable"))}</p><p>{html.escape(description)}</p>{editorial_analysis(card)}<h2>Benefits, limits and conditions</h2><ul>{facts}</ul><h2>Sources</h2><ul>{sources}</ul>'
    image_url = f'{ORIGIN}{card["imageUrl"]}' if card.get("imageUrl", "").startswith("/") else card.get("imageUrl")
    write(Path("cards") / card["id"], page(f"{name} — fees, rewards and benefits | CardIQ", description, f'{ORIGIN}/cards/{card["id"]}/', route, body, image_url=image_url))

issuers = sorted({card["issuer"] for card in CARDS})
for issuer in issuers:
    matches = [card for card in CARDS if card["issuer"] == issuer]
    count = len(matches)
    description = f"Compare {count} currently catalogued {issuer} credit cards, fees, rewards and sourced benefits on CardIQ."
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

category_links = "".join(f'<li><a href="{ORIGIN}/categories/{category["id"]}/">{html.escape(category["label"])} credit cards</a></li>' for category in published_categories)
issuer_links = "".join(f'<li><a href="{ORIGIN}/issuers/{slug(issuer)}/">{html.escape(issuer)} credit cards</a></li>' for issuer in issuers)
catalog_body = f'''<h1>Explore Indian credit cards</h1><p>Browse CardIQ’s sourced catalogue by use case or issuer. Each card page brings together fees, rewards, important limitations, source links and a transparent editorial view.</p>
<h2>Browse by category</h2><ul>{category_links}</ul><h2>Browse by issuer</h2><ul>{issuer_links}</ul><h2>All cards</h2>{card_links(CARDS)}'''
catalog_description = f"Browse {len(CARDS)} Indian credit cards by category and issuer, with sourced fees, benefits, limitations and editorial guidance."
write(Path("catalog"), page("Indian credit card catalogue | CardIQ", catalog_description, f"{ORIGIN}/catalog/", f"{ORIGIN}/#/cards", catalog_body))

methodology_body = '''<h1>How CardIQ researches and ranks credit cards</h1>
<p>CardIQ helps Indian customers compare credit cards and understand the trade-offs before visiting an issuer. We may earn revenue when a customer continues to an application, but payment does not improve a card’s match score or editorial treatment.</p>
<h2>Sources and updates</h2><p>Fees, rewards, caps, exclusions and availability are documented from issuing-bank pages, key-fact statements, terms, and official co-brand partner pages. Every card shows its source links and the date its details were checked. Issuer terms remain authoritative.</p>
<h2>Editorial analysis</h2><p>CardIQ maintains a structured editorial assessment for every card: our take, who it suits, key strengths, trade-offs, verdict and useful alternatives. Editors review this layer when material card facts change. It does not use customer contact information, represent approval odds or replace financial advice.</p>
<h2>Recommendations and revenue</h2><p>Quiz matches use customer-selected priorities and catalogue attributes. Issuers cannot pay to increase a match score. Application approval, credit limits and final product terms are decided by the issuing bank.</p>
<h2>Corrections</h2><p>Benefits can change. Customers should verify the linked issuer terms before applying and can report outdated information from a CardIQ result page.</p>
<p class="muted">Methodology reviewed 17 October 2026.</p>'''
write(Path("methodology"), page("CardIQ editorial methodology and disclosures", "Learn how CardIQ sources card facts, generates editorial analysis, ranks recommendations and separates issuer revenue from match scores.", f"{ORIGIN}/methodology/", f"{ORIGIN}/#/cards", methodology_body))

sitemap_urls = [f"{ORIGIN}/", f"{ORIGIN}/catalog/", f"{ORIGIN}/methodology/"]
sitemap_urls += [f'{ORIGIN}/cards/{card["id"]}/' for card in CARDS]
sitemap_urls += [f'{ORIGIN}/issuers/{slug(issuer)}/' for issuer in issuers]
sitemap_urls += [f'{ORIGIN}/categories/{category["id"]}/' for category in published_categories]
(BUILD / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in sitemap_urls) + "\n</urlset>\n")
(BUILD / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n")
(BUILD / "catalog-manifest.json").write_text(json.dumps({
    "source": CATALOG_SOURCE, "origin": ORIGIN, "card_ids": [card["id"] for card in CARDS],
}, indent=2))

print(f"Generated {len(CARDS)} card, {len(issuers)} issuer and {len(published_categories)} useful category pages")
