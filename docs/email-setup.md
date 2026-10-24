# Email setup

CardIQ sends directly through an independently owned Resend account over HTTPS.
No platform email proxy or additional SDK is used. Email defaults to disabled:
the catalogue, recommendations, calculator and admin do not require email credentials.
An explicit email request returns 503 until configuration is complete. Quiz welcome
email failures remain non-fatal and failed sends are not marked delivered.

## Enable delivery

1. Create your own Resend account and verify a sending domain you control. Add the
   exact verification/DKIM/SPF DNS records shown by the provider in Namecheap.
   Preserve the website's `@`, `www` and `api` records. A verified sender does not
   create an inbox; use a monitored address for replies.
2. In DigitalOcean, add the following **alongside the existing variables** under
   the API component's environment settings. Do not replace the whole variable list.

   | Variable | Value | Encrypt |
   |---|---|---|
   | `EMAIL_PROVIDER` | `resend` | No |
   | `RESEND_API_KEY` | Your sending API key | Yes |
   | `EMAIL_FROM_ADDRESS` | A sender on the verified domain | No |
   | `EMAIL_FROM_NAME` | `CardIQ` | No |
   | `EMAIL_REPLY_TO` | An address you monitor, optional | No |

3. Set scope to **Run time**, save and wait for the deployment to go live.
4. Choose a test recipient explicitly before sending. Verify welcome and requested
   result emails, then card alerts and both reminder flows using isolated test data.
   Do not trigger existing customer reminder batches as a smoke test.

Provider API documentation: https://resend.com/docs/api-reference/emails/send-email

## Behavior and limits

- All five existing flows use the shared `send_email` helper and retain their
  server-side recipients, templates and content checks.
- Provider rejection, timeout, redirect or missing message ID returns an email
  delivery failure; the API never reports these as a successful send.
- SMTP ports are not needed. No credentials enter frontend bundles.
- Sending routes for card alerts and reminders remain admin-triggered. This cleanup
  does not create a recurring job or send mail to existing subscribers.
- Set `EMAIL_PROVIDER=disabled` to stop email delivery without taking the API offline.
- Old credentials have been removed from the local environment file; previously
  issued keys still need revocation in their issuing account. Removal is not revocation.
