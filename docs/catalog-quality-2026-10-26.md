# Catalogue quality update — 26 October 2026

This is a targeted quality pass, not a full re-verification of all 261 products.

## Changes

- Official artwork: **168 → 197 of 261 cards** (64 still missing). Added 13 Axis and 16 AU product images. Each was matched to its official product page/listing, decoded for actual dimensions and visually reviewed. Existing artwork was preserved.
- Expanded four fact profiles: CASHBACK SBI, Axis ACE, Flipkart Axis and Airtel Axis. Added redemption details, fuel waiver limits, exclusions and, where verified, welcome conditions, foreign-currency fees and lounge status. ACE now states the shared ₹500 accelerated cashback cap and Android requirement. Flipkart and Airtel explicitly disclose discontinued lounge access.
- Source evidence and field-check dates: [fact checks](catalog-fact-checks-2026-10-26.json). Image provenance: [artwork manifest](catalog-artwork-sources.json). Image-only changes do not refresh a product’s verification date.
- Fixed false fee conflicts caused by matching “Rs” inside “years” or treating ₹0 as a positive fee. Real positive-fee conflicts remain detectable.
- Importer now validates real WebP dimensions, restricts issuer hosts, supports picture/lazy sources and prioritises reviewed exact artwork. Install its optional authoring dependencies with `pip install -r scripts/requirements-catalog.txt`. Unreviewed imports still require visual review.
- Editorial generation no longer presents discontinued benefits as strengths.

## Coverage and remaining work

Economics completeness changes from **210 limited / 51 medium** to **207 limited / 51 medium / 3 high** under the unchanged checker. Completeness measures populated fields, not issuer approval or independently certified accuracy. Explicitly discontinued benefits count as known information; unknown benefits have not been invented. Four targeted profiles have field-level evidence; other product verification dates retain their prior meaning.

Remaining missing artwork by issuer:

- American Express India: 2
- Axis Bank: 2
- BOBCARD: 15
- City Union Bank: 2
- Federal Bank: 7
- HDFC Bank: 3
- ICICI Bank: 1
- IDBI Bank: 4
- IDFC FIRST Bank: 1
- Indian Bank: 1
- Kotak Mahindra Bank: 1
- Punjab National Bank: 7
- RBL Bank: 8
- SBM Bank India: 1
- Utkarsh Small Finance Bank: 1
- YES BANK: 8

Continue in issuer batches, prioritising missing fees/waiver conditions, reward caps and exclusions before promotional benefits. Some issuer sites blocked automated retrieval; no substitute artwork or unsupported values were accepted. Axis REWARDS Amex remains unresolved rather than using another network’s image.

## Validation

- 111 frontend tests, 48 backend tests, 18 generated-page tests and four importer/editorial boundary tests.
- Production frontend build and generation of 261 card, 20 issuer, 29 category and 96 comparison pages.
- All 29 imported files were decoded and visually checked.
- Live deployment verification is recorded in the completion message after publishing.
