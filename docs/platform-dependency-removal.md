# Platform dependency removal

The original platform's email proxy, frontend overlay and visual-edit packages,
development configuration adapters, preview image metadata, and preview cron
scripts have been removed. The frontend lockfile was regenerated with Yarn 1.22.22.
The generic local health-check plugin and webpack-dev-server compatibility remain.

The email transport now uses HTTPX to contact Resend directly. It is isolated in
`backend/email_transport.py` and included in the DigitalOcean image. See
[email setup](email-setup.md) for credentials and sender verification. Without a
provider account, real email delivery cannot be verified or enabled.

Historical audit/test documents retain references to the old integration as records
of past behavior. They are not executable dependencies or current setup instructions.
Previously issued credentials must be revoked in the original account; neither
deleting files nor deploying this change revokes them.

No database records, customer data, card content, live admin token or CORS origins
are changed by this migration. No replacement reminder schedule is installed:
the removed cron files only supported the original preview environment.
