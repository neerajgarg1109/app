"""Render shared homepage copy before the React application loads."""
import json
from html import escape
from pathlib import Path
from public_footer import render_footer, CSS
from public_navigation import render_navigation
import html

COPY = json.loads((Path(__file__).resolve().parents[1] / 'frontend/src/data/homeCopy.json').read_text())


def render_homepage_highlights(cards, origin):
    news_path = Path(__file__).resolve().parents[1] / 'frontend/src/data/cardNews.json'
    news = [item for item in json.loads(news_path.read_text()) if item.get('active') and item.get('status') in ('announcement', 'upcoming')]
    promoted = next((card for card in cards if card.get('applicationLinkType') == 'partner' and card.get('active', True) and card.get('applicationsOpen', True)), None)
    promoted = promoted or next((card for card in cards if card.get('id') == 'sbi-cashback-sbi'), None)
    live = next((card for card in cards if card.get('id') == 'hdfc-swiggy-ornge-hdfc-bank-credit-card' and card.get('active', True) and card.get('applicationsOpen', True)), None)
    announcement = next((item for item in news if item.get('status') == 'announcement'), None)
    rule = next((item for item in news if 'sbi' in item.get('id', '')), None) or next((item for item in news if item.get('status') == 'upcoming'), None)

    def card_tile(label, status, card, action='View card'):
        if not card:
            return f'<article class="ciq-highlight-panel"><p class="ciq-highlight-badge">{label}</p><h2>{status}</h2><p>Browse the CardIQ card catalogue.</p><a href="{origin}/catalog/">Browse cards →</a></article>'
        summary = html.escape((card.get('editorial') or {}).get('summary') or card.get('rewardLine') or '')
        return f'<article class="ciq-highlight-panel"><p class="ciq-highlight-badge ciq-highlight-badge--launch">{label}</p><p>{html.escape(card.get("issuer", ""))}</p><h2>{html.escape(card["name"])}</h2><p>{summary}</p><a href="{origin}/cards/{html.escape(card["id"])}/">{action} →</a></article>'

    def news_tile(label, item, variant):
        if not item:
            return f'<article class="ciq-highlight-panel"><p class="ciq-highlight-badge">{label}</p><h2>No active updates</h2><a href="{origin}/guides/news/">Browse archive →</a></article>'
        return f'<article class="ciq-highlight-panel"><p class="ciq-highlight-badge ciq-highlight-badge--{variant}">{html.escape(item.get("statusLabel", label))}</p><p>{html.escape(item.get("issuer", ""))}</p><h2>{html.escape(item.get("headline") or item.get("cardName", ""))}</h2><p>{html.escape(item.get("summary", ""))}</p><a href="{html.escape(item.get("sourceUrl", ""))}" target="_blank" rel="noopener noreferrer">Read issuer source →</a>'

    return f'''<section class="ciq-home-highlights" aria-labelledby="ciq-home-highlights-title"><div class="ciq-container ciq-container--wide"><header class="ciq-highlights-heading"><p class="ciq-highlights-eyebrow">THE CARDIQ DESK</p><h2 id="ciq-home-highlights-title">Cards &amp; updates</h2><p>New cards, useful highlights and issuer changes worth knowing.</p></header><div class="ciq-highlights-grid ciq-highlights-grid--four">{card_tile("Featured card", "Editor’s pick", promoted)}{card_tile("Latest live launch", "No recent launch", live, "View details")}{news_tile("Announced / upcoming", announcement, "announcement")}{news_tile("Existing card updates", rule, "rule")}</div><div class="ciq-highlights-more"><a href="{origin}/guides/news/">Show more updates &amp; archives →</a></div><p class="ciq-news-editorial">CardIQ editorial desk · <a href="mailto:hi@findmybest.cards">hi@findmybest.cards</a> for corrections. Confirm current terms with the issuer.</p></div></section>'''


def render_homepage_copy(cards, origin):
    count, issuers = len(cards), len({c['issuer'] for c in cards})
    fill = lambda text: escape(text.replace('{cards}', str(count)).replace('{issuers}', str(issuers)))
    pillars = ''.join(f'<article><h2>{fill(title)}</h2><p>{fill(text)}</p></article>' for title, text in COPY['pillars'])
    tools = ''.join(f'<article><h3><a href="{origin}{tool["url"]}">{fill(tool["title"])}</a></h3><p>{fill(tool["text"])}</p></article>' for tool in COPY['tools'])
    return f'''<style>{CSS}.homepage-copy{{max-width:1120px;margin:auto;padding:32px 20px;font:16px/1.7 Inter,Arial,sans-serif;color:#202337}}.homepage-copy h1{{font-size:clamp(32px,5vw,60px);line-height:1.15}}.homepage-copy .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px}}.homepage-copy a{{color:#5142bd}}.homepage-copy .ciq-highlights-grid--four{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.homepage-copy .ciq-highlight-panel{{padding:22px;border:1px solid #e6e3ef;border-radius:20px;background:#fff;box-shadow:0 8px 30px -24px rgba(35,27,75,.28)}}.homepage-copy .ciq-highlight-panel h2{{margin:12px 0 8px;font-size:19px;line-height:1.4}}.homepage-copy .ciq-highlight-panel p{{font-size:13px;line-height:1.65}}@media(max-width:639px){{.homepage-copy .ciq-highlights-grid--four{{grid-template-columns:1fr}}}}</style>{render_navigation(origin, origin+'/')}<main class="homepage-copy"><h1>{fill(COPY['headline'])}</h1><p>{fill(COPY['subheadline'])}</p><p><a href="{origin}/calculator/">{fill(COPY['primaryCta'])}</a> · <a href="{origin}/compare/">{fill(COPY['secondaryCta'])}</a></p><p>About a minute to enter your preferences. Savings and approval depend on your spending and issuer terms.</p><section class="grid" aria-label="Our research principles">{pillars}</section><section><h2>Start with what you need</h2><div class="grid">{tools}</div></section></main>{render_homepage_highlights(cards, origin)}{render_footer(origin)}'''
