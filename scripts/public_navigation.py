"""Shared public menu for generated pages, sourced from the app's menu data."""
import html
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ITEMS = json.loads((ROOT / 'frontend/src/data/mainNavigation.json').read_text())
STATIC_DESTINATIONS = {'/updates': '/guides/new-credit-cards/', '/restricted-cards': '/guides/invite-only-credit-cards/'}
CSS = '''.main-navigation{display:block;width:100%;max-width:1280px;margin:14px auto 0;padding:0 32px;box-sizing:border-box}.main-navigation-links{display:flex;flex-wrap:wrap;gap:8px}.main-navigation a{display:inline-block;border:1px solid #e4e2f1;border-radius:999px;background:#fff;color:#202337;padding:8px 12px;font:600 13px/1.5 Inter,Arial,sans-serif;text-decoration:none;box-sizing:border-box}.main-navigation a[aria-current=page]{border-color:#6350d7;background:#f2efff;color:#5142bd}.main-navigation a:hover{border-color:#aaa0df}.main-navigation a:focus-visible{outline:3px solid #a89ae9;outline-offset:3px}.journal-main-navigation{max-width:1180px}@media(max-width:640px){.main-navigation{padding:0 20px}.main-navigation-links{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.main-navigation a{border-radius:12px;text-align:center;font-size:12px;padding:8px}}'''


def render_navigation(origin, canonical, journal=False):
    path = urlparse(canonical).path
    active = '/guides/' if path.startswith('/guides') else '/cards?mode=compare' if path.startswith('/compare') else '/calculator' if path.startswith('/calculator') else '/updates' if path.startswith('/updates') else '/restricted-cards' if path.startswith('/restricted-cards') else '/cards' if path.startswith(('/cards', '/catalog', '/issuers', '/categories', '/lounges')) else None
    links = []
    for item in ITEMS:
        target = item.get('to') or item['href']
        url = origin + ('/' if target == '/' else '/#' + target) if item.get('to') else origin + target
        if target in STATIC_DESTINATIONS:
            url = origin + STATIC_DESTINATIONS[target]
        current = ' aria-current="page"' if target == active else ''
        links.append(f'<a href="{html.escape(url, quote=True)}"{current}>{html.escape(item["label"])}</a>')
    modifier = ' journal-main-navigation' if journal else ''
    return f'<nav class="main-navigation{modifier}" aria-label="Main navigation"><div class="main-navigation-links">{"".join(links)}</div></nav>'
