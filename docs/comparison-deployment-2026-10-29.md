# Comparison engine deployment

Release: 34d75a333c7b24826542012745f4e0a4dc6afef7. Both frontend deployment and isolated operations verification succeeded. The first frontend attempt found a build-only pymongo dependency; the follow-up release moved the database import inside seed_cards. Static generation was then validated without site packages and catalogue/scoring tests passed (42).

Production checks confirmed all 20 priority routes return the four comparison blocks and raw JSON-LD, all are present in the 459-URL sitemap, and the API serves 268 cards including original Jupiter Edge CSB RuPay. The new application redirect returned 302 to the official issuer with no-store and noindex headers; verification did not follow the issuer application link.

Frontend workflow: https://github.com/neerajgarg1109/app/actions/runs/40927647345
Operations workflow: https://github.com/neerajgarg1109/app/actions/runs/40927647330

PROJECT_HANDOFF.md and internal operational reports remain local. This report is local only. No files were deleted or local Git history reset. Production backup exports remain disabled and Better Stack setup remains deferred.
