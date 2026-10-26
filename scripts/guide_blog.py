"""Presentation for the static CardIQ journal; issuer facts stay in the generator."""
import html
import json
import math
import re
from pathlib import Path

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
    styles = (TEMPLATES / 'guide-blog.css').read_text()
    schema_json = json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c')
    og_type = 'website' if schema.get('@type') == 'Blog' else 'article'
    return f'''<!doctype html><html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><meta name="description" content="{escape(description)}"><link rel="canonical" href="{escape(canonical)}">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}"><meta property="og:url" content="{escape(canonical)}"><meta property="og:type" content="{og_type}"><meta name="twitter:card" content="summary">
<script type="application/ld+json">{schema_json}</script><style>{styles}</style></head><body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header wrap"><a class="brand" href="{origin}/"><span class="brand-mark">c</span>cardIQ<span class="brand-divider"></span><span class="brand-journal">Journal</span></a>
<nav aria-label="Page navigation"><button type="button" class="back-link" onclick="history.length &gt; 1 ? history.back() : location.href='{origin}/'">← Back</button><a href="{origin}/">Home</a><a href="{origin}/guides/" aria-current="page">Guides</a><a class="nav-cta" href="{origin}/#/cards">Browse cards <span aria-hidden="true">↗</span></a></nav></header>
<main id="main">{content}</main>
<footer class="site-footer wrap"><div><a class="brand" href="{origin}/">cardIQ</a><p>Clearer choices. Better-informed cardholders.</p></div><div><a href="{origin}/methodology/">Our editorial approach</a><a href="{origin}/#/help/issuers">Issuer help</a><a href="{origin}/#/cards">Card catalogue</a></div><p class="footer-note">Card facts are dated and linked to issuer sources. Eligibility and approval are decided by the issuing bank.</p></footer>{script}</body></html>'''


def article_card(post, featured=False):
    category, title, url = (escape(post[key]) for key in ('category', 'title', 'url'))
    data = f'data-topic="{category}" data-search="{escape(post["title"] + " " + post["description"] + " " + post["category"])}"'
    return f'''<article class="{'featured-post' if featured else 'post-card'}" {data}>
<a class="cover-link" href="{url}" aria-label="Read {title}">{cover(post)}</a>
<div class="post-card-content"><div class="article-meta"><span>{'Editor’s pick · ' if featured else ''}{category}</span><span>{minutes(post['body'])} min read</span></div>
<h{'2' if featured else '3'}><a href="{url}">{title}</a></h{'2' if featured else '3'}><p>{escape(post['description'])}</p>
<a class="read-link" href="{url}">Read the guide <span aria-hidden="true">↗</span></a></div></article>'''


def render_index(posts, origin, share):
    featured = next(post for post in posts if post['slug'] == 'best-cashback-credit-cards-india')
    ordered = [p for p in posts if p is not featured]
    categories = list(dict.fromkeys(post['category'] for post in posts))
    filters = '<button type="button" data-filter="all" aria-pressed="true">All articles</button>' + ''.join(f'<button type="button" data-filter="{escape(cat)}" aria-pressed="false">{escape(cat)}</button>' for cat in categories)
    cards = ''.join(article_card(post) for post in ordered)
    description = 'Practical credit card guides, thoughtful shortlists and clear explanations of fees, rewards and the fine print.'
    content = f'''<section class="journal-hero wrap"><p class="eyebrow">GUIDES, IDEAS & EXPLAINERS</p><h1>Good reads.<br><em>Better card decisions.</em></h1><p class="hero-description">{description}</p></section>
<div class="wrap journal-content"><section aria-label="Featured guide">{article_card(featured, True)}</section>
<section id="all-guides" class="article-library" aria-labelledby="library-title"><div class="library-heading"><div><p class="eyebrow">THE READING LIST</p><h2 id="library-title">Find your next good read</h2></div><label class="search-label"><span>Search guides</span><input type="search" id="guide-search" placeholder="Search a topic or issuer…" aria-label="Search guides"></label></div>
<div class="topic-filters" role="group" aria-label="Filter guides by topic">{filters}</div><p id="result-count" class="result-count" role="status" aria-live="polite">{len(posts)} guides to explore</p>
<div class="article-grid">{cards}</div><div id="no-results" class="empty-state" hidden><h3>No guides found</h3><p>Try another topic or issuer.</p><button type="button" id="reset-search">Show all guides</button></div></section>
<section class="editorial-note"><p class="eyebrow">A LITTLE CLARITY GOES A LONG WAY</p><h2>Useful advice, with the fine print.</h2><p>Our guides connect you to maintained card details and official issuer sources. Shortlists are editorial starting points, not approval promises or paid rankings.</p><a class="read-link" href="{origin}/methodology/">How we research cards <span aria-hidden="true">↗</span></a></section><div class="index-share">{share}</div></div>'''
    schema = {'@context': 'https://schema.org', '@type': 'Blog', 'name': 'CardIQ Journal', 'description': description, 'url': f'{origin}/guides/', 'blogPost': [{'@type': 'BlogPosting', 'headline': p['title'], 'url': p['url'], 'description': p['description']} for p in posts]}
    script = '<script>' + (TEMPLATES / 'guide-blog.js').read_text() + '</script>'
    return shell('Credit card guides & stories | CardIQ Journal', description, f'{origin}/guides/', content, origin, schema, script)


def render_article(post, posts, origin, share):
    body = re.sub(r'^<h1>.*?</h1><p>.*?</p>', '', post['body'], count=1, flags=re.S)
    related = [p for p in posts if p['slug'] != post['slug']]
    related.sort(key=lambda p: p['category'] != post['category'])
    related_cards = ''.join(article_card(p) for p in related[:3])
    content = f'''<article class="reading-wrap"><a class="breadcrumb" href="{origin}/guides/">← All guides</a><header class="article-header"><p class="eyebrow">{escape(post['category'])}</p><h1>{escape(post['title'])}</h1><p class="standfirst">{escape(post.get('standfirst', post['description']))}</p><div class="byline"><span class="author-mark">c</span><span>By <strong>CardIQ</strong></span><span>·</span><span>{minutes(post['body'])} min read</span></div></header><div class="prose">{body}</div>
<div class="article-next"><p>Ready to put this into practice?</p><a class="nav-cta" href="{escape(post['destination'])}">Explore in CardIQ <span aria-hidden="true">↗</span></a></div>{share}</article>
<section class="wrap related-posts" aria-labelledby="related-title"><p class="eyebrow">KEEP EXPLORING</p><h2 id="related-title">A few more good reads</h2><div class="article-grid">{related_cards}</div></section>'''
    schema = post.get('schema') or {'@context': 'https://schema.org', '@type': 'Article', 'headline': post['title'], 'description': post['description'], 'url': post['url'], 'inLanguage': 'en-IN', 'author': {'@type': 'Organization', 'name': 'CardIQ'}}
    return shell(post['title'] + ' | CardIQ Journal', post['description'], post['url'], content, origin, schema)
