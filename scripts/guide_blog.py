"""Presentation for the static CardIQ journal; issuer facts stay in the generator."""
import html
import json
import math
import re
from datetime import date
from pathlib import Path
from public_navigation import CSS as MAIN_NAV_CSS, render_navigation
from public_footer import CSS as FOOTER_CSS, render_footer

TEMPLATES = Path(__file__).with_name('templates')


def escape(value):
    return html.escape(str(value), quote=True)


def minutes(body):
    return max(1, math.ceil(len(re.sub('<[^>]+>', ' ', body).split()) / 200))


def theme(post):
    for key in ('cashback', 'travel', 'fuel', 'rupay', 'first', 'lifetime', 'close', 'invite'):
        if key in post['slug']:
            return key
    return 'updates'


def cover(post):
    labels = {'cashback': 'Everyday rewards', 'travel': 'Miles & moments', 'fuel': 'Everyday journeys', 'rupay': 'Pay your way', 'first': 'A fresh start', 'lifetime': 'Less fee. More value.', 'close': 'A clean slate', 'invite': 'Beyond the invitation', 'updates': 'What’s changing'}
    return f'<div class="cover cover--{theme(post)}" aria-hidden="true"><span class="cover-kicker">THE CARDIQ JOURNAL</span><div class="cover-orbit"></div><div class="cover-card cover-card--back"></div><div class="cover-card cover-card--front"><span class="cover-chip"></span><span>{labels[theme(post)]}</span><i>cardIQ</i></div></div>'


def shell(title, description, canonical, content, origin, schema, script=''):
    styles = (TEMPLATES / 'guide-blog.css').read_text() + MAIN_NAV_CSS + FOOTER_CSS
    schema_json = json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c')
    nodes = schema.get('@graph', [schema])
    og_type = 'article' if any(node.get('@type') in ('Article', 'BlogPosting', 'NewsArticle') for node in nodes) else 'website'
    return f'''<!doctype html><html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{origin}/favicon.ico" sizes="any"><link rel="icon" type="image/svg+xml" href="{origin}/favicon.svg"><link rel="icon" type="image/png" sizes="48x48" href="{origin}/favicon-48.png"><link rel="apple-touch-icon" sizes="180x180" href="{origin}/apple-touch-icon.png">
<title>{escape(title)}</title><meta name="description" content="{escape(description)}"><link rel="canonical" href="{escape(canonical)}">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}"><meta property="og:url" content="{escape(canonical)}"><meta property="og:type" content="{og_type}"><meta name="twitter:card" content="summary">
<script type="application/ld+json">{schema_json}</script><style>{styles}</style></head><body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header wrap"><a class="brand" href="{origin}/"><span class="brand-mark">c</span>cardIQ<span class="brand-divider"></span><span class="brand-journal">Journal</span></a>
<button type="button" class="back-link" onclick="history.length &gt; 1 ? history.back() : location.href='{origin}/'">← Back</button></header>{render_navigation(origin, canonical, journal=True)}
<main id="main">{content}</main>
{render_footer(origin)}{script}</body></html>'''


def article_card(post, featured=False):
    category, title, url = (escape(post[key]) for key in ('category', 'title', 'url'))
    read_label = 'Read the comparison' if post['category'] == 'Card comparisons' else 'Read the guide'
    data = f'data-topic="{category}" data-search="{escape(post["title"] + " " + post["description"] + " " + post["category"])}"'
    return f'''<article class="{'featured-post' if featured else 'post-card'}" {data}>
<a class="cover-link" href="{url}" aria-label="Read {title}">{cover(post)}</a>
<div class="post-card-content"><div class="article-meta"><span>{'Editor’s pick · ' if featured else ''}{category}</span><span>{minutes(post['body'])} min read</span></div>
<h{'2' if featured else '3'}><a href="{url}">{title}</a></h{'2' if featured else '3'}><p>{escape(post['description'])}</p>
<a class="read-link" href="{url}">{read_label} <span aria-hidden="true">↗</span></a></div></article>'''


def news_section(origin):
    news_path = TEMPLATES.parents[1] / 'frontend/src/data/cardNews.json'
    items = [item for item in json.loads(news_path.read_text()) if item.get('active') is True]
    items.sort(key=lambda item: item['verifiedOn'], reverse=True)
    cards = []
    for item in items[:6]:
        checked = date.fromisoformat(item['verifiedOn'])
        label = checked.strftime('%d %B %Y').lstrip('0')
        post = {'slug': item['id']}
        cards.append(f'''<article class="post-card news-card"><a class="cover-link" href="{escape(item['sourceUrl'])}" target="_blank" rel="noopener noreferrer" aria-label="Read official source: {escape(item['headline'])}">{cover(post)}</a>
<div class="post-card-content"><div class="article-meta"><span>{escape(item['statusLabel'])}</span><time datetime="{checked.isoformat()}">Verified {label}</time></div><h3><a href="{escape(item['sourceUrl'])}" target="_blank" rel="noopener noreferrer">{escape(item['headline'])}</a></h3><p>{escape(item['summary'])}</p><p class="news-caveat">{escape(item['availabilityNote'])}</p><a class="read-link" href="{escape(item['sourceUrl'])}" target="_blank" rel="noopener noreferrer">Read at {escape(item['sourceLabel'])} <span aria-hidden="true">↗</span></a></div></article>''')
    if not cards:
        return ''
    return f'''<section class="top-news" aria-labelledby="news-title"><div class="news-heading"><div><p class="eyebrow">THE LATEST FROM ISSUERS</p><h2 id="news-title">Top News <span>&amp; Offers</span></h2><p>Card announcements, benefit changes and offers, with official sources.</p></div><a class="read-link" href="{origin}/#/updates">View all updates <span aria-hidden="true">→</span></a></div><div class="article-grid">{''.join(cards)}</div><p class="news-disclosure">Dates show when CardIQ checked the source. Availability and offer eligibility remain subject to issuer terms.</p></section>'''


def render_index(posts, origin, share):
    posts = [post for post in posts if post['category'] != 'Card management']
    ordered = sorted(posts, key=lambda post: post['category'] != 'Choosing a card')
    categories = list(dict.fromkeys(post['category'] for post in posts))
    filters = '<button type="button" data-filter="all" aria-pressed="true">All articles</button>' + ''.join(f'<button type="button" data-filter="{escape(cat)}" aria-pressed="false">{escape(cat)}</button>' for cat in categories)
    cards = ''.join(article_card(post) for post in ordered)
    description = 'Practical credit card guides, thoughtful shortlists and clear explanations of fees, rewards and the fine print.'
    content = f'''<section class="journal-hero wrap"><p class="eyebrow">THE CARDIQ JOURNAL</p><h1>News, offers <span>&amp; insights</span></h1><p class="hero-description">{description}</p></section>
<div class="wrap journal-content">
<section id="all-guides" class="article-library" aria-labelledby="library-title"><div class="library-heading"><div><p class="eyebrow">THE FULL CARDIQ LIBRARY</p><h2 id="library-title">All articles &amp; guides</h2></div><label class="search-label"><span>Search guides</span><input type="search" id="guide-search" placeholder="Search a topic or issuer…" aria-label="Search guides"></label></div>
<div class="topic-filters" role="group" aria-label="Filter guides by topic">{filters}</div><p id="result-count" class="result-count" role="status" aria-live="polite">{len(posts)} articles to explore</p>
<div class="article-grid">{cards}</div><div id="no-results" class="empty-state" hidden><h3>No guides found</h3><p>Try another topic or issuer.</p><button type="button" id="reset-search">Show all guides</button></div></section>
{news_section(origin)}
<section class="editorial-note"><p class="eyebrow">A LITTLE CLARITY GOES A LONG WAY</p><h2>Useful advice, with the fine print.</h2><p>Our guides connect you to maintained card details and official issuer sources. Shortlists are editorial starting points, not approval promises or paid rankings.</p><a class="read-link" href="{origin}/methodology/">How we research cards <span aria-hidden="true">↗</span></a></section><div class="index-share">{share}</div></div>'''
    schema = {'@context': 'https://schema.org', '@type': 'Blog', 'name': 'CardIQ Journal', 'description': description, 'url': f'{origin}/guides/', 'blogPost': [{'@type': 'BlogPosting', 'headline': p['title'], 'url': p['url'], 'description': p['description']} for p in posts]}
    script = '<script>' + (TEMPLATES / 'guide-blog.js').read_text() + '</script>'
    return shell('Credit Card Guides & Comparisons in India | CardIQ', description, f'{origin}/guides/', content, origin, schema, script)


def render_article(post, posts, origin, share):
    body = re.sub(r'^<h1>.*?</h1><p>.*?</p>', '', post['body'], count=1, flags=re.S)
    closing = post['category'] == 'Card management'
    if post['slug'] == 'close-credit-card-india':
        issuer_guides = [p for p in posts if p['category'] == 'Card management' and p['slug'] != post['slug']]
        body += '<h2>Find your issuer’s closure guide</h2><ul>' + ''.join(
            f'<li><a href="{escape(p["url"])}">{escape(p["title"])}</a></li>' for p in issuer_guides
        ) + '</ul>'
    back_url = f'{origin}/#/help/issuers' if closing else f'{origin}/guides/'
    back_label = '← Close a card' if closing else '← All guides'
    related = [p for p in posts if p['slug'] != post['slug'] and (p['category'] == 'Card management') == closing]
    related.sort(key=lambda p: p['category'] != post['category'])
    related_cards = ''.join(article_card(p) for p in related[:3])
    content = f'''<article class="reading-wrap"><a class="breadcrumb" href="{back_url}">{back_label}</a><header class="article-header"><p class="eyebrow">{escape(post['category'])}</p><h1>{escape(post['title'])}</h1><p class="standfirst">{escape(post.get('standfirst', post['description']))}</p><div class="byline"><span class="author-mark">c</span><span>By <a href="{origin}/methodology/"><strong>CardIQ editorial</strong></a></span><span>·</span><span>{minutes(post['body'])} min read</span></div></header><div class="prose">{body}</div>
<div class="article-next"><p>Ready to put this into practice?</p><a class="nav-cta" href="{escape(post['destination'])}">Explore in CardIQ <span aria-hidden="true">↗</span></a></div>{share}</article>
<section class="wrap related-posts" aria-labelledby="related-title"><p class="eyebrow">KEEP EXPLORING</p><h2 id="related-title">A few more good reads</h2><div class="article-grid">{related_cards}</div></section>'''
    schema = post.get('schema') or {'@context': 'https://schema.org', '@type': 'Article', 'headline': post['title'], 'description': post['description'], 'url': post['url'], 'inLanguage': 'en-IN', 'author': {'@type': 'Organization', 'name': 'CardIQ'}}
    nodes = schema.get('@graph', [schema])
    for node in nodes:
        if node.get('@type') in ('Article', 'BlogPosting', 'NewsArticle'):
            node.setdefault('author', {'@type': 'Organization', 'name': 'CardIQ', 'url': f'{origin}/methodology/'})
            node['author'].setdefault('url', f'{origin}/methodology/')
            node.setdefault('publisher', {'@type': 'Organization', 'name': 'CardIQ', 'url': f'{origin}/'})
            node.setdefault('mainEntityOfPage', {'@type': 'WebPage', '@id': post['url']})
            node.setdefault('inLanguage', 'en-IN')
    return shell(post['title'] + ' | CardIQ Guides', post['description'], post['url'], content, origin, schema)
