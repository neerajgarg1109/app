"""Check boundary-sensitive examples and source disclosure in reviewed articles."""
import unittest
from decimal import Decimal

from comparison_editorial import earn, examples, render_comparison, FLIPKART, NEU, FOOD, REVIEWS


class ComparisonExamplesTests(unittest.TestCase):
    def test_caps_and_upi_app_difference_change_results(self):
        self.assertEqual([(a,b) for _,a,b in examples(FLIPKART)], [(700,700),(4000,4000),(6000,4000)])
        self.assertEqual([(a,b) for _,a,b in examples(NEU)], [(200,200),(50,200),(500,500)])
        self.assertEqual([(a,b) for _,a,b in examples(FOOD)], [(310,300),(650,1500),(600,400)])
        self.assertEqual(earn(80000, '.05', 4000), Decimal('4000'))
        self.assertEqual(earn(80020, '.05', 4000), Decimal('4000'))

    def test_unreviewed_comparison_does_not_get_generic_example_content(self):
        self.assertEqual(render_comparison('unreviewed', {}, {}), '')

    def test_each_review_discloses_sources_and_excludes_fees_from_gross_examples(self):
        for slug, review in REVIEWS.items():
            source = render_comparison(slug, {'name':'Card A'}, {'name':'Card B'})
            self.assertIn('Sources for this comparison', source)
            self.assertIn('before fees and taxes', source)
            self.assertIn('2026-10-29', source)
            self.assertIn('scope="row"', source)
            for _, url in review['sources']:
                self.assertIn(url.replace('&','&amp;'), source)


if __name__ == '__main__':
    unittest.main()
