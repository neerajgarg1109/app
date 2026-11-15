# Production readiness audit — 25 October 2026

Website: https://findmybest.cards  
API: https://api.findmybest.cards  
Release: `dd2f3469d291dee2f33488a604b9be86c35b27dc`

## Release and fixes

- DigitalOcean deployment `74449169-0a06-4642-9279-33ec8141b47a` went live at 14:56:42 IST and reports Healthy.
- GitHub Pages [run 40180534817](https://github.com/neerajgarg1109/app/actions/runs/40180534817) succeeded. The public website serves `/static/js/main.9b90cb0a.js`, matching the tested production build.
- Review-reminder emails now use the frontend's `/#/review/{token}` route. A regression test checks the generated email link and its invitation token without sending mail.
- Failed or empty quiz responses preserve saved answers. A failed refinement preserves the previous recommendation and displays a retry message.
- Admin errors distinguish invalid credentials, permission failures, connection failures and server failures; keys are trimmed before use.
- General API calls have a finite 30-second timeout. The recommendation call retains its existing 50-second limit.

## Verification

- Final public production sweep: **874/874 checks passed**, covering all card-detail endpoints, generated HTML pages, every built card image/SVG, JavaScript/CSS, catalogue parity, selected service routes, expected authorization/404 errors and the corrected review-route entry point. Raw results are in `production-readiness-results-2026-10-25.json` beside this report. These checks supplement the functional browser/API tests below; an HTTP success alone does not prove a complete workflow.
- Backend: **47 tests passed**, with a disposable in-memory database; real email delivery is mocked.
- Frontend: **105 tests passed** across 28 suites, including failed quiz/retry, empty recommendations, failed refinement and admin error cases.
- Generated static pages: **18 tests passed**. Optimized production build succeeded.
- HTTPS certificate validation succeeds for the website and API. HTTP apex and HTTPS www redirect to HTTPS apex.
- Production full/summary catalogues and deployed fallback catalogues contain all **261 cards across 20 issuers**. Repository fields match production with no missing IDs or field differences. All 261 card-detail endpoints respond successfully.
- Public API checks cover catalogue, updates, restricted cards, site content, comparison, annual-value calculation and wallet optimization; invalid input and unknown IDs return expected errors. Unauthenticated admin requests are rejected. HTTPS apex/www CORS preflights succeed and an untrusted origin is rejected.
- Browser walkthrough: six-step anonymous quiz, recommendation, catalogue search, card detail, recommendation comparison, annual-value calculation, wallet comparison, updates, restricted-card directory, issuer help and alert form rendering. Sample mobile result/detail/tool pages fit a 375px viewport without document overflow; sampled card images loaded.
- Authenticated admin refresh succeeds and reports all 261 cards and 20 issuers. No publish, reminder-batch, alert-subscription or customer-data edits were made during the audit.
- After deployment, an anonymous synthetic recommendation was saved and retrieved from MongoDB; its shared-result page rendered successfully. The invalid review invitation route shows “This review link is unavailable” and no browser console errors were captured for that page.
- Resend was already verified by a delivered test email and the user's receipt confirmation immediately before this audit. No additional email was sent in this audit.
- DigitalOcean's displayed six-hour metrics showed CPU about 2.5–5.5%, memory about 16–25%, and API ingress P95 values about 24–480ms. These are observed low-traffic metrics, not capacity certification. Restart-count range was 0–1 in a window containing configuration deployments; no cause beyond that chart was established.

## Remaining gaps

1. **Catalogue completeness:** 93 cards have no `imageUrl` and use designed fallback artwork. Production enrichment labels 210 cards as having limited economics coverage; estimates disclose limited confidence. These require source research and editorial validation, rather than copying unsupported values. The admin's additional SBI Unnati joining-fee warning is a false positive: its currency pattern matches the ending of “years”; the recorded joining fee is zero with four fee-free years.
2. **Recovery — confirmed blocker:** Signed-in Atlas inspection shows the CardIQ cluster is on the Free tier with **Backups OFF**. The Backup page offers upgrades for daily or continuous backups; no managed snapshot history or retention policy is available to verify on this cluster. Restore recovery and historical private-data migration remain unverified. Repository catalogue parity does not prove that every record from the previous host was migrated.
3. **Operations — partial coverage:** DigitalOcean email alerts are enabled for Failed Deployment and Failed Domain Configuration; Insights has no alert policies. Atlas has enabled Project Owner email rules and no open alerts, but actual notification delivery and external website/API uptime monitoring remain unverified. There is no reminder job in the committed deployment, no DigitalOcean job invocation history, and Atlas Triggers is at its initial Get Started screen. Reminder endpoints remain admin-triggered. The DO health probe checks the API route, not continuous database readiness; this audit separately verified database reads/writes.
4. **Capacity:** No heavy load, soak, fault injection, regional-browser matrix or disaster recovery test was run against production. The $5 instance has one worker and one instance; observed spare capacity does not establish peak-load reliability.
5. **Issuer destinations:** This audit checks application-link configuration and sampled UI, not successful card applications or every external issuer's availability. No financial applications were submitted.

Service checks establish that tested customer flows work at the audit time. They cannot guarantee uninterrupted availability or independently certify every issuer fact. Close the recovery and monitoring gaps before treating the launch as operationally complete.

## Operational verification follow-up

After the request to verify the outstanding sign-off items:

| Item | Evidence and current conclusion |
|---|---|
| Light concurrency | 60 read-only production requests passed at stages of 1, 2 and 4 concurrent requests (20 per stage). P95 was 490ms, 479ms and 537ms respectively; maximum was 635ms. No errors. This is a bounded smoke test, not a sustained or peak-load test. |
| Catalogue warnings | Fresh production API response confirms 261 cards, 93 missing `imageUrl`, 210 limited economics profiles and 51 medium profiles. These warnings are real content-coverage gaps. |
| Reminder schedule | Application startup runs the application-link monitor only. The committed DO spec contains one web service and no jobs. The only GitHub Actions schedule refreshes SEO pages every six hours. Migration documentation explicitly says no replacement reminder schedule was installed. Signed-in DO overview shows only the web service; Jobs says there have been no invocations. Atlas Triggers shows initial setup, not configured triggers. No automatic reminder runner was found in the inspected systems; an unrelated third-party scheduler cannot be ruled out. |
| Database health probe | Confirmed from source: `/api/` returns a constant message and does not ping MongoDB. Functional database checks passed separately; the deployment health badge alone cannot detect a database outage. |
| Atlas backup and restore | Signed-in CardIQ project overview shows Free tier, Backups OFF, auto-scaling OFF, data size 160.8 MB / 512 MB and 11 / 500 connections. Backup page offers cluster upgrades for daily or continuous backups. Managed recovery is not configured; no production restore was attempted. An independently maintained manual backup has not been established. |
| DigitalOcean alerts | App settings show Failed Deployment and Failed Domain Configuration enabled with Email delivery. Failed Job Invocation and Failed to Scale are off. Insights alert policies: None. Log forwarding destinations: None. Delivery settings were inspected without saving changes or triggering an incident. |
| Atlas alerts | No open project alerts. Enabled email rules notify Project Owner, including Free Cluster logical size above 440 MB, connections above 80%, disk above 90%, and user CPU above 95%. Rule enablement does not prove applicability of every metric to the Free tier or email delivery. The organization also warns that designated security and operations contacts are missing. |
| External uptime monitoring | No external website/API uptime monitor or delivered alert evidence was verified in the inspected configuration. Deployment/domain alerts and Atlas resource alerts do not constitute end-to-end website availability monitoring. |

Raw bounded-concurrency evidence: `production-operations-check-2026-10-25.json` beside this report. The account findings above were inspected after the user signed in. No settings were saved, paid upgrades started, data restored, customer emails sent, subscriptions created or reminder batches triggered.

### Work needed before operational sign-off

1. Establish a backup method with retention and off-cluster storage, then restore a backup into an isolated database and verify records/indexes. The current Atlas UI requires a cluster upgrade for managed backups; this audit did not approve or purchase one.
2. Add database-aware readiness and external checks of the website and API, with verified notification delivery. Add suitable resource/error alerts to the API service.
3. Configure and verify a recurring runner for consented reminders using isolated test records before enabling customer delivery.
4. Define expected launch traffic and validate that target in an isolated environment with sustained realistic quiz/calculator workloads. The production concurrency smoke test is insufficient for peak-load sign-off.

## Prepared operations and 50-user verification

At the user's request, free-service workflows and tools are now committed on
`main` through `977264d`. See [activation and recovery instructions](production-operations-setup.md).

- **Backend and safety checks:** 48 backend tests passed; six operations safety
  tests passed. A subsequent focused test passed for the version-safe reminder
  runner route. Tests simulate unavailable MongoDB, empty catalogue, unauthorized
  access, dry runs, concurrent runners, absent consent and ambiguous provider
  failures; no customer mail is sent.
- **Real synthetic recovery drill passed:** [Operations verification run
  40194634892](https://github.com/neerajgarg1109/app/actions/runs/40194634892)
  dumped a disposable MongoDB 8.0 database, encrypted the archive, restored it into
  an isolated database, and checked all documents, BSON IDs/dates and indexes.
  Existing restore targets and remote/production restore destinations are refused.
  This proves the tooling against synthetic data, not recovery from a production
  archive; production backups remain disabled until configured and approved.
- **50-user isolated test passed:** 2,187 journeys in 60 seconds; zero failures;
  median 308ms, P95 965ms, maximum 1,395ms. One-CPU/512-MiB API container, real
  disposable MongoDB, one worker, 50 closed-loop users with one-second think time.
  Mix: quiz submission with database save/readback, value calculation and catalogue
  reads. Production Atlas/network, shared-CPU contention, geography and long-term
  load are outside this test. Raw measurements: `isolated-load-result-2026-10-25.json`.
- **Database-aware readiness deployed:** `/api/ready` checks MongoDB and a usable
  catalogue, returning generic HTTP 503 on failure. The external read-only monitor
  passed against production. The actual DO component was discovered to have a TCP
  readiness check (the earlier `/api/` description referred to the committed app
  spec). Its live settings have now been saved as HTTP `/api/ready`, every 10s,
  traffic paused after nine failures and resumed after one success. The setting
  was observed in the saved UI; rollout status is verified separately.
- **Monitoring schedule installed:** a best-effort GitHub Actions check every 15
  minutes verifies website assets, TLS, readiness and catalogue. GitHub account
  settings confirm failure notifications on GitHub and by email, failed workflows
  only. The user explicitly authorized one simulated failure notification to the
  existing account email. [Run 40194916681](https://github.com/neerajgarg1109/app/actions/runs/40194916681)
  intentionally failed without interrupting production. The user confirmed receipt
  of this test alert, verifying the tested GitHub-to-inbox notification path.
- **Consented reminder schedule prepared, gated off:** the hourly workflow defaults
  to dry run and requires a narrow `REMINDER_RUNNER_TOKEN` plus explicit enable/send
  flags. Atomic claims prevent duplicate sends by concurrent runners; ambiguous
  deliveries require human review. Partial-quiz reminders are excluded because
  their stored records do not establish reminder consent.
- **Encrypted backup schedule prepared, gated off:** daily logical dump, AES-256-GCM
  encryption before upload, three-day encrypted artifact retention. This repository
  is public. No customer data has been exported to GitHub. Activation requires
  approval of that specific data flow, a dedicated read-only database credential,
  an independently stored encryption key, an approved runner network path and
  quota/budget checks. No Atlas network permissions were expanded or paid backups
  enabled. Logical dumps are not point-in-time snapshots.

Full operational sign-off still requires an actual approved production backup and
isolated restore, enabled/verified reminder credentials and dry run, a dependable monitoring schedule,
and validation of production network effects at the target load.
