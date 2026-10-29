"""Exercise crawl discovery checks against a small disposable generated site."""
import tempfile
import unittest
from pathlib import Path

from audit_seo import audit


class CrawlDiscoveryTests(unittest.TestCase):
    def check_site(self, home_links):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            urls = ['https://cardiq.test/', 'https://cardiq.test/research/']
            root.joinpath('sitemap.xml').write_text('<urlset>' + ''.join(f'<url><loc>{u}</loc></url>' for u in urls) + '</urlset>')
            for index, url in enumerate(urls):
                target = root / ('research/index.html' if index else 'index.html')
                target.parent.mkdir(exist_ok=True)
                links = home_links if index == 0 else '<a href="/">Home</a><a href="/research/">Self</a>'
                target.write_text(f'<title>Page {index}</title><meta name="description" content="Description {index}"><link rel="canonical" href="{url}"><script type="application/ld+json">{{"@type":"WebPage"}}</script><h1>Page {index}</h1>{links}')
            return audit(root)

    def test_relative_internal_link_makes_research_discoverable(self):
        result = self.check_site('<a href="/research/">Research</a>')
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['orphan_urls'], [])

    def test_sitemap_and_self_link_do_not_replace_an_incoming_link(self):
        result = self.check_site('<a href="/#research">A fragment on this page</a>')
        self.assertEqual(result['orphan_urls'], ['https://cardiq.test/research/'])
        self.assertTrue(any('No crawlable internal link' in error for error in result['errors']))


if __name__ == '__main__':
    unittest.main()
