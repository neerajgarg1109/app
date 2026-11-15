# CardIQ production hosting options for India

Last reviewed: 19 October 2026

## Executive recommendation

For CardIQ's first production release, the best balance of Indian-user latency, predictable cost and low operational effort is:

- **Frontend:** Cloudflare Pages or the existing GitHub Pages deployment, behind the final custom domain.
- **API:** DigitalOcean App Platform in Bangalore, initially on the 1 GiB fixed shared plan.
- **Database:** MongoDB Atlas in an Indian region on the same cloud provider where practical.
- **DNS, TLS and edge protection:** Cloudflare.
- **Production hostnames:** `www.<domain>` for the customer site and `api.<domain>` for FastAPI.

The expected launch infrastructure cost is approximately **$18–$40 per month (about ₹1,620–₹3,600 at the planning rate below), before tax and domain registration**, depending mainly on the MongoDB tier. The application host itself starts at $10 per month.

Google Cloud Run in Mumbai is the strongest alternative when automatic scaling and usage-based cost are more important than billing simplicity. It may be cheaper at low traffic, but requires more cloud configuration and careful cold-start control.

## Scope and pricing assumptions

This review is specific to CardIQ's current stack:

- React static frontend
- FastAPI/Uvicorn backend
- MongoDB Atlas
- GitHub source repository and automated deployment
- Indian users as the primary audience
- Low initial traffic, with unpredictable growth
- Recommendation requests that should feel fast and should not wait for a sleeping service

Prices below are public list prices checked on 19 October 2026. They exclude GST or other taxes, domain registration, paid support, excess bandwidth, backups not included in the plan and third-party monitoring.

For easy comparison, USD prices are also shown in INR using a **budgeting rate of ₹90 per US dollar**. This is not a foreign-exchange quote; the actual card or invoice conversion rate will vary.

## Ranked shortlist

| Rank | Option | Indian location | Starting application cost | Operational effort | Best use |
|---|---|---:|---:|---|---|
| 1 | DigitalOcean App Platform | Bangalore | $10/month ≈ ₹900 for 1 GiB | Low | Best practical launch choice |
| 2 | Google Cloud Run | Mumbai or Delhi | Roughly $0–$25/month ≈ ₹0–₹2,250 at early traffic | Medium | Best autoscaling and long-term flexibility |
| 3 | Azure Container Apps | Central India, South India and Jio India Central | Often $0 at very low usage; budget $10–$30/month | Medium | Good managed alternative, especially with Microsoft experience |
| 4 | AWS App Runner | Mumbai | Budget $15–$35/month for a small warm API | Medium | Managed AWS deployment with predictable warm availability |
| 5 | E2E Cloud | India/Delhi NCR | FaaS from ₹405/month; general compute is typically higher | Medium to high | Indian provider, INR billing and local support |

The low-cost unmanaged alternatives—Hostinger VPS, AWS Lightsail, Oracle Cloud Compute and a regular E2E virtual machine—are covered later. They are inexpensive in cash terms but require CardIQ to operate the server. BigRock was also evaluated, but its inexpensive shared and cloud-hosting products are not a clean fit for the Python backend.

## 1. DigitalOcean App Platform — recommended

### Why it fits

DigitalOcean App Platform can deploy directly from GitHub, build the FastAPI service, inject encrypted environment variables, issue TLS certificates and redeploy after a push. Bangalore is available for dynamic applications. This removes the overseas API round trip present in the current Render deployment.

### Published pricing

| Plan | Resources | Monthly price | Planning INR |
|---|---:|---:|---:|
| Fixed shared | 1 vCPU, 512 MiB, 50 GiB transfer | $5 | ₹450 |
| Fixed shared | 1 vCPU, 1 GiB, 100 GiB transfer | $10 | ₹900 |
| Shared, manually scalable | 1 vCPU, 1 GiB, 150 GiB transfer | $12 | ₹1,080 |
| Shared, manually scalable | 1 vCPU, 2 GiB, 200 GiB transfer | $25 | ₹2,250 |
| Dedicated egress IP | Per application | $25 | ₹2,250 |

The recommended launch size is **1 vCPU and 1 GiB for $10/month**. The 512 MiB option can work, but it leaves little safety margin for the Python process, imports and concurrent requests.

### Advantages

- Indian application region
- Always-on process without a scale-from-zero delay
- Simple GitHub deployment and rollback workflow
- Predictable monthly ceiling
- Automatic HTTPS and custom-domain support
- Far less server administration than a VPS

### Limitations

- Fixed shared plans do not autoscale.
- A dedicated egress IP costs $25/month. Without it, MongoDB Atlas access must use the platform's supported outbound addressing approach or a broader Atlas network rule.
- Shared CPU can have some performance variation.

Sources: [DigitalOcean App Platform pricing](https://docs.digitalocean.com/products/app-platform/details/pricing/), [App Platform regional availability](https://docs.digitalocean.com/products/app-platform/details/availability/), [creating an App Platform application](https://docs.digitalocean.com/products/app-platform/how-to/create-apps/).

## 2. Google Cloud Run

### Why it fits

Cloud Run runs the existing FastAPI application as a container, automatically scales request capacity and is available in both Mumbai (`asia-south1`) and Delhi (`asia-south2`). It is likely to have the lowest compute bill at low traffic.

### Published pricing model

For request-based services, Google's published default rates are:

- Active CPU: $0.000024 per vCPU-second
- Idle CPU for a configured minimum instance: $0.0000025 per vCPU-second
- Active or idle memory: $0.0000025 per GiB-second
- Requests: $0.40 per million
- Monthly free grant: 180,000 vCPU-seconds, 360,000 GiB-seconds and two million requests

A continuously warm minimum instance using 1 vCPU and 512 MiB has a theoretical idle compute baseline of roughly **$9.72/month before free grants and active processing**. A reasonable CardIQ launch budget is **$10–$25/month**, although a scale-to-zero service may remain inside the free grant.

### Advantages

- Mumbai and Delhi regions
- Excellent automatic scaling
- Pay only for measured use
- Managed revisions, traffic splitting and rollbacks
- Strong monitoring and reliability tooling

### Limitations

- Scale-to-zero can cause a first-request delay. CardIQ should either configure one minimum instance or prove through load testing that cold starts meet the target.
- Direct Cloud Run domain mapping is not offered in every region, including Mumbai. A load balancer, Firebase Hosting or Cloudflare proxy arrangement may be needed for `api.<domain>`.
- Billing is less predictable than a fixed $10 plan.

Sources: [Cloud Run pricing](https://cloud.google.com/run/pricing), [Cloud Run locations](https://cloud.google.com/run/docs/locations), [Cloud Run service-level agreement](https://cloud.google.com/run/sla).

## 3. Azure Container Apps

### Why it fits

Azure Container Apps is a managed container service with HTTP-based scaling and scale-to-zero support. The service is available in Central India, South India and Jio India Central, depending on the selected workload profile.

### Published pricing model

Azure publishes the following monthly free grant for the consumption plan:

- 180,000 vCPU-seconds
- 360,000 GiB-seconds
- Two million requests

The regional per-second rate is selected dynamically on Microsoft's pricing page and may vary by agreement and currency. For planning, allow **$0–$15/month for a low-traffic scale-to-zero API** and **$10–$30/month when retaining a warm minimum replica**. A final quote should be saved from the Azure pricing calculator before purchase.

### Advantages

- Multiple Indian regions
- Managed containers and automatic scaling
- Free grant suitable for early traffic
- Minimum replicas can reduce cold-start delays
- Good option if the team already uses Microsoft tooling

### Limitations

- More concepts and configuration than DigitalOcean
- Regional price is not as immediately transparent
- Azure networking and observability can become complex

Sources: [Azure Container Apps pricing](https://azure.microsoft.com/en-in/pricing/details/container-apps/), [Container Apps Express regions](https://learn.microsoft.com/azure/container-apps/express-overview), [Azure regions](https://learn.microsoft.com/azure/reliability/regions-list).

## 4. AWS App Runner

### Why it fits

App Runner deploys source from GitHub or a container image and manages TLS, deployment and scaling. AWS lists App Runner in Mumbai (`ap-south-1`). Unlike a free sleeping host, its default provisioned instance keeps memory available while idle.

### Published pricing model

AWS's reference rates for several base regions are:

- Provisioned memory: $0.007 per GB-hour
- Active CPU: $0.064 per vCPU-hour
- Active memory: $0.007 per GB-hour

AWS's own lightweight, latency-sensitive example for a 1 vCPU/2 GiB service is **$25.50/month** in the example region. Mumbai pricing can differ, so use a planning range of **$15–$35/month** and confirm it in the AWS calculator.

### Advantages

- Indian AWS region
- GitHub or container-image deployment
- Managed scaling and TLS
- Warm provisioned memory reduces cold starts
- Natural path to other AWS services later

### Limitations

- More expensive than DigitalOcean for a small, mostly idle API
- AWS permissions, logging and networking require more expertise
- Build, automated deployment and CloudWatch usage can add charges

Sources: [AWS App Runner pricing](https://aws.amazon.com/apprunner/pricing/), [App Runner architecture and GitHub support](https://docs.aws.amazon.com/apprunner/latest/dg/architecture.html), [App Runner regional endpoints](https://docs.aws.amazon.com/general/latest/gr/apprunner.html).

## 5. E2E Cloud — Indian-provider option

### Why it fits

E2E Networks is an Indian cloud provider with INR billing and India-based infrastructure and support. It is worth retaining as a negotiating and sovereignty option, even though its managed application workflow is less turnkey than App Platform or Cloud Run.

### Published pricing

- CPU Functions as a Service has a **₹405 monthly activation charge**, excluding GST.
- That activation includes the first 450,000 GB-seconds; additional CPU usage is ₹0.0009 per GB-second.
- E2E advertises CPU-intensive general compute starting around **₹3.1/hour**, which is approximately ₹2,263 for 730 hours before storage, bandwidth and tax.

The functions product would require validating that CardIQ's FastAPI request lifecycle, startup behavior and MongoDB connection reuse work well in E2E's FaaS model. A regular E2E compute instance requires server administration.

### Advantages

- India-hosted infrastructure and INR billing
- Local support hours and no USD exchange-rate exposure
- Low published FaaS entry price
- Potentially useful when Indian data-location requirements become stricter

### Limitations

- More engineering validation is required for the existing application.
- Managed deployment and observability are not as mature or as familiar as the hyperscaler offerings.
- A virtual machine shifts patching, hardening, deployment and recovery to CardIQ.

Sources: [E2E FaaS billing](https://docs.e2enetworks.com/docs/myaccount/functions/faas_billing/), [E2E compute product information](https://www.e2enetworks.com/product/l4), [E2E 2026 pricing update](https://docs.e2enetworks.com/docs/myaccount/billing/pricing-update-july-2026/).

## Lower-cost VPS alternatives

These can host CardIQ in India but are not the recommended first-production path for a small team.

### Hostinger VPS in India — best budget VPS alternative

Hostinger can run CardIQ, but the important product distinction is that **FastAPI requires Hostinger VPS**. Hostinger's own framework-support documentation says Python, Django and Flask are supported exclusively on VPS hosting because they require root access. Its shared, Web Apps and managed cloud-hosting plans should therefore not be selected for the CardIQ backend.

| VPS plan | Resources | Introductory price | Published renewal price |
|---|---:|---:|---:|
| KVM 1 | 1 vCPU, 4 GiB RAM, 50 GB NVMe, 4 TB bandwidth | ₹599/month | ₹999/month |
| KVM 2 | 2 vCPU, 8 GiB RAM, 100 GB NVMe, 8 TB bandwidth | ₹799/month | ₹1,199/month |
| KVM 4 | 4 vCPU, 16 GiB RAM, 200 GB NVMe, 16 TB bandwidth | ₹1,099/month | ₹2,399/month |

These advertised monthly rates require the displayed multi-year purchase; the checkout total is paid upfront and GST is additional. Hostinger advertises Indian data-centre availability, a 1 Gbps network, a public API, weekly backups, firewall controls and Docker templates. For CardIQ, KVM 1 has ample memory at a lower promotional price than the recommended DigitalOcean plan.

The trade-off is responsibility. Hostinger describes VPS as customer-controlled: CardIQ would need to maintain Ubuntu, Docker, Nginx or Caddy, TLS, system packages, application restarts, security patches, firewall rules, monitoring, log rotation, database egress rules, backups and rollback automation. Weekly VPS backups alone are not a substitute for MongoDB backups or a tested recovery process.

**Verdict:** viable when minimizing cash cost is more important than minimizing operational risk. It is the strongest low-cost VPS option reviewed, but it does not replace the managed-platform recommendation for a first production release. If selected, use KVM 1 in India and budget the renewal rate—not only the promotional rate.

Sources: [Hostinger VPS pricing and specifications](https://www.hostinger.com/in/vps-hosting), [Hostinger Python and framework support](https://www.hostinger.com/support/which-programming-languages-and-frameworks-are-supported-at-hostinger/), [Hostinger infrastructure and Indian location](https://www.hostinger.com/in/technology).

### BigRock — not recommended for the CardIQ backend

BigRock's low advertised prices mostly describe shared, cPanel, WordPress or managed website hosting rather than a managed Python application platform.

| BigRock product | Advertised price | CardIQ suitability |
|---|---:|---|
| Linux shared hosting | ₹69/month introductory; ₹409/month renewal | Static frontend only; not suitable for FastAPI |
| Cloud Hosting Starter SSD | ₹479/month introductory; ₹619/month renewal | India option with 2 cores/2 GiB, but cPanel-oriented and no verified always-on Python/FastAPI runtime |
| Business Hosting Starter | ₹639/month introductory; ₹1,249/month renewal | Website/cPanel product; not a clean FastAPI deployment target |
| Self-managed VPS | From ₹329/month | Technically viable with root access, but the prominently listed entry VPS shows a USA server location |
| Dedicated server | From ₹5,199/month | Can run CardIQ and is available in India, but excessive for launch |

BigRock does offer India-hosted shared/cloud products and advertises India or USA selections on several plans. It also has managed VPS material referring to India and Asia locations. However, the public product information does not establish a GitHub-to-FastAPI managed deployment flow, Python process management, container deployment, automatic application rollback or the exact India VPS configuration and renewal cost as clearly as the shortlisted platforms.

The shared or cloud plans could host a separately built static frontend, but GitHub Pages or Cloudflare Pages can already do that without another paid origin. The backend would need a VPS or dedicated server, bringing back the same patching and operations burden as Hostinger or Lightsail without a compelling CardIQ-specific advantage.

**Verdict:** suitable as a domain registrar, email provider or conventional website host; not recommended as CardIQ's primary application host. If BigRock is considered further, obtain written confirmation of the server city, root access, Docker support, dedicated IP, backup retention, SLA, renewal price and whether support covers a FastAPI/Uvicorn deployment before paying.

Sources: [BigRock cloud-hosting plans](https://www.bigrock.in/cloudhosting), [BigRock shared-hosting plans](https://www.bigrock.in/web-hosting), [BigRock managed VPS](https://www.bigrock.in/managed-vps-hosting), [BigRock product summary and VPS location shown](https://www.bigrock.in/), [BigRock dedicated-server locations](https://ss.bigrock.in/dedicated-servers.php).

### AWS Lightsail in Mumbai

| Plan | Resources | Monthly price | Planning INR |
|---|---:|---:|---:|
| Linux IPv4 | 2 vCPU, 1 GiB RAM, 40 GB SSD | $7 | ₹630 |
| Linux IPv4 | 2 vCPU, 2 GiB RAM, 60 GB SSD | $12 | ₹1,080 |

Mumbai receives half of the headline transfer allowance: 1 TB on the 1 GiB plan and 1.5 TB on the 2 GiB plan. Lightsail is good value, but we must configure and maintain Ubuntu, Docker or systemd, Nginx, TLS renewal, firewall rules, logging, patches, monitoring, backups and rollback procedures.

Sources: [Lightsail bundles](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-bundles.html), [Mumbai transfer allowances](https://aws.amazon.com/lightsail/faq/), [Lightsail pricing](https://aws.amazon.com/lightsail/pricing/).

### Oracle Cloud Infrastructure in Mumbai or Hyderabad

OCI has Mumbai and Hyderabad regions and flexible VM pricing, including an Always Free allowance for eligible resources when capacity is available. It can be cost-effective, but it has similar server-operation requirements to Lightsail and free-capacity availability is not guaranteed. It is better suited to a team already comfortable operating Linux infrastructure.

Sources: [Oracle India cloud price list](https://www.oracle.com/in/cloud/price-list/), [OCI regional footprint](https://www.oracle.com/apac/a/ocom/docs/cloud/oracle-cloud-infrastructure-platform-overview-wp.pdf).

### Fly.io in Mumbai

Fly.io supports Mumbai and offers small, inexpensive machines close to Indian users. It gives more infrastructure control than a conventional PaaS but also requires more Docker, networking and capacity management. It remains a technically credible alternative, but not one of the top five for CardIQ's first supported production release.

Sources: [Fly.io regions](https://fly.io/blog/the-region-consolidation-project/), [Fly.io pricing](https://fly.io/docs/about/pricing/).

## Full-stack monthly budget

Hosting the API is only part of the production cost. MongoDB is likely to become the largest early infrastructure expense.

### MongoDB Atlas

| Tier | Published price | Planning INR | Appropriate use |
|---|---:|---:|---|
| Flex | $8–$30/month | ₹720–₹2,700 | Soft launch, low traffic and early validation |
| Dedicated M10+ | Starts around $60/month | From ₹5,400 | Low-traffic production needing dedicated resources and stronger backup controls |
| Dedicated M30+ | Region-dependent | Region-dependent | MongoDB's recommended starting class for sustained production workloads |

MongoDB describes Flex as shared infrastructure better suited to learning and exploration. It allows up to 5 GB and 100 operations per second at the $8 base, scales with operations and is capped at $30. M10 and M20 can serve low-traffic production, but use burstable infrastructure. CardIQ can soft-launch on Flex only if monitoring, exports/backups and a tested upgrade path are in place; otherwise M10 is the safer production choice.

Sources: [Atlas Flex pricing](https://www.mongodb.com/docs/atlas/billing/atlas-flex-costs/), [Atlas billing and dedicated starting cost](https://www.mongodb.com/docs/atlas/billing/billing-breakdown-optimization/), [Atlas sizing guidance](https://www.mongodb.com/docs/atlas/sizing-tier-selection/).

### Estimated launch scenarios

| Scenario | Frontend | API | Database | Estimated monthly total before tax |
|---|---:|---:|---:|---:|
| Lean soft launch | $0 | DigitalOcean $10 | Atlas Flex $8–$30 | **$18–$40 / ₹1,620–₹3,600** |
| Scalable soft launch | $0 | Cloud Run $0–$25 | Atlas Flex $8–$30 | **$8–$55 / ₹720–₹4,950** |
| Managed production baseline | $0 | DigitalOcean $10–$25 | Atlas M10 from $60 | **From $70 / ₹6,300** |
| AWS managed baseline | $0 | App Runner $15–$35 | Atlas M10 from $60 | **From $75–$95 / ₹6,750–₹8,550** |
| Self-managed budget host | $0 | Lightsail $7–$12 | Atlas Flex $8–$30 | **$15–$42 / ₹1,350–₹3,780**, plus operations |
| Hostinger promotional VPS | $0 | KVM 1 ₹599 | Atlas Flex ₹720–₹2,700 | **₹1,319–₹3,299**, plus operations and GST |
| Hostinger VPS after renewal | $0 | KVM 1 ₹999 | Atlas Flex ₹720–₹2,700 | **₹1,719–₹3,699**, plus operations and GST |

Static frontend hosting can remain free at launch. Domain registration, transactional email/SMS, analytics, uptime monitoring and log retention should be budgeted separately.

## Can CardIQ run for free?

Yes. The most credible zero-compute-cost configuration is:

- **Frontend:** the existing GitHub Pages deployment — $0
- **API:** Google Cloud Run in Mumbai with minimum instances set to zero — potentially $0 inside the monthly free grant
- **Database:** MongoDB Atlas Free cluster — $0
- **Domain:** keep the current `github.io` and provider URLs — $0, or pay separately for a branded domain

Cloud Run's request-based free grant includes 180,000 vCPU-seconds, 360,000 GiB-seconds and two million requests each month. It can run the existing Python application and scales to zero when unused. Azure Container Apps offers the same headline free grants and is available in Indian regions, making it the second-best free API option.

MongoDB Atlas Free clusters never expire, but they are intentionally constrained: only one per project, a subset of regions, 512 MB maximum storage and a maximum of 100 combined reads and writes per second. Free-cluster backups are optional, limited and currently a separately billed preview at up to $3/month.

### Free-option comparison

| Option | Normal monthly cost | India region | Main compromise |
|---|---:|---|---|
| GitHub Pages frontend | $0 | Global static delivery | No server-side application runtime |
| Cloud Run API | $0 within free grant | Mumbai/Delhi | Scale-to-zero cold start and usage overage risk |
| Azure Container Apps API | $0 within free grant | Multiple Indian regions | Scale-to-zero cold start and more configuration |
| MongoDB Atlas Free | $0 | Only supported subset shown during setup | 512 MB, shared resources, limited throughput and backup |
| Oracle Always Free VM | $0 when capacity is available | Mumbai/Hyderabad tenancy region | Fully self-managed server and capacity availability risk |
| Render free service | $0 | No India region | Sleeps when idle; unsuitable for the recommendation path |

### Why the fully free stack is not the main launch recommendation

The free stack is appropriate for staging, private beta and a traffic-limited soft launch. It is not the preferred revenue-producing production setup because:

- The API can scale to zero, so the first user after inactivity may wait for startup.
- The free database is shared and has strict storage and throughput limits.
- Robust backup and restore controls are limited.
- A usage spike can either degrade the experience or generate an unplanned cloud bill.
- Free plans can change and generally provide weaker service commitments.

The minimum sensible paid improvement is to keep the frontend free, use an always-on $10 DigitalOcean API and start Atlas on the $8 Flex tier. That produces the earlier **$18/month / approximately ₹1,620 before tax** baseline while removing the most visible cold-start risk and increasing database capacity.

### AWS Free Tier credits

AWS's current new-customer offer can subsidize CardIQ, but it is not permanent free hosting:

- A new customer receives $100 in credits at sign-up.
- Up to another $100 is earned by completing specified AWS exploration activities; the headline is therefore **up to** $200, not $200 automatically.
- The Free account plan ends after six months or when its credits are exhausted, whichever occurs first.
- If the account is not upgraded, AWS closes it when the Free plan ends. AWS retains the resources for 90 days before permanent deletion, but the production service would be unavailable.
- A Paid account plan provides all services and applies eligible credits, but charges the payment method for usage beyond the remaining credits.
- Credits are only available to new AWS customers. Existing or previous AWS customers are not eligible for this new-account offer.
- Credits do not pay for everything; exclusions include Route 53 domain registration, Marketplace purchases and certain upfront commitments.

For CardIQ, an App Runner service budgeted around $15–$35/month could be covered for several introductory months. AWS's own 1-vCPU/2-GiB example is $25.50/month, meaning $100 covers about four example months and $200 about eight—but the no-charge Free account itself still ends after at most six months. MongoDB Atlas remains a separate bill and does not consume AWS credits unless Atlas is purchased through an eligible AWS Marketplace arrangement, which should not be assumed.

AWS Lightsail is a cheaper way to stretch the credit. A $7/month 1-GiB instance would consume only $42 during a six-month Free-plan period. However, it is a self-managed server, so the operational trade-offs described above still apply.

**Recommendation:** treat AWS credits as a launch subsidy, not as the reason to choose AWS. If CardIQ selects App Runner on technical merit, the credits make its first months attractive. Do not put the public production service on the Free account plan because the account closes when the period or balance ends. A Paid plan with strict AWS Budgets alerts is safer, but it permits real charges.

Sources: [AWS Free Tier offer](https://aws.amazon.com/free/), [AWS Free Tier FAQ](https://aws.amazon.com/free/free-tier-faqs/), [Free versus Paid account plans](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html), [AWS credit exclusions](https://aws.amazon.com/awscredits/), [Lightsail and the new credit programme](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-frequently-asked-questions-faq-billing-and-account-management.html).

Sources: [Cloud Run free allowances](https://cloud.google.com/run/pricing), [Azure Container Apps free allowances](https://azure.microsoft.com/en-in/pricing/details/container-apps/), [deploying an Atlas Free cluster](https://www.mongodb.com/docs/atlas/tutorial/deploy-free-tier-cluster/), [Atlas Free limits](https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/), [Atlas Free backups](https://www.mongodb.com/docs/atlas/backup/cloud-backup/free-cluster-backup/), [Oracle Always Free overview](https://docs.oracle.com/cd/E97706_01/pdf/gsg/OCI_Getting_Started.pdf).

## Decision matrix

Scores are CardIQ-specific, from 1 (weak) to 5 (strong).

| Criterion | Weight | DigitalOcean | Cloud Run | Azure | App Runner | E2E |
|---|---:|---:|---:|---:|---:|---:|
| Indian-user latency | 25% | 5 | 5 | 5 | 5 | 5 |
| Ease of operation | 20% | 5 | 4 | 3 | 4 | 2 |
| Predictable early cost | 15% | 5 | 3 | 3 | 3 | 4 |
| Scaling headroom | 15% | 3 | 5 | 5 | 5 | 3 |
| GitHub deployment | 10% | 5 | 4 | 4 | 5 | 2 |
| Observability and rollback | 10% | 4 | 5 | 5 | 5 | 3 |
| Local billing/support | 5% | 3 | 3 | 3 | 3 | 5 |
| **Weighted score / 5** | 100% | **4.50** | **4.35** | **4.05** | **4.35** | **3.30** |

DigitalOcean wins the launch recommendation because CardIQ currently benefits more from operational simplicity and predictable performance than from hyperscale complexity. Cloud Run and App Runner score similarly overall but optimize for different priorities.

## Production requirements independent of provider

Whichever host is selected, release readiness requires all of the following:

1. **Same-region data path.** Put the API and Atlas cluster in India and, where possible, on the same underlying cloud provider. Cross-region database latency can erase the benefit of moving the API.
2. **No free-tier sleeping in the recommendation flow.** Use an always-on service or minimum replica, or demonstrate through measurement that cold-start latency meets the product target.
3. **Custom domains.** Use the final customer domain and `api` subdomain rather than exposing GitHub Pages or provider URLs.
4. **Restricted CORS.** Production CORS should allow only the final customer domains and explicitly approved preview/local origins.
5. **Secret management.** MongoDB credentials, admin keys, JWT secrets and third-party credentials must live in encrypted host settings, never in Git.
6. **Database network controls.** Avoid a permanent `0.0.0.0/0` Atlas rule. Prefer static egress IPs, private networking or the narrowest provider ranges available.
7. **Health checks.** Maintain separate liveness and readiness endpoints; readiness should verify critical startup state without performing an expensive database operation for every probe.
8. **Monitoring.** Track API availability, p50/p95/p99 latency, recommendation failures, MongoDB errors, frontend JavaScript errors and external apply-button failures.
9. **Backups and recovery.** Define the recovery point objective, recovery time objective and a tested restore procedure before collecting meaningful customer data.
10. **Deployment safety.** Use a staging environment, automated tests, production smoke tests and a documented rollback to the previous release.
11. **Cost alerts.** Add monthly budget alerts at 50%, 80% and 100% of the approved amount.
12. **Data governance.** Set retention and deletion rules for optional names, phone numbers, email addresses, quiz answers, ratings and feedback.

## Recommended rollout

### Phase 1 — production foundation

- Buy or confirm the final domain.
- Create a Bangalore DigitalOcean App Platform service using the 1 GiB fixed plan.
- Deploy the current FastAPI backend from GitHub.
- Create a dedicated MongoDB database user for production.
- Place Atlas in an Indian region as close as possible to the API.
- Configure encrypted production variables and restrictive CORS.
- Add `api.<domain>` and verify HTTPS.

### Phase 2 — controlled launch

- Deploy a staging service from a separate branch or environment.
- Run backend, frontend and end-to-end tests against staging.
- Run a measured recommendation-flow load test.
- Verify analytics and affiliate click attribution.
- Enable uptime, error and cost alerts.
- Run a database backup-and-restore exercise.

### Phase 3 — public traffic

- Point the final frontend domain at the static deployment.
- Execute production smoke tests from an Indian network.
- Monitor latency and errors closely for the first 48 hours.
- Move to the $12 or $25 App Platform plan only when measurements justify it.
- Reassess Cloud Run when traffic becomes bursty enough that autoscaling would materially improve cost or reliability.

## Final decision

**Recommended now:** DigitalOcean App Platform, Bangalore, 1 GiB fixed shared service, with MongoDB Atlas in India.

**Recommended when traffic becomes more variable:** Google Cloud Run, Mumbai, with explicit cold-start controls.

**Recommended database posture:** Atlas Flex for a monitored soft launch only; budget for M10 when CardIQ begins collecting material customer data or when revenue-generating traffic makes availability more important than the additional cost.

**Budget VPS fallback:** Hostinger KVM 1 in India. Choose it only if CardIQ explicitly accepts responsibility for server security, updates, monitoring and recovery. BigRock is not recommended for the current FastAPI architecture.
