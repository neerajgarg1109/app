# Production operations status — 26 October 2026

Code on production: `977264d`. DigitalOcean configuration deployment
`4cdf2f2f-73e2-4d9b-bef1-ce8417913135` is live and the component reports Healthy.
The saved readiness probe is HTTP `/api/ready` every 10 seconds; traffic pauses
after nine failed checks and resumes after one success. A fresh external monitor
run passed website assets/TLS, MongoDB-aware readiness and a usable catalogue.

## Verified

- **50-user isolated workload:** 2,187 journeys in 60 seconds, zero failures,
  median 308ms, P95 965ms, maximum 1,395ms. Real disposable MongoDB, production
  API Dockerfile, one worker, one CPU and 512 MiB; one-second think time. This
  does not include production Atlas/network/shared-host contention or a long soak.
- **Synthetic encrypted restore:** MongoDB archive encryption/decryption, complete
  BSON record parity and indexes passed. Restore guards refuse remote hosts,
  existing target databases and non-isolated database names. This is tooling
  verification, not a production disaster-recovery certification.
- **Alert delivery:** the authorized controlled failure
  [40194916681](https://github.com/neerajgarg1109/app/actions/runs/40194916681)
  completed intentionally without interrupting production. The user confirmed
  receiving its failure notification. Account settings enable GitHub and email
  notifications for failed workflows only.
- **Normal monitoring:** scheduled runs
  [40213709430](https://github.com/neerajgarg1109/app/actions/runs/40213709430) and
  [40225619872](https://github.com/neerajgarg1109/app/actions/runs/40225619872)
  passed. They started at 16:51 and 19:21 UTC on 25 October respectively.

## Remaining activation and verification

1. **Monitoring timing:** these scheduled checks were 150 minutes apart despite
   the configured 15-minute cron schedule. Successful checks and tested alerts
   do not establish timely outage detection. Keep this as a supplementary check;
   prepare a dedicated external monitor with a known interval as the primary check.
2. **Production backups:** Atlas managed backups are still off. The encrypted
   logical-backup workflow is prepared but disabled. No customer archive was
   uploaded. The owner explicitly chose to keep production exports disabled on 26 October.
   Do not activate or export customer data without a new explicit instruction.
   Future activation would require a dedicated read-only database credential,
   private key custody, network access and storage/quota checks. A real production archive
   must then be restored in isolation and verified. Three-day retention and a
   live logical dump do not provide point-in-time or long-term archival recovery.
3. **Automatic reminders:** the consent-only review runner is prepared but gated
   off. The observed scheduled run
   [40214790463](https://github.com/neerajgarg1109/app/actions/runs/40214790463)
   was skipped, as expected. A narrow runner token must be added to DO and GitHub;
   then verify a production dry run before enabling actual sends. GitHub cron
   delays also apply to this runner, so delivery times are best-effort.
4. **Production capacity:** the isolated 50-user test passed; actual Atlas/network
   and sustained production load remain outside the test. No heavy production
   traffic or customer-email batch was generated to obtain this result.

Preparation, workflow gates and activation commands are documented in
[production-operations-setup.md](production-operations-setup.md). No full
operational sign-off is claimed while backup activation and timely monitoring
remain incomplete.

## Dedicated monitoring handoff

Better Stack advertises a free tier of ten monitors with three-minute checks.
The owner needs a new account; the free signup tab is open. Account creation
requires the owner to accept terms and complete the magic-link login. Website
and API-readiness monitors can be configured after sign-in. Until then, GitHub
checks are supplemental only and no dedicated monitoring activation is claimed.
