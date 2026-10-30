"""Render shared homepage copy before the React application loads."""
import json
from html import escape
from pathlib import Path
from public_footer import render_footer, CSS
from public_navigation import render_navigation

COPY = json.loads((Path(__file__).resolve().parents[1] / 'frontend/src/data/homeCopy.json').read_text())


def render_homepage_copy(cards, origin):
    count, issuers = len(cards), len({c['issuer'] for c in cards})
    fill = lambda text: escape(text.replace('{cards}', str(count)).replace('{issuers}', str(issuers)))
    pillars = ''.join(f'<article><h2>{fill(title)}</h2><p>{fill(text)}</p></article>' for title, text in COPY['pillars'])
    tools = ''.join(f'<article><h3><a href="{origin}{tool["url"]}">{fill(tool["title"])}</a></h3><p>{fill(tool["text"])}</p></article>' for tool in COPY['tools'])
    return f'''<style>{CSS}.homepage-copy{{max-width:1120px;margin:auto;padding:32px 20px;font:16px/1.7 Inter,Arial,sans-serif;color:#202337}}.homepage-copy h1{{font-size:clamp(32px,5vw,60px);line-height:1.15}}.homepage-copy .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px}}.homepage-copy a{{color:#5142bd}}</style>{render_navigation(origin, origin+'/')}<main class="homepage-copy"><h1>{fill(COPY['headline'])}</h1><p>{fill(COPY['subheadline'])}</p><p><a href="{origin}/calculator/">{fill(COPY['primaryCta'])}</a> · <a href="{origin}/compare/">{fill(COPY['secondaryCta'])}</a></p><p>About a minute to enter your preferences. Savings and approval depend on your spending and issuer terms.</p><section class="grid" aria-label="Our research principles">{pillars}</section><section><h2>Start with what you need</h2><div class="grid">{tools}</div></section></main>{render_footer(origin)}'''
