# Mobile performance audit and comparison upgrades — 29 October 2026

Baseline production release: `2b1be90c4b0183f34d354ffe145065a8f7280b09`. This batch is implemented and verified locally; it is not deployed.

## Measured production baseline

Google PageSpeed Insights UI ran Lighthouse 13.5.0 with an emulated Moto G Power, slow 4G and an initial page load. The unauthenticated PageSpeed API returned quota-exceeded HTTP 429, so the UI was used successfully instead. Results are individual laboratory runs, not real-user performance guarantees.

| Page | Mobile performance | Accessibility | SEO | FCP | LCP | TBT | CLS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Homepage | 82 | 98 | 100 | 3.0 s | 3.4 s | 0 ms | 0.077 |
| Cashback guide | 87 | 95 | 100 | 3.2 s | 3.2 s | 0 ms | 0 |
| CASHBACK SBI review | 89 | 100 | 100 | 2.9 s | 3.0 s | 0 ms | 0 |

All three reports showed **No Data** for real users. No field INP measurement or field Core Web Vitals pass/fail claim is established. Full baseline records and report URLs are in `docs/mobile-performance-2026-10-29.json`.

- [Homepage report](https://pagespeed.web.dev/analysis/https-findmybest-cards/8hn4fc03al?form_factor=mobile)
- [Guide report](https://pagespeed.web.dev/analysis/https-findmybest-cards-guides-best-cashback-credit-cards-india/7km6g0li32?form_factor=mobile)
- [Card report](https://pagespeed.web.dev/analysis/https-findmybest-cards-cards-sbi-cashback-sbi/snb559n271?form_factor=mobile)

## Changes addressing observed issues

The homepage loaded two Google Fonts stylesheets, including a CSS import chain. Lighthouse estimated 1,310 ms render-blocking savings on the homepage, 2,480 ms on the guide and 2,240 ms on the card page. These are Lighthouse opportunity estimates, not measured improvements after this change.

- Consolidated the font families and weights into one request per document, with a separate no-JavaScript fallback.
- Removed Google Fonts CSS `@import` chains from the app and journal.
- Load the stylesheet initially with print media, switching to all media on load; system fallback text remains readable immediately.
- Use `display=optional` so slow font delivery does not force a late swap. The deliberate trade-off is that a slow connection can retain the system font for the visit.
- Added the missing homepage main landmark reported by the accessibility audit.
- Removed reduced opacity from the journal cover kicker and cardIQ label that PageSpeed identified as low-contrast text.

Unused JavaScript and hosting-controlled cache lifetimes remain opportunities. No speculative route rewrite or hosting migration was included. The full app bundle remains about 156.5 kB gzipped; this change addresses the font critical path rather than claiming a large JavaScript reduction.

**Post-change PageSpeed scores have not been measured.** After deployment, rerun these same three URLs and compare the loading diagnostics as well as scores. Lab results vary; field data needs sufficient real visits.

## Three existing comparisons upgraded

The maintained 96 comparison routes are preserved. Three now include original decision guidance, worked examples, assumptions, exclusions, review dates and direct primary-source citations:

1. `axis-flipkart-axisbank-credit-card-vs-sbi-flipkart-sbi-card`
   - Explains the separate Flipkart/Myntra/Cleartrip caps and the preferred-merchant cap difference.
   - Examples show ₹700/₹700 for the stated eligible monthly basket, ₹4,000/₹4,000 for ₹90,000 quarterly Flipkart spending, and ₹6,000/₹4,000 for the illustrative eligible preferred-merchant quarter.
   - Merchant eligibility on both programmes and unused caps are explicit assumptions. The large-spend example is not a recommendation to spend more.
2. `hdfc-tata-neu-plus-vs-sbi-tata-neu-plus-sbi-card`
   - Explains HDFC's Tata Neu UPI-ID bonus and the difference between calendar-month and statement-cycle caps.
   - ₹20,000 eligible UPI produces 200/200 NeuCoins using Tata Neu UPI ID; another UPI ID produces 50/200. A higher-spend example demonstrates the 500-coin ceiling.
   - NeuCoins remain a restricted redemption currency, not withdrawable cash.
3. `axis-axis-bank-ace-credit-card-vs-hdfc-swiggy-ornge-hdfc-bank-credit-card`
   - Explains ACE's shared ₹500 cap and Android Google Pay condition, and Ornge's shared ₹1,500 accelerated cap, separate base cap and transaction minimums.
   - Eligible example baskets produce ₹310/₹300, ₹650/₹1,500 and ₹600/₹400 before fees/taxes.
   - Ornge is distinguished from BLCK and the older Swiggy card; the terms published on 15 October 2026 are cited.

The examples intentionally show gross earn; they exclude membership fees, taxes, borrowing costs, reversals, welcome benefits and rounding as stated. They do not promise a universal winner or personalise approval advice. Fee summaries retain their own catalogue verification dates, distinct from this comparison review date. No catalogue fees or application eligibility were silently changed.

Sources are maintained directly in `scripts/comparison_editorial.py`, including issuer product pages and current reward PDFs. SBI's official product JSON was also checked for fee and waiver consistency. No third-party review was used as authority for product terms.

## Validation and preview

- Frontend: 123 tests across 31 suites passed, including the homepage main landmark.
- Generated pages: 32 tests passed, including nonblocking fonts and the three reviewed comparisons.
- Comparison arithmetic: three tests passed, checking cap boundaries, app-dependent UPI results and source disclosures.
- Discovery audit: two tests passed.
- Fresh optimized React build passed. SEO audit covered 438 URLs with zero errors and zero orphan pages; eight pre-existing long-title advisories remain.
- Mobile browser preview at 390 px: document width remained 390 px. The 540 px comparison table scrolls inside a 342 px container instead of widening the page. Temporary viewport override was reset.
- CI now runs the comparison arithmetic and discovery-audit tests alongside the existing generated-page and SEO checks.

Local preview: `http://127.0.0.1:8768/compare/hdfc-tata-neu-plus-vs-sbi-tata-neu-plus-sbi-card/`.

Previous previews, unrelated operations documents and current production remain unchanged. Production backup exports remain disabled; Better Stack remains deferred.
