# Artwork and admin deployment — 29 October 2026

Release: `b48b8b1a61010af45fce6c3d0d08cc9430d9abba`, based on `d20237f`.

- Frontend: https://github.com/neerajgarg1109/app/actions/runs/40922992493 — succeeded.
- Operations verification: https://github.com/neerajgarg1109/app/actions/runs/40922992595 — succeeded, including image permission/validation/publish tests, matching Docker image build and isolated load workload.

69 application, test, artwork and feature-documentation files were published. The Dockerfile now includes card_images.py and Pillow is installed in the backend. All previously deployed changes from today remain in the parent release.

Production verification: homepage and comparison page HTTP 200; real comparison artwork present; compiled app contains admin upload controls; all 36 new image files return matching Git blob hashes. API readiness HTTP 200, 267 cards, 239 with imageUrl, including the new Amex image. The public image handler returns its expected card-image-specific 404 for an unknown digest; unauthenticated uploads return 401. No production upload or card edit was needed for verification. The first OpenAPI observation was during rollout and showed the old schema; direct image route checks and a fresh OpenAPI schema subsequently confirmed both deployed image endpoints.

Local verification before publication: 129 frontend tests, 23 backend catalogue/image tests, optimized build, 33 static-page tests, 438-URL SEO audit with no errors/orphans. 28 cards still need suitable verified artwork.

The handoff document and its README link stayed local at the user's explicit choice after automatic approval review rejected public disclosure of internal administrative/infrastructure/configuration details. Deployment/audit reports containing operations details also stayed local after review rejected that disclosure. No workaround was used; no rejected document was included in the release tree. Local source, reports and unrelated operations documents remain preserved. No files were deleted from the remote tree. Backup exports remain disabled and Better Stack deferred.

This post-deployment record is local only. Local Git HEAD remains stale; compare file hashes with remote main before deciding what is undeployed.
