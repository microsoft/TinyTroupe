# MultiLever — Rapid Diagnostic & Action Plan for Demand Shortfall

Prepared by: Lisa Carter (Wild Advice Partners)  
Date: [Prepared on delivery]

---

## Executive summary

MultiLever is operating in an environment of sustained elevated inflation (~10%) and has experienced a material pullback in consumer demand concentrated in three core categories: food, home appliances, and toys. Reported retail and channel sales indicate an aggregate demand decline of approximately 20% in the most recent quarter, with concentrated impacts by SKU, region and channel. This document provides a rapid, actionable pathway the client can adopt immediately: a 5-business-day rapid diagnostic to identify principal demand drivers; 2–3 week modelling to prioritise tactics and estimate financial impacts across price, pack-size and promotion levers; and a pragmatic operational contingency and pilot deployment approach with low-capex hybrid solutions to preserve critical service delivery and customer trust during the operational downturn.

Key recommendations (high-level):
- Execute a 5-business-day rapid diagnostic to produce SKU and category-level elasticities and an initial causal prioritisation of demand drivers (Owner: Lisa; Data: Alex).
- Run in-parallel 2–3 week scenario modelling to quantify price/promotions/pack-size/margin trade-offs and recommend prioritized tactics by ROI and operational feasibility (Owner: Lisa).
- Deliver a prioritized implementation plan and pilot deployments by the end of week 4; pilots to validate assumptions, deliver quick wins, and build lender/investor confidence (Owners: Lisa, Oscar, Marcos, Sara).
- Where continuity of critical services is at risk (cold chain, clinics, telecom nodes), deploy rapid hybrid energy contingency solutions (rental/refurb gensets + battery buffers) that minimize lead-time and capital outlay.

Intended outcomes:
- Arrest demand decline in prioritized cohorts by implementing targeted price/pack and promotion micro-experiments.
- Preserve margin by selecting high-ROI actions and minimizing blanket discounting.
- Protect critical operations and customer trust via short-term, low-capex operational contingency deployments.
- Produce lender-ready investor-risk and procurement-waiver materials to unlock staged funding and vendor flexibility.

---

## Background and scope

Problem statement:
- Inflation has risen to ~10% YoY across the operating geography. Wage growth and disposable income erosion have been uneven; however, observed basket behaviour indicates a material shift away from discretionary and mid-tier value goods toward essentials and lower-price alternatives.
- MultiLever's sales telemetry shows a ~20% decline in consumer demand this past quarter concentrated in food (fresh and value-pack staples), home appliances (entry-to-mid tier), and toys (seasonality exacerbated by price sensitivity). Channel shifts toward informal markets and competitor promotions are likely contributors.

Client ask:
- Provide a rapid, practical diagnostic of the demand falloff.
- Recommend short- and medium-term tactics to stabilise demand and margins.
- Propose operational contingency measures for critical loads and an immediate pilot pathway for rapid deployment where continuity is essential.
- Produce investor-facing materials to expedite procurement and pilot funding.

Scope:
- Rapid diagnostic (0–5 business days).
- Scenario modelling and prioritisation (2–3 weeks).
- Short-term operational contingency & pilot deployment plan (0–4 weeks).
- Procurement and investor considerations for staged funding, rentals/refurbishment acceptance and limited telemetry read access.
- Deliverables include: diagnostic summary, scenario deck, pilot BOM and siting checklist, investor-risk memo, procurement waiver rationale and a prioritized implementation plan with named owners.

Assumptions and boundaries:
- This engagement focuses on short-to-medium term interventions; we do not propose full product redesigns or long-lead R&D pipelines within the first 4 weeks.
- Data access is partial and may include sanitized billing slices, channel-level data, third-party e-commerce telemetry, and fallback proxies (satellite nightlights) where direct SCADA or full telemetry are unavailable.
- All operational contingency solutions assume compliance with local regulations; permit risks and local restrictions will be flagged and mitigations proposed but cannot be overridden without client approvals.

---

## Rapid diagnostic (0–5 business days) — objective and deliverable

Objective:
- Identify the primary drivers of demand decline, decomposed by category and SKU: price elasticity vs. income effects (household budget reallocation) vs. channel shifts vs. competitive promotional activity vs. availability/stockouts.
- Produce SKU/category-level elasticity estimates and an actionable prioritised list of micro-tests (price, pack-size, targeted promotion) to run immediately.

Primary deliverable:
- A concise 1-page executive diagnostic that highlights top 10 demand drivers, top 20 SKUs by lost sales potential (absolute and %), and a data appendix with assumptions and confidence bands.

Owners:
- Lisa — rapid synthesis and lead for diagnostic write-up and stakeholder communication.
- Alex — data ingestion, validation, and provisional elasticity model outputs.

Data & methods (detailed):
- Inputs:
  - Sales/billing slices by SKU, channel and geography (last 12 months, weekly or daily granularity if available).
  - E-commerce telemetry (click-through rates, add-to-cart, conversion rates by SKU).
  - Promotional calendar and competitor observed promotions (retail ad scraping where available).
  - Inventory & stockout logs (if available).
  - Cost inputs and margin structures at SKU level (or best-estimate cost-to-serve).
  - External proxies: satellite nightlights (to infer demand shifts across zones), mobility indices, publicly available CPI breakdowns.
- Models:
  - Short-run price elasticity estimation using difference-in-differences across adjacent weeks and matched-control SKUs where an internal price change exists.
  - Cross-elasticity checks for cannibalisation between pack sizes.
  - Channel shift decomposition using panel regressions that include fixed effects for store/region/time.
  - A simple Bayesian shrinkage approach to produce conservative confidence bands when data is thin.
- Fallback plan:
  - If SCADA or detailed telemetry is blocked, use conservative envelopes: assume lower-bound elasticity estimates and higher uncertainty; produce a "safe action" list that is robust to worst-case elasticity realizations.

Expected outputs:
- 1-page diagnostic (narrative + 1 composite chart showing SKU-level demand change and elasticities).
- Data appendix with:
  - Assumptions log.
  - Confidence band methodology.
  - Raw data descriptors and missing-data notes.
- A prioritized micro-test list (3–6 high-probability, low-cost interventions) ready for immediate execution.

Rapid diagnostic templates (to be populated):
- SKU priority table (example):

| Rank | SKU | Category | QoQ Demand Δ (%) | Estimated Price Elasticity | Confidence (High/Med/Low) | Immediate Action |
|---:|---|---|---:|---:|---|---|
| 1 | SKU-12345 | Food – Staple rice 2kg | -28% | -1.6 | Med | Trial smaller 1kg value-pack at -5% price |
| 2 | SKU-23456 | Home appliance – Toaster | -32% | -2.1 | Low | Targeted promotion to loyalty cohort |
| ... | ... | ... | ... | ... | ... | ... |

Milestones & timing (0–5 business days):
- Day 0: Kickoff, data requests issued (Lisa/Alex).
- Day 1–2: Data ingestion, initial cleaning and exploratory analysis (Alex).
- Day 2–4: Rapid modelling and synthesis (Lisa & Alex).
- Day 5: Delivery of 1-page diagnostic + data appendix and short briefing call with client.

Confidence & caveats:
- Where telemetry is limited, we will flag conservative bounds and recommend micro-tests that are robust in direction under the plausible elasticity range.
- All outputs should be interpreted as provisional and used to prioritise real-world micro-experiments; definitive decisions should await validation via pilots.

---

## Modelling & scenarios (2–3 weeks)

Objective:
- Build a suite of analytic models that quantify demand and margin impacts across tactical levers: price adjustment, pack-size, targeted promotions, and cost-to-serve improvements.
- Provide prioritization by expected ROI, implementation speed and operational feasibility.

Deliverables:
- Scenario deck (10–25 slides/pages) showing uplift/downside under multiple tactics, ROI sensitivity tables and a recommended prioritisation list.
- Detailed model appendix including elasticities, channel covariance matrices and cost assumptions.

Owners:
- Lisa — modelling lead, recommendations author.
- Alex — data integration, model validation and sensitivity analysis.
- Sara — procurement inputs and vendor cost validation for operational interventions.

Model approach (granular):
- Elasticity models:
  - Short-run own-price elasticity per SKU using time-series models and where possible quasi-experimental identification (price changes, promotions, geo-based differences).
  - Cross-price elasticities estimated for related SKUs (substitutes/complements).
- Promotion response model:
  - Lift estimation for promotions by channel and cohort (loyalty vs. new customers).
  - Promotion ROI calculated as incremental gross margin / incremental promotional cost.
- Pack-size optimisation:
  - Evaluate margin per unit of consumption and consumer purchase frequency response.
  - Simulate introductions of value packs (smaller pack at lower absolute price) to capture budget-constrained households.
- Cost-to-serve scenarios:
  - Logistics routing and channel-mix optimisation: estimate margin impact from shifting a % of sales from home-delivery to retail, or to hub-and-pick.
  - Packaging & product-cost tradeoffs: smaller pack sizes often increase per-unit FOB cost but may unlock volume.

Key scenarios to model (examples):
1. Price reduction across top 20 elastic SKUs by -5% and -10% with promotion targeting top 25% of customers by past purchase frequency.
2. Introduce 1kg value-pack for top 10 staple SKUs (repackaging cost known) and forecast incremental volume and margin changes.
3. Shift 20% of fulfilment from high-cost last-mile to consolidated pick-up hubs and estimate cost-to-serve savings.
4. Temporary targeted couponing for the top 10% high-ROI cohorts (loyalty members) vs. blanket 10% off site-wide promotions.
5. Rapid product-tiering: introduce a lower-cost formulation/value-tier at a 20–30% lower price with assumed cannibalisation rates.

Scenario output template (partial example):

| Scenario ID | Action | Implementation Lead | Time to Deploy | Estimated Volume Δ (qtr) | Estimated Margin Impact (qtr) | IRR / ROI | Key Risks |
|---:|---|---|---:|---:|---:|---:|---|
| S1 | -5% price on 20 elastic SKUs + targeted coupon | Lisa/Sales Ops | 1–2 weeks | +6% | -1.2% absolute margin | High (low friction) | Competitor match |
| S2 | 1kg value-pack for staples | Ops/Procure | 3–5 weeks | +11% | +0.8% | High (packaging cost acceptable) | Supply chain delays |
| S3 | Hub-and-pick logistics shift 20% | Logistics | 4–6 weeks | +3% | +1.5% | Med | Customer convenience reduction |

Sensitivity & confidence:
- Each scenario will include a sensitivity table across three elasticity bands (optimistic/central/pessimistic) and three competitor-response assumptions (no match / partial match / full match).

Operationalisation of micro-tests:
- For the highest-priority micro-tests, develop an A/B testing plan with control stores/channels, duration (2–4 weeks), and measurement KPIs (incremental units, retention, margin per customer, redemption rate).

Budgeting & financial modelling:
- Include cost inputs from procurement (Sara) for packaging changes, promotional costs (media/discount), and operational changes (hub setup costs).
- Produce simple P&L impact per scenario for the first 3 months and a 12-month run-rate projection under a roll-out assumption.

---

## Short-term operational contingency & pilot deployment (0–4 weeks)

Rationale:
- For critical operations (cold-chain for perishables, health clinic refrigeration, telecom nodes, water pumps), the priority is to maintain service continuity and customer trust. Procurement lead-times and FX constraints make new CAPEX unattractive; rentals/refurb approach reduces time-to-implement and preserves capital and lender flexibility.

Prototype summary (rapid hybrid energy solution):
- Core concept: a locally rented/purchased diesel genset (50–80 kVA) paired with a modest battery buffer (20–100 kWh, refurbished where feasible) with Automatic Transfer Switch (ATS) and basic protection. The hybrid approach reduces fuel usage compared to pure genset and provides transient ride-through and clean switching.
- Key components (prototype BOM overview):
  - Diesel genset: 50–80 kVA, IP-rated enclosure, noise attenuated where required.
  - Battery buffer: 20–100 kWh (refurb Li-ion modules or lead-acid depending on vendor availability), inverter/charger sized to match genset output.
  - ATS & basic distribution, protection & metering.
  - Modular skid, minimal civil works, basic fire and spill containment.
- Ballpark scoping (deployment-only, site placeholder until final BOM):
  - Purchase CAPEX per site: $26k–75k (variance for genset size, battery capacity, shipping and installation).
  - Rental/refurb initial outlay per site: $10k–25k (first-month rental + transportation + installation/commissioning).
  - OPEX: fuel, rental fees, battery replacement provisioning, maintenance. Fuel expected to be the dominant OPEX for pure genset-only options.

Prototype cost table (example ranges):

| Item | Unit cost (purchase) | Rental (per month) | Notes |
|---|---:|---:|---|
| 60 kVA diesel genset (incl. shipping & install) | $22,000 | $1,500–2,500 | Noise and fuel consumption spec to be confirmed |
| Battery buffer 40 kWh (refurb) | $8,000 | $800–1,200 | Cycle life and warranties limited |
| ATS & protection | $1,500 | n/a | ATS rated for site configuration |
| Installation & commissioning | $3,000 | $750 | Local labour rates apply |
| Containment & siting works | $1,500 | $300 | Depending on site |
| Total (typical mid-range purchase) | $36,000 | $3,500–5,000 | Excludes permits and fuel |

Critical loads to protect (examples and sizing guidance):
- Health clinic refrigeration: Typical continuous load 1–3 kW; high surge on compressor start; battery buffer 10–20 kWh recommended for ride-through; genset sized 30–45 kVA to handle simultaneous clinic loads and ancillary lighting.
- Vaccine cold-chain: Highly sensitive; require redundant cooling; propose refrigerated container with separate monitoring and dual power sources.
- Water pumps: Pumps for distribution can be high starting current; require genset sizing to accommodate motor inrush.
- Telecom nodes: Low continuous power, high availability required; batteries provide ride-through, genset for extended outages.
- Targeted household circuits (vulnerable users): consider small rental inverter/genset combos and prioritize community hubs.

Pilot approach and timeline:
- Site selection (24 hours): Marcos to propose two pilot sites. Selection criteria include existing genset or clear rental option, permission to host, presence of critical loads, security, and local vendor access.
- Prototype spec & BOM (12 hours): Oscar to deliver detailed BOM, siting checklist, and basic electrical layouts.
- Energy envelopes (48 hours): Alex to provide hourly/daily energy demand envelopes and priority loads per candidate site.
- Vendor matrix (48 hours): Sara to provide rental/refurb vendor list with lead-times, payment terms, logistics feasibility and permit sensitivity.
- Deployment window: Rapid pilot to be installed within 7–14 days of site confirmation (dependent on vendor lead-times).
- Monitoring: Remote metering where possible (basic CT-based kWh and runtime) and daily operational logs for the first 2 weeks.

Pilot task list (detailed):
- Pre-deployment:
  - Confirm site host agreement and permits (Marcos).
  - Confirm exact load list and criticality ranking (Alex).
  - Vendor contracting and delivery windows (Sara).
  - Logistics & security plan (Oscar/Marcos).
- Deployment:
  - Site preparation (concrete pad if required, spill containment).
  - Install genset, battery and ATS, wiring to critical circuits.
  - Commissioning including load testing, fuel and charging cycles.
  - Remote telemetry setup (if allowed) for runtime and energy data.
- Post-deployment:
  - 14-day operational monitoring, daily check-ins, weekly report.
  - Micro-experiment measuring customer/household service continuity and any demand response (do customers return? are purchases maintained?).
  - Decision gate: scale, modify or exit.

Pilot acceptance criteria:
- System meets load requirements under design scenarios for 24 hours continuous operation with refuelling/rental schedules defined.
- Operational metrics: <2 unplanned outages in first 14 days; fuel consumption within predicted envelope ±15%.
- Customer metrics: no increase in customer complaints for service availability post-deployment vs baseline.
- Financial: rental & fuel costs within budget envelope; minimal capex committed prior to lender sign-off.

Environmental, regulatory and safety considerations:
- Fuel storage and noise regulations frequently bind. Include local authority permit checks early.
- Fire and spill containment must meet local environmental rules.
- Batteries (refurb) require careful testing, containment and handling procedures; vendor warranties should be documented.

---

## Procurement & investor considerations

Objective:
- Enable rapid pilots and lender support by providing clear, lender-ready materials that justify rentals/refurbs, staged deliverables, and limited read-only telemetry access where privacy-compliant.

Key documents to produce:
1. 1-page executive summary for lenders (fast read).
2. 2–3 page investor-risk memo that articulates data limitations, procurement strategies, milestone-based funding release, and downside mitigation.
3. Procurement-waiver rationale to permit rentals/refurb procurement, staged deliverables and limited telemetry access.

Investor-risk memo structure (recommended contents):
- Context & immediate need: succinct rationale for pilot deployments and the link to demand stabilisation.
- Data limitations: explicit detail on missing telemetry, impact on certainty and proposed conservative assumptions.
- Procurement & contracting approach: rationale for rentals/refurbs, vendor selection criteria, payment-terms and FX exposure mitigation.
- Staged funding & milestone triggers:
  - Stage A: Upfront funds for rentals/refurbs upon site confirmation and vendor commitment (e.g., 30% hold).
  - Stage B: Release for installation as acceptance tests pass (e.g., commissioning certificate).
  - Stage C: Scale-up funding contingent on pilot KPI thresholds being met for 14–28 days.
- Risk-sharing with lenders: propose capped exposure, lender collateral where feasible, and clear exit clauses.
- Compliance & approvals: clarity on permits and environmental checks required; request limited read-only telemetry access to de-risk operations.
- Appendices: sample BOM, vendor list, cost-breakdown and pilot KPIs.

Procurement-waiver rationale (points to include):
- Time-critical nature of deployment and limited lead-times for new CAPEX.
- Rentals/refurb mitigate capital and FX constraints while delivering continuity.
- Staged payments reduce lender exposure; vendor performance guarantees or deposit structures recommended.
- Read-only telemetry limited to operational metrics (kWh, runtime) with anonymized customer data and privacy protections.

Suggested lender materials deliverables and timeline:
- Lisa to upload drafts to BlueHarbor/Technical/Investor_Memo/ within 12 hours.
- One-page executive summary completed same day as diagnostic to allow lender briefing pre-pilot.

Vendor contracting & payment considerations:
- Prefer local vendors where possible to reduce shipping and customs delays.
- Evaluate deposit vs. progress payment structures; where FX volatility is high, consider indexed payment clauses.
- Where warranty on refurbished batteries is limited, negotiate remuneration or replacement clauses.

---

## Data & inputs required (priority & deadlines)

To execute the rapid diagnostic and pilot correctly, the following inputs are required with recommended formats and deadlines.

Priority inputs (owner & deadline):
- Provisional demand models (billing-slices + satellite night-lights fallback) and conservative hourly/daily envelopes per candidate site — Owner: Alex (48 hours). Required formats: CSV time series per SKU (date, store/channel, units sold, price, promo flag), or summarized pivot table if raw data access limited.
- Vendor/rental/refurb matrix (lead-times, payment terms, local delivery feasibility, permit blockers) — Owner: Sara (48 hours). Required format: spreadsheet with vendor contact, lead-time in days, rental cost/month, deposit required, warranty details.
- Prototype spec, BOM, siting notes and sketches — Owner: Oscar (~12 hours). Required format: PDF/Excel with part numbers, sizes, electrical drawing (single-line), and site siting checklist.
- Two pilot site recommendations with short rationales (access, genset/rental potential, critical loads, permitting risk) — Owner: Marcos (24 hours). Required format: one-page per site with photos, contacts, and permit status.

Upload locations:
- BlueHarbor/Technical/Investor_Memo/ — investor memo drafts and executive summary.
- BlueHarbor/Technical/Marcos_MultiLever/ — site materials, photos and BOM.
- BlueHarbor/Technical/Data/ — provisional demand models and data appendix.

Data quality checklist (for Alex & Data team):
- Ensure timestamps normalized to local timezone.
- Fill missing price observations with preceding observation where price stable; flag where uncertain.
- Provide explicit measurement of promotional channels (coupon, buy-one-get-one, display).
- Provide metadata for each data field (source, frequency, owner, last update).

---

## Risks & mitigation

Below is a detailed risk matrix with likelihood, impact and mitigation actions.

Risk register:

| ID | Risk description | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation actions | Owner |
|---:|---|---:|---:|---|---|
| R1 | Data access limitations (SCADA denied / sanitized billing) | H | H | Use satellite/mobility proxies; Bayesian conservative bands; micro-tests with robust designs; notify lenders of data uncertainty | Lisa/Alex |
| R2 | Long vendor lead-times & FX/payment constraints | H | H | Prioritise rentals/refurb, local vendors, staged procurement, include FX clauses; consider temporary fuel ops | Sara |
| R3 | Permitting/regulatory blockers (fuel storage, noise) | M | H | Site selection filter to avoid heavy-regulated zones; early engagement with local authorities; temporary waivers where feasible | Marcos/Sara |
| R4 | Competitor price-matching erodes uplift | M | M | Use targeted promotions rather than blanket discounts; prioritise value-pack tests & loyalty rewards; monitor competitor activity daily | Lisa/Sales Ops |
| R5 | Pilot technical failure (battery hazards, genset mismatch) | L | H | Vendor vetting, pre-deployment load testing, insurance, safety checklist and training | Oscar |
| R6 | Lender reluctance to fund rentals/refurb | M | M | Produce clear investor memo and staged milestones; limit initial exposure; provide acceptance tests & operation KPIs | Lisa |

Mitigation playbook (examples):
- For data issues: run double-sourced validation (billing + e-commerce telemetry), and pre-registered micro-tests with control groups to reduce model dependence.
- For vendor/FX: include a "rental first" clause, and seek performance bonds from vendors for refurbished components.
- For permitting: identify two candidate sites per region with lower permitting friction; obtain written pre-approvals from local councils where possible.

Escalation matrix:
- Day 0–2 issues: Lisa & Alex triage; operations and procurement informed.
- Day 3–5 critical vendor or permit failures: escalate to client senior sponsor and lender representative for potential emergency waiver.

---

## Implementation timeline & owners (proposed, detailed)

Below is a week-by-week plan with key deliverables and named owners. This plan assumes immediate green-light to proceed.

High-level Gantt (textual):

Week 0 (Day 0 — Kickoff)
- Kickoff meeting and data requests issued — Lisa (lead), Alex, Sara, Marcos, Oscar.
- Investors & lenders informed of planned approach — Lisa.

Days 0–5 (Rapid diagnostic)
- Data ingestion and provisional models — Alex.
- 1-page diagnostic + data appendix produced — Lisa.
- Stakeholder briefing and decision for micro-tests — Lisa.

Week 2 (Days 6–14)
- Scenario modelling starts — Lisa & Alex.
- Procurement vendor shortlist compiled — Sara.
- Pilot site confirmation & preliminary vendor engagement — Marcos & Sara.

Week 3 (Days 15–21)
- Scenario deck completed with prioritized ROI list — Lisa.
- Prototype BOM finalised and vendor selected — Oscar & Sara.
- Final investor risk memo delivered — Lisa.

Week 4 (Days 22–28)
- Pilot deployment: installation and commissioning for Site A — Oscar/Marcos.
- Pilot monitoring and initial reporting — Alex.
- Procurement waiver executed and funds staged for Site B or scale-up — Lisa/Sara.

Parallel activities:
- Legal and compliance reviews for telemetry & procurement waiver.
- Lender briefings and sign-offs for staged funding.

Detailed owner list (contact & responsibilities):

- Lisa Carter (Wild Advice Partners) — overall lead, scenario modelling, investor memo, final recommendations, primary client contact.
- Alex [LastName] (Data Lead) — data ingestion, provisional models, hourly/daily energy envelopes, pilot monitoring metrics.
- Sara [LastName] (Procurement Lead) — vendor/rental/refurb matrix, procurement negotiation, payment terms.
- Oscar [LastName] (Technical Lead) — prototype spec, BOM, siting checklist and pilot deployment lead.
- Marcos [LastName] (Site/Client Liaison) — pilot site identification, site access/permission management, local logistics.

Decision gates (staged):
- Gate 0 (Day 0): Proceed to rapid diagnostic — client approval (email suffices).
- Gate 1 (Day 5): Post-diagnostic decision to run micro-tests and pilot site selection — client sign-off.
- Gate 2 (Week 3): After scenario deck, lender approval for staged funds to execute pilots.
- Gate 3 (Post-pilot): Go/No-go to scale up based on pilot KPI achievement.

---

## Recommended next steps (immediate, 24–48h)

Actionable checklist (owners & deadlines — high priority):
1. Marcos: Paste two pilot site proposals with links/photos/contacts into BlueHarbor/Technical/Marcos_MultiLever/ (24 hours). Include assessment on permit friction and risk.
2. Oscar: Upload prototype spec + BOM and siting notes to BlueHarbor/Technical/ (12 hours). Include single-line electrical diagram and basic installation timeline.
3. Alex: Upload provisional demand models and conservative hourly/daily envelopes for candidate sites (48 hours). Provide zipped CSV and short readme for fields and assumptions.
4. Sara: Upload vendor / rental / refurb matrix with lead-times and permit flags (48 hours). Provide contact names and payment/FX terms.
5. Lisa: Upload investor-risk memo and procurement-waiver drafts to BlueHarbor/Technical/Investor_Memo/ (within 12 hours). Request expedited lender feedback.

Communication:
- Schedule a 30-minute briefing call 24 hours after deliverables begin arriving to agree on Site A selection and immediate vendor holds.

---

## KPIs and monitoring framework (pilot & rollout)

Primary KPIs for diagnostics and pilots:
- Customer demand indicators:
  - Incremental units sold (pilot catchment) vs. control (% change).
  - Redemption and repeat purchase rate for targeted promotions.
  - Basket size and change in channel mix (pick-up vs delivery).
- Financial KPIs:
  - Incremental gross margin (per SKU and aggregated) attributable to intervention.
  - Promotion ROI = Incremental gross contribution / promotional cost.
  - OPEX pilot: fuel cost per day, rental cost, labour.
- Operational KPIs:
  - Uptime (%) for protected critical loads.
  - Fuel consumption vs predicted (litres/day).
  - Number of unplanned outages.
- Lender/investor KPIs (for funding gates):
  - Pilot acceptance by site host.
  - Achievement of defined customer and operational KPIs for 14 days.

Reporting cadence:
- Daily operational logs for first 14 days of pilot.
- Weekly KPI snapshot for stakeholders.
- End-of-pilot 2–3 page summary with recommendation to scale, modify or exit.

Monitoring tools:
- Basic meter telemetry (CT-based kWh counter) feeding into a simple dashboard (Excel/Google Sheets).
- Daily photo logs and runtime logs (SMS/WhatsApp as low-bandwidth fallback).
- Weekly telecon to review lessons and course-correct.

---

## Vendor selection & evaluation template

Vendor evaluation criteria (weighting suggestion included):
- Lead time (25%)
- Price / Total Cost (20%)
- Reliability & warranty (20%)
- Local logistics capability / spare parts (15%)
- Safety & IEC/standards compliance (10%)
- Permitting & regulatory experience (10%)

Vendor evaluation example table:

| Vendor | Lead time (days) | Rental $/mo | Warranty | Local presence | Notes | Score |
|---|---:|---:|---|---|---|---:|
| Vendor A | 3 | 2,000 | 6 months (genset) | Strong | Good local support | 88 |
| Vendor B | 12 | 1,200 | 3 months (refurb batt) | Medium | Needs import | 65 |

Contract clauses recommended:
- Performance testing acceptance prior to 2nd payment.
- Short-term replacement clause for battery failure in first 90 days.
- Option for conversion to purchase at pre-agreed price after pilot success.

Payment terms:
- Prefer monthly rental invoices in local currency where FX is volatile.
- If import unavoidable, specify indexed payments or partial escrow.

---

## Sample permit & site checklist (for pilots)

Site selection & permit checklist:
- Site name and address, host contact & backup.
- Security: fenced site, night security, insurance coverage.
- Ground & siting: flat concrete pad recommended; drainage and spill containment checked.
- Fuel storage: allowed on site? Max litres permitted and secondary containment.
- Noise constraints: local quiet hours and noise limits.
- Electrical connection points: nearest distribution panel and load mapping.
- Fire safety: nearby hydrants, fire extinguishers, signage.
- Environmental permits: check local municipality requirements for temporary genset and battery deployment.

Operational checklist (pre-commissioning):
- Verify generator sizing vs load sheet (including starting currents).
- Battery state-of-health test and vendor certification.
- ATS wiring & fail-safe testing.
- Fuel arrangement: supplier, delivery windows, storage documentation.
- Emergency contacts and escalation numbers.

---

## Risks revisited with contingency playbooks

Top 3 near-term contingencies:

1. Vendor lead-time spike:
   - Contingency: switch to rental vendors with shorter lead-times even if marginally more expensive; start partial deployments focusing on highest risk circuits.
2. Permit denial for fuel storage:
   - Contingency: move to genset-per-run model where fuel deliveries are smaller and more frequent; consider temporary community hubs in locations with permits.
3. Diagnostic model uncertainty:
   - Contingency: prioritize micro-tests that are low-cost and reversible (e.g., targeted coupons, value-packs) rather than broad price cuts.

---

## Appendix — sample outputs, templates & attachments (to be uploaded)

Note: The following are recommended attachments to be produced and uploaded to the BlueHarbor repository. Placeholders and sample structures are provided below.

Required attachments (to be uploaded by named owners):
- Prototype spec + BOM — Oscar (BlueHarbor/Technical/Marcos_MultiLever/).
  - Includes: single-line electrical diagram, equipment part numbers, dimensions, shipping weight, installation notes.
- Vendor matrix & rental/refurb list — Sara (BlueHarbor/Technical/).
  - Includes: contact names, lead-times, rental rates, deposit requirements, payment terms, vendor references.
- Provisional demand models and envelopes — Alex (BlueHarbor/Technical/Data/).
  - Includes: raw CSVs or pivot summaries, elasticity outputs, model code snippet and readme.
- Site photos & notes — Marcos/Oscar (BlueHarbor/Technical/Marcos_MultiLever/).
  - Includes: high-resolution photos, GPS coordinates, host contact info and site risk notes.
- Investor risk memo and procurement-waiver drafts — Lisa (BlueHarbor/Technical/Investor_Memo/).
  - Includes: 1-page executive summary and 2–3 page detailed memo.

Sample model output (illustrative excerpt):
- SKU elasticity table (top 10 SKUs):

| SKU | Category | Price ($) | Units/Qtr (baseline) | QoQ Δ Units | Est. Price Elasticity | 95% CI |
|---|---|---:|---:|---:|---:|---:|
| SKU-12345 | Rice 2kg | 4.50 | 120,000 | -28% | -1.6 | [-2.2, -1.0] |
| SKU-23456 | Toaster | 22.00 | 6,500 | -32% | -2.1 | [-3.5, -0.9] |

Sample pilot BOM excerpt (technical):

| Component | Description | Qty | Unit Price | Vendor | Lead-time (days) |
|---|---|---:|---:|---|---:|
| Genset 60kVA | Diesel, sound-attenuated canopy | 1 | $22,000 | Vendor A | 3 |
| Inverter/Charger | 70 kVA hybrid inverter | 1 | $6,500 | Vendor B | 7 |
| Battery 40kWh (refurb) | Li-ion modules, refurbished | 1 | $8,000 | Vendor C | 5 |
| ATS panel | Auto transfer switch & protections | 1 | $1,500 | Local | 2 |

---

## Closing & next steps (confirmations)

If the team approves this approach, Wild Advice Partners will:
A) Finalise the investor memo and procurement-waiver wording for lenders (Lisa) and upload it to BlueHarbor within the next 12 hours.
B) Begin the rapid diagnostic immediately upon receipt of Alex's provisional models and other data feeds.
C) Stand ready to support pilot deployments once Marcos/Oscar/Sara confirm site feasibility and vendor availability.

Immediate contacts for follow-up:
- Lisa Carter — lead consultant (Wild Advice Partners) — [email address placeholder]
- Alex [LastName] — data lead — [email placeholder]
- Sara [LastName] — procurement lead — [email placeholder]
- Oscar [LastName] — technical/pilot lead — [email placeholder]
- Marcos [LastName] — site liaison — [email placeholder]

Prepared and uploaded file:
- MultiLever_Rapid_Diagnostic_and_Action_Plan_Lisa_Carter.md (BlueHarbor/Technical/Investor_Memo/)

---

Prepared by:
Lisa Carter  
Wild Advice Partners

[End of report]