# Deployment — 29 October 2026 (Asia/Kolkata)

Published release: `1a612e07975db4138f3364a200ad831f3ac5c4aa`.

- Catalogue/application commit: `4865a8e103b97f98f6934b69f9f985d9b5678c54`.
- Isolated CI runner compatibility fix: `bc854fe4a3c766d0e8fb7455539ef916e9466a2e`.
- Load-test catalogue validation fix: `1a612e07975db4138f3364a200ad831f3ac5c4aa`.
- [Frontend deployment succeeded](https://github.com/neerajgarg1109/app/actions/runs/40751353983).
- [Operations verification succeeded](https://github.com/neerajgarg1109/app/actions/runs/40751354073).

## Scope

Added six verified cards and official images, taking production to 267 cards and 438 sitemap URLs. Explicit conditional-free exclusions for PNB Kiwi and SBM Niyo are carried through API summaries and offline fallbacks. Existing records and unrelated local operations documents were preserved. The existing 1838 news caveat was refreshed.

## Verification

Backend: 74 tests passed. Frontend: 123 tests across 31 suites passed. Production-origin build and 26 static-page tests passed. SEO audit checked 438 URLs with zero errors; eight existing long comparison-title advisories remain.

Live checks confirmed all six new product pages, images and API records return HTTP 200; image bytes match local SHA-256 hashes and fee/access facts match the catalogue. API readiness returned 200. The public sitemap contains all six new pages. PNB Kiwi and SBM Niyo are absent from the lifetime-free category, and both API summary flags are false.

The isolated CI workload completed 2,076 journeys with 50 concurrent users over 60 seconds: zero failures, median 405 ms, P95 1,061 ms, maximum 1,428 ms. This is a synthetic local MongoDB/API container check under resource limits, not a measurement of production traffic or geographical latency.

## CI issues resolved during deployment

The first operations run failed before application tests because MongoDB 8.0 rejected the newer kernel on the Ubuntu 24.04 runner (SERVER-121912). The isolated job now uses Ubuntu 22.04, whose published runner image uses kernel 6.8. Revisit this temporary compatibility pin after MongoDB supports the newer runner kernel.

The next run exposed a hard-coded 261-card assertion in the load harness. It now checks the active repository card-ID set and exact count. The zero-error requirement and P95 <= 2-second limit remain unchanged. The final run passed.

Production backup exports remain disabled. Better Stack setup remains deferred. Search Console sitemap resubmission was unnecessary: the sitemap retains its existing URL and now serves the updated contents.

## Local state

Remote `main` was updated through the GitHub connector with file hash verification and guarded branch publication. Local Git HEAD was not reset or synchronized, and the existing dirty/untracked workspace was preserved. Do not infer undeployed scope from `git status` alone.
