#!/usr/bin/env python3
"""Generate crawlable GitHub Pages entry documents for public catalog routes."""
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "frontend" / "build"
CARDS = json.loads((ROOT / "backend" / "cards_catalog.json").read_text())
ORIGIN = "https://neerajgarg1109.github.io/app"


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def page(title, description, canonical, destination, body):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(description, quote=True)}">
<link rel="canonical" href="{html.escape(canonical, quote=True)}">
<meta property="og:title" content="{html.escape(title, quote=True)}"><meta property="og:description" content="{html.escape(description, quote=True)}">
<script>location.replace({json.dumps(destination)});</script></head>
<body><main>{body}</main><p><a href="{html.escape(destination, quote=True)}">Open this page in CardIQ</a></p></body></html>'''


def write(relative, contents):
    target = BUILD / relative / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(contents)


for card in CARDS:
    name, issuer = card["name"], card["issuer"]
    description = f'{card.get("rewardLine", "")} Annual fee: {card.get("annualFee", "Not specified")}. Verified card details from CardIQ.'
    route = f'{ORIGIN}/#/cards/{quote(card["id"])}'
    facts = "".join(f"<li>{html.escape(item)}</li>" for item in card.get("highlights", []))
    body = f'<h1>{html.escape(name)}</h1><p>{html.escape(issuer)}</p><p>{html.escape(description)}</p><ul>{facts}</ul>'
    write(Path("cards") / card["id"], page(f"{name} — fees, rewards and benefits | CardIQ", description, f'{ORIGIN}/cards/{card["id"]}/', route, body))

issuers = sorted({card["issuer"] for card in CARDS})
for issuer in issuers:
    count = sum(card["issuer"] == issuer for card in CARDS)
    description = f"Compare {count} currently catalogued {issuer} credit cards, fees, rewards and verified benefits on CardIQ."
    destination = f'{ORIGIN}/#/cards?issuer={quote(issuer)}'
    write(Path("issuers") / slug(issuer), page(f"{issuer} credit cards | CardIQ", description, f'{ORIGIN}/issuers/{slug(issuer)}/', destination, f'<h1>{html.escape(issuer)} credit cards</h1><p>{html.escape(description)}</p>'))

for category in ("cashback", "travel", "lounge", "free", "fuel", "upi", "secured", "premium"):
    description = f"Search and compare {category} credit cards in India with sourced fees, rewards, limits and conditions."
    destination = f'{ORIGIN}/#/cards?category={category}'
    write(Path("categories") / category, page(f"{category.title()} credit cards in India | CardIQ", description, f'{ORIGIN}/categories/{category}/', destination, f'<h1>{category.title()} credit cards</h1><p>{description}</p>'))

print(f"Generated {len(CARDS)} card, {len(issuers)} issuer and 8 category entry pages")
