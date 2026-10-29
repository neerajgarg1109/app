# Real card artwork — 29 October 2026

Implemented locally; not deployed. Production remains at release `d20237f`.

Real issuer artwork replaces coloured blocks in Browse Cards, both comparison views, comparison search and alternative recommendations. Images also appear in invite-only listings, calculator/optimizer results, compact details, public catalogue/category/issuer/comparison pages and comparison/shortlist journal tiles. Downloaded recommendation images use issuer artwork instead of drawing a fictional card.

The shared component preserves image proportions, lazy-loads images, and labels missing or failed artwork. The generated `frontend/src/data/cardArtwork.json` lookup covers historical saved results missing imageUrl; `frontend/scripts/syncCatalog.js` refreshes it. Explicit image URLs retain priority.

Added 36 visually checked issuer assets: Amex (2), Axis (1), RBL (8), HDFC (3), PNB (7), BOBCARD (12), ICICI (1) and CUB SalarySe product representations (2). Coverage rose from 203 to 239 of 267 cards. Provenance is in `catalog-artwork-sources.json`; the outstanding 28 cards are listed in `card-artwork-coverage-2026-10-29.json`.

Some official assets include a product background, phone representation or reverse face. Generic cross-sell images, placeholders, tiny card faces within lifestyle banners and inaccessible assets were rejected. The request for authentic images on all 267 cards remains incomplete pending suitable images for those 28 cards.

Validation: optimized React build; full frontend suite (125 tests across 32 suites before the final historical-artwork test); 33 generated-page checks; 438-URL SEO audit with zero errors/orphans and eight existing long-title advisories. All local image files exist and validate as raster images or SVG XML. Browser checks confirmed real artwork in selected comparison panels, comparison tables and public comparison articles. Final targeted test results are appended after execution.

Preview: http://127.0.0.1:8769/#/cards?compare=axis-axis-bank-ace-credit-card,hdfc-swiggy-ornge-hdfc-bank-credit-card

No catalogue cards or unrelated operations documents were removed. Backup exports remain disabled; Better Stack remains deferred.

Final targeted checks: 19 tests across five suites passed, including the historical-result lookup regression. The final build passed at 161.16 kB gzipped app JavaScript (about 4.9 kB added for the complete artwork lookup).
