#!/usr/bin/env python3
"""Regression checks for CardIQ's generated, indexable catalogue pages."""
import json
import html
import os
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from restricted_access import restricted_access
from financial_copy import fee_copy
BUILD = Path(os.environ.get("CARDIQ_BUILD_DIR", ROOT / "frontend" / "build"))
MANIFEST = json.loads((BUILD / "catalog-manifest.json").read_text())
CARD_IDS = MANIFEST["card_ids"]
CARDS_BY_ID = {card["id"]: card for card in json.loads((ROOT / "backend" / "cards_catalog.json").read_text())}
ORIGIN = os.environ.get("CARDIQ_PUBLIC_ORIGIN", MANIFEST["origin"]).rstrip("/")


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.meta = {}
        self.links = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "meta" and attrs.get("name"):
            self.meta[attrs["name"]] = attrs.get("content", "")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.meta["canonical"] = attrs.get("href", "")
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def generated_pages():
    roots = [BUILD / "cards", BUILD / "issuers", BUILD / "categories", BUILD / "catalog", BUILD / "methodology", BUILD / "calculator", BUILD / "compare", BUILD / "updates", BUILD / "lounges", BUILD / "restricted-cards", BUILD / "guides"]
    return [path for root in roots for path in root.glob("*/index.html")] + [root / "index.html" for root in roots if (root / "index.html").exists()]


class StaticCatalogTests(unittest.TestCase):
    def test_comparisons_and_catalog_lists_show_available_card_artwork(self):
        pages = list((BUILD / 'compare').glob('*/index.html'))
        self.assertGreater(len(pages), 0)
        for path in pages:
            source = path.read_text()
            schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', source, re.S)[1])
            products = [node for node in schema['@graph'] if node.get('@type') == 'FinancialProduct']
            self.assertEqual(len(products), 2)
            for product in products:
                card = CARDS_BY_ID[product['url'].rstrip('/').split('/')[-1]]
                if card.get('imageUrl'):
                    self.assertIn(html.escape(card['imageUrl'], quote=True), source)
        source = (BUILD / 'catalog' / 'index.html').read_text()
        for card in CARDS_BY_ID.values():
            if card.get('imageUrl'):
                self.assertIn(html.escape(card['imageUrl'], quote=True), source)

    def test_brand_fonts_do_not_block_first_render_or_use_css_import_chains(self):
        for path in self.pages + [BUILD / 'index.html']:
            source = path.read_text()
            self.assertNotIn('@import url(', source, path)
            self.assertIn('display=optional', source, path)
            self.assertRegex(source, r'<link[^>]+(?:media="print")[^>]+onload=', path)

    def test_three_reviewed_comparisons_have_examples_and_primary_sources(self):
        from comparison_editorial import REVIEWS
        for slug in REVIEWS:
            source = (BUILD / 'compare' / slug / 'index.html').read_text()
            self.assertIn('Worked spending examples', source)
            self.assertIn('Sources for this comparison', source)
            self.assertIn('Comparison terms reviewed', source)
            self.assertIn('before fees and taxes', source)

    def test_card_pages_expose_current_fees_access_and_context_without_javascript(self):
        for card_id, card in CARDS_BY_ID.items():
            source = (BUILD / 'cards' / card_id / 'index.html').read_text()
            self.assertIn(html.escape(fee_copy(card, 'joiningFee')), source, card_id)
            self.assertIn(html.escape(fee_copy(card)), source, card_id)
            self.assertIn('Fees and application requirements', source, card_id)
            self.assertIn('Continue your research', source, card_id)
            if card.get('imageUrl'):
                self.assertIn(f'src="{html.escape(card["imageUrl"], quote=True)}"', source, card_id)
            access = restricted_access(card)
            if access:
                self.assertIn(html.escape(access['accessExplanation']), source, card_id)

    def test_decision_guides_add_distinct_questions_and_clear_examples(self):
        for topic in ('cashback', 'lifetime-free', 'travel', 'fuel', 'rupay-upi', 'first'):
            guide_slug = 'best-rupay-upi-credit-cards-india' if topic == 'rupay-upi' else f'best-{topic}-credit-cards-india'
            source = (BUILD / 'guides' / guide_slug / 'index.html').read_text()
            self.assertIn('A practical comparison', source)
            self.assertIn(f'href="{ORIGIN}/methodology/">', source)
        cashback = (BUILD / 'guides/best-cashback-credit-cards-india/index.html').read_text()
        self.assertIn('Hypothetical example', cashback)
        self.assertIn('not an offer from a listed card', cashback)

    def test_shortlists_require_positive_benefits_and_unconditional_free_fees(self):
        cashback = Document((BUILD / 'guides/best-cashback-credit-cards-india/index.html').read_text())
        for link in cashback.links:
            if f'{ORIGIN}/cards/' in link:
                card_id = link.split('/cards/', 1)[1].strip('/')
                self.assertIn('cashback', CARDS_BY_ID[card_id].get('bestFor', []))
        free = Document((BUILD / 'guides/best-lifetime-free-credit-cards-india/index.html').read_text())
        for link in free.links:
            if f'{ORIGIN}/cards/' in link:
                card = CARDS_BY_ID[link.split('/cards/', 1)[1].strip('/')]
                self.assertEqual(card['joiningFeeAmount'], 0)
                self.assertEqual(card['annualFeeAmount'], 0)
                self.assertNotIn('current', card['annualFee'].lower())

    def test_closure_hub_links_to_every_issuer_without_mixing_editorial_topics(self):
        hub = (BUILD / 'guides/close-credit-card-india/index.html').read_text()
        for path in (BUILD / 'guides').glob('close-*/index.html'):
            if path.parent.name != 'close-credit-card-india':
                self.assertIn(f'{ORIGIN}/guides/{path.parent.name}/', hub)

    def test_conditional_free_new_cards_are_excluded_from_lifetime_free_category(self):
        source = (BUILD / "categories/lifetime-free/index.html").read_text()
        for card_id in ("pnb-kiwi-credit-card", "sbm-niyo-global-credit-card"):
            self.assertNotIn(f'/cards/{card_id}/', source)

    @classmethod
    def setUpClass(cls):
        cls.pages = generated_pages()
        cls.documents = {path: Document(path.read_text()) for path in cls.pages}

    def test_guides_prioritizes_curated_comparisons_and_unique_factual_excerpts(self):
        from comparison_engine import TOP_COMPARISONS, comparison_excerpt
        source = (BUILD / 'guides/index.html').read_text()
        cards = re.findall(r'<article class="post-card".*?</article>', source, re.S)
        self.assertGreater(len(cards), 20)
        for card, priority in zip(cards[:20], TOP_COMPARISONS):
            self.assertIn('/compare/' + priority['slug'] + '/', card)
            self.assertIn('Popular Comparison', card)
        self.assertNotIn('Popular Comparison', ''.join(cards[20:]))
        snippets = []
        for row in TOP_COMPARISONS:
            excerpt = comparison_excerpt(CARDS_BY_ID[row['cardA']], CARDS_BY_ID[row['cardB']])
            self.assertIn(html.escape(excerpt), source)
            self.assertIn('annual fee', excerpt)
            self.assertNotIn('See dated issuer sources and a spending scenario', excerpt)
            snippets.append(excerpt)
        self.assertEqual(len(set(snippets)), 20)
        self.assertNotIn('/#/updates', source)
        self.assertNotIn('/#/restricted-cards', source)
        hydration = (BUILD / 'public-footer.js').read_text()
        self.assertIn("'/updates': '/guides/new-credit-cards/'", hydration)
        self.assertIn("'/restricted-cards': '/guides/invite-only-credit-cards/'", hydration)

    def test_card_pages_have_tracked_placements_and_complete_matching_comparisons(self):
        from urllib.parse import parse_qs
        comparison_urls = MANIFEST['comparison_urls']
        from comparison_engine import TOP_COMPARISONS
        priority = [ORIGIN + '/compare/' + row['slug'] + '/' for row in TOP_COMPARISONS]
        for card_id in CARD_IDS:
            source = (BUILD / 'cards' / card_id / 'index.html').read_text()
            document = Document(source)
            apply = [link for link in document.links if '/go/' in link]
            if apply:
                placements = [parse_qs(urlparse(link).query) for link in apply]
                self.assertEqual({p['subid'][0] for p in placements}, {'card_page_hero','card_page_verdict','card_page_sticky'})
                self.assertTrue(all(p['source'] == [card_id] for p in placements))
                self.assertEqual(source.count('rel="sponsored nofollow noopener" target="_blank"'), 3)
            else:
                self.assertIn('Explore secured and first-card alternatives', source)
            self.assertIn('/calculator/?card=' + card_id, source)
            matching = []
            for url in comparison_urls:
                path = BUILD / urlparse(url).path.strip('/') / 'index.html'
                graph = re.search(r'<script type="application/ld\+json">(.*?)</script>',path.read_text(),re.S).group(1)
                products = [n for n in json.loads(graph)['@graph'] if n['@type']=='FinancialProduct']
                if any('/cards/' + card_id + '/' in n.get('url','') for n in products): matching.append(url)
            links = [link for link in document.links if link in comparison_urls]
            self.assertEqual(set(links), set(matching), card_id)
            self.assertEqual([link for link in links if link in priority], [link for link in priority if link in matching], card_id)
        sbi = (BUILD / 'cards/sbi-cashback-sbi/index.html').read_text()
        for pair in ('sbi-cashback-vs-hdfc-millennia', 'sbi-cashback-vs-amazon-pay-icici', 'rbl-jalsa-vs-sbi-cashback-sbi'):
            self.assertIn('/compare/' + pair + '/', sbi)

    def test_homepage_prerenders_shared_copy_and_every_page_discloses_affiliates(self):
        copy = json.loads((ROOT / 'frontend/src/data/homeCopy.json').read_text())
        footer = json.loads((ROOT / 'frontend/src/data/footerContent.json').read_text())
        source = (BUILD / 'index.html').read_text()
        self.assertIn('<h1>' + html.escape(copy['headline']) + '</h1>', source)
        self.assertIn(str(len(CARD_IDS)) + ' Indian credit cards', source)
        self.assertIn(copy['primaryCta'], source)
        self.assertIn(copy['secondaryCta'], source)
        for tool in copy['tools']:
            self.assertIn(html.escape(tool['title']), source)
        for path in self.pages + [BUILD / 'index.html']:
            text = path.read_text()
            self.assertIn(html.escape(footer['transparency']['body']), text, path)
            self.assertLess(text.index('Our Editorial &amp; Financial Transparency'), text.index('<footer'), path)
        for path in (BUILD / 'compare').glob('*/index.html'):
            text = path.read_text()
            self.assertIn('Estimated annual rewards (₹ equivalent)', text)
            self.assertNotIn('100% approval-rate FD cards', text)
            self.assertNotIn('Cash in Pocket', text)

    def test_comparison_index_priority_order_and_list_application_links(self):
        from comparison_engine import TOP_COMPARISONS
        from urllib.parse import parse_qs
        source = (BUILD / 'compare/index.html').read_text()
        listing = re.search(r'<ul>(.*?)</ul>', source, re.S).group(1)
        links = Document(listing).links
        self.assertEqual(links[:20], [ORIGIN + '/compare/' + row['slug'] + '/' for row in TOP_COMPARISONS])
        for path in self.pages:
            relative = path.relative_to(BUILD).as_posix()
            if not relative.startswith(('catalog/', 'categories/', 'issuers/', 'guides/')):
                continue
            for article in re.findall(r'<article class="card">.*?</article>', path.read_text(), re.S):
                if '<strong>Annual fee:</strong>' not in article:
                    continue
                self.assertIn('View details', article, relative)
                if 'Applications closed' in article:
                    continue
                apply = next(link for link in Document(article).links if '/go/' in link)
                query = parse_qs(urlparse(apply).query)
                self.assertEqual(query['subid'], ['list_card'])
                self.assertTrue(query['source'][0])
                self.assertIn('rel="sponsored nofollow noopener" target="_blank"', article)

    def test_every_generated_page_has_the_complete_shared_main_menu(self):
        items = json.loads((ROOT / "frontend/src/data/mainNavigation.json").read_text())
        expected = {ORIGIN + ("/" if item["to"] == "/" else "/#" + item["to"]) if item.get("to") else ORIGIN + item["href"] for item in items}
        expected -= {ORIGIN + '/#' + route for route in ('/updates', '/restricted-cards', '/cards', '/cards?mode=compare', '/calculator')}
        expected |= {ORIGIN + route for route in ('/guides/new-credit-cards/', '/guides/invite-only-credit-cards/', '/catalog/', '/compare/', '/calculator/')}
        for path in self.pages:
            matches = re.findall(r'<nav[^>]*aria-label="Main navigation"[^>]*>(.*?)</nav>', path.read_text(), re.S)
            self.assertEqual(len(matches), 1, path)
            self.assertEqual(set(Document(matches[0]).links), expected, path)

    def test_every_generated_page_has_the_same_complete_footer(self):
        content = json.loads((ROOT / "frontend/src/data/footerContent.json").read_text())
        from public_footer import destination
        expected = {ORIGIN + "/"} | {destination(ORIGIN, link["url"]) for group in content["groups"] for link in group["links"]}
        for path in self.pages:
            source = path.read_text()
            footers = re.findall(r'<footer[^>]*aria-label="Site footer"[^>]*>(.*?)</footer>', source, re.S)
            self.assertEqual(len(footers), 1, path)
            self.assertEqual(set(Document(footers[0]).links), expected, path)
            self.assertIn(content["description"], footers[0], path)
            self.assertIn(content["notice"], footers[0], path)
            self.assertIn('.customer-footer .customer-footer-grid', source, path)
            self.assertIn(f'src="{ORIGIN}/public-footer.js"', source, path)
        self.assertTrue((BUILD / "public-footer.js").exists())

    def test_every_card_has_substantial_sourced_editorial_content(self):
        pages = list((BUILD / "cards").glob("*/index.html"))
        self.assertEqual({path.parent.name for path in pages}, set(CARD_IDS))
        for path in pages:
            source = path.read_text()
            self.assertIn("CardIQ editorial view", source)
            self.assertIn("Our take", source)
            self.assertIn("Who it suits", source)
            self.assertIn("Trade-offs to understand", source)
            self.assertIn("CardIQ verdict", source)
            self.assertIn("Issuer source", source)
            self.assertIn('application/ld+json', source)
            self.assertIn('BreadcrumbList', source)
            self.assertIn('CreditCard', source)
            self.assertNotIn('\"@type\": \"Product\"', source)
            self.assertNotRegex(source.lower(), r"likely to meet|guaranteed approval|approval odds")

    def test_titles_descriptions_and_canonicals_are_unique(self):
        canonical_docs = [doc for path, doc in self.documents.items() if doc.meta["canonical"] == f"{ORIGIN}/{path.parent.relative_to(BUILD).as_posix()}/"]
        titles = [doc.title for doc in canonical_docs]
        descriptions = [doc.meta.get("description") for doc in canonical_docs]
        canonicals = [doc.meta.get("canonical") for doc in canonical_docs]
        self.assertNotIn("", titles + descriptions + canonicals)
        self.assertEqual(len(titles), len(set(titles)))
        self.assertEqual(len(descriptions), len(set(descriptions)))
        self.assertEqual(len(canonicals), len(set(canonicals)))
        self.assertTrue(all(url.startswith(f"{ORIGIN}/") and "#" not in url for url in canonicals))

    def test_catalog_hub_links_to_every_indexable_detail_page(self):
        hub = Document((BUILD / "catalog" / "index.html").read_text())
        expected = {doc.meta["canonical"] for path, doc in self.documents.items() if "/cards/" in doc.meta["canonical"] or "/issuers/" in doc.meta["canonical"] or "/categories/" in doc.meta["canonical"]}
        self.assertTrue(expected.issubset(set(hub.links)))

    def test_every_published_category_contains_multiple_real_choices(self):
        for path in (BUILD / "categories").glob("*/index.html"):
            card_links = {link for link in self.documents[path].links if f"{ORIGIN}/cards/" in link}
            self.assertGreaterEqual(len(card_links), 3, path)

    def test_sitemap_and_robots_cover_generated_pages(self):
        sitemap = (BUILD / "sitemap.xml").read_text()
        for doc in self.documents.values():
            self.assertIn(f"<loc>{doc.meta['canonical']}</loc>", sitemap)
        locations = re.findall(r"<loc>([^<]+)</loc>", sitemap)
        self.assertEqual(len(locations), len(set(locations)))
        robots = (BUILD / "robots.txt").read_text()
        self.assertIn(f"Sitemap: {ORIGIN}/sitemap.xml", robots)

    def test_generated_internal_links_resolve_to_generated_pages(self):
        generated = {document.meta["canonical"] for document in self.documents.values()}
        generated.add(f"{ORIGIN}/")
        for path, document in self.documents.items():
            for link in document.links:
                if link.startswith(f"{ORIGIN}/") and "#" not in link:
                    if urlparse(link).path.startswith('/go/'):
                        target = BUILD / urlparse(link).path.strip('/') / 'index.html'
                        self.assertTrue(target.is_file(), link)
                        self.assertIn('noindex,nofollow', target.read_text())
                    else:
                        self.assertIn(link.split("?", 1)[0], generated, f"Broken generated link in {path}: {link}")

    def test_methodology_discloses_sources_automation_and_revenue(self):
        source = (BUILD / "methodology" / "index.html").read_text().lower()
        for disclosure in ("sources and updates", "structured editorial assessment", "earn revenue", "cannot pay to increase"):
            self.assertIn(disclosure, source)

    def test_calculator_has_indexable_intent_and_honest_limitations(self):
        source = (BUILD / "calculator" / "index.html").read_text().lower()
        for phrase in ("credit card value calculator for india", "annual fees", "reward caps", "no login"):
            self.assertIn(phrase, source)
        self.assertIn(f'{ORIGIN}/#/calculator', source)
        self.assertIn('title="cardiq credit card value calculator"', source)
        self.assertIn(f'src="{ORIGIN}/#/calculator?embedded=1"', source)
        self.assertIn('scrolling="no"', source)
        self.assertIn("resizeobserver", source)
        self.assertIn("open the calculator in a full page", source)

    def test_comparisons_are_substantial_editorial_pairs_with_deep_links(self):
        pages = list((BUILD / "compare").glob("*/index.html"))
        self.assertGreaterEqual(len(pages), 50)
        for path in pages:
            source = path.read_text()
            self.assertIn("Key decision", source)
            self.assertIn("Renewal fee + GST", source)
            self.assertIn("Joining fee + GST", source)
            self.assertIn("CardIQ view", source)
            self.assertIn("#/cards?compare=", source)
            self.assertIn('"@type": "ItemList"', source)

    def test_updates_distinguish_verification_from_launch_dates(self):
        pages = list((BUILD / "updates").glob("*/index.html"))
        self.assertGreaterEqual(len(pages), 1)
        for path in pages:
            source = path.read_text().lower()
            self.assertIn("verification date", source)
            self.assertIn("not necessarily a product launch", source)

    def test_lounge_hub_explains_access_limits(self):
        source = (BUILD / "lounges" / "index.html").read_text().lower()
        for phrase in ("airport lounge credit cards", "airport", "terminal", "spend thresholds", "issuer terms"):
            self.assertIn(phrase, source)

    def test_restricted_hub_separates_discovery_from_eligibility(self):
        source = (BUILD / "restricted-cards" / "index.html").read_text().lower()
        for phrase in ("invite-only", "restricted", "excluded from cardiq’s general quiz", "does not guarantee approval", "issuing bank decides"):
            self.assertIn(phrase, source)
        self.assertIn(f'{ORIGIN}/#/restricted-cards', source)

    def test_guides_cover_high_intent_discovery_journeys(self):
        pages = list((BUILD / "guides").glob("*/index.html"))
        slugs = {path.parent.name for path in pages}
        expected = {
            "new-credit-cards", "invite-only-credit-cards", "close-credit-card-india",
            "best-cashback-credit-cards-india", "best-lifetime-free-credit-cards-india",
            "best-travel-credit-cards-india", "best-fuel-credit-cards-india",
            "best-rupay-upi-credit-cards-india", "best-first-credit-cards-india",
        }
        self.assertTrue(expected.issubset(slugs))
        combined = " ".join(path.read_text().lower() for path in pages)
        for phrase in ("launch", "invitation-only", "close a credit card", "official closure channel"):
            self.assertIn(phrase, combined)

    def test_every_guide_has_an_explicit_home_link(self):
        pages = [BUILD / "guides" / "index.html", *(BUILD / "guides").glob("*/index.html")]
        self.assertGreater(len(pages), 1)
        for path in pages:
            source = path.read_text()
            self.assertIn("← Back", source, path)
            self.assertIn(">Home</a>", source, path)
            self.assertIn(f'href="{ORIGIN}/"', source, path)

    def test_journal_lists_editorial_guides_without_closure_articles(self):
        path = BUILD / "guides" / "index.html"
        source = path.read_text()
        schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', source, re.S).group(1))
        self.assertEqual(schema["@type"], "Blog")
        expected = {f"{ORIGIN}/guides/{page.parent.name}/" for page in (BUILD / "guides").glob("*/index.html") if not page.parent.name.startswith("close-")}
        expected |= {self.documents[page].meta["canonical"] for page in (BUILD / "compare").glob("*/index.html")}
        self.assertEqual({post["url"] for post in schema["blogPost"]}, expected)
        self.assertTrue(expected.issubset(set(self.documents[path].links)))
        self.assertEqual(source.count("<h1>"), 1)
        self.assertIn('aria-label="Search guides"', source)
        self.assertIn('aria-label="Filter guides by topic"', source)
        self.assertIn('aria-live="polite"', source)

    def test_invite_only_page_includes_infinia_and_excludes_relationship_cards(self):
        source = (BUILD / "restricted-cards" / "index.html").read_text()
        self.assertIn('HDFC Bank INFINIA Metal Edition', source)
        self.assertNotIn('HSBC Premier', source)
        self.assertNotIn('Shaurya SBI Card', source)

    def test_article_metadata_identifies_author_publisher_and_page(self):
        for path in (BUILD / "guides").glob("*/index.html"):
            source = path.read_text()
            schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', source, re.S).group(1))
            articles = [node for node in schema.get("@graph", [schema]) if node.get("@type") == "Article"]
            self.assertTrue(articles, path)
            for node in articles:
                self.assertEqual(node["author"]["url"], f"{ORIGIN}/methodology/")
                self.assertEqual(node["publisher"]["name"], "CardIQ")
                self.assertEqual(node["mainEntityOfPage"]["@id"], self.documents[path].meta["canonical"])
            self.assertIn('property="og:type" content="article"', source)

    def test_article_library_is_visible_before_news(self):
        source = (BUILD / "guides" / "index.html").read_text()
        self.assertLess(source.index('id="all-guides"'), source.index('class="top-news"'))
        self.assertIn('All articles &amp; guides', source)
        self.assertIn('data-filter="Card comparisons"', source)
        self.assertIn('Read the comparison', source)
        self.assertGreaterEqual(source.count('class="post-card" data-topic='), 8)

    def test_journal_articles_have_one_heading_and_related_reading(self):
        for path in (BUILD / "guides").glob("*/index.html"):
            source = path.read_text()
            self.assertEqual(source.count("<h1>"), 1, path)
            self.assertIn('class="reading-wrap"', source)
            self.assertIn('aria-labelledby="related-title"', source)
            self.assertIn("min read", source)
            self.assertIn("← Close a card" if path.parent.name.startswith("close-") else "← All guides", source)

    def test_best_card_guides_are_sourced_substantial_and_not_paid_rankings(self):
        pages = list((BUILD / "guides").glob("best-*/index.html"))
        self.assertGreaterEqual(len(pages), 6)
        for path in pages:
            source = path.read_text()
            document = self.documents[path]
            card_links = {link for link in document.links if f"{ORIGIN}/cards/" in link}
            self.assertGreaterEqual(len(card_links), 3, path)
            for link in card_links:
                card_id = link.split("/cards/", 1)[1].strip("/")
                card = CARDS_BY_ID[card_id]
                self.assertTrue(card.get("active", True), card_id)
                self.assertTrue(card.get("applicationsOpen", True), card_id)
                self.assertIsNone(restricted_access(card), card_id)
            self.assertIn("How to choose", source)
            self.assertIn("Check before applying", source)
            self.assertIn("not from best to worst", source)
            self.assertIn("No issuer can pay to improve its position", source)
            self.assertIn('"@type": "ItemList"', source)

    def test_verified_issuers_have_specific_credit_card_closure_guides(self):
        support = json.loads((ROOT / "frontend" / "src" / "data" / "issuerSupport.json").read_text())
        for issuer in support:
            slug = "close-" + "-".join(part for part in "".join(char.lower() if char.isalnum() else " " for char in issuer["issuer"]).split()) + "-credit-card"
            source = (BUILD / "guides" / slug / "index.html").read_text().lower()
            self.assertIn("before requesting closure", source)
            self.assertIn("official customer support", source)
            self.assertIn(issuer["supportUrl"].lower(), source)
            self.assertIn("blocking a card is not the same as closing", source)

    def test_every_public_page_has_social_sharing_for_its_canonical_url(self):
        for path, document in self.documents.items():
            source = path.read_text()
            encoded = document.meta["canonical"].replace(":", "%3A").replace("/", "%2F")
            self.assertIn("https://wa.me/", source)
            self.assertIn("https://twitter.com/intent/tweet", source)
            self.assertIn("https://www.facebook.com/sharer/sharer.php", source)
            self.assertIn(encoded, source)

    def test_homepage_has_canonical_metadata_and_a_non_javascript_catalogue_path(self):
        source = (BUILD / "index.html").read_text()
        document = Document(source)
        self.assertEqual(document.meta.get("canonical"), f"{ORIGIN}/")
        self.assertIn(f'href="{ORIGIN}/catalog/"', source)


if __name__ == "__main__":
    unittest.main()
