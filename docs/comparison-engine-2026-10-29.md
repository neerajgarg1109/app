# Comparison engine — local implementation, 29 October 2026

Status: implemented and validated locally; not deployed by this task. Keep this operational report and PROJECT_HANDOFF.md local.

## Architecture and entry points

React/CRACO remains the interactive application. The existing Python SSG in scripts/generate_static_catalog_pages.py now calls scripts/comparison_engine.py to produce complete comparison documents. Only scripts/templates/comparison-calculator.js enhances the calculator; all headings, verdicts, fee/exclusion tables, FAQs and JSON-LD are present without JavaScript.

Twenty priority definitions live in scripts/data/top_comparisons.json. Existing comparison routes remain accessible; duplicate pairs canonicalize to the preferred priority route. Output contains 115 canonical comparisons. The catalogue now contains 268 cards across 21 issuers after adding the original Jupiter Edge CSB RuPay product, distinct from Edge+.

The SEO utility generateComparisonSeoMeta supports curated overrides and attribute-based dynamic metadata. Each page contains a verdict, spend calculator, exclusions/source table and alternatives, plus editorial methodology, two FinancialProduct nodes and visible FAQ content. Unknown APRs are omitted from structured data rather than fabricated. Canonical URLs use trailing slashes for static hosting.

## Redirect and attribution

Static /go/<card-id>/ bridges forward to /api/go/<card-id>. Configure CARDIQ_API_ORIGIN at generation time; default is the production API. The API validates card status and HTTPS destinations, selects live partner links or official issuer fallback, preserves campaign parameters and records placement/comparison attribution in apply_events. Query parameters cannot choose an arbitrary destination. Redirects and bridge pages are noindex. Local static previews need an API running the new route before application links work; the production API does not receive this change until deployment.

## Financial limits and source corrections

Eight card records currently have bounded calculation models: SBI Cashback, Millennia, Amazon Pay ICICI, Flipkart Axis, HSBC Live+, Airtel Axis, original Swiggy HDFC and Swiggy Ornge HDFC. Supported merchant/category baskets and cap periods are explicitly stated per model. Other scenarios return Not estimated. Catalogue term fingerprints invalidate models when maintained economic fields change. Adding rules requires verifying issuer earn rates, caps, reward conversion and exclusions, then updating both Python and JavaScript arithmetic and fingerprint fixtures.

Fees include 18% GST, and first-year joining fees are distinct from renewal waivers. The model excludes interest, redemption charges, milestones, paid plans and speculative travel-point valuations. Different cards can require different eligible merchant baskets. Waiver eligibility is an explicit simplifying assumption.

The brief's outdated HSBC cap, Airtel benefits, universal LTF claims and guaranteed FD approval language were corrected using issuer sources. PNB Kiwi is identified explicitly; Jupiter Jewels and reward points are not treated as rupees without a verified conversion. Alternatives disclose approval/deposit conditions. Eleven issuer MITC PDF links were fetched and validated as PDFs on 29 October; availability checks do not constitute a new full audit of every term. Issuer-record review dates remain separately displayed.

FAQ schema is included as requested, but Google retired FAQ rich results in May 2026. Search rankings, indexing or approval rates cannot be guaranteed.

## Validation

Optimized frontend build compiled successfully. Frontend suite: 129 tests across 33 suites passed. Engine unit tests: four passed; calculator arithmetic checks passed. Static regression suite: 33 passed. Generated SEO audit: 459 sitemap URLs, no errors, warnings or orphan pages. Backend catalogue/scoring/artwork/redirect selection tested; redirect coverage includes partner parameter preservation, paused fallback, validation and unavailable cards.

Browser verification at http://127.0.0.1:8771/compare/sbi-cashback-vs-hdfc-millennia/ confirmed the monthly slider updates: at ₹40,000 eligible online spend SBI shows ₹24,000 gross annual rewards versus Millennia ₹12,000, with the winner CTA carrying calculator_winner_cta and the comparison slug. Preview screenshot: /tmp/cardiq-comparison-engine-preview.png.

## Follow-up

Expand structured issuer-verified reward, lounge, APR and exclusion coverage before claiming exact calculations for all twenty matchups. Recheck personal/limited acquisition offers before publication. No production deployment was performed for this implementation.
