# CardIQ production deployment

Selected launch plan: DigitalOcean App Platform, Bangalore (`blr`), one shared
vCPU and 512 MiB RAM (`apps-s-1vcpu-0.5gb`), $5/month before tax and overages.
The frontend stays on GitHub Pages; MongoDB Atlas is billed separately.

## Deploy the API

1. Push `.do/app.yaml` and `backend/Dockerfile` to `main`.
2. In DigitalOcean App Platform, create an app from the GitHub repository
   `neerajgarg1109/app`. Import the app spec in `.do/app.yaml`. Authorize GitHub
   access if requested. Confirm Bangalore, one instance and the $5 size before
   creating the paid service.
3. Set `MONGO_URL` as an encrypted secret with the production Atlas connection
   string. Use a dedicated database user with access to `cardiq_prod`. This name
   creates a separate database: it does not migrate existing customer or admin data.
   If existing data must be retained, migrate and verify it before switching traffic.
4. Set `ADMIN_TOKEN` as an encrypted, randomly generated secret. Optional role
   tokens (`ADMIN_VIEWER_TOKEN`, `ADMIN_EDITOR_TOKEN`, `ADMIN_PUBLISHER_TOKEN`)
   and email settings can also be added as encrypted secrets when needed.
   For direct email delivery, follow [email setup](email-setup.md). Leave email
   disabled until an independently owned provider and verified sender are configured.
5. Configure Atlas network access for the service's supported outbound addresses.
   Confirm connectivity before switching traffic. Dedicated egress IPs are a
   separate paid feature, outside the $5 budget.
6. Deploy. The app listens on port 8080 with a single Uvicorn worker. Startup seeds
   the card catalogue and creates database indexes. The `/api/` probe returns
   successfully after startup; it does not continuously check database health.
7. Check the assigned HTTPS URL: `/api/` must respond and `/api/cards?view=summary`
   must return cards. Verify a recommendation, admin access and a saved record
   against the production database before directing customers to it.

## Switch the frontend

1. Set the GitHub repository Actions variable `CARDIQ_BACKEND_URL` to the assigned
   DigitalOcean HTTPS origin, with no trailing slash and no `/api` suffix.
2. Run the **Deploy frontend to GitHub Pages** workflow. The variable controls
   both the React API origin and scheduled catalogue refreshes.
3. Verify the quiz and recommendation flow from the published frontend. Check
   browser network requests reach DigitalOcean and CORS succeeds. The default
   allowed origin is `https://neerajgarg1109.github.io` (origins never include paths).
4. When connecting a custom domain, update `PUBLIC_APP_URL`, `CORS_ORIGINS` and
   the frontend public URL settings to match the chosen domains. Rebuild the frontend.
5. Keep Render available until the switch is verified. To roll back, restore the
   previous `CARDIQ_BACKEND_URL` and rerun the Pages workflow. Account for any
   writes made since the switch before rolling back to a different database.

## Operate the $5 service

Monitor memory, restarts, API errors and latency during launch. Use the single
worker configuration on 512 MiB; move to the $10 1 GiB fixed size if measured
memory pressure or latency requires it. Set up uptime monitoring and verify Atlas
backup/restore procedures. The $5 plan has no automatic scaling.

This repository contains deployment preparation only. The paid app, secrets, Atlas
access, DNS and traffic switch must be configured in the respective accounts.

References: [pricing](https://docs.digitalocean.com/products/app-platform/details/pricing/),
[app specification](https://docs.digitalocean.com/products/app-platform/reference/app-spec/),
[Dockerfile builds](https://docs.digitalocean.com/products/app-platform/reference/dockerfile/).
