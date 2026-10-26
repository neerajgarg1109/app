"""The same footer content and styles used by the React app."""
import html
import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = json.loads((ROOT / 'frontend/src/data/footerContent.json').read_text())
CSS = (ROOT / 'frontend/src/components/CustomerFooter.css').read_text()


def destination(origin, url):
    if url.startswith('https://'):
        return url
    spa = url == '/' or any(url.startswith(path) for path in ('/cards', '/updates', '/restricted-cards', '/calculator', '/wallet-optimizer', '/alerts', '/help/issuers'))
    return origin + ('/#' + url if spa else url)


def render_footer(origin):
    groups = []
    for index, group in enumerate(CONTENT['groups']):
        links = ''.join(f'<li><a href="{html.escape(destination(origin, link["url"]), quote=True)}">{html.escape(link["label"])}</a></li>' for link in group['links'])
        groups.append(f'<section aria-labelledby="footer-group-{index}"><h2 id="footer-group-{index}">{html.escape(group["title"])}</h2><ul>{links}</ul></section>')
    endpoint = os.environ.get('CARDIQ_SITE_CONTENT_API_URL', 'https://api.findmybest.cards/api/site-content')
    return f'''<footer class="customer-footer" aria-label="Site footer" data-content-url="{html.escape(endpoint, quote=True)}" data-public-origin="{html.escape(origin, quote=True)}"><div class="customer-footer-inner"><div class="customer-footer-grid"><div class="customer-footer-about"><a href="{origin}/" class="customer-footer-brand" aria-label="CardIQ home"><span class="customer-footer-mark" aria-hidden="true"><span></span></span><span>card<span class="customer-footer-iq">IQ</span></span></a><p>{html.escape(CONTENT['description'])}</p></div>{''.join(groups)}</div><div class="customer-footer-notice">© {datetime.now().year} CardIQ. {html.escape(CONTENT['notice'])}</div></div></footer><script src="{origin}/public-footer.js" defer></script>'''
