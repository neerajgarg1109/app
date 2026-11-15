# Production audit — 24 October 2026

API: `https://api.findmybest.cards`

## Catalogue parity

- Repository catalogue: 261 cards across 20 issuers.
- Production full catalogue: 261 cards; zero missing or extra IDs.
- All repository card fields match production values.
- Production summary catalogue: 261 cards.
- Deployed static fallback catalogue: 261 cards.
- All 261 individual card detail endpoints returned HTTP 200.
- Deployed frontend bundle references `https://api.findmybest.cards`, not Render.

## Service checks

| Check | Result |
|---|---|
| root | HTTP 200 |
| api | HTTP 200 |
| summary | HTTP 200 |
| restricted | HTTP 200 |
| updates | HTTP 200 |
| content | HTTP 200 |
| openapi | HTTP 200 |
| compare | HTTP 200 |
| calculator | HTTP 200 |
| optimizer | HTTP 200 |
| admin-protection | HTTP 401 |

Admin protection correctly returned 401 without credentials. One synthetic quiz with no lead returned three recommendations; the result was retrieved successfully from MongoDB. No customer messages were sent.

## Outstanding issues

- Resolved: browser CORS preflights now return HTTP 200 with the matching allowed origin for HTTP and HTTPS `findmybest.cards` and HTTPS `www.findmybest.cards`.
- Live CORS origins are now configured; remove transitional HTTP origins once HTTPS is enforced.
- Signed into DigitalOcean; deployment is Healthy and live. Runtime logs confirm successful requests; periodic background-job execution remains unverified.
- SMTP/email integration, admin-authenticated endpoints, reminder jobs, and historical private data migration are not verified by this public-endpoint audit.
- Previous Render API did not respond within 30 seconds; historical admin-managed records could not be compared with that service.
- Frontend HTTPS certificate mismatch remains a separate issue.

## Catalogue visibility

The explorer shows 24 cards initially and provides a **Show more cards** button. Its production page reports 261 cards found. Search and issuer filters operate on the complete loaded list.

## Live configuration follow-up

- Signed into DigitalOcean and saved component runtime `CORS_ORIGINS` for the HTTP and HTTPS production website, www aliases and the existing GitHub origin. HTTP origins are transitional until HTTPS is enforced.
- Set runtime `PUBLIC_APP_URL=https://findmybest.cards`.
- DigitalOcean started deployment `33b1dbe4-f6fb-4a77-ac6e-802521e6eab9`; it went live successfully. Browser calculator returned five value matches for a synthetic ₹35,000/month spending scenario.
- Live environment variable lists contain MongoDB settings and the two new public settings, but no admin role token or `EMERGENT_EMAIL_KEY`. Admin access and outbound email require those secrets to be configured by the account owner.
- GitHub Pages reports DNS success and certificate activation, with global availability still pending.
