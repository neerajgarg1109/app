"""External, read-only production checks. Failures intentionally fail the Actions run."""
import os
import re
import sys
import urllib.request
import urllib.parse


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'CardIQ-Availability-Check/1'})
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError('Unexpected HTTP status')
        return response.read()


def check(site, api):
    import json
    for origin in (site, api):
        if urllib.parse.urlparse(origin).scheme != 'https':
            raise ValueError('Monitoring requires HTTPS origins')
    html = fetch(site + '/').decode()
    assets = re.findall(r'(?:src|href)="([^\"]+/static/[^\"]+|/static/[^\"]+)"', html)
    if not assets:
        raise RuntimeError('Website has no production assets')
    for asset in assets:
        url = urllib.parse.urljoin(site + '/', asset)
        if urllib.parse.urlparse(url).netloc != urllib.parse.urlparse(site).netloc:
            raise RuntimeError('Unexpected asset origin')
        fetch(url)
    if json.loads(fetch(api + '/api/ready')).get('status') != 'ready':
        raise RuntimeError('API/database not ready')
    cards = json.loads(fetch(api + '/api/cards?view=summary'))
    if not isinstance(cards, list) or not cards:
        raise RuntimeError('Catalogue unavailable')
    if not any(card.get('applicationsOpen') is not False for card in cards):
        raise RuntimeError('No available cards')
    print('Website assets, TLS, API/database readiness and catalogue checks passed.')


if __name__ == '__main__':
    try:
        check(os.environ.get('CARDIQ_SITE_URL', 'https://findmybest.cards').rstrip('/'),
              os.environ.get('CARDIQ_API_URL', 'https://api.findmybest.cards').rstrip('/'))
    except Exception as error:
        print('Availability check failed: ' + type(error).__name__, file=sys.stderr)
        sys.exit(1)
