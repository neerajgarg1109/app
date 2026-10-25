# Free-tier operations preparation

Prepared for the launch target of **50 concurrent active users**. Preparation is
not evidence that production backups, notification delivery or scheduled emails
have been activated successfully.

## What runs and what remains gated

- `production-monitor.yml`: read-only HTTPS website, current JS/CSS asset,
  database-aware `/api/ready`, and catalogue checks every 15 minutes. A failed
  check fails the Actions run. Enable GitHub Actions failure notifications in the
  intended recipient's GitHub notification settings and verify a controlled test
  failure arrives. No customer email address is used by this monitor.
- `production-backup.yml`: daily at 02:13 IST, **disabled** until repository
  variable `CARDIQ_BACKUPS_ENABLED=true`. Uses environment `production-backups`.
  Uploads only AES-256-GCM encrypted MongoDB archives to GitHub Actions artifacts;
  archives expire after **three days**. The decryption key must also be held
  independently in the owner's password manager. Loss of the key prevents recovery.
- `production-reminders.yml`: hourly at minute 19, **disabled** until repository
  variable `CARDIQ_REMINDERS_ENABLED=true`. Environment `production-reminders`.
  Defaults to a dry run; sending requires `CARDIQ_REMINDERS_SEND=true`. Only
  review follow-ups with explicit `review_consent=true` are eligible. Incomplete
  quiz reminders are deliberately excluded: existing partial-session records do
  not record reminder consent.
- `operations-verification.yml`: a synthetic BSON/index backup/restore drill and
  50-user load test using a real disposable MongoDB 8.0 service. The API container
  is constrained to **one CPU and 512 MiB**, with the production Dockerfile and
  one worker. Email is disabled and no production URI or token is provided.

GitHub cron schedules are best-effort and can be delayed or disabled by the
platform. They are not a precise scheduler or an always-on monitoring service.
The prepared backup is a logical dump of a live database, not a cross-collection
point-in-time snapshot; application writes during dumping can produce skew.

## Activation checklist — credentials stay out of chat

Before enabling backups, approve the specific data flow: **production database
contents (including customer records), encrypted on a GitHub runner, stored in this
repository's GitHub Actions artifacts for three days**. Repository workflows will
receive a dedicated read-only MongoDB URI and a backup encryption secret. This
is new security-sensitive access and must be deliberately configured by the owner.
Do not reuse an unrestricted admin database user.

1. Confirm repository visibility, artifact access, artifact size, remaining Actions
   allowance and a hard spending budget before activation. Public repository
   artifacts may be downloadable by other authenticated GitHub users; encryption
   is mandatory. This is short retention, not archival or provider-independent
   disaster recovery. Keep an independent encrypted copy for longer recovery.
2. In Atlas, create a dedicated user with `read` on the production database only.
   Keep TLS validation enabled. GitHub-hosted runner egress changes: use an
   already-approved network path or restricted runner. **Do not open Atlas to
   `0.0.0.0/0` to make a workflow pass.** If no suitable path exists, keep the
   backup job disabled and use an approved runner or a managed backup option.
3. Add environment secrets `MONGODB_BACKUP_URI` and `BACKUP_ENCRYPTION_KEY` to
   `production-backups`; add repository variable `CARDIQ_DATABASE_NAME` with the
   actual production DB name. The encryption key is base64 for 32 random bytes.
   Owner creates and stores it privately; do not paste it into the chat.
4. Protect the backup environment, enable `CARDIQ_BACKUPS_ENABLED`, run one
   backup, download the encrypted artifact and restore into an isolated local
   MongoDB 8.0 database. Verify collection counts, representative BSON records,
   indexes, archive age and usable credentials. The restore command refuses
   remote hosts and existing target DBs; it never uses `--drop`.
5. For reminders, generate a dedicated random token privately and add it to DO
   as encrypted runtime `REMINDER_RUNNER_TOKEN` and to the `production-reminders`
   GitHub environment under the same name. This token can call only the review
   reminder endpoint, not other admin endpoints. Start with a dry run. Verify
   synthetic follow-ups in an isolated environment before enabling sends. A
   production test message requires an explicitly authorized recipient.
6. Review ambiguous reminder deliveries (`delivery_state=needs_review` or stale
   `claimed`) manually against Resend. They are not retried automatically, to
   avoid duplicate emails after a provider timeout. Each call claims at most 20
   records; workflow concurrency prevents overlapping scheduled invocations and
   database claims also protect concurrent manual invocations.
7. Configure DO's live health check path to `/api/ready` after deployment verifies
   the route. The committed app spec uses it; editing that spec alone does not
   update an app originally created through the UI.

## Verification commands

```sh
python -m unittest discover -s ops/tests -v
python ops/restore_drill.py
python ops/load_test.py --users 50 --seconds 60 --output load-report.json
python ops/monitor.py
```

The restore drill requires `mongodump`, `mongorestore`, Python `cryptography`,
`pymongo`, and a local disposable MongoDB service. It preserves 261 synthetic
catalogue records, BSON IDs/dates and index definitions. It does not restore a
real production archive, and therefore cannot certify production recovery.

The load test uses 50 closed-loop users, a one-second think time, anonymous quiz
submission plus saved-result retrieval, calculator and catalogue traffic. Its
initial acceptance target is zero failed journeys and P95 <= 2 seconds for 60
seconds. This is an explicitly bounded test, not a soak test. Runner CPU scheduling,
network latency, real Atlas limits and multi-region users differ from production.
A failed result is a capacity finding; do not relabel it as a passing launch test.

## Costs and evidence

These workflows use ordinary GitHub-hosted Linux runners and require no new paid
service. They can still consume account quotas and incur overages if spending is
allowed. Do not promise zero cost without checking the account's allowance/budget.
A three-day artifact retention window is intentionally small, but its storage
usage must still be measured on an actual encrypted production archive.

References: [MongoDB backup tooling](https://www.mongodb.com/docs/database-tools/mongodump/),
[GitHub Actions billing and usage](https://docs.github.com/en/actions/concepts/billing-and-usage).
