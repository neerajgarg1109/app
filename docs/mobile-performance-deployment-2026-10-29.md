# Deployment and mobile audit — 29 October 2026

Release `d20237f056c7a66c7cb7094e2ece0707c26c307d` is live at https://findmybest.cards.

[Successful deployment workflow](https://github.com/neerajgarg1109/app/actions/runs/40817492987).

This release deploys the font-loading improvements, homepage main landmark, journal contrast fixes, and three expanded comparisons documented in `mobile-performance-and-comparisons-2026-10-29.md`. That earlier document is the pre-deployment snapshot; this record supersedes its deployment status and unmeasured-results statements.

## Live verification

- Homepage, cashback guide and CASHBACK SBI review returned HTTP 200 with the new nonblocking font links.
- All three expanded comparisons returned HTTP 200 and include worked spending examples, primary-source sections, and fee/tax exclusions.
- Compiled app CSS has no Google Fonts `@import` chain.
- Sitemap retains 438 URLs; API readiness returned HTTP 200. No backend deployment was required.
- Pre-deployment validation passed: 123 frontend tests, 32 generated-page tests, three comparison tests, two discovery tests, optimized build, and a 438-URL SEO audit with zero errors or orphan URLs. Eight existing long-title advisories remain.

## Post-deployment mobile lab results

| Page | Baseline performance | Deployed performance | Accessibility | SEO | LCP | CLS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Homepage | 82 | 83 | 100 | 100 | 3.4 s | 0 |
| Cashback guide | 87 | 100 | 100 | 100 | 1.5 s | 0 |
| CASHBACK SBI review | 89 | 88 | 100 | 100 | 3.0 s | 0 |

All three also scored 100 for best practices. These are individual Lighthouse laboratory runs, with no real-user data available. The guide improved substantially; the homepage changed slightly and the card review decreased by one point. The results do not establish a consistent speed improvement across all pages or a field Core Web Vitals pass.

Full metrics and report links are preserved in `mobile-performance-post-deploy-2026-10-29.json`. Homepage render-blocking opportunity decreased from 1,310 ms to 190 ms. Remaining opportunities include unused homepage JavaScript/CSS, cache lifetimes, and card-page LCP discovery. They are future optimization work, not part of this completed deployment.

Existing workspace changes and unrelated operations documents were preserved. Production backup exports remain disabled; Better Stack remains deferred. These post-deployment records are local handoff documents, not an additional production release.
