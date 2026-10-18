# CardIQ v2 product plan

## Product objective

Help an Indian customer make a defensible credit-card decision and confidently continue to an issuer, while earning trust through current facts, transparent trade-offs and realistic value estimates.

The v2 north-star metric is **qualified issuer handoff rate**: the percentage of unique visitors who complete the quiz and click through to the recommended issuer. Supporting metrics are quiz-start rate, quiz-completion rate, optional lead-share rate, value-personalisation rate and return/review rate.

## v1 product review

### What works

- A focused six-question flow is faster and less overwhelming than a searchable directory.
- The landing page has a distinct evidence-led position and clearly rejects paid ranking.
- The result explains fees, key benefits, trade-offs and source recency in one journey.
- Anonymous completion and optional contact sharing preserve customer control.
- The catalog, result snapshots, admin publishing workflow and source links form a credible operating base.

### What limits trust and conversion

1. **Evidence gap:** match confidence and estimated value are partly heuristic, while the copy sounds definitive. Runner-ups can show the same percentage as the “strongest” card.
2. **Value interruption:** v1 opened contact capture immediately after the result appeared, before the customer could evaluate the recommendation.
3. **Unclear action hierarchy:** email, sharing, comparison, saving, refining, feedback and application compete for attention.
4. **Incomplete product imagery:** a fictional card face is less credible than an explicitly branded placeholder when no official image exists.
5. **Weak learning loop:** v1 could count results and clicks but could not measure the complete anonymous funnel.
6. **Eligibility ambiguity:** the credit-route question avoids approval claims, but the result still needs clearer separation between product fit and bank eligibility.
7. **Monetisation readiness:** application links can be configured, but partner attribution, reconciliation and conversion-quality reporting are not yet productised.
8. **Acquisition constraints:** GitHub Pages is sufficient for beta, but hash routing and a client-rendered app limit SEO and campaign landing-page flexibility.

## v2 scope

### Phase 1 — measurable, lower-friction beta

- Privacy-safe first-party funnel events with no arbitrary metadata or session replay.
- Admin funnel for landing, quiz start, result, optional lead and issuer click.
- Show the recommendation before asking for contact details.
- Replace fictional card details with issuer/card identity when an image is unavailable.
- Establish production baselines before changing quiz or result structure further.

Acceptance criteria:

- Events are deduplicated by anonymous session, event and result.
- Analytics failure never blocks the customer journey.
- Admin date filters apply to funnel counts.
- No name, email, phone, answers or free text is stored in product-event records.
- Result renders without an automatic modal.

### Phase 2 — defensible recommendation and value

- Public searchable card catalogue and direct card-detail links, with no quiz required.
- Complete verified details for the winner and both alternative recommendations.
- Category and issuer discovery, persistent three-card comparison and structured benefit/source fields.
- Crawlable static entry documents for card, issuer and category routes on GitHub Pages.
- Model issuer-specific earn rules, category caps, exclusions, point values, milestones and fee waivers.
- Show value assumptions before the headline number and distinguish guaranteed, conditional and estimated value.
- Explain why the winner beats each alternative, not only why it generally fits.
- Replace tied percentages with meaningful score bands or remove percentages when differentiation is weak.
- Add an eligibility checklist without presenting approval odds.

Acceptance criteria:

- Every published value component traces to a dated source or an explicit customer input.
- Automated examples cover caps, excluded categories, waived fees, milestone thresholds and point conversions.
- The same inputs always reproduce the displayed calculation.

### Phase 3 — conversion and partner operations

- One primary result CTA with secondary actions progressively disclosed.
- Affiliate-link versioning, partner/campaign identifiers and click reconciliation.
- Application-intent capture only when it provides a clear customer benefit.
- Admin reporting by issuer, card, partner link and campaign.
- Broken-link monitoring and automatic pause controls.

### Phase 4 — retention and acquisition

- Consent-based reminders, saved comparisons and post-application review loop.
- Indexable editorial/card pages on production hosting suitable for SEO.
- Content landing pages for high-intent use cases such as cashback, travel, fuel and secured cards.
- Experiment framework with predeclared success and guardrail metrics.

## Guardrails

- Never trade consent clarity for lead volume.
- Never describe editorial estimates as guaranteed savings or approval probability.
- Do not let issuer payment affect ranking.
- Do not publish customer ratings below the minimum sample threshold.
- A failed analytics, email or partner service must not prevent a customer from seeing a recommendation.

## Initial decision cadence

Run Phase 1 until at least 500 unique landing sessions or four weeks, whichever is later. Review the funnel weekly. Investigate the largest absolute drop-off first, while monitoring complaint rate, outdated-card reports and issuer-link failures as trust guardrails.

## Implementation status — 18 October 2026

The first eight post-review priorities are implemented:

1. Restricted-access discovery is integrated into the API, customer portal and crawlable publishing layer.
2. Application destinations are checked automatically every 24 hours while the API is running; two consecutive partner-link failures pause the partner destination and preserve the official issuer fallback.
3. JSON or CSV partner reconciliation imports connect applications, approvals and paid commission to attributed CardIQ clicks and Admin reporting.
4. Value estimates expose their assumptions, fee-waiver treatment, explicit first-year value and per-card structured-economics coverage; limited records are flagged in catalog health.
5. Every card detail view has an eligibility checklist that explicitly separates access requirements from approval odds.
6. Comparison selections persist locally and can be recovered or shared through a card-ID deep link.
7. Crawlable acquisition coverage includes cards, issuers, categories, comparisons, updates, lounges, restricted products and guides for launches, invite-only cards and safe closure journeys.
8. A stable anonymous CTA experiment records only allow-listed experiment and variant identifiers, with issuer-handoff rate reported by variant in Admin.

The acquisition layer also publishes catalogue-driven editorial guides for cashback, lifetime-free, travel, fuel, RuPay UPI and first-card searches; maintained head-to-head comparisons; launch and restricted-card guidance; and issuer-specific closure pages only where CardIQ has a reviewed official support channel. Guide facts and card links are regenerated from the same catalogue used by the application.

Operational configuration: `ENABLE_APPLY_LINK_MONITOR=true` enables the monitor (the default) and `APPLY_LINK_MONITOR_HOURS` controls its interval. Production partner reports may be uploaded in Admin as JSON or CSV with `external_id`, `status`, `commission`, and at least one of `card_id`, `campaign_id` or `tracking_id`.
