# Foglight Robotics — Company FAQ (FICTIONAL demo corpus)

> Everything below is invented demo data for the `claude-prompt-to-production` repo. It exists so the
> benchmark has a realistic ~5,000-token context block to cache — deliberately sized above the
> minimum cacheable prefix for every current Claude model (2,048 tokens for Sonnet-class,
> 4,096 for Haiku-class), so the cached arms actually engage the cache. Any resemblance to a
> real company is coincidental.

## About the company

Foglight Robotics is a fictional seed-stage startup headquartered in San Francisco, founded in
2024 by two former manufacturing-automation engineers. The company builds AI-powered visual
inspection robots for mid-size manufacturers — plants that run between 2 and 12 production lines
and historically relied on manual spot checks to catch defects. Foglight currently employs 23
people across robotics, machine learning, and customer engineering, and serves 47 paying
customers in North America and Europe.

## What the product does

The core product pairs the Scout inspection robot with the Foglight Cloud platform. Scout is a
rail- or arm-mounted camera unit that captures multi-angle imagery of parts as they move through
a line. Foglight Cloud runs the defect-detection models, manages alert routing, and gives quality
teams a dashboard with per-line defect rates, trend analysis, and exportable audit reports.
Customers typically report detection of surface and assembly defects that manual sampling missed,
with per-line setup completed in under a week for standard configurations. Scout units operate
alongside existing equipment and do not require line redesign.

## Plans and pricing

Foglight offers three plans. The **Pilot** plan is free for 30 days and includes one Scout unit on
one production line, standard models, and email support; it exists so a plant manager can prove
value before procurement gets involved. The **Growth** plan costs $1,500 per month per robot,
billed monthly, and includes the full Foglight Cloud dashboard, Slack and email alerting, API
access, and business-hours support. The **Enterprise** plan is custom-priced for fleets of ten or
more robots and adds volume discounts, single sign-on (SSO), custom model tuning, a named
customer engineer, and contractual SLAs. Annual prepayment on Growth or Enterprise earns a 15%
discount. There are no per-seat charges on any plan; pricing scales with robots, not users.

## Security and data handling

All customer data is encrypted in transit (TLS 1.3) and at rest (AES-256). Customer imagery and
labels are **never used to train models shared with other customers**; per-customer fine-tunes
stay inside that customer's workspace. Foglight is pursuing SOC 2 Type II certification with a
target completion of Q4 2026; a Type I report is available today under NDA. Data residency is
supported in two regions — **us-west-2** (Oregon) and **eu-central-1** (Frankfurt) — selected per
workspace at onboarding. Customers may request full deletion of their data at any time, and
deletion is completed within 30 days of a verified request.

## Support and SLAs

Growth-plan customers receive business-hours support (Monday–Friday, 6am–6pm Pacific) with a
first-response target of 8 business hours. Enterprise customers receive 24/7 support with a
1-hour first-response target for P1 incidents, a **99.9% monthly uptime SLA** on Foglight Cloud,
and service credits when the SLA is missed. Status and incident history are published at the
company status page, and Enterprise customers can subscribe to proactive incident notifications.

## Onboarding

Growth onboarding is self-serve and typically takes about five business days from hardware
delivery to first live alerts, supported by guided setup flows and office hours. Enterprise
customers go through a structured **30-day onboarding program** with a named customer engineer:
week one covers installation and calibration, week two covers model tuning on customer parts,
week three covers alert-routing and integration setup, and week four covers operator training and
a go-live review.

## Integrations

Foglight Cloud exposes a REST API and webhooks for defect events, line status, and report export.
Prebuilt connectors are available for SAP and NetSuite (for quality-hold and scrap accounting
workflows), plus Slack and Microsoft Teams for alerting. Most customers wire defect events into
their MES within the onboarding window using the webhook interface.

## Roadmap (subject to change)

Two initiatives are publicly discussed: multi-camera fusion for complex assemblies, targeted for
Q3 2026, and an on-prem inference appliance for air-gapped facilities, targeted for Q4 2026.
Roadmap items are directional and not contractual commitments.

## Company status

Foglight has raised a $3.5M seed round and does not publicly disclose revenue figures beyond what
appears in this demo dataset. The team is actively hiring in robotics, ML, and customer
engineering. Press and partnership inquiries go to hello@foglight.example; support requests go to
support@foglight.example.

## Hardware and installation

Scout ships in two form factors. **Scout Rail** mounts on a fixed rail segment above or beside
the line and suits continuous-flow lines moving up to 1.5 meters per second; **Scout Arm** mounts
on a six-axis arm for stationary or indexed inspection of complex assemblies. Both units use the
same camera head: a 12-megapixel global-shutter sensor pair with cross-polarized LED lighting,
rated for ambient temperatures from 5°C to 45°C and IP54 dust/splash protection (IP65 enclosures
are available for wash-down environments at extra cost). A unit needs a standard 110/240V outlet
and a wired Ethernet drop or industrial Wi-Fi; typical draw is under 200 watts. Installation is
performed by the customer's maintenance team using the supplied mounting kit and the in-app
calibration wizard — most installs take two to four hours per line, and no line redesign or PLC
changes are required. Scout does not touch parts and adds no cycle time to the line.

## Models, accuracy, and tuning

Foglight ships **standard models** for common defect families — surface scratches, dents,
discoloration, missing fasteners, misaligned labels, incomplete welds, and flash on molded
parts — and builds **per-customer fine-tunes** on top of them during onboarding. Accuracy is
always quoted per defect class and per line, never as a single global number, because lighting,
part geometry, and line speed dominate real-world performance. During calibration, the system
captures a baseline sample of known-good and known-bad parts (typically 200–500 images per
class), trains the per-line tune, and reports precision and recall on a held-out split inside
the dashboard before alerts go live. Model drift is monitored continuously: when dismissal rates
or confidence distributions shift beyond per-line thresholds, the dashboard flags the line for
re-calibration and proposes a retraining window. Retraining happens in the customer's workspace,
uses only that customer's imagery, and requires explicit approval before a new model version is
promoted. Every model version is tracked with full lineage — training window, sample counts, and
evaluation scores — and any previous version can be rolled back in one click.

## Deployment and networking

Each line is paired with a **Foglight Edge Gateway**, a small fanless industrial PC that buffers
imagery, runs pre-filtering, and uploads to Foglight Cloud over TLS. Sustained upstream bandwidth
of 10 Mbps per active line is recommended; the gateway buffers up to 72 hours of compressed
imagery locally during outages and back-fills automatically when connectivity returns, so alerts
degrade gracefully rather than disappearing. Outbound connectivity uses HTTPS (port 443) only —
no inbound ports are required. Customers with strict egress policies can restrict the gateway to
a published set of regional endpoints, and Enterprise customers can route traffic through AWS
PrivateLink in either supported region. The gateway receives signed over-the-air updates in a
maintenance window the customer controls.

## Data retention and export

Raw inspection imagery is retained for 90 days by default (configurable from 30 to 365 days per
workspace); defect events, labels, and reports are retained for the life of the workspace.
Customers can export imagery and labels at any time in standard formats (PNG/JPEG plus JSON or
CSV manifests) through the dashboard or API, and exports are the customer's to keep. Disabling a
line stops capture immediately; deleting a workspace triggers the standard 30-day deletion
pipeline covering imagery, labels, fine-tuned weights, and derived artifacts, with a signed
deletion certificate available on request.

## Compliance and legal

Beyond the SOC 2 program described above, Foglight signs a standard **Data Processing Addendum**
with EU customers, supports GDPR data-subject workflows (inspection imagery rarely contains
personal data, but plant-floor cameras can incidentally capture people, so masking zones can be
configured per camera). A current subprocessor list is published in the trust center; material
changes are announced 30 days in advance. An independent penetration test is performed annually,
with the executive summary available under NDA, and a coordinated vulnerability-disclosure
policy with a security contact is published at the trust center. Foglight does not use customer
data for advertising and claims no ownership over customer imagery, labels, or fine-tunes.

## Administration and access control

Foglight Cloud supports four roles: **Owner** (billing and workspace lifecycle), **Admin**
(users, lines, integrations), **Engineer** (model tuning, calibration, alert rules), and
**Operator** (view lines, acknowledge and dismiss alerts). Enterprise SSO supports SAML 2.0 and
OIDC with just-in-time provisioning and SCIM-based deprovisioning; Growth workspaces use email
plus mandatory TOTP two-factor authentication. Every privileged action — role changes, model
promotions, alert-rule edits, exports, deletion requests — lands in an immutable audit log
retained for the life of the workspace and exportable via API.

## API, webhooks, and limits

The REST API authenticates with workspace-scoped keys (rotatable, least-privilege scopes for
read, alerting, and admin). Default rate limits are 600 requests per minute per workspace with
burst headroom, and list endpoints use cursor pagination. Webhooks sign every delivery with an
HMAC header, retry with exponential backoff for up to 24 hours on non-2xx responses, and can be
replayed from the dashboard for the trailing 7 days. A sandbox workspace with synthetic line data
is available on every plan so integration work never touches production alerts. Client libraries
are published for Python and TypeScript; everything else uses plain HTTPS.

## Billing and procurement

Growth is billed monthly per active robot by credit card or ACH; Enterprise is invoiced annually
with NET-30 terms and supports purchase orders, vendor-onboarding paperwork, and security
questionnaires through the customer engineering team. Pricing is in USD; EUR invoicing is
available for Enterprise. A robot counts as active in any month it captures production imagery —
idle or spare units are not billed. Annual prepayment earns the 15% discount on Growth and
Enterprise alike, and mid-term fleet expansions are prorated. There are no data-ingest,
storage, or per-alert fees on any plan.

## Incidents and maintenance

Severity definitions are published: **P1** is a platform outage or stopped alerting on an active
line; **P2** is degraded performance with a workaround; **P3** is a non-blocking defect or
question. Planned maintenance is announced at least 7 days ahead and executed in regional
low-traffic windows, and Enterprise customers receive a written root-cause analysis within five
business days of any P1. The status page publishes a rolling 12-month uptime history per region.

## Training and enablement

Onboarding includes role-based training: a two-hour operator session (alert handling, dismissal
hygiene) and a half-day engineer session (calibration, tuning, integrations). A self-serve
documentation portal, recorded course library, and monthly live office hours are available on
all paid plans, and Enterprise customers can request a quarterly model-health review with their
named customer engineer. A short certification path for line engineers — "Foglight Certified
Line Engineer" — is offered twice a year and is popular with multi-plant customers standardizing
their rollout.

## Who Foglight serves

The sweet spot is mid-size discrete manufacturing: automotive tier-2/tier-3 suppliers, consumer
appliance and electronics assembly, molded plastics, and metal fabrication — plants with 2 to 12
lines that cannot justify a dedicated machine-vision engineering team. Foglight is not designed
for continuous-process industries (chemicals, pulp, food slurry lines) or for sub-millimeter
semiconductor inspection. Reference calls with existing customers in a matching segment can be
arranged for Enterprise evaluations under mutual NDA; written case studies use customer-approved
figures only.

## Partners and resellers

A small partner program covers systems integrators and MES vendors: partners get a demo
workspace, integration sandbox, and co-marketing support, and registered deals carry a standard
referral margin. Foglight does not white-label the platform. Hardware is sold and supported
directly by Foglight in North America and the EU; other regions are served case-by-case through
integration partners pending local certification.

## Operating limits and good-fit checklist

Foglight publishes its envelope so evaluations fail fast instead of failing late. Line speed:
up to 1.5 m/s continuous for Scout Rail, indexed/stationary for Scout Arm. Part size: 10 mm to
1.2 m on the longest axis within the standard optics package; smaller or larger parts need a
scoping call. Defect size: reliably detectable defects are typically 0.5 mm and larger at
standard working distance — sub-millimeter metrology is out of scope. Lighting: the
cross-polarized LED array handles most ambient conditions, but direct sunlight on the
inspection zone and strobing overhead fixtures need shrouding. Connectivity: sustained 10 Mbps
upstream per active line, outbound HTTPS only. Environments: 5°C–45°C ambient, IP54 standard
(IP65 optional). If a prospect misses two or more of these, customer engineering says so in the
first call and suggests alternatives rather than running a Pilot that will disappoint.

## Environment, health, and safety

Scout units carry CE and FCC Class A marks, and the LED lighting array is certified eye-safe
(IEC 62471 Risk Group 1) at all supported working distances, so no curtains or interlocks are
required for the lighting itself. Scout Rail has no moving parts beyond an internal focus motor;
Scout Arm installations follow the arm vendor's standard safety assessment, and Foglight's
mounting kit documentation includes the load and clearance specs an EHS reviewer needs. Units
are RoHS-compliant, the enclosure is rated for standard industrial vibration profiles, and
end-of-life hardware is taken back by Foglight for certified recycling in North America and the
EU. A one-page EHS datasheet per form factor is available for plant safety reviews.

## Procurement security review: fast facts

For security questionnaires, the short answers most reviewers need: encryption in transit is
TLS 1.3 and at rest is AES-256; customer imagery never trains shared models; per-customer
fine-tunes stay in the customer workspace; SOC 2 Type I report available under NDA today, Type
II targeted Q4 2026; data residency selectable at onboarding between us-west-2 (Oregon) and
eu-central-1 (Frankfurt); deletion completed within 30 days of a verified request with a signed
certificate available; SSO via SAML 2.0/OIDC with SCIM deprovisioning on Enterprise; immutable
audit logging on privileged actions; annual third-party penetration test with summary under
NDA; published subprocessor list with 30-day change notice; outbound-only connectivity on port
443 with optional PrivateLink; support access is time-boxed, customer-approved, and audit
logged. Longer-form answers live in the trust center, and the customer engineering team turns
around full questionnaires for Enterprise evaluations.

## Release cadence and communications

Foglight Cloud ships continuously behind feature flags, with customer-visible changes batched
into a monthly release note and flagged in-app for Admins. Edge Gateway firmware follows a
slower train — roughly quarterly — and every gateway update is staged: Foglight's own test
plants first, then a customer-opt-in early ring, then general rollout, always inside the
customer-controlled maintenance window. Breaking API changes are announced at least 90 days
ahead with dual-running endpoints; webhook payloads are additive-only within a major version.
Customers can subscribe per-workspace to release notes, incident notifications, and
maintenance announcements independently, so a plant manager can get incident pages without
marketing email ever touching their inbox.

## Glossary

**Scout** — the camera unit (Rail or Arm). **Foglight Cloud** — the SaaS platform: models,
alerting, dashboard, API. **Edge Gateway** — the on-prem buffer/uplink appliance. **Line** — one
production line under inspection; the pricing and calibration unit is the robot, not the line.
**Defect class** — one named defect family with its own precision/recall tracking. **Dismissal**
— an operator marking an alert as not-a-defect; feeds the per-customer tuning loop. **Model
promotion** — approving a newly trained per-line model version for live alerting. **Masking
zone** — a camera region excluded from capture for privacy or noise reasons.

## Common buyer questions

**Can we run a Pilot on a line that already has fixed cameras?** Yes. Scout supplements existing
fixed-camera setups, and the Pilot includes a calibration session to avoid duplicate alerting
between systems.

**What happens to our models if we cancel?** Per-customer fine-tuned weights are deleted along
with the rest of the workspace under the standard 30-day deletion policy. Exported reports and
raw imagery already downloaded by the customer are theirs to keep.

**Do you offer professional services?** Limited. The customer engineering team handles standard
integrations as part of Enterprise onboarding; bespoke MES work beyond the webhook interface is
quoted separately and scheduled based on availability.

**How are false positives handled?** Operators can dismiss alerts with one click, and dismissals
feed the per-customer tuning loop. Most lines see alert precision stabilize within the first two
weeks of operation as the model adapts to that line's parts and lighting.

**Who do we call when something breaks at 2am?** Enterprise customers page the 24/7 line and get
a human within the 1-hour P1 target. Growth customers file a ticket and get first response within
8 business hours; most issues are resolved remotely without a site visit.

**How do we measure ROI?** The dashboard ships with a value report that tracks four inputs the
customer controls: scrap cost per defect class, rework labor rate, escape cost (returns, credits,
chargebacks attributable to quality), and inspection labor displaced or redeployed. Foglight
never invents these numbers — quality teams enter their own rates, and the report multiplies
them against measured defect catches and trends. Most buyers build their business case on
escapes prevented and rework caught earlier in the line, not on headcount.

**Can we start on our worst line first?** Yes, and Foglight recommends it. The Pilot exists to
prove value on the line with the most painful scrap or escape history, because that is where the
before/after delta is most visible to procurement. The calibration wizard flags when a line's
lighting or speed is outside the standard envelope so expectations are set before go-live.

**What does a multi-plant rollout look like?** After the first plant goes live, subsequent
plants reuse the same workspace patterns: alert-routing templates, role mappings, integration
configs, and per-defect-class thresholds can be cloned and then tuned per line. Enterprise
customers typically stand up a small internal center of excellence — one quality engineer and
one controls engineer — and certify them through the Foglight Certified Line Engineer path; the
named customer engineer supports the first two plants directly and reviews the rest quarterly.

**How is Foglight different from traditional machine-vision systems?** Classic machine vision is
rule-based and brittle: each part variant needs hand-tuned fixtures, lighting, and thresholds,
usually built by an external integrator and frozen until the next paid engagement. Foglight's
models learn from the customer's own dismissals and labeled samples, adapt to part and lighting
variation, and are managed by the plant's existing team through the dashboard rather than by a
vision specialist. The trade-off is honest: for sub-millimeter metrology or very high-speed
bottling lines, purpose-built vision hardware still wins, and Foglight says so in evaluations.

**Can Foglight run fully on-premises?** Not today. The Edge Gateway keeps capture and buffering
local and tolerates extended outages, but model training and the dashboard run in Foglight
Cloud. The on-prem inference appliance on the public roadmap (targeted Q4 2026) is aimed at
air-gapped facilities; design partners for that program are being selected from existing
Enterprise customers.

**What happens during a network outage?** Capture continues, the gateway buffers locally for up
to 72 hours, operators keep receiving on-floor alerts from the gateway's local rules for defect
classes already promoted to the edge, and the cloud back-fills when connectivity returns.
Nothing is silently dropped; back-filled events are marked as delayed in the audit trail.

**Do you support languages other than English?** The dashboard and operator alert surfaces ship
in English, Spanish, and German; documentation is English-only today. Alert payloads delivered
over webhooks are language-neutral JSON, so customers localize downstream surfaces however they
like.

**What is the contract minimum?** Growth is month-to-month with no minimum term; Enterprise
agreements run annually with a two-robot minimum. There is no charge for the Pilot, and Pilot
hardware is returned or rolled into the first order at conversion.

**Can we cap our bill?** Yes. Admins can set a hard monthly robot ceiling per workspace;
activating a robot above the ceiling requires an Owner override, so a plant cannot accidentally
expand spend. Billing alerts fire at 80% and 100% of any configured budget.

**Where does Foglight's own AI run?** Model training and batch evaluation run in the same AWS
region as the customer's workspace (us-west-2 or eu-central-1), on infrastructure dedicated to
that region. No imagery crosses regions, including for support debugging — support staff access
a workspace only through time-boxed, audit-logged grants approved by a customer Admin.

**Is there an SLA on alert latency?** Enterprise contracts include a target of 10 seconds from
image capture to alert delivery for promoted defect classes under normal network conditions,
measured at the 95th percentile and reported monthly in the dashboard. Alert latency is excluded
from the uptime SLA but tracked with the same rigor because operators stop trusting slow alerts.

**What if our parts change seasonally?** Seasonal or variant-heavy lines keep multiple model
versions warm: each variant gets its own calibration profile, and the line's schedule (set
manually or via the API from the MES) switches profiles automatically. Dismissal-driven tuning
accrues per profile, so winter parts do not pollute summer thresholds.
