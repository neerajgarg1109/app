# CardIQ code review — 28 October 2026

Status: review and verified fixes are local. Nothing was deployed, and no repository files were deleted. Existing operations documents and pending SEO work were preserved.

## Remaining findings, in priority order

### P1 — Shared-result identifiers also authorize contact mutation and email sends

`backend/server.py:1296` (`attach_result_lead`) authorizes solely by the public `result_id`, reuses the existing `lead_id`, and overwrites its name/email/phone. The result URL is explicitly shareable. A recipient of that URL can therefore replace the originating lead's contact details. `email_result` also authorizes solely by that public identifier and can repeatedly send to the stored address. Removing the recipient email from its response closes the direct address disclosure, but does not establish ownership or prevent email abuse.

Recommended design: separate public read-only result identifiers from an owner capability, store only a hash of that capability server-side, require it for lead changes/email requests, and apply send limits/idempotency. Existing results need an explicit migration policy; avoid silently breaking saved links or granting a capability merely by viewing a shared result. This requires a coordinated API/frontend change and remains open.

### P2 — Outbound link checks follow redirects without validating each network destination

`backend/server.py:1682` (`_check_destination`) checks the initial URL's syntax and rejects numeric hosts, then creates an HTTP client with automatic redirects. A configured hostname can resolve to a private address, or an external server can redirect to an internal endpoint. Source URLs are administered, but the destination network responses remain outside CardIQ's control.

Recommended design: enforce network egress restrictions or use a DNS-pinned transport, reject non-global resolved addresses, validate every redirect, forbid credentials and non-HTTPS redirect targets, and cap redirects/response sizes. A hostname-only preflight check is insufficient against DNS rebinding. No unsafe network probes were performed during this review.

### P2 — Public writes and legacy reminder delivery need further abuse protection

Public event/report/partial-session/result endpoints have no application-level rate limiting in the reviewed code. A reverse proxy may impose limits, but that was not verified. Legacy abandoned-quiz reminders now require explicit consent, but that older sending loop still lacks the atomic delivery claim used by review reminders and the corrected card-alert campaigns. Concurrent admin calls could duplicate a legacy reminder. Add distributed limits and an atomic delivery ledger; do not rely on disabled frontend buttons as server-side protection.

### Operations follow-up — MongoDB container compatibility

The previous deployment's Operations verification job failed while starting its MongoDB container, before application tests ran. The recorded log identifies a kernel/version incompatibility. This review ran isolated in-memory backend integration tests and operations unit tests; it did not certify the real-Mongo restore/load job. Keep production backup exports disabled and Better Stack setup deferred as requested.

## Verified fixes implemented

| Area | Problem | Result |
| --- | --- | --- |
| Public card data | Full card responses copied nested admin drafts and internal fields; direct detail/compare endpoints could retrieve new unpublished drafts. | Draft/internal fields are stripped from public serialization, new drafts are excluded from detail and comparison responses, and database drafts are preserved. Archived historical published cards remain readable. |
| Review invitations | Separate read, insert and consume operations allowed concurrent submissions using one invitation. | Invitations are claimed atomically before insertion. A lost acknowledgement is marked for manual review rather than reopening the token and risking a duplicate. |
| Card-alert campaigns | Checking an idempotency key and recording it only after delivery allowed simultaneous requests to send repeatedly. | Campaigns reserve an atomic unique MongoDB `_id` before delivery. An in-progress campaign is not resent automatically. |
| Unsubscribe links | Each new card alert overwrote the sole unsubscribe-token hash, invalidating earlier emails' links. | Valid prior hashes are retained; the new hash is persisted before delivery, and unsubscribe accepts both legacy and retained hashes. |
| Admin authentication | Blank environment tokens could match an empty supplied header. | Empty tokens are removed from the role map; they cannot grant a role. |
| Result privacy | The public email action returned the lead's complete recipient address. | Recipient email is no longer returned. The UI confirms the address the user entered locally. This does not resolve the owner-capability issue above. |
| Welcome benefit estimates | The largest rupee amount in a voucher line could be the qualifying spending threshold. | Only labelled gift/voucher/membership amounts are counted; qualifying spending amounts are excluded. Example: a ₹600 voucher requiring ₹10,000 spending contributes ₹600. |
| Waiver estimates | A comma-formatted threshold such as ₹1,00,000 was parsed as ₹1. | Comma-formatted and decimal amounts are parsed before applying unit multipliers. |
| Numeric inputs | Infinity, NaN or extreme numeric strings in quiz answers could overflow calculations. | Numeric parsing rejects non-finite or unsupported large values and uses the defined fallback. The maximum corresponds to the calculator's total supported monthly input. |
| Analytics startup | The current unique event index was dropped and rebuilt on every restart. | Ordinary restarts preserve the existing matching unique index. Only a mismatched legacy definition triggers migration. |
| Shared-result navigation | Changing the result ID kept the previous recommendation visible during loading. | Previous data is cleared and loading state restored before fetching the next result. |
| Reminder consent | The abandoned-quiz reminder sender selected records without an explicit reminder-consent requirement. | Consent defaults to false, is recorded with a timestamp, and only explicitly opted-in records are selected. Legacy records without consent remain untouched and are skipped. |

## Validation

- Backend: **71 tests pass**, including isolated in-memory API integration tests and new concurrency, privacy, consent, index and economics regressions.
- Frontend: **122 tests pass across 31 suites**.
- Optimized frontend production build: passes in a new temporary output directory.
- Generated-site regressions: **25 tests pass**.
- Read-only SEO audit: **431 sitemap URLs checked, zero errors**, eight title-length advisories retaining full product names.
- Operations safety unit tests: **6 pass**. Editorial/image importer tests: **4 pass**.
- `git diff --check`: passes.
- Email delivery was mocked in tests; no real messages or production database writes were made. Backup/export jobs were not enabled.

## Review coverage and limits

The review examined API authorization and public serialization, draft publication, recommendation/value calculations, review/alert/reminder flows, analytics startup, shared-result and comparison behavior, frontend API/fallback behavior, static generation/SEO, container/deployment definitions, and operations safety controls. Existing broad test suites were run alongside targeted new regressions.

This is a repository-wide review pass, not a claim that every line is defect-free. Real MongoDB concurrency/restore/load validation, third-party dependency vulnerability scanning, production network policy verification and browser performance testing remain outside the completed checks. No dependencies or files were removed without proof they were unused. Larger file reorganization was avoided while security and correctness changes are under review.
