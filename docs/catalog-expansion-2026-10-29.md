# Catalogue additions — 29 October 2026

Six missing products were added to `backend/cards_catalog.json`, taking the catalogue from 261 to 267 cards across the existing 20 issuers. Every previous record was preserved. “Added” means new to CardIQ, not necessarily newly launched by the bank. No launch date was inferred from a page's presence or a verification date.

| Addition | Verification sources | Access and fee interpretation |
| --- | --- | --- |
| Eternal SBI Card | [Product](https://www.sbicard.com/en/personal/credit-cards/eternal-sbi-card.html), [issuer product JSON](https://www.sbicard.com/json/templatedata/product/card/data/en/personal/eternal-sbi-card.json), [MITC](https://www.sbicard.com/en/most-important-terms-and-conditions.page) | ₹499 joining/renewal, plus GST; ₹2 lakh renewal waiver. Discount and preferred-partner caps remain separate. Catalogue `isOnline` is `no`; searchable but excluded from general quiz recommendations pending confirmed onboarding access. This does not establish invitation-only status. |
| 1838 Reserve ICICI Bank Credit Card | [Product and FAQ](https://www.icici.bank.in/personal-banking/cards/credit-card/1838-reserve-icici-credit-card) | ₹1,75,000 joining and annual fees, plus GST; no spend waiver. Invitation required; excluded from general quiz. Membership valuations are not counted as cash savings. |
| PNB Kiwi Credit Card | [Issuer product](https://creditcard.pnb.bank.in/types18.html), [official partner FAQ](https://gokiwi.in/helpcenter/cardapplication/4d1/) | Nil virtual joining/annual fees. Physical card: ₹500 joining, ₹750 annual, plus applicable tax; annual waiver at ₹1.5 lakh previous-year spending. Kiwis earn remains distinct from cash and paid Neon subscriptions. |
| SBM Paisabazaar Paisa+ Credit Card | [Partner product](https://www.paisabazaar.com/sbm-bank/paisabazaar-paisa-plus-credit-card/), [bank KFS](https://www.sbm.bank.in/pdf/kfs/PB_paisaplus_KFS.pdf), [reward terms](https://www.sbm.bank.in/pdf/notice-board/PB_paisaplus_Reward-Structure.pdf) | Secured FD card; ₹499 annual fee plus GST, waived at ₹50,000. KFS governs fees: the reward PDF contains conflicting zero-fee figures, so those were not used. No promotional FD interest rate is quoted. |
| SBM Niyo Global Credit Card | [Partner FD product](https://goniyo.com/fd-credit-card), [SBM explanation](https://goniyo.com/sbm-scc/how-scc-works), [bank KFS](https://www.sbm.bank.in/pdf/kfs/Niyo-KFS.pdf) | ₹5,000 minimum FD; published ₹500 membership fees currently waived. Zero issuer forex markup does not remove other charges. General quiz excludes it until the Niyo relationship and SBM route are confirmed. The separate YES BANK Niyo waitlist is not this product. |
| SBM Magnet Credit Card | [Bank catalogue](https://www.sbm.bank.in/personal-banking/cards/secured-credit-card), [bank KFS](https://www.sbm.bank.in/pdf/kfs/SBM-Magnet-CC-Key-Fact-Statement.pdf) | FD-backed; nil joining/annual fees, separate early closure/cancellation charges. Current public partner onboarding was not verified, so it stays searchable but excluded from the general quiz. Magnet Coins are not assigned an invented cash value. |

## Artwork

All six entries use locally hosted, visually reviewed artwork downloaded from issuer sites. `docs/catalog-artwork-sources.json` records exact sources, dimensions, review date and SHA-256 hashes. Original image bytes were retained. 1838 Reserve uses official mobile promotional artwork; PNB Kiwi uses the issuer's front-and-back illustration. No artificial bank-card designs were created. Unused candidate downloads were preserved.

## Behaviour and maintenance

PNB Kiwi and SBM Niyo set `lifetimeFree: false`: their zero current/base fee must not put them in the Lifetime Free category. Both interactive browsing and static category generation respect this explicit flag. The flag is carried in API and offline summary catalogues. Low-fee browsing still includes them.

The existing 1838 news item now acknowledges the current issuer listing and points readers to Browse Cards; verification dates remain distinct from launch dates. Official application links and source citations are included with each added record.

No production deployment, database mutation, backup export or monitoring setup is part of this batch. Unrelated operations documents were preserved. The new batch is identified by `catalogBatch: verified-missing-products-2026-10-29`.

## Validation

- Backend suite: 74 tests passed; the three batch tests were rerun after adding API summary checks and passed.
- Frontend: 123 tests in 31 suites passed, including conditional-fee category filtering.
- Optimized React build completed successfully in a fresh preview directory.
- Static catalogue: 26 tests passed; 267 card pages, 20 issuers, 29 categories and 96 comparisons generated.
- SEO audit: 438 sitemap URLs checked, zero errors. Eight existing comparison-title length advisories remain.
- Browser preview: PNB Kiwi is searchable in the 267-card catalogue; official artwork and both fee formats render in the detail panel.
- Local preview: `http://127.0.0.1:8766/#/cards` using static catalogue fallback, without a production API dependency. The previous preview on port 8765 remains untouched.
