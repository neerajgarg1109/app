#!/usr/bin/env python3
"""Read-only audit of every sitemap URL in a generated CardIQ build."""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urlparse, unquote, urljoin
import xml.etree.ElementTree as ET


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.title = ''
        self.in_title = False
        self.canonicals = []
        self.description = []
        self.headings = 0
        self.links = []
        self.schemas = []
        self.json_text = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'title': self.in_title = True
        if tag == 'h1': self.headings += 1
        if tag == 'link' and a.get('rel') == 'canonical': self.canonicals.append(a.get('href'))
        if tag == 'meta' and a.get('name') == 'description': self.description.append(a.get('content', ''))
        if tag == 'a' and a.get('href'): self.links.append(a['href'])
        if tag == 'script' and a.get('type') == 'application/ld+json': self.json_text = ''

    def handle_data(self, data):
        if self.in_title: self.title += data
        if self.json_text is not None: self.json_text += data

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag == 'script' and self.json_text is not None:
            self.schemas.append(json.loads(self.json_text))
            self.json_text = None


def audit(build):
    urls = [node.text for node in ET.parse(build / 'sitemap.xml').findall('{*}url/{*}loc')]
    origin = urlparse(urls[0]).netloc
    errors, warnings, titles, descriptions = [], [], [], []
    linked_urls = set()
    def local_path(url):
        path = unquote(urlparse(url).path).lstrip('/')
        target = build / path
        return target / 'index.html' if not Path(path).suffix else target
    for url in urls:
        target = local_path(url)
        if not target.is_file():
            errors.append(f'Missing sitemap target: {url}')
            continue
        try: page = Page(target.read_text())
        except (ValueError, OSError) as e:
            errors.append(f'Invalid document or JSON-LD: {url}: {e}')
            continue
        if page.canonicals != [url]: errors.append(f'Canonical mismatch: {url}')
        if not page.title: errors.append(f'Missing title: {url}')
        if len(page.description) != 1 or not page.description[0]: errors.append(f'Missing/duplicate description: {url}')
        if page.headings != 1: errors.append(f'Expected one H1: {url}, found {page.headings}')
        if not page.schemas: errors.append(f'Missing structured data: {url}')
        if len(page.title) > 70: warnings.append(f'Long title ({len(page.title)} characters): {url}')
        titles.append(page.title)
        descriptions.extend(page.description)
        for link in page.links:
            resolved = urljoin(url, link).split('#', 1)[0].split('?', 1)[0]
            if resolved != url:
                linked_urls.add(resolved)
            parsed = urlparse(link)
            if parsed.scheme in ('mailto', 'tel') or parsed.netloc not in ('', origin) or parsed.fragment: continue
            if not local_path(link).is_file(): errors.append(f'Broken internal link in {url}: {link}')
    for label, values in [('title', titles), ('description', descriptions), ('sitemap URL', urls)]:
        for value, count in Counter(values).items():
            if count > 1: errors.append(f'Duplicate {label} ({count}): {value}')
    orphan_urls = sorted(set(urls) - linked_urls)
    errors.extend(f'No crawlable internal link to sitemap page: {url}' for url in orphan_urls)
    return {'sitemap_urls_checked': len(urls), 'orphan_urls': orphan_urls, 'errors': sorted(set(errors)), 'warnings': warnings}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=Path('frontend/build'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.build)
    output = json.dumps(result, indent=2) + '\n'
    if args.output: args.output.write_text(output)
    print(output)
    raise SystemExit(bool(result['errors']))
