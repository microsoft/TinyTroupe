# MultiLever: Rapid Diagnostic & Action Plan

Author: Lisa Carter (Wild Advice Partners)  
Date: (prepared immediately)

---

## Executive summary (expanded)

Situation summary
- Over the last quarter MultiLever has observed approximately a 10% increase in input costs and an approximately 20% drop in consumer demand concentrated in three core categories: Food, Home Appliances, and Toys. The demand contraction is uneven across channels and cohorts (strongest in cash-constrained households and in lower-throughput rural/peri-urban sites). Freight and packaging costs represent much of the input inflation; some supplier contracts show spot-price increases and lengthened lead-times.
- Client objective: identify immediate, pragmatic, low-risk levers to arrest demand decline and protect contribution margins within a near-term window (2–8 weeks), while preserving brand trust and pilot feasibility.

Short recommendation (one-line)
- Run a tightly scoped 2-week rapid pilot that combines pack-sizing changes, targeted promotional experiments, and prioritized procurement (including passive PCM kits for cold-sensitive items where relevant) while simultaneously modelling elasticity and margin impacts. Immediate cross-functional coordination is required: Procurement (Sara), Site/GIS (Alex), Technical/BOM (Oscar), Client Branding (GreenRiver), Clinical sign-off (Marcos). Convene a 24–72 hour rapid execution cell to ensure pilot readiness.

Key expected outcomes of pilot
- Faster validation of price sensitivity and channel elasticities for prioritized SKUs (within 10–14 days of pilot start).
- Short-term demand recovery of 5–12% in targeted segments (projected based on moderate elasticity scenarios), with controllable margin impact through targeted promotions.
- A prioritized procurement map that minimizes single-point-of-failure exposure for rollout scale-up.

This document contains:
- a concise diagnostic approach and expected deliverables,
- immediate 24–72h “must do” actions and checklists to preserve pilot feasibility,
- modelling and scenario planning methodology and example outputs,
- prioritized short-term tactics with estimated impacts and owners,
- a two-week pilot implementation plan with SOPs, staffing, monitoring metrics and budgets,
- explicit owners, timelines and decision gates,
- an expanded risk register with triggers and mitigations,
- templates and appendices for rapid use (procurement brief, BOM, experiment plan, community messaging, checklists).

---

## Background & problem statement (expanded)

Observed indicators
- Input inflation: approximately +10% overall; concentrated increases in packaging (up to +15%), freight (+12–25 depending on lane), and select raw inputs (some up to +18%).
- Demand: ~20% quarter-over-quarter drop in observed sales volumes across Food, Home Appliances, and Toys. Drop is heterogeneous: Food shows more resilience in urban channels; Home Appliances & Toys show steeper decline in discretionary purchasers.
- Channel shifts: increased share of lower-value micro-retail channels; reduced high-value purchases through subscription/loyalty cohorts.
- Operational constraints: some suppliers reporting 2–6 week lead-times; R&D capacity available but needs focused brief to deliver rapid feasibility inputs.

Client objective and constraints
- Recover demand and preserve margins within 2–8 weeks.
- Maintain clinical and brand trust (GreenRiver constraints around co-branding).
- Procurement and supplier lead-times may limit certain interventions; emergency procurement routes must be mapped.

Primary hypothesis for demand shortfall (to be tested in diagnostic)
- Combination of price-channel-income effects: reduced real purchasing power + suboptimal pack-sizing (pack sizes too large for constrained shoppers) + competitor promotions.
- Operational frictions (stockouts at key micro-retail sites) magnify the observed demand drop.

---

## Quick diagnostic approach (recommended, 5 business days) — detailed plan

Overall objective: deliver a one-page diagnostic plus a 10–20 page data appendix within 5 business days that attributes demand change to primary drivers and produces prioritized pilot SKU list.

Day-by-day plan (0–5 business days)
- Day 0 (kickoff, within 6 hours): Confirm data access, owners and immediate 24–72h deliverables. Convene 1-hour touchpoint with Alex, Oscar, Sara, GreenRiver, Marcos.
- Day 1: Ingest sales/transaction data. Produce initial sales decompositions by SKU, channel, geography, cohort. Identify top 50 SKUs by revenue and top 30 by volume.
- Day 2: Compute top-down elasticity proxies using historical price promotions and competitor observed pricing (if available). Begin bottom-up elasticity model preparation for highest-volume SKUs.
- Day 3: Attribute change drivers using regression decomposition and difference-in-differences where possible (to separate competitor promotions and channel reallocation from price/income effects).
- Day 4: Produce top-3 drivers per category and prioritize candidate SKUs for pilot (pack-size candidates, high-margin vs high-volume tradeoffs).
- Day 5: Finalize one-page diagnostic and appendix, circulate to partners.

Tasks and owners (summary)
- Descriptive analytics (sales decomposition): Owner Lisa (lead), Alex (data ingestion & preprocessing).
- Elasticity estimates: Owner Lisa (statistical models); Alex to provide channel/cohort data; procurement costs from Sara & Oscar.
- Driver prioritization: Owner Lisa. Deliverable: top-3 drivers per category, pilot SKU shortlist.

Deliverable format
- One-page executive diagnostic (PDF) summarizing key numbers, top drivers, and 8–12 bullet tactical recommendations.
- Data appendix: tables and charts by SKU/channel/cohort, model outputs (elasticity point estimates + uncertainty), list of recommended pilot SKUs and rationales.

Sample deliverable outline (for the one-page diagnostic)
- Header: date, author, data coverage (dates), sample size.
- Key metrics: % change volumes, % change input costs, top 10 SKUs impacted.
- Drivers: ranked top 3 per category with short evidence lines.
- Pilot recommendation: 2-week pilot scope and target metrics (lift, conversion, margin guardrails).
- Immediate asks: GreenRiver branding, Oscar BOM, Sara procurement envelope, Alex site mapping.

---

## Immediate (24–72h) asks to preserve pilot feasibility — detailed checklist and templates

These items are required to proceed with procurement and field readiness. Each item includes acceptance criteria, owner, and a quick escalation path should it not be delivered.

1) Branding confirmation (Owner: GreenRiver)
- Due: within 12 hours.
- Acceptable deliverable: short signed approval letter from Dr. Amina Khan confirming minimal co-branding plus a one-paragraph brand placement guideline (logo size, placement, color background). If GreenRiver insists on prominent signage, provide explicit statement so trust mitigation steps can be activated.
- Template: one-paragraph sign-off (see Appendix A: Branding sign-off template).
- Escalation: contact Lisa and Marcos immediately; prepare “trust mitigation” community launch script.

2) Procurement-ready BOM + one-page procurement brief (Owner: Oscar)
- Due: within 6 hours (already committed).
- Acceptable deliverable:
  - Per-site BOM (line-by-line) in spreadsheet or CSV including SKU code, description, qty per site (for 2-week pilot), unit cost, supplier, supplier lead-time, single-point-of-failure flag.
  - One-page procurement brief describing slowest lead-time items, items with >2 week vendor lead-time, and recommended immediate alternatives.
- Escalation: if lead-times >2 weeks for critical items, trigger fallback options (regional vendor list) and inform Lisa/Sara.

3) Emergency procurement envelope and permitted procurement routes (Owner: Sara)
- Due: within 24 hours.
- Acceptable deliverable:
  - Emergency envelope value (USD) and authorized procurement methods (direct purchase, rental, emergency exception).
  - Approved supplier list for emergency procurement, plus banking/contact info for each.
- Escalation: if envelope not approved, prepare reduced-scope pilot plan with lower kit counts.

4) Site mapping & logistics constraints (Owner: Alex)
- Due: within 12 hours.
- Acceptable deliverable:
  - Shapefiles for shortlisted sites, throughput bands (remote 30–50, peri-urban ~100, community clinic 100–200 vials/day), local logistics constraints (road access, cold chain availability).
  - Shapefile metadata should include coords, catchment population, expected daily throughput, nearest hub, transit time to distribution center.
- Escalation: if site access uncertain, propose alternate site.

5) Compile and clinical sign-off (Owner: Lisa)
- Due: compile everything within 1 hour of receipt and circulate to Marcos for clinical sign-off.
- Acceptable deliverable: compiled package (PDF + files) and a clinical issues checklist (AEFI pathway, safety, storage constraints).

24–72 hour operational checklist (for rapid ops cell)
- Confirm GreenRiver branding letter.
- Receive Oscar’s BOM and procurement brief.
- Sara confirms emergency envelope and procurement routes.
- Alex shares site shapefiles and site profiles.
- Schedule 30–60 minute clinical sign-off review with Marcos.
- Finalize count and shipping plan for pilot kit orders.

Immediate fallback decision rules (if a single event occurs)
- If any critical BOM item has lead-time >14 days AND no regional alternative available: reduce initial kit counts by 50%, prioritize highest-throughput site(s), and order expedited air freight for critical items (cost estimate to be provided by Oscar/Sara).
- If branding sign-off delayed >12 hours and GreenRiver insists on prominent branding: delay visible launch activities and proceed with community leader-based trust activation.

---

## Modelling & scenarios (2–3 weeks) — methodology, outputs and example scenarios

Goals
- Quantify price and promotion elasticity for representative SKUs.
- Model margin trade-offs under varying promotion intensities and pack-size changes.
- Simulate expected uplift in demand under candidate tactics and identify most cost-efficient levers.

Key components and methods
1) Elasticity models by SKU/category
- Approaches:
  - Log-linear OLS on aggregated time series for high-frequency SKUs where price variation exists.
  - Hierarchical Bayesian models for sparse SKUs (pool information across SKUs within category to improve estimates).
  - Incorporate channel and cohort fixed effects to capture heterogeneity (channel-level intercepts).
- Outputs: point estimates of elasticity (E[ΔQ/ΔP]) and 90% credible/confidence intervals.

2) Promotion/pack-size simulations
- Simulations include:
  - Introduce smaller pack sizes (e.g., 20% or 30% reduction in unit content) with proportional price adjustments to retain similar price/unit or reduce absolute price.
  - Simulate value-lines: lower-cost formulations or bundle promotions (e.g., buy-1-get-25% off second).
  - Channel-targeted promotions (loyalty-only coupons, SMS-only codes for high-ROI).
- Outputs: estimated incremental volume, cannibalization rates, and net margin impact.

3) Margin & supply impact
- Include procurement cost inputs (unit cost, freight per unit, packaging), fulfillment costs (cost-to-serve by channel), and promotion costs.
- Scenarios to include expedited shipping cost where needed.
- Outputs: per scenario contribution margin (absolute and %), break-even uplift required to maintain baseline margins.

4) R&D feasibility
- Quick assessment for top 10 SKUs where small input changes could reduce cost without quality loss. R&D to produce feasibility and regulatory implications.
- Outputs: yes/no feasibility, estimated cost savings per unit, estimated lead-time for reformulated pack.

Deliverable: scenario deck
- Contents: elasticity results with uncertainty, scenario modeling tables, sensitivity checks, prioritized interventions ranked by incremental margin per dollar spent and projected incremental volume.
- Delivery timeframe: 2–3 weeks.

Example modelling results (illustrative — to be replaced with live numbers)
- SKU A (Food staple): baseline weekly volume 5,000 units; estimated price elasticity = -0.9 (90% CI: -0.6 to -1.2). A 10% price reduction expected to increase volume by ~9% (range 6–12%). With pack-size reduction of 25% and 10% price cut, expected conversion of new buyers from price-sensitive cohorts ~14% uplift; margin compression estimated at 4 pp but net contribution may improve if increased volume reduces cost-to-serve per unit.
- SKU B (Toy): baseline weekly 1,200 units; elasticity = -1.6 (highly price-sensitive). A modest 5% price cut + targeted loyalty promo predicted to increase volume 8–10% but with higher cannibalization from off-promo periods.

Scenario table (example)

| Scenario | Intervention | Expected Vol Change | Margin impact (pp) | Key risks |
|---|---:|---:|---:|---|
| A | Introduce 25% smaller pack at 20% lower shelf price (Food) | +12% (range 8–16) | -3 pp | Packaging lead-time; consumer confusion |
| B | Targeted 15% promo to loyalty cohort (Home Appliances) | +6% (range 3–9) | -2 pp | Spillover to non-target channels |
| C | Tactical A/B 20% price cut for 7 days on 5 SKUs (Toys) | +18% (range 10–25) | -8 pp | High margin erosion if not targeted |

Note: all numbers above are illustrative and will be replaced with model outputs when the data is ingested.

Model quality assurance and sensitivity checks
- Cross-validate models on historical promotion events.
- Use hierarchical pooling to stabilize estimates for low-volume SKUs.
- Perform counterfactual checks comparing non-promoted control stores/sites.

Decision rules informed by modelling
- Only scale price promotions if projected uplift yields net contribution improvement or meets client tolerance thresholds (e.g., no >5 pp long-term margin erosion unless strategic).
- Pack-size interventions preferred where they reduce immediate consumer price barrier without large incremental packaging cost.

---

## Short-term tactics (prioritized and expanded)

Priority ranking logic: highest expected net contribution per dollar of promotional spend + fastest operational lead-time.

1) Adjust pack-sizing and introduce lower-price/value SKU variants
- Rationale: reduces barrier to purchase by lowering absolute outlay per transaction; good for cash-constrained cohorts.
- Implementation steps:
  - Identify top 10 high-volume SKUs with potential for smaller pack option (Lisa + Oscar).
  - Confirm packaging feasibility and incremental unit cost (Oscar + R&D).
  - Produce label/packaging spec consistent with GreenRiver branding (GreenRiver sign-off required).
  - Launch controlled in 1–2 channels/sites (pilot).
- Estimated timeline: packaging fastest if in-house packaging stock available (2–7 days); otherwise 2+ weeks.
- Expected effect: immediate affordability improvement; projected 8–15% lift in the most price-sensitive cohorts.

2) Targeted promotions to high-ROI channels and cohorts
- Rationale: limit promotional leakage and preserve margin by focusing offers to segments with highest response (loyal customers, value-seeking shoppers).
- Implementation steps:
  - Use loyalty data to define top 20% loyalty customers; craft coupon codes or SMS offers redeemable at selected sites.
  - Allocate modest promo budget (e.g., 2–3% of expected weekly revenue in channel) to validate ROI.
  - Monitor redemptions daily and cap program automatically if CPA exceeds threshold.
- Measurement: incremental lift in redemption cohort vs matched control; incremental margin per redeemed unit.
- Estimated timeline: 48–72 hours to configure offers and SMS/coupon distribution.

3) Tactical price promotion experiments (A/B testing)
- Rationale: quantify short-term price elasticity with controlled experiments to guide broader pricing strategy.
- Experiment design:
  - Randomize sites or households into control and treatment groups.
  - Keep test duration small (7–10 days) to limit long-term margin exposure.
  - Primary outcomes: incremental units sold, incremental revenue, margin impact.
  - Power calculations: detect an absolute volume increase of 8% with 80% power given baseline variance — sample size calculations provided in Appendix C.
- Owner: Commercial leads (execution), experiment design & analysis by Lisa.

4) Cost-to-serve optimizations and SKU rationalization
- Rationale: protect margins by reducing fulfillment costs and focusing assortment.
- Tactics:
  - Identify low-velocity, high-cost-to-serve SKUs to temporarily de-list or consolidate.
  - Optimize delivery routes for pilot sites to reduce per-unit freight.
  - Introduce local pick-up incentives where feasible.
- Owner: Supply Chain & Sara.

5) Loyalty and subscription pilots (medium-term)
- Rationale: secure recurring revenue and shift purchase patterns from discretionary to habitual.
- Approach:
  - Pilot a 6–8 week subscription pilot for staple Food SKUs in 1 peri-urban and 1 community site.
  - Incentivize initial sign-up with small discount; monitor retention beyond 4 weeks.
- Owner: CRM/Engineering.

R&D-driven tactics (if client has capacity)
- Fast-track reformulation: look for ingredient substitutions or packaging adjustments to save small %s on cost-per-unit without impacting quality. Prioritize top-volume SKUs where a 2–4% per-unit cost reduction materially impacts margins.

Prioritization matrix (example)

| Tactic | Speed | Expected Lift | Margin Risk | Implementation Complexity |
|---|---:|---:|---:|---|
| Pack-size | Fast–Medium | Medium–High | Low–Medium | Medium |
| Targeted promotions | Fast | Medium | Low | Low |
| A/B price tests | Fast | Medium–High | Medium | Low |
| Cost-to-serve | Medium | Low–Medium | Low | Medium–High |
| Subscription pilots | Medium–Long | Medium | Low | High |

---

## Procurement & Pilot implementation notes (two-week pilot) — operational detail and BOM template

Pilot sites and throughput assumptions
- Candidate sites (to be confirmed by Alex):
  - Site 1 (Remote): throughput target 30–50 vials/day or equivalent unit flow. Logistics: single unpaved access road; nearest hub 6 hours by truck.
  - Site 2 (Peri-urban): throughput target ~100 units/day; daily last-mile available.
  - Site 3 (Community clinic): throughput target 100–200 units/day; secure storage available; community leader engagement possible.

Per-site BOM (example template)
- The BOM must list all kit components, consumables and spare parts. Oscar to provide per-site variant counts. Below is an example BOM line format and sample row(s).

BOM columns (required)
- Item code | Item description | Qty per kit | Kits per site (2-week pilot) | Unit cost (USD) | Total cost | Supplier | Supplier lead-time (days) | Single-point-of-failure (Y/N) | Notes (packaging, cold sensitivity)

Sample BOM rows (illustrative)
- KIT-001 | Passive PCM transport cooler (24h hold) | 1 | Remote: 20; Peri-urban: 40; Clinic: 80 | 35.00 | 5,040 | Supplier A | 10 days | N | Include 2 spare PCM blocks/site
- LOG-002 | Temperature logger (digital) | 1 | Remote: 2; Peri-urban: 4; Clinic: 6 | 18.00 | 216 | Supplier B | 14 days | Y | Calibrated within 30d
- PACK-010 | Consumer pack-size small (0.75x volume) | 1 | See per SKU | 0.85*base | varied | Supplier C | 5 days | N | Co-branding label area 45x20 mm

Procurement prioritization triage (logic)
- Triage A (order immediately): single-point-of-failure items, items without local substitutes, cold-chain equipment.
- Triage B (order within 48 hours): standard consumables with >7 day lead-time.
- Triage C (order if budget allows): non-essential promotional materials, extra spares.

Packing, labelling and branding rules
- Labeling: items with cold sensitivity must include explicit labelling (e.g., "Keep between 2–8°C", "Do not freeze"). Oscar to include label mockups; GreenRiver to approve co-branding placement (minimal presence on packaging as per sign-off).
- Co-branding: minimal placement preferred — logo no larger than 25% of primary panel area; neutral background.

Staffing & training
- Per site staffing for pilot:
  - Trainer: 1 (visits site for day 0 training).
  - Community health workers: ~2 per site for operational tasks and basic AEFI flow.
  - On-call clinical advisor (Marcos) for any clinical queries.
- Training materials:
  - 1-page quick reference for assembly & storage.
  - 2-hour remote training session plus on-site 1-hour practical workshop.
  - AEFI flow chart (Appendix D) with contact phone numbers.

Assembly & check-in SOP (day-by-day)
- Day -1: Site receives kits; local team verifies counts against BOM and takes photos; completes initial checklist and temperature log installation.
- Day 0: On-site trainer conducts operational verification; cold-chain verification (temperature log check) and mock-run of client interaction.
- Day 1–14: Daily morning check-ins (15 minutes) reporting throughput, stock consumption, logger temperatures and any incidents. Weekly review with Lisa/Oscar.

Monitoring & data capture
- Daily site report template (to be sent to shared drive):
  - Date, Site ID, Throughput (units/day), Starting temperature, Average temp (24h), Number of kits used, Stock remaining, AEFI incidents (if any), Local promotions run.
- Real-time ingestion: Alex to provide simple ingestion pipeline to capture CSVs. Lisa to run daily checks and provide updates to commercial leads.

Spare parts & buffer policy
- Maintain minimum buffer stock for single-point-of-failure items: 20% additional spares for PCM blocks and loggers.
- If supply constrained, reallocate spares to highest-throughput site.

Sample per-site cost estimate (illustrative)
- Site 1 (Remote): BOM cost $3,750 + freight $420 + training $350 + contingency 12% = $4,990
- Site 2 (Peri-urban): BOM cost $6,800 + freight $360 + training $400 + contingency 10% = $7,680
- Site 3 (Clinic): BOM cost $12,600 + freight $520 + training $450 + contingency 10% = $13,900
- Pilot total (3 sites): ~$26,570 (illustrative; to be updated with actual BOM).

Procurement checklist for Sara/Oscar
- Confirm orderable supplier contacts and payment terms for each BOM line.
- Confirm shipping ETA to each site and first-mile pickup slot for next 72 hours.
- Confirm import/customs clearance needs (if cross-border).
- Authorize emergency exception orders if necessary.

---

## Two-week pilot: day-by-day Gantt-style operational plan (textual)

Week 0 (preparation: 0–72 hours)
- Hour 0–6: Kickoff meeting; Oscar shares BOM; GreenRiver confirms branding within 12h; Alex shares site shapefiles; Sara confirms procurement envelope.
- Hour 6–48: Place urgent orders for Triage A items; initiate logistics bookings; trainer schedules.
- Day 3: Receive first shipments to distribution hub; pack kits for each site; quality check.

Week 1 (pilot launch)
- Day 4 (pilot day 0): Deliver kits to sites; trainer conducts on-site setup.
- Day 5–7: Live pilot operations; targeted promotions go live per channel; begin A/B price tests in assigned sites.
- Daily: collect site reports, check temperature logs, monitor redemption and sales.

Week 2 (pilot test & iterate)
- Day 8–11: Continue operations; adjust promotions based on early signals (daily decision gate).
- Day 12–13: Consolidate weekly interim analysis; run elasticity calculations on pilot data.
- Day 14: Close experiments; final day for data capture; prepare final two-week pilot report and recommended next steps.

Decision gates
- Gate 1 (72 hours pre-launch): Bill of materials and branding sign-off completed — if not, proceed with reduced-scope pilot.
- Gate 2 (Day 5): If daily throughput <50% of expected and no operational/stock issues identified, pause promotions and re-evaluate targeting.
- Gate 3 (Day 10): If promotions show negative marginal contribution above threshold, stop promotions.

---

## Measurement, evaluation & KPIs

Primary KPIs
- Volume change (units/day) per pilot SKU and site.
- Conversion rate change (visits → purchases) where applicable.
- Redemption rates for promotions and coupon ROI.
- Contribution margin per unit and overall margin change for pilot SKUs.
- Cold-chain compliance: % time within acceptable temperature band (e.g., 2–8°C for cold-sensitive items).
- Operational uptime: % days with full kit availability.

Secondary KPIs
- Customer satisfaction (short exit questionnaire for buyers: net promoter-like 5-point).
- AEFI incidents (if relevant): count and severity; time to resolution.
- Supplier lead-time adherence.

Data collection instruments
- Daily site report CSV (fields: date, site_id, sku_id, units_sold, units_dispensed, starting_temp, ending_temp, #coupons_redeemed, incidents).
- Short customer feedback form (3 questions: price perception, pack-size satisfaction, overall satisfaction).
- Incident report template for AEFI & operational problems.

Dashboard & reporting cadence
- Daily snapshot (email) of critical KPIs to leads (Lisa, Oscar, Sara).
- Interim analysis at Day 7 with initial elasticity signals.
- Final pilot report at Day 14 with recommendation to scale or adapt.

Experiment analysis plan (A/B tests)
- Primary endpoint: % change in weekly units sold for SKU in treatment vs control.
- Statistical test: difference-in-differences using site-level daily panel; cluster-robust standard errors.
- Power analysis: given baseline average daily sales of 200 units per site for SKU, standard deviation 40, to detect 8% absolute change at alpha=0.05, power=0.8, need n≈8 sites per arm OR extend test duration. See Appendix C for calculations.

---

## Timeline & owners (expanded with deadlines and contact cadence)

High-level timeline (recap)
- 0–5 business days: Rapid diagnostic deliverable + procurement triage. Owner: Lisa (lead), Alex & Oscar supporting.
- 0–3 days (parallel): Immediate procurement inputs and branding decisions. Owners: GreenRiver (12h), Oscar (6h), Sara (24h), Alex (12h).
- 2–3 weeks: Elasticity modelling, scenario analysis. Owner: Lisa with Alex and Sara.
- Week 4: Final recommendations & prioritized implementation plan. Owner: Lisa.

Routine meetings
- Daily 15-minute standup (ops cell): 08:30 local time — attendees: Lisa, Oscar, Sara, Alex, GreenRiver rep, on-call trainer.
- Twice-weekly modelling check-ins: Lisa & Alex — to review incoming pilot data and update models.
- Weekly steering call: client execs + Lisa — review risks and decide scale-up.

Owner contact list (template — fill with real contact numbers/emails)
- Lisa Carter — Project Lead (email, phone)
- Alex (Site/GIS lead) — data ingestion & site mapping
- Oscar (Technical/BOM lead) — BOM and procurement briefing
- Sara (Procurement lead) — purchasing & emergency envelope
- Marcos (Clinical sign-off) — clinical advisor
- GreenRiver — Brand lead (Dr. Amina Khan)

Explicit deadlines (immediate)
- Oscar: procurement-ready BOM + one-page procurement brief — within 6 hours (from time of reading).
- GreenRiver: brand sign-off letter — within 12 hours.
- Alex: site-to-throughput mapping & shapefiles — within 12 hours.
- Sara: emergency envelope and procurement route confirmation — within 24 hours.
- Lisa: compile package and send to Marcos for clinical sign-off — within 1 hour of receiving above inputs.

---

## Milestones with explicit owners/partners (detailed)

- Day 5: Diagnostic + data appendix (Owner: Lisa; Partner: Alex).
  - Deliverable: one-page diagnostic PDF and zipped data appendix with CSVs and charts.
- 6 hours post-commitment: Procurement-ready package (Owner: Oscar; Partners: Sara, Lisa).
  - Deliverable: BOM spreadsheet, one-page procurement brief, vendor contacts.
- 12 hours: Branding sign-off (Owner: GreenRiver).
  - Deliverable: signed one-paragraph approval and branding guidelines.
- 24 hours: Procurement envelope & permitted procurement routes (Owner: Sara).
  - Deliverable: signed procurement envelope and permitted channels.
- 12 hours: Site confirmations & shapefiles (Owner: Alex).
  - Deliverable: shapefile and site profile table.

Acceptance criteria and signatures
- Each deliverable needs a sign-off from at least one client owner and project lead (Lisa) before the next action is triggered. Use an email sign-off or a shared drive signature sheet.

---

## Key risks & mitigations (expanded risk register)

Risk 1: Supplier lead-times >2 weeks for critical items
- Trigger: Any BOM item with supplier lead-time >14 days and tagged as single-point-of-failure.
- Mitigation:
  - Immediately trigger fallback vendor list (regional vendors) and assess expedited shipping cost.
  - Reduce initial kit counts and prioritize high-throughput sites.
  - Reassign spares to remote sites only upon operational confirmation.
- Owner: Oscar + Sara.

Risk 2: Heavy government branding requirement reduces community trust
- Trigger: GreenRiver insists on prominent external branding for stigmatized items (e.g., medical kits).
- Mitigation:
  - Seek a minimal signed approval letter instead of prominent branding where possible.
  - Activate community trust plan: engage local leaders, run pre-launch information sessions and provide neutral packaging for front-line distribution.
  - Limit visible on-site signage and emphasize neutral product labelling.
- Owner: GreenRiver + Lisa + Marcos.

Risk 3: Data gaps / messy datasets
- Trigger: Missing SKU-level history beyond X weeks, discrepancies in units vs revenue, inconsistent channel tags.
- Mitigation:
  - Allocate dedicated time for data cleaning; use conservative (wide) priors in Bayesian models.
  - Use hierarchical pooling to borrow strength across SKUs.
  - Use quick proxy metrics (store-level trends) where SKU-level is unavailable.
- Owner: Lisa + Alex.

Risk 4: Margin erosion from promotions
- Trigger: Promotions yield marginal contribution below pre-defined threshold (e.g., <20% of cost-of-promo).
- Mitigation:
  - Run controlled A/B experiments and stop promotions that don’t meet ROI criteria.
  - Prefer targeted promotions to high-ROI cohorts to minimize leakage.
- Owner: Lisa + Marketing.

Risk 5: Cold-chain failure (temperature excursions)
- Trigger: Logger records temperature outside acceptable band for >2 hours.
- Mitigation:
  - Immediate quarantine of affected product; trigger rapid re-supply from hub.
  - Use passive PCM kits and additional insulation for remote shipments.
  - Re-train site teams on storage checks and response.
- Owner: Oscar + site trainer.

Risk 6: AEFI incidents or clinical safety events
- Trigger: Any moderate/severe AEFI reported.
- Mitigation:
  - Immediate clinical triage and reporting protocol (Marcos).
  - Pause distribution if cluster identified; full clinical review before resumption.
- Owner: Marcos + Lisa.

Risk register table (condensed)

| Risk | Trigger | Impact | Mitigation | Owner |
|---|---|---:|---|---|
| Supplier lead-times | lead-time >14d | High | Fallback vendors; staged roll-out | Oscar/Sara |
| Branding trust issues | demand drop near launch | High | Community leader launch; minimal branding | GreenRiver/Lisa |
| Data gaps | missing SKU data | Medium | Conservative models; pooling | Lisa/Alex |
| Promo margin erosion | negative ROI | Medium | Stop tests; retarget | Lisa/Marketing |
| Cold-chain failure | temp excursion >2h | High | Quarantine; resupply | Oscar |
| Clinical events | AEFI report | High | Clinical triage; pause | Marcos |

---

## Data & access requirements (concrete request list)

Immediate data needs (what we need now from client systems)
1) SKU-level sales history
- Fields: date, store/site_id, sku_id, units_sold, gross_revenue, discount_amount, promotion_id (if any), returns, channel.
- Coverage: last 26 weeks preferred; minimum 13 weeks.
- Owner: Alex to ingest (source: POS systems / e-commerce logs).

2) Costing by SKU
- Fields: sku_id, input_cost, packaging_cost, freight_cost per typical route, unit_cost_to_company, current pack-size (units/volume), product weight, dimensions.
- Owner: Client Finance / Procurement; Sara to coordinate.

3) Channel & cohort metadata
- Fields: store_id, channel_type (micro-retailer, clinic, e-commerce), geo coords, catchment population approximation, loyalty_segment_id if any; customer-level metadata where privacy permits (age cohort, socio-economic band).
- Owner: CRM & Alex.

4) Supplier lead-time & contacts
- Fields: supplier_name, item_codes supplied, typical lead-time (days), contact person, payment/terms, alternative regional suppliers if available.
- Owner: Oscar to collect; Sara to validate.

5) Logistics and last-mile constraints
- Fields: site_id, hub_distance_km, road_condition, average transit time, cold storage capacity (Y/N), security constraints.
- Owner: Alex & local ops.

Access permissions & format
- Provide S3/FTP or secure shared drive access for CSV/Excel exports.
- If direct DB access possible, provide read-only credentials and schema documentation.
- Timeline: delivery to Lisa/Alex within 12–24 hours.

Data quality & handling notes
- If missing fields exist, flag and provide proxies (store-level aggregates).
- Ensure consistent sku_id across files; provide mapping table if codes differ.

---

## Budget estimate & procurement economics (high-level)

Note: all numbers illustrative until BOM finalized.

Line-item budget categories (two-week pilot)
- BOM items (per-site components): $23,000
- Freight and last-mile: $1,300
- Training and staffing costs: $1,200
- Data ingestion and modeling labor (2 weeks): $7,500
- Contingency (10–12%): $2,000
- Total illustrative pilot budget: ~$35,000

Cost assumptions to validate
- Confirm unit costs in BOM and freight assumptions.
- Confirm trainer/day-rate and community worker stipends.
- Contingency to cover expedited shipping or replacement of spoiled goods.

Payment milestones
- 50% upon order placement for Triage A items.
- 30% upon shipment from supplier.
- 20% upon delivery and site confirmation.

---

## Communication & stakeholder engagement plan

Internal communications
- Daily ops email to be sent by Lisa with critical KPIs and urgent asks.
- Use a shared folder (e.g., Google Drive or S3) with structured folders: /BOM, /Diagnostics, /PilotData, /Branding, /Clinical.
- Slack channel or WhatsApp group for real-time coordination (ops-only).

Client & external communications
- Pre-launch: neutral community messaging (sample script in Appendix E) to avoid over-expectation and to manage trust.
- Post-launch: community leader briefing and data-sharing for transparency.
- Media: avoid broad public announcements until pilot conclusions unless GreenRiver approves.

Templates included
- Appendix A: Branding sign-off template.
- Appendix B: One-page procurement brief template.
- Appendix C: Experiment power calculation & test design.
- Appendix D: AEFI flow and incident report template.
- Appendix E: Community messaging script and FAQ for distribution teams.

Sample external message (brief)
- “We’re introducing a short-term availability of smaller/affordable pack options in this community for the next two weeks to better meet household needs. If you have questions, speak to your local health worker or call [hotline].”

---

## Next steps (practical, immediate)

Action list (immediate; owners & deadlines)
1) Oscar: send procurement-ready BOM + one-page procurement brief within ~6 hours; flag any lead-times >2 weeks. (Owner: Oscar)
2) GreenRiver: confirm branding approach (signed short approval letter + minimal co-branding preferred) within 12 hours. (Owner: GreenRiver)
3) Sara: send emergency envelope amount and permitted procurement routes / approved supplier list within 24 hours. (Owner: Sara)
4) Alex: confirm site-to-throughput mapping and share shapefiles within 12 hours. (Owner: Alex)
5) Lisa: compile package and circulate to Marcos for clinical sign-off within 1 hour of receiving the above inputs. (Owner: Lisa)

Decision points and timelines
- T=0+12h: If branding & site mapping not complete, proceed with internal-only packaging and minimal branding while escalating.
- T=0+24h: If procurement envelope not confirmed, scale down pilot and prioritize Triage A items.

---

## Appendix (templates, checklists, and technical details)

Appendix A — Branding sign-off template (one-paragraph)
- "I, Dr. Amina Khan (GreenRiver), authorize minimal co-branding for the MultiLever pilot kits. Co-branding shall be limited to a single small logo no greater than X mm on the side panel. GreenRiver approves the following placement/colour specifications: [specs]. This approval is valid for the two-week pilot period only. Signed: __________________ Date: _______."

Appendix B — One-page procurement brief template
- Header: SKU range, pilot site list, total units required.
- Critical items (list), supplier, current lead-time, immediate alternatives.
- Recommended procurement route (direct purchase / rental / emergency exception).
- Estimated cost and shipping ETA.
- Sign-off block for procurement lead.

Appendix C — Experiment power calculation (worked example)
- Baseline daily units for SKU = 200 (per site).
- Standard deviation of daily units (observed) = 40.
- Desired detection: 8% relative increase (16 units).
- Using two-sample t-test approximation with alpha=0.05, power=0.8:
  - Required sample size per arm ≈ ( (Z_α/2 + Z_β)^2 * 2 * σ^2 ) / Δ^2
  - With σ=40, Δ=16, Z_α/2=1.96, Z_β=0.84 → n≈(7.84*2*1600)/256 ≈ (25,088)/256 ≈ 98 observations per arm (can be achieved by 7 sites over 14 days = 98 site-day observations per arm).
- Practical implication: either run across multiple sites or extend test duration.

Appendix D — AEFI flow chart (summary)
- If any AEFI reported: immediate stop distribution to affected recipient batch, notify Marcos within 1 hour, fill incident report, arrange clinical assessment, escalate to local health authorities if required, preserve product for testing.

Appendix E — Community messaging script (for local leaders)
- Key points: explain purpose (affordability trial), duration (2 weeks), how to access kits, who to contact for questions, reassure about product safety and clinical oversight.
- FAQ: pricing rationale, returns/exchange policy, storage guidance.

Appendix F — Data dictionary (example fields)
- sku_id: unique SKU code
- site_id: unique site code
- units_sold: integer units sold
- revenue: gross revenue pre-discount
- promo_id: identifier for promotion
- temp_logger_mean: mean temp over 24h
- incidents: free-text incidents

Appendix G — Sample email templates
- Procurement request email to supplier:
  - Subject: URGENT: Pilot order for [item] — [pilot name] — required [date]
  - Body: include order details, delivery address, contact, payment terms and request for lead-time confirmation.

Appendix H — Preliminary mock data schema and sample CSV (for ingestion)
- Provide a one-row sample of the daily site report to validate ingestion pipelines.

---

If the team agrees, I will:
- Assemble the actual attachments (one-page diagnostic, procurement BOM spreadsheets, scenario deck, risk table) as inputs arrive.
- Run the first-pass elasticity models within 48 hours of receiving the sales and costing data and provide initial signals to inform pilot adjustments.
- Coordinate daily standups to operationalize the 24–72h checklist and ensure pilot readiness.

Prepared by: Lisa Carter (Wild Advice Partners) — please confirm acceptance of the immediate 24–72h asks so we can mobilize procurement and site teams.