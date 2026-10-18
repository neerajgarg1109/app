#!/usr/bin/env python3
"""Regression checks for CardIQ's generated, indexable catalogue pages."""
import json
import os
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "frontend" / "build"
MANIFEST = json.loads((BUILD / "catalog-manifest.json").read_text())
CARD_IDS = MANIFEST["card_ids"]
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
    @classmethod
    def setUpClass(cls):
        cls.pages = generated_pages()
        cls.documents = {path: Document(path.read_text()) for path in cls.pages}

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
            self.assertIn('Product', source)
            self.assertNotRegex(source.lower(), r"likely to meet|guaranteed approval|approval odds")

    def test_titles_descriptions_and_canonicals_are_unique(self):
        titles = [doc.title for doc in self.documents.values()]
        descriptions = [doc.meta.get("description") for doc in self.documents.values()]
        canonicals = [doc.meta.get("canonical") for doc in self.documents.values()]
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
        robots = (BUILD / "robots.txt").read_text()
        self.assertIn(f"Sitemap: {ORIGIN}/sitemap.xml", robots)

    def test_methodology_discloses_sources_automation_and_revenue(self):
        source = (BUILD / "methodology" / "index.html").read_text().lower()
        for disclosure in ("sources and updates", "structured editorial assessment", "earn revenue", "cannot pay to increase"):
            self.assertIn(disclosure, source)

    def test_calculator_has_indexable_intent_and_honest_limitations(self):
        source = (BUILD / "calculator" / "index.html").read_text().lower()
        for phrase in ("credit card value calculator for india", "annual fees", "reward caps", "no login"):
            self.assertIn(phrase, source)
        self.assertIn(f'{ORIGIN}/#/calculator', source)

    def test_comparisons_are_substantial_editorial_pairs_with_deep_links(self):
        pages = list((BUILD / "compare").glob("*/index.html"))
        self.assertGreaterEqual(len(pages), 50)
        for path in pages:
            source = path.read_text()
            self.assertIn("Key decision", source)
            self.assertIn("Annual fee:", source)
            self.assertIn("Joining fee:", source)
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
        self.assertEqual({path.parent.name for path in pages}, {"new-credit-cards", "invite-only-credit-cards", "close-credit-card-india"})
        combined = " ".join(path.read_text().lower() for path in pages)
        for phrase in ("launch", "invitation-only", "close a credit card", "official closure channel"):
            self.assertIn(phrase, combined)

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
        self.assertIn("/app/catalog/", source)


if __name__ == "__main__":
    unittest.main()
