# Emergent dependency audit

Audited: 24 October 2026. Source revision: `fb52cbf`.

Historical snapshot: the active integrations described below were removed in
`15233dd`. See `docs/platform-dependency-removal.md` and `docs/email-setup.md`
for the replacement and configuration requirements.

## Conclusion

CardIQ is independently hosted, but is **not yet independent of Emergent**.
Email is a hard runtime integration. Frontend installation still downloads two
Emergent packages. Legacy preview infrastructure remains tracked but is excluded
from the DigitalOcean image. No Emergent URLs were found in the card catalogue
or the inspected production frontend assets.

This is an audit, not a completed migration. No application code, package, secret,
or production setting was removed as part of this audit. No customer email was sent.

## Findings

| Priority | Area | Evidence | Impact and required action |
|---|---|---|---|
| P1 | Email runtime | `backend/server.py:93–97,177–201` | Hardcoded `integrations.emergentagent.com/api/v1/email/send`, `X-Email-Key`, and `EMERGENT_EMAIL_KEY`. Replace the transport with a directly owned email provider before retiring the key. |
| P1 | CI/install dependency | `frontend/package.json:87–88`, `frontend/yarn.lock:1239–1247` | Overlay and visual-edit packages are fetched from `assets.emergent.sh`. GitHub Actions runs `yarn install --frozen-lockfile`, including development dependencies. A fresh install still needs this host even though production compilation excludes the plugins. Remove both packages and regenerate the frontend lockfile. |
| P2 | Local development hooks | `frontend/craco.config.js:74–95,131–134,162–235` | Development mode loads Emergent overlay/visual-edit adapters. Remove their imports, wrappers, injection and obsolete disable flags; retain ordinary CRACO configuration and webpack-dev-server compatibility. |
| P2 | Preview cron infrastructure | `.emergent/cron/*`, `.emergent/emergent.yml`, `.emergent/markers/*` | Tracked preview artifacts reference Emergent's image and internal cron API. Remove from the maintained app after confirming preview workflows are no longer used. They are not copied into the production API container. |
| P2 | Local credential | Ignored `backend/.env` | A nonempty `EMERGENT_EMAIL_KEY` is present locally. Its value was not printed. Retire/revoke it after email migration and remove it from local/deployment secret stores where configured. Deleting a file does not revoke a key. |
| P3 | Documentation and naming | `backend/.env.example:5`, `contracts.md:32–34`, `frontend/src/constants/testIds/home.js:5`, `frontend/src/constants/testIds/auth.js:12`, `test_result.md` | Update current setup/contracts and remove unused test identifiers/comments. Historical test logs describe the old integration and are not evidence that current production email works. Preserve or clearly label historical records rather than rewriting test history as a new success. |

The two frontend packages installed locally are overlay `0.1.31` and visual-edits
`1.0.12`; the latter is distributed in a tarball named `1.0.13`. Neither installed
package declares preinstall/install/postinstall/prepare lifecycle scripts in its
package manifest. This observation is not a complete third-party package security audit.

## Email features affected

All five paths call the same `send_email` helper:

1. Welcome email after lead capture (`POST /api/quiz/submit`). Failures are caught;
   a successful quiz response does not prove email delivery.
2. Recommendation email (`POST /api/results/{result_id}/email`).
3. Card-change campaigns (`POST /api/admin/card-alerts/send`).
4. Incomplete-quiz reminders (`POST /api/admin/send-reminders`).
5. Review reminders (`POST /api/admin/send-review-reminders`).

The current payload uses `from_name` and `contact_email`, with an `X-Email-Key`
header. A direct-provider API key is not a drop-in replacement for the Emergent key:
the endpoint, authentication, sender identity, payload and response/error handling
must also change. Retain server-side recipient selection, existing content checks,
consent rules and send-status bookkeeping during migration.

## Scheduling boundary

The tracked preview crontab only schedules the Emergent configuration watcher;
no application reminder schedule was found there. The dispatcher reads an optional
`WEBHOOK_CRON_SECRET` and can call configured webhook destinations, but the current
API does not expose that authentication mechanism as an application dependency.

DigitalOcean's Dockerfile copies only the Python requirements, three application
modules and card JSON. It starts one Uvicorn worker and does not install or launch
the preview cron scripts. The app spec defines one web service and no scheduled
reminder job. GitHub's six-hour schedule rebuilds static catalogue pages; it does
not send reminders. Reminder and card-alert send routes therefore remain manual
unless an independently configured external scheduler exists.

The application-link monitor runs within FastAPI's lifespan and uses HTTPX; it
does not depend on Emergent. Removing preview cron files must not be presented as
installing a replacement reminder scheduler.

## Independent components and artifacts checked

- API hosting: DigitalOcean, Python base image, FastAPI/Uvicorn.
- Data: MongoDB driver and repository catalogue; no Emergent SDK in Python requirements.
- Frontend hosting and deployment: GitHub Pages and GitHub Actions.
- React source/public assets: no active Emergent tracking script or badge found.
- Production-mode CRACO config: both Emergent integrations are gated to development.
- Local production build JS/CSS: no Emergent host/package markers found.
- Live HTTP-served HTML, `/static/js/main.7095de57.js` and
  `/static/css/main.8930d192.css`: no Emergent host/package markers found.
- Card catalogue and full/summary static fallbacks: no Emergent URLs found.
- Generic local health-check plugins: no Emergent network endpoint found. They
  are optional development diagnostics, not production API health checks.
- Root `yarn.lock`: no Emergent package entries; CI uses `frontend/yarn.lock`.

## Migration order and acceptance checks

1. Remove frontend Emergent packages and dev hooks. Refresh the lockfile with the
   configured Yarn version. Run a clean frozen install, frontend tests, production
   build and a local development-server smoke check. Verify generated JS/CSS/HTML
   has no injected Emergent runtime references.
2. Implement a directly owned email transport with a verified `findmybest.cards`
   sender. Configure new encrypted credentials and sender settings in DigitalOcean.
   Unit-test request mapping, missing configuration, provider rejection and timeout
   handling without sending real messages.
3. With an explicitly chosen test recipient, verify each affected email flow,
   sender identity, links, unsubscribe behavior and database send-status updates.
   Do not trigger existing customer reminder batches as a migration smoke test.
4. Choose whether reminders stay manual or get a separately configured scheduler.
   If scheduled, validate authentication and duplicate-send protection first.
5. Revoke the old Emergent key, remove obsolete environment variables and tracked
   preview artifacts, update current documentation, and repeat the source/lockfile
   and deployed-asset scans. Check archived hosting accounts separately.

## Limits

This audit inspects the current repository, local dependency metadata/build output
and available production evidence. It does not prove the absence of references in
Git history, inaccessible hosting accounts, external schedulers, or user-created
database records. The local credential was checked for presence only. Production
email delivery has not been exercised; the earlier live configuration inspection
did not contain an email-service key. No keys were retrieved or disclosed.
