# cardIQ — API Contracts & Integration

## Overview
Frontend quiz + recommendation now backed by FastAPI + MongoDB. Questions stay in
`mock.js` (static UI). Cards, scoring, results, leads and email move to backend.

## Mocked data now replaced by backend
- The frontend demo catalog and scoring were removed; real card facts and scoring are served by the backend.
- Frontend keeps: `QUIZ_QUESTIONS`, `TRUST_POINTS`, `PROBLEMS` (static).

## MongoDB collections
- `cards`: 192 sourced records in `backend/cards_catalog.json`, upserted by `cards_seed.py`. Known demos are archived with `active: false`; paused applications have `applicationsOpen: false`. Products with invitation, upgrade, banking relationship, professional or partner-channel prerequisites have `recommendationEligible: false` and a factual `eligibilityNote`; the quiz cannot establish these prerequisites.
- `quiz_results`: { result_id, answers, recommended_card_id, scored_ids, scored, lead_id, email_sent, created_at }. New `scored` snapshots preserve historical issuer facts; older results resolve their stored IDs.
- `leads`: { lead_id, name, email, phone, result_id, created_at }

## Endpoints (all prefixed `/api`)
- `GET /cards` → current catalog, including clearly flagged paused products; archived demos are excluded. New quiz recommendations exclude paused applications and cards with `recommendationEligible: false`; these restricted products remain visible in the catalog and direct lookups.
- `GET /cards/{id}` → one card
- `POST /cards/compare` { ids: [] } → cards in requested order
- `POST /quiz/submit` { answers:{goal,spend,fee,usage,priority}, lead:{name,email,phone?} }
   → { result_id, scored:[{card,score,reasons}] }  (saves lead + result)
- `GET /results/{result_id}` → { result_id, scored:[...] }
- `POST /results/{result_id}/email` → emails stored lead the top recommendation (Resend managed)

## Lead capture (both points)
1. Before result: LeadForm after quiz → `POST /quiz/submit` (captures lead + computes result).
2. After result: "Email me my recommendation" → `POST /results/{result_id}/email`.

## Email
- Emergent managed Resend. `EMAIL_FROM_NAME=cardIQ`. Recipient read server-side from
  the lead record (never from request body). Template server-side only.

## Frontend integration
- `src/api.js`: axios helpers using `REACT_APP_BACKEND_URL`.
- Flow: Landing → Quiz → LeadForm → (submit) Analyzing → Result → optional Email / Compare.
- `App.js` orchestrates screens + holds { answers, resultId, scored }.
- Compare: modal/screen using `POST /cards/compare` with top-3 ids.
