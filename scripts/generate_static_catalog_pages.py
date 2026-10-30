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
from public_fonts import font_links
from comparison_engine import TOP_COMPARISONS, generateComparisonSeoMeta, render_comparison_page, comparison_excerpt
from comparison_editorial import render_comparison
from guide_blog import render_index as render_blog_index, render_article as render_blog_article
from public_navigation import CSS as MAIN_NAV_CSS, render_navigation
from public_footer import CSS as FOOTER_CSS, render_footer
from seo_content import CSS as SEO_CSS, product_facts, product_research, category_research, choosing_section, shortlist_matches

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from restricted_access import restricted_access
BUILD = Path(os.environ.get("CARDIQ_BUILD_DIR", ROOT / "frontend" / "build"))
CATEGORIES = json.loads((ROOT / "frontend" / "src" / "data" / "cardCategories.json").read_text())
ISSUER_SUPPORT = json.loads((ROOT / "frontend" / "src" / "data" / "issuerSupport.json").read_text())
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
BUILD.mkdir(parents=True, exist_ok=True)
shutil.copyfile(ROOT / "scripts/templates/public-footer.js", BUILD / "public-footer.js")


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


def page(title, description, canonical, destination, body, image_url=None, structured_data=None, head_extra=""):
    image_meta = f'<meta property="og:image" content="{html.escape(image_url, quote=True)}"><meta name="twitter:card" content="summary_large_image">' if image_url else '<meta name="twitter:card" content="summary">'
    schema = structured_data or {"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": description, "url": canonical, "inLanguage": "en-IN"}
    schema_markup = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
    return f'''<!doctype html><html lang="en-IN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{ORIGIN}/favicon.ico" sizes="any"><link rel="icon" type="image/svg+xml" href="{ORIGIN}/favicon.svg"><link rel="icon" type="image/png" sizes="48x48" href="{ORIGIN}/favicon-48.png"><link rel="apple-touch-icon" sizes="180x180" href="{ORIGIN}/apple-touch-icon.png">
{font_links()}{head_extra}
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(description, quote=True)}">
<link rel="canonical" href="{html.escape(canonical, quote=True)}">
<meta property="og:title" content="{html.escape(title, quote=True)}"><meta property="og:description" content="{html.escape(description, quote=True)}"><meta property="og:url" content="{html.escape(canonical, quote=True)}"><meta property="og:type" content="website">{image_meta}<script type="application/ld+json">{schema_markup}</script>
<style>body{{margin:0;background:#f8f7ff;color:#172033;font:16px/1.55 Inter,Arial,sans-serif}}header,main,footer{{max-width:960px;margin:auto;padding:24px}}header{{max-width:1280px;display:flex;justify-content:space-between;align-items:center;gap:16px}}header nav{{display:flex;align-items:center;justify-content:flex-end;gap:10px;flex-wrap:wrap}}a{{color:#4538c8}}.brand{{font-size:22px;font-weight:800;text-decoration:none}}.nav-action{{border:1px solid #d8d5e8;border-radius:999px;background:white;color:#4538c8;padding:8px 13px;font:700 14px Inter,Arial,sans-serif;text-decoration:none;cursor:pointer}}h1{{font-size:38px;line-height:1.15}}.cta{{display:inline-block;background:#5b4ff0;color:white;text-decoration:none;padding:12px 18px;border-radius:12px;font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}.card,.share{{background:white;border:1px solid #e4e2f1;border-radius:16px;padding:16px}}.share{{margin-top:24px}}.share-links{{display:flex;flex-wrap:wrap;gap:8px}}.share-links a,.share-links button{{border:1px solid #d8d5e8;border-radius:10px;background:white;color:#4538c8;padding:9px 12px;font:600 14px Inter,Arial,sans-serif;text-decoration:none;cursor:pointer}}.muted{{color:#5d6478}}li{{margin:7px 0}}@media(max-width:600px){{header{{align-items:flex-start}}header nav{{gap:8px}}header nav>a:last-child{{display:none}}h1{{font-size:32px}}}}{MAIN_NAV_CSS}{SEO_CSS}{FOOTER_CSS}</style></head>
<body><header><a class="brand" href="{ORIGIN}/">cardIQ</a><button class="nav-action" type="button" onclick="history.length &gt; 1 ? history.back() : location.href='{ORIGIN}/'">← Back</button></header>{render_navigation(ORIGIN, canonical)}<main>{body}{social_links(title, canonical)}<p><a class="cta" href="{html.escape(destination, quote=True)}">Explore and compare in CardIQ</a></p></main>{render_footer(ORIGIN)}</body></html>'''


def write(relative, contents):
    target = BUILD / relative / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(contents)


def clean_generated_routes():
    """Remove stale generated routes while preserving CRA assets such as card images."""
    shutil.rmtree(BUILD / "categories", ignore_errors=True)
    shutil.rmtree(BUILD / "issuers", ignore_errors=True)
    shutil.rmtree(BUILD / "calculator", ignore_errors=True)
    shutil.rmtree(BUILD / "compare", ignore_errors=True)
    shutil.rmtree(BUILD / "updates", ignore_errors=True)
    shutil.rmtree(BUILD / "lounges", ignore_errors=True)
    shutil.rmtree(BUILD / "restricted-cards", ignore_errors=True)
    shutil.rmtree(BUILD / "guides", ignore_errors=True)
    cards_directory = BUILD / "cards"
    if cards_directory.exists():
        for child in cards_directory.iterdir():
            if child.is_dir():
                shutil.rmtree(child)


def category_match(card, definition):
    if definition.get("id") == "lifetime-free" and card.get("lifetimeFree") is False:
        return False
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


def card_artwork(card):
    image = card.get("imageUrl")
    if not image:
        return ''
    return f'<img class="product-image" src="{html.escape(image, quote=True)}" alt="{html.escape(card["name"], quote=True)} card" width="240" height="180" loading="lazy" decoding="async">'


def card_links(cards, source):
    return '<div class="grid">' + "".join(
        f'<article class="card">{card_artwork(card)}<h2><a href="{ORIGIN}/cards/{html.escape(card["id"])}/">{html.escape(card["name"])}</a></h2>'
        f'<p class="muted">{html.escape(card["issuer"])}</p><p>{html.escape(card.get("rewardLine", ""))}</p>'
        f'<p><strong>Annual fee:</strong> {html.escape(card.get("annualFee", "Not specified"))}</p>'
        f'<p><a href="{ORIGIN}/cards/{html.escape(card["id"])}/">View details</a> · '
        + (f'<a class="cta" href="{ORIGIN}/go/{quote(card["id"])}/?subid=list_card&amp;source={quote(source)}" rel="sponsored nofollow noopener" target="_blank">Apply now →</a>' if card.get('active', True) and card.get('applicationsOpen', True) else '<span>Applications closed</span>') + '</p></article>' 
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
            '<p class="muted">This CardIQ editorial assessment is maintained separately from issuer facts and commercial links. CardIQ may earn a commission from some applications. Verify current terms before applying.</p></section>'
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


if os.environ.get("CARDIQ_PRESERVE_GENERATED") != "true":
    clean_generated_routes()
cards_by_id = {card["id"]: card for card in CARDS}
category_counts = {category['id']: sum(category_match(card, category) for card in CARDS) for category in CATEGORIES}

for card in CARDS:
    name, issuer = card["name"], card["issuer"]
    editorial = card.get("editorial") or {}
    description = editorial.get("summary") or f'{name}: {card.get("rewardLine", "")}. Annual fee: {card.get("annualFee", "Not specified")}. Sourced card details from CardIQ.'
    route = f'{ORIGIN}/#/cards/{quote(card["id"])}'
    facts = "".join(f"<li>{html.escape(item)}</li>" for item in card.get("highlights", []))
    sources = "".join(f'<li><a href="{html.escape(url, quote=True)}">Issuer source {index + 1}: {html.escape(url.split("/")[2])}</a></li>' for index, url in enumerate(card.get("sourceUrls", [])))
    body = f'<h1>{html.escape(name)}</h1><p class="muted">{html.escape(issuer)} · Checked {html.escape(card.get("verifiedOn", "date unavailable"))}</p><p>{html.escape(description)}</p>{editorial_analysis(card)}<h2>Benefits, limits and conditions</h2><ul>{facts}</ul><h2>Sources</h2><ul>{sources}</ul>'
    image_url = f'{ORIGIN}{card["imageUrl"]}' if card.get("imageUrl", "").startswith("/") else card.get("imageUrl")
    canonical = f'{ORIGIN}/cards/{card["id"]}/'
    body = body.replace('</h1>', '</h1>' + product_facts(card, ORIGIN, restricted_access(card)), 1)
    related_categories = [category for category in CATEGORIES if category_match(card, category)
                          and category_counts[category['id']] >= 3]
    body += product_research(card, related_categories, ORIGIN, slug(issuer))
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "name": f"{name} review", "description": description, "url": canonical, "inLanguage": "en-IN", "dateModified": card.get("verifiedOn")},
        {"@type": "CreditCard", "name": name, "provider": {"@type": "Organization", "name": issuer}, "areaServed": "IN", "feesAndCommissionsSpecification": card.get("termsNote", "Confirm fees and conditions with the issuer."), "description": description, "url": canonical, **({"image": image_url} if image_url else {})},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Credit cards", "item": f"{ORIGIN}/catalog/"},
            {"@type": "ListItem", "position": 2, "name": issuer, "item": f"{ORIGIN}/issuers/{slug(issuer)}/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical},
        ]},
    ]}
    write(Path("cards") / card["id"], page(f"{name} review: Fees & Rewards | CardIQ" if len(name) <= 33 else f"{name} review | CardIQ", description, canonical, route, body, image_url=image_url, structured_data=schema))

issuers = sorted({card["issuer"] for card in CARDS})
for issuer in issuers:
    matches = [card for card in CARDS if card["issuer"] == issuer]
    count = len(matches)
    description = f"Compare {count} currently catalogued {issuer} credit cards, fees, rewards and sourced benefits on CardIQ."
    destination = f'{ORIGIN}/#/cards?issuer={quote(issuer)}'
    body = f'<h1>{html.escape(issuer)} credit cards</h1><p>{html.escape(description)}</p>{card_links(matches, "issuers-" + slug(issuer))}'
    write(Path("issuers") / slug(issuer), page(f"{issuer} credit cards | CardIQ", description, f'{ORIGIN}/issuers/{slug(issuer)}/', destination, body))

published_categories = []
for category in CATEGORIES:
    matches = [card for card in CARDS if category_match(card, category)]
    if len(matches) < 3:
        continue
    published_categories.append(category)
    description = category["description"]
    destination = f'{ORIGIN}/#/cards?category={category["id"]}'
    body = f'<h1>{html.escape(category["label"])} credit cards in India</h1><p>{html.escape(description)}</p>{category_research(category["id"], ORIGIN)}<p class="muted">{len(matches)} matching cards · Details checked against issuer or official partner sources.</p>{card_links(matches, "categories-" + category["id"])}'
    write(Path("categories") / category["id"], page(f'{category["label"]} credit cards in India | CardIQ', description, f'{ORIGIN}/categories/{category["id"]}/', destination, body))

# Only publish comparisons that both cards' maintained editorial records recommend.
# This prevents the SEO layer from manufacturing arbitrary or thin pairings.
directed_alternatives = {
    (card["id"], alternative["id"])
    for card in CARDS
    for alternative in (card.get("editorial") or {}).get("alternatives", [])
    if alternative.get("id") in cards_by_id
}
comparison_pairs = sorted({
    tuple(sorted((left, right)))
    for left, right in directed_alternatives
    if left != right and (right, left) in directed_alternatives
})
comparison_links = []
comparison_posts = []
priority_by_pair = {frozenset((row['cardA'], row['cardB'])): row for row in TOP_COMPARISONS}
comparison_routes = [(f"{left}-vs-{right}", left, right, None) for left,right in comparison_pairs]
comparison_routes += [(row['slug'], row['cardA'], row['cardB'], row) for row in TOP_COMPARISONS]
comparison_canonicals = []
comparison_styles = (ROOT / 'scripts/templates/comparison.css').read_text()
shutil.copyfile(ROOT / 'scripts/templates/comparison-calculator.js', BUILD / 'comparison-calculator.js')
for route_slug, left_id, right_id, custom in comparison_routes:
    primary = custom or priority_by_pair.get(frozenset((left_id, right_id)))
    left, right = (cards_by_id[primary['cardA']], cards_by_id[primary['cardB']]) if primary else (cards_by_id[left_id], cards_by_id[right_id])
    meta = generateComparisonSeoMeta(left, right, primary or {'slug': route_slug}, ORIGIN)
    canonical = meta['canonicalUrl']
    destination = f'{ORIGIN}/#/cards?compare={quote(left["id"])},{quote(right["id"])}'
    extra = render_comparison(f'{left_id}-vs-{right_id}', left, right)
    body, schema = render_comparison_page(left, right, meta, CARDS, primary, extra)
    head = f'<style>{comparison_styles}</style><script defer src="{ORIGIN}/comparison-calculator.js"></script>'
    write(Path('compare') / route_slug, page(meta['title'], meta['metaDescription'], canonical, destination, body, structured_data=schema, head_extra=head))
    if route_slug != meta['slug']:
        continue  # Preserve old URLs with full content and the preferred canonical; no duplicate sitemap entry.
    comparison_canonicals.append(canonical)
    comparison_posts.append({'slug':route_slug,'title':f'{left["name"]} vs {right["name"]}','description':comparison_excerpt(left, right),'priorityRank':next((i for i,row in enumerate(TOP_COMPARISONS) if row['slug']==route_slug),None),'url':canonical,'destination':destination,'body':body,'category':'Card comparisons','artwork':[{'url':card['imageUrl'],'name':card['name']} for card in (left,right) if card.get('imageUrl')]})
    comparison_links.append(f'<li><a href="{canonical}">{html.escape(left["name"])} vs {html.escape(right["name"])}</a></li>')

priority_order = {row['slug']: i for i, row in enumerate(TOP_COMPARISONS)}
comparison_posts.sort(key=lambda post: (0, priority_order[post['slug']]) if post['slug'] in priority_order else (1, post['slug']))
comparison_links = [f'<li><a href="{post["url"]}">{html.escape(post["title"])}</a></li>' for post in comparison_posts]

compare_description = f"Browse {len(comparison_canonicals)} maintained Indian credit card comparisons with fees, reward scenarios, exclusions and issuer sources."
compare_body = f'<h1>Indian credit card comparisons</h1><p>{html.escape(compare_description)}</p><p class="muted">Twenty priority matchups and maintained editorial pairings. Estimates do not guarantee approval or savings.</p><ul>{"".join(comparison_links)}</ul>'
write(Path('compare'), page('Compare Indian credit cards side by side | CardIQ',compare_description,f'{ORIGIN}/compare/',f'{ORIGIN}/#/cards?mode=compare',compare_body))

# Static-host bridge: the backend makes the authoritative destination decision and records placement.
api_origin = os.environ.get('CARDIQ_API_ORIGIN', 'https://api.findmybest.cards').rstrip('/')
for card in CARDS:
    endpoint = f'{api_origin}/api/go/{card["id"]}'
    script_target = json.dumps(endpoint).replace('<','\\u003c')
    write(Path('go') / card['id'], f'<!doctype html><html lang="en-IN"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Continue to the issuer | CardIQ</title></head><body><h1>Continue to {html.escape(card["name"])}</h1><p>The issuer decides eligibility and approval. CardIQ may earn a commission through a partner link.</p><a href="{html.escape(endpoint,quote=True)}" rel="sponsored nofollow noopener">Continue to issuer</a><script>location.replace({script_target}+location.search)</script><noscript><p>Use the link above to continue. Placement tracking is unavailable without JavaScript.</p></noscript></body></html>')

# A verification history is useful and accurate; it must not be presented as a launch date.
verification_dates = sorted({card.get("verifiedOn") for card in CARDS if card.get("verifiedOn")}, reverse=True)
update_links = []
for verified_on in verification_dates:
    matches = [card for card in CARDS if card.get("verifiedOn") == verified_on]
    description = f"See {len(matches)} Indian credit card records whose issuer or official-partner details CardIQ checked on {verified_on}."
    body = f'<h1>Card details checked on {html.escape(verified_on)}</h1><p>{html.escape(description)}</p><p class="muted">This is a verification date, not necessarily a product launch or benefit-change date.</p>{card_links(matches, "updates-" + verified_on)}'
    write(Path("updates") / verified_on, page(f"Credit card catalogue checks: {verified_on} | CardIQ", description, f"{ORIGIN}/updates/{verified_on}/", f"{ORIGIN}/#/cards?sort=recent", body))
    update_links.append(f'<li><a href="{ORIGIN}/updates/{verified_on}/">{html.escape(verified_on)} — {len(matches)} card records checked</a></li>')
updates_description = "Follow CardIQ’s dated Indian credit card catalogue checks without confusing verification dates with card launch dates."
updates_body = f'<h1>CardIQ catalogue updates</h1><p>{html.escape(updates_description)}</p><ul>{"".join(update_links)}</ul>'
write(Path("updates"), page("Indian credit card catalogue updates | CardIQ", updates_description, f"{ORIGIN}/updates/", f"{ORIGIN}/#/cards?sort=recent", updates_body))

lounge_cards = [card for card in CARDS if "lounge" in " ".join([*(card.get("bestFor") or []), *(card.get("highlights") or []), *(card.get("loungeBenefits") or [])]).lower()]
lounge_description = f"Explore {len(lounge_cards)} Indian credit cards whose sourced catalogue details mention airport lounge access or lounge benefits."
lounge_body = f'<h1>Airport lounge credit cards in India</h1><p>{html.escape(lounge_description)}</p><p class="muted">Access rules can depend on airport, terminal, network, spend thresholds and quarterly limits. Confirm current eligibility in the linked issuer terms before travelling.</p>{card_links(lounge_cards, "lounges")}'
write(Path("lounges"), page("Airport lounge credit cards in India | CardIQ", lounge_description, f"{ORIGIN}/lounges/", f"{ORIGIN}/#/cards?category=travel", lounge_body))

restricted_cards = [(card, access) for card in CARDS
                    if (access := restricted_access(card)) and access["accessType"] == "invite-only"]
restricted_columns = "".join(
    f'<article class="card"><p><strong>{html.escape(access["accessLabel"])}</strong></p><h2><a href="{ORIGIN}/cards/{html.escape(card["id"])}/">{html.escape(card["name"])}</a></h2>'
    f'<p class="muted">{html.escape(card["issuer"])}</p><p>{html.escape(access["accessExplanation"])}</p></article>'
    for card, access in restricted_cards
)
restricted_description = f"Research {len(restricted_cards)} invitation-only Indian credit cards with issuer-confirmed invitation requirements."
restricted_body = f'''<h1>Invite-only credit cards in India</h1><p>{html.escape(restricted_description)}</p>
<p class="muted">These cards are excluded from CardIQ’s general quiz because access cannot be assumed. An invitation, relationship or listed customer segment does not guarantee approval; the issuing bank decides eligibility.</p><div class="grid">{restricted_columns}</div>'''
write(Path("restricted-cards"), page("Invite-only credit cards in India | CardIQ", restricted_description, f"{ORIGIN}/restricted-cards/", f"{ORIGIN}/#/restricted-cards", restricted_body))

guides = [
    ("new-credit-cards", "New credit cards and benefit changes in India", "Follow sourced Indian credit card launches, fee revisions, reward changes and discontinued benefits without confusing publication dates with launch dates.", f"{ORIGIN}/updates/", "Use CardIQ’s dated change log to verify what changed, when it takes effect and which issuer source supports it."),
    ("invite-only-credit-cards", "Invite-only credit cards in India", "Understand invitation-only and relationship-restricted Indian credit cards, their access routes and why exclusivity does not guarantee approval.", f"{ORIGIN}/restricted-cards/", "CardIQ separates invitation-only products from partner-channel and profession-restricted cards so customers can research the real access requirement."),
    ("close-credit-card-india", "How to close a credit card in India", "Find official issuer support and card-closure channels, prepare for outstanding balances and keep written confirmation of closure.", f"{ORIGIN}/#/help/issuers", "Pay or transfer outstanding balances, redeem rewards that may expire, use the issuer’s official closure channel and retain the closure acknowledgement. Never share an OTP, PIN or CVV with a caller."),
]
guide_posts = []
for guide_slug, guide_title, guide_description, destination, guidance in guides:
    canonical = f"{ORIGIN}/guides/{guide_slug}/"
    guide_body = f'<h1>{html.escape(guide_title)}</h1><p>{html.escape(guide_description)}</p><h2>What to do next</h2><p>{html.escape(guidance)}</p><p class="muted">Issuer terms and official service channels remain authoritative. CardIQ does not provide approval or legal advice.</p>'
    topic = "Card updates" if guide_slug == "new-credit-cards" else "Access & eligibility" if guide_slug == "invite-only-credit-cards" else "Card management"
    guide_posts.append({"slug": guide_slug, "title": guide_title, "description": guide_description, "url": canonical, "destination": destination, "body": guide_body, "category": topic})

# High-intent editorial guides are generated from the same catalogue records as card pages.
# This keeps fees, card availability and card links synchronized when the catalogue changes.
category_by_id = {item["id"]: item for item in CATEGORIES}
editorial_guides = [
    ("best-cashback-credit-cards-india", "Best cashback credit cards in India", "cashback", "Compare eligible cashback rates, monthly caps, excluded transactions and annual fees—not only the headline percentage."),
    ("best-lifetime-free-credit-cards-india", "Best lifetime-free credit cards in India", "lifetime-free", "A zero annual fee lowers the cost of keeping a card, but rewards, exclusions and application eligibility still differ."),
    ("best-travel-credit-cards-india", "Best travel credit cards in India", "travel", "Compare airline and hotel rewards, lounge conditions, foreign-currency costs, redemption choices and annual fees."),
    ("best-fuel-credit-cards-india", "Best fuel credit cards in India", "fuel", "Compare eligible fuel outlets, reward caps, surcharge-waiver conditions and the spending needed to recover the annual fee."),
    ("best-rupay-upi-credit-cards-india", "Best RuPay credit cards for UPI in India", "rupay-upi", "Check UPI eligibility, merchant restrictions, reward exclusions, caps and the issuing bank behind each RuPay card."),
    ("best-first-credit-cards-india", "Best first credit cards in India", "beginner", "Compare straightforward fees, secured alternatives and documented benefits without treating a shortlist as an approval promise."),
]
editorial_guide_slugs = []
for guide_slug, guide_title, category_id, guidance in editorial_guides:
    definition = category_by_id[category_id]
    matches = [card for card in CARDS if card.get("active", True) and card.get("applicationsOpen", True) and not restricted_access(card) and category_match(card, definition) and shortlist_matches(card, category_id)]
    matches.sort(key=lambda card: (-len(card.get("sourceUrls") or []), -len(card.get("highlights") or []), -float(card.get("rating") or 0), card["name"]))
    shortlist = matches[:12]
    description = f"CardIQ’s sourced shortlist of {len(shortlist)} {definition['label'].lower()} credit cards in India, with fees, benefits and important trade-offs to verify."
    canonical = f"{ORIGIN}/guides/{guide_slug}/"
    destination = f"{ORIGIN}/#/cards?category={category_id}"
    body = f'''<h1>{html.escape(guide_title)}</h1><p>{html.escape(description)}</p>
<h2>How to choose</h2><p>{html.escape(guidance)}</p>
{choosing_section(category_id)}
<p class="muted">This is an editorial shortlist, not a personalised recommendation or approval ranking. Eligible cards are ordered by the completeness of their maintained sources and decision-critical details—not from best to worst. No issuer can pay to improve its position.</p>
{card_links(shortlist, guide_slug)}<h2>Check before applying</h2><ul><li>Confirm the current fee, waiver threshold and applicable GST.</li><li>Check reward caps, excluded transactions and redemption value.</li><li>Open the card page to review dated issuer sources and CardIQ’s trade-offs.</li></ul>'''
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": guide_title, "description": description, "url": canonical, "inLanguage": "en-IN"},
        {"@type": "ItemList", "name": guide_title, "itemListElement": [
            {"@type": "ListItem", "position": index, "url": f'{ORIGIN}/cards/{card["id"]}/', "name": card["name"]}
            for index, card in enumerate(shortlist, 1)
        ]},
    ]}
    guide_posts.append({"slug": guide_slug, "title": guide_title, "description": guidance, "standfirst": description, "url": canonical, "destination": destination, "body": body, "category": "Choosing a card", "schema": schema, "artwork": [{"url": card["imageUrl"], "name": card["name"]} for card in shortlist if card.get("imageUrl")][:2]})
    editorial_guide_slugs.append(guide_slug)

# Only publish issuer-specific closure pages where an official channel has been reviewed.
closure_guide_slugs = []
for support in ISSUER_SUPPORT:
    issuer = support["issuer"]
    product_name = issuer if issuer.lower().endswith("card") else f"{issuer} credit card"
    guide_slug = f'close-{slug(issuer)}-credit-card'
    canonical = f"{ORIGIN}/guides/{guide_slug}/"
    description = f"How to close {product_name} using official support and closure guidance checked by CardIQ on {support['checkedOn']}."
    phone = f'<li><strong>Customer care:</strong> <a href="tel:{html.escape(support["phone"].replace(" ", ""), quote=True)}">{html.escape(support["phone"])}</a></li>' if support.get("phone") else ""
    email = f'<li><strong>Email:</strong> <a href="mailto:{html.escape(support["email"], quote=True)}">{html.escape(support["email"])}</a></li>' if support.get("email") else ""
    closure = f'<li><a href="{html.escape(support["closureUrl"], quote=True)}">Official {html.escape(issuer)} closure guidance</a></li>' if support.get("closureUrl") else ""
    body = f'''<h1>How to close {html.escape(product_name)}</h1><p>{html.escape(description)}</p>
<h2>Before requesting closure</h2><ul><li>Clear outstanding balances, pending EMIs and unbilled transactions.</li><li>Redeem eligible rewards that may expire and move recurring payments.</li><li>Download recent statements and retain the written closure acknowledgement.</li></ul>
<h2>Official {html.escape(issuer)} channels</h2><ul>{phone}{email}<li><a href="{html.escape(support['supportUrl'], quote=True)}">Official customer support</a></li>{closure}</ul>
<p class="muted">Blocking a card is not the same as closing the credit account. Never share your PIN, CVV or OTP. Contact details were checked {html.escape(support['checkedOn'])}; verify them on the linked issuer page.</p>'''
    guide_posts.append({"slug": guide_slug, "title": f"How to close {product_name}", "description": description, "url": canonical, "destination": f"{ORIGIN}/#/help/issuers", "body": body, "category": "Card management"})
    closure_guide_slugs.append(guide_slug)

for post in guide_posts:
    write(Path("guides") / post["slug"], render_blog_article(post, guide_posts, ORIGIN, social_links(post["title"], post["url"])))
write(Path("guides"), render_blog_index(guide_posts + comparison_posts, ORIGIN, social_links("CardIQ Journal", f"{ORIGIN}/guides/")))

category_links = "".join(f'<li><a href="{ORIGIN}/categories/{category["id"]}/">{html.escape(category["label"])} credit cards</a></li>' for category in published_categories)
issuer_links = "".join(f'<li><a href="{ORIGIN}/issuers/{slug(issuer)}/">{html.escape(issuer)} credit cards</a></li>' for issuer in issuers)
catalog_body = f'''<h1>Explore Indian credit cards</h1><p>Browse CardIQ’s sourced catalogue by use case or issuer. Each card page brings together fees, rewards, important limitations, source links and a transparent editorial view.</p>
<p><a class="cta" href="{ORIGIN}/calculator/">Estimate annual card value</a></p>
<p><a href="{ORIGIN}/compare/">Head-to-head comparisons</a> · <a href="{ORIGIN}/updates/">Catalogue updates</a> · <a href="{ORIGIN}/lounges/">Airport lounge cards</a> · <a href="{ORIGIN}/restricted-cards/">Restricted-access cards</a> · <a href="{ORIGIN}/guides/">Credit card guides</a></p>
<h2>Browse by category</h2><ul>{category_links}</ul><h2>Browse by issuer</h2><ul>{issuer_links}</ul><h2>All cards</h2>{card_links(CARDS, "catalog")}'''
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

calculator_body = f'''<h1>Credit card value calculator for India</h1>
<p>Compare Indian credit cards using your own monthly spending instead of headline reward rates. Enter approximate spending for online shopping, dining, travel, fuel, international purchases and everything else. No login or contact details are required.</p>
<section class="card" aria-labelledby="calculator-tool-title"><h2 id="calculator-tool-title">Calculate your card value</h2>
<p class="muted">Enter a typical month of spending below. The calculator uses CardIQ’s current catalogue and the same calculation model as the main app.</p>
<script>function resizeCardIqCalculator(frame){{const resize=()=>{{const doc=frame.contentDocument;if(!doc)return;frame.style.height=Math.max(760,doc.documentElement.scrollHeight,doc.body.scrollHeight)+'px'}};resize();new ResizeObserver(resize).observe(frame.contentDocument.body);setTimeout(resize,500)}}</script>
<iframe title="CardIQ credit card value calculator" src="{ORIGIN}/#/calculator?embedded=1" loading="eager" scrolling="no" onload="resizeCardIqCalculator(this)" style="display:block;width:100%;height:760px;overflow:hidden;border:1px solid #e4e2f1;border-radius:16px;background:white"></iframe>
<p><a href="{ORIGIN}/#/calculator">Open the calculator in a full page</a></p></section>
<h2>What the estimate considers</h2><ul><li>Your annualised card spending</li><li>How well each card’s documented categories match your spending</li><li>Published annual fees and fee-waiver thresholds</li><li>Explicitly priced welcome or milestone benefits</li><li>Your expected airport-lounge use</li></ul>
<h2>What can change the result</h2><p>Merchant classification, monthly reward caps, excluded transactions, redemption choices and issuer rule changes can reduce actual value. CardIQ therefore shows an editorial range rather than promising an exact return. The issuing bank’s current terms remain authoritative.</p>'''
write(Path("calculator"), page("Indian credit card value calculator | CardIQ", "Estimate and compare annual credit card rewards after fees using your monthly spending across common Indian purchase categories.", f"{ORIGIN}/calculator/", f"{ORIGIN}/#/calculator", calculator_body))

sitemap_urls = [f"{ORIGIN}/", f"{ORIGIN}/catalog/", f"{ORIGIN}/methodology/", f"{ORIGIN}/calculator/", f"{ORIGIN}/compare/", f"{ORIGIN}/updates/", f"{ORIGIN}/lounges/", f"{ORIGIN}/restricted-cards/", f"{ORIGIN}/guides/"]
sitemap_urls += [f"{ORIGIN}/guides/{guide_slug}/" for guide_slug, *_ in guides]
sitemap_urls += [f"{ORIGIN}/guides/{guide_slug}/" for guide_slug in editorial_guide_slugs + closure_guide_slugs]
sitemap_urls += [f'{ORIGIN}/cards/{card["id"]}/' for card in CARDS]
sitemap_urls += [f'{ORIGIN}/issuers/{slug(issuer)}/' for issuer in issuers]
sitemap_urls += [f'{ORIGIN}/categories/{category["id"]}/' for category in published_categories]
sitemap_urls += comparison_canonicals
sitemap_urls += [f'{ORIGIN}/updates/{verified_on}/' for verified_on in verification_dates]
(BUILD / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in sitemap_urls) + "\n</urlset>\n")
(BUILD / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n")
homepage = BUILD / "index.html"
homepage.write_text(homepage.read_text().replace("%REACT_APP_PUBLIC_APP_URL%", ORIGIN))
(BUILD / "catalog-manifest.json").write_text(json.dumps({
    "source": CATALOG_SOURCE, "origin": ORIGIN, "card_ids": [card["id"] for card in CARDS], "comparison_urls": comparison_canonicals, "priority_comparisons": [row["slug"] for row in TOP_COMPARISONS],
}, indent=2))

print(f"Generated {len(CARDS)} card, {len(issuers)} issuer, {len(published_categories)} category and {len(comparison_canonicals)} canonical comparison pages")
