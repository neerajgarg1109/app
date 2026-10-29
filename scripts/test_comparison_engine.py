import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from comparison_engine import TOP_COMPARISONS, generateComparisonSeoMeta, estimate, render_comparison_page, known_text, money

CARDS = json.loads((ROOT / 'backend/cards_catalog.json').read_text())
BY_ID = {c['id']:c for c in CARDS}


class ComparisonEngineTests(unittest.TestCase):
    def test_twenty_distinct_priority_routes_reference_real_products(self):
        self.assertEqual(len(TOP_COMPARISONS),20)
        self.assertEqual(len({row['slug'] for row in TOP_COMPARISONS}),20)
        for row in TOP_COMPARISONS:
            a,b=BY_ID[row['cardA']],BY_ID[row['cardB']]
            meta=generateComparisonSeoMeta(a,b,row)
            self.assertEqual(meta['title'],row['title'])
            self.assertEqual(meta['h1'],row['h1'])
            self.assertEqual(meta['canonicalUrl'],f'https://findmybest.cards/compare/{row["slug"]}/')
            body,schema=render_comparison_page(a,b,meta,CARDS,row)
            self.assertLess(body.index('id="verdict"'),body.index('id="spending"'))
            self.assertLess(body.index('id="spending"'),body.index('id="terms"'))
            self.assertLess(body.index('id="terms"'),body.index('id="alternatives"'))
            self.assertIn('<table>',body)
            self.assertIn('Insurance premiums',body)
            self.assertEqual(sum(node['@type']=='FinancialProduct' for node in schema['@graph']),2)
            faq=next(node for node in schema['@graph'] if node['@type']=='FAQPage')
            self.assertEqual(len(faq['mainEntity']),4)
            self.assertTrue(all(q['name'] in body for q in faq['mainEntity']))
            self.assertEqual(body.count('subid=fallback_footer_ltf'),2)

    def test_currency_and_evidence_word_boundaries(self):
        self.assertEqual(money(200000), "₹2,00,000.00")
        self.assertEqual(money(-1234.5), "₹-1,234.50")
        self.assertEqual(known_text({"highlights":["Subject to current conditions"]}, ["rent"], "Unknown"), "Unknown")

    def test_calculator_caps_waivers_gst_and_unknowns(self):
        sbi=BY_ID['sbi-cashback-sbi']
        self.assertAlmostEqual(estimate(sbi,10000)['net'],4821.18)
        self.assertEqual(estimate(sbi,40000)['gross'],24000)
        self.assertEqual(estimate(sbi,100000)['gross'],24000)
        self.assertEqual(estimate(sbi,20000)['fee'],0)
        self.assertAlmostEqual(estimate(sbi,20000,year='first')['fee'],1178.82)
        self.assertEqual(estimate(BY_ID['axis-flipkart-axisbank-credit-card'],100000)['gross'],16000)
        self.assertEqual(estimate(BY_ID['hdfc-millennia-credit-card'],100000)['gross'],12000)
        self.assertEqual(estimate(BY_ID['axis-airtel-axis-bank-credit-card'],20000,'utilities')['gross'],0)
        self.assertIsNone(estimate(BY_ID['axis-axis-bank-atlas-credit-card'])['gross'])
        changed={**sbi,'rewardLine':'Updated earn conditions'}
        self.assertIsNone(estimate(changed)['gross'])

    def test_dynamic_titles_are_short_unique_and_have_no_approval_promises(self):
        priority_pairs = {frozenset((row['cardA'], row['cardB'])) for row in TOP_COMPARISONS}
        for a,b in zip(CARDS,CARDS[1:]):
            if frozenset((a['id'],b['id'])) in priority_pairs: continue
            title=generateComparisonSeoMeta(a,b,{'slug':a['id']+'-vs-'+b['id']})['title']
            self.assertLess(len(title),65)
            self.assertNotIn('100% approval', title.lower())


if __name__=='__main__':unittest.main()
