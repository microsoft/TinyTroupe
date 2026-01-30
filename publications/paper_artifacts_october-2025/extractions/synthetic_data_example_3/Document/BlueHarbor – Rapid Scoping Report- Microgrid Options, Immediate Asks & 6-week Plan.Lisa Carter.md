# BlueHarbor – Rapid Scoping Report: Microgrid Options, Immediate Asks & 6‑week Plan

Prepared by: Lisa Carter (Wild Advice Partners)  
Status: Draft — please review and comment in the shared folder.

---

## Executive summary

BlueHarbor has requested urgent support to stabilize electricity service and reduce costly diesel exposure across its island network. This rapid scoping pack provides a practical, phased approach to deliver an implementable set of technical and commercial options — prioritised, costed at high level, and investor‑ready by the end of a six‑week engagement.

This document:
- Summarises the immediate diagnostic approach and quality checks we will run on the data.
- Lists critical data and stakeholder asks needed within the next 24–48 hours to maintain schedule.
- Proposes a detailed analytical and delivery plan for the next six weeks, with owners, deliverables, timelines and explicit outputs.
- Provides sample templates, scoring matrices, and decision criteria that will be used to prioritise sites and options.
- Surfaces key risks, probability/impact assessments and mitigations with owners.

Key immediate ask of the client: provide secure access to the datasets listed below and confirm primary contacts for operations, treasury, procurement and regulator liaison within 24 hours where possible. Early access to time series load and outage data materially reduces uncertainty and delivers faster, higher‑fidelity outcomes.

Target outcome at 6 weeks: investor‑grade business case for an initial pilot microgrid(s) with modular options (small/medium/full), clear procurement path, a 30/60/90 day implementation sequencing and a lender/donor ready term‑sheet annex.

---

## 1. Context & objective

Context
- BlueHarbor operates multiple island electrification networks served predominantly by diesel generators. Recent volatility in fuel prices, logistics constraints and reliability concerns are generating unsustainable operating costs and elevated outage risk for customers and critical services.
- The client seeks options that reduce diesel consumption and improve reliability while preserving the ability to access blended finance (donors + lenders) — i.e., a bankable business case with credible technical, commercial and procurement pathways.

Primary objective
- Produce a prioritised, implementable set of technical and commercial options: pack‑size modular microgrids (containerised or prefabricated), CAPEX/OPEX trade‑offs, near‑term operational levers, and a medium‑term investor‑ready business case that preserves developer and lender confidence.

Scope
- Island networks (multiple sites) within the BlueHarbor portfolio. Emphasis on:
  - Short‑term diagnostics (first 5 business days) to identify priority pilot sites and quantify diesel exposure.
  - Medium‑term investor‑ready package (6 weeks) including procurement annex, sensitivity analysis and term‑sheet draft.
  - Deliverables tailored to both internal decision‑making (BlueHarbor board/excom) and external financing conversations (donor & lender info pack).

Boundaries (what we will not deliver in 6 weeks)
- Full detailed engineering design for site construction (e.g., civil drawings, full SCADA integration design). We will deliver technical spec annexes and procurement‑ready technical requirements.
- Full EPC contracting and final vendor negotiations. We will prepare the term‑sheet, procurement approach and parallel vendor shortlists.

---

## 2. Rapid diagnostic (what we will do immediately)

Objective for days 1–5
- Convert raw data into actionable metrics that immediately indicate where diesel exposure and reliability risk are highest, and which sites are good candidates for near‑term modular microgrids or operational interventions.

Primary outputs
- One‑page diagnostic per island (uniform template) summarising: peak and energy metrics, diesel burn and cost exposure, outage frequency/severity, candidate sites and siting constraints, immediate operational levers and high‑level CAPEX/OPEX band estimates.
- Data appendix: validated raw time series (where possible), data quality log and assumptions.

Detailed tasks and owners (Day 1–5)

1. Data ingestion & validation (Owner: Alex)
   - Actions:
     - Collect the time series: 12–24 months of load profiles (15‑minute preferred, hourly minimum).
     - Ingest time‑stamped outage/event logs, planned and unplanned maintenance records and fuel deliveries.
     - Import asset register (gensets, fuel tanks, transformers, protective devices) and recent maintenance notes.
   - Validation checks:
     - Timestamp alignment and timezone consistency.
     - Missing data windows flagged with start/end, percent missing.
     - Outlier detection: identify negative values, spikes >5x local median, impossible ramp rates.
     - Cross‑check fuel deliveries against diesel consumption logs.
   - Deliverables:
     - Dataset receipt log with checksum and file naming conventions.
     - Data quality dashboard (missing %, longest gap, anomalous days flagged).
   - Expected time: 48 hours for initial ingestion and checks, additional 48 hours for remediation with client clarifications.

2. Preliminary load, diesel exposure & outage analysis (Owner: Alex / Oscar)
   - Actions:
     - Generate average daily and weekly load profiles per island; calculate peak demand, energy per day, load factor.
     - Compute diesel burn per island (monthly and rolling 12‑month), unit diesel L/kWh and fuel cost per kWh using historical fuel price.
     - Map outages: frequency (events/month), duration (average and distribution), and critical customer impact mapping (health clinic, water pump, telecom).
   - Deliverables:
     - Preliminary loss‑of‑load estimation using simplified reserve margin and outage clustering.
     - Diesel exposure table showing monthly fuel cost, % of total OPEX and sensitivity to ±20% fuel price change.

3. High‑level siting constraints and candidate prioritisation (Owner: Oscar)
   - Actions:
     - Review GIS maps and site notes for land tenure, access, security, space constraints, and grid topology.
     - Identify candidate sites for modular microgrids (containerised battery + inverter + controls) based on contiguous load centres, proximity to fuel storage, and security.
     - Assess structural constraints: road access for container delivery, crane availability, interconnection points.
   - Deliverables:
     - Siting constraint score (see sample scoring matrix below in section Appendix).
     - Ranked list of candidate pilot sites with rationale.

4. Demand patterns and elasticity observations (Owner: Alex, supported by Lisa)
   - Actions:
     - Identify peak drivers (residential evening peaks vs commercial daytime) and seasonal effects.
     - Estimate minimal curtailment levels and potential DSM interventions (e.g., targeted demand response or time‑of‑use).
     - If smart meter data not available, infer usage segmentation by clustering typical day profiles.
   - Deliverables:
     - Demand drivers memo with suggested low‑cost interventions (curtailment windows, incentive structures).
     - Initial elasticity estimates (coarse band: high/medium/low) with explanation of data limitations.

5. Consolidation and issue log (Owner: Lisa)
   - Actions:
     - Compile the one‑page diagnostic per island using standard template.
     - Produce a short executive slide per island that highlights top 3 opportunities and top 3 risks.
   - Deliverables:
     - One‑page diagnostic (to be reviewed by BlueHarbor operations in Day 5 session).
     - Data appendix and issue/blocker log.

Sample one‑page diagnostic template (to be used for each island)
- Island name:
- Summary snapshot (1–2 lines)
- Key metrics:
  - Average daily energy (kWh/day)
  - Peak demand (kW)
  - Load factor (%)
  - Average monthly diesel burn (litres) / fuel cost (USD)
  - Outages: frequency (events/month), median duration (minutes)
- Top 3 constraints / siting issues
- Candidate microgrid option(s) (Small / Medium / Full) – quick CAPEX/OPEX band
- Primary recommended immediate action (0–30 days)
- Owner for follow‑up

Example (sample data to illustrate format)
- Island: Harbor East
- Summary: High evening residential peak; average monthly diesel cost USD 85k; frequent short outages during fuel transfers.
- Key metrics: Energy 540,000 kWh/month; Peak 750 kW; Load factor 0.30; Diesel 65,000 L/month (USD 85,000); Outages 4 events/month, median 90 minutes.
- Top constraints: No secure flat staging area for container delivery (40 m2 required), single supplier for fuel; limited grid interconnection switchgear.
- Candidate option: Medium modular (500 kW inverter + 1.5 MWh battery + 2x 300 kW genset control) – CAPEX band USD 900k–1.4M; projected diesel reduction 45–60%.
- Immediate action: Inspect potential staging yard and secure letter of consent for land use.
- Owner: Oscar (technical), Alex (demand) / Lisa (stakeholder engagement)

---

## 3. Immediate data & stakeholder asks (24–48h priorities)

Urgency and rationale
- The quality and timeliness of these datasets materially affect our ability to produce credible scenario modelling and investor‑grade outputs within the 6‑week window. Please provide or grant secure access to the following ASAP. Where items are sensitive, provide a named contact and expected ETA for secure transfer.

Primary owner for collection and upload: Alex (technical/data) & Lisa (stakeholder liaison).

A. Operational & network data (Owner: Alex to collect/upload)
- 12–24 months of load profiles (15‑min preferred; hourly acceptable). If multiple feeders or end‑user classes exist, provide separate files per feeder/class.
- Time‑stamped outage/event logs for the same period (include tags for planned vs unplanned; cause codes if available).
- Asset registers: gensets (make, model, rated efficiency curves at load levels), transformers, critical switchgear, meters and SCADA logs (if available).
- Current protection settings and one‑line diagrams.
- Network/GIS maps & shapefiles for candidate sites and feeders (coordinate system declared).
- Sample filename convention requested:
  - islandname_load_15m_YYYYMM.csv
  - islandname_outage_log_YYYYMM.csv

B. Fuel & financial (Owner: Alex / Lisa to collect)
- Diesel consumption history and recent fuel contracts (supply terms, indexation clauses, minimum volumes).
- Tariff schedules (by customer class), recent collections, accounts receivable aging and any cross‑subsidy notes.
- Historical monthly fuel pricing (delivered price) and any hedging activities or forward contracts.
- Any lender/donor pre‑conditions, term‑sheet drafts or reporting templates (highly material for packaging).

C. Technical & site constraints (Owner: Oscar)
- Site access notes: landowner agreements, security provisions, crane/road limits, constraints on night work.
- Permitting timelines for civil works and electrical interconnection (typical approvals and lead times).
- Environmental & social constraints (shoreline setbacks, cultural sites).

D. Procurement & vendors (Owner: Sara)
- Known or preferred battery/inverter/containerised system vendors and regional lead‑times. For each vendor, provide:
  - Typical lead time (weeks) for a 500 kW/1 MWh system.
  - Warranty terms, local spares availability, after‑sales support.
- Any existing vendor contracts or procurement templates and procurement policy constraints (e.g., single source, local content requirements).

E. Stakeholder contacts (Owner: Lisa)
- Primary client contacts: CEO/MD, Technical Director, CFO/Treasury, Head of Procurement, regulator liaison.
- Any donor/lender contacts or regulatory points‑of‑contact (email + phone + preferred contact hours).
- Suggested meeting windows for a Day‑1 kickoff and weekly touchpoints.

If any item is unavailable, please state the blocker and an ETA in the shared issue log. Fallbacks: public network maps / satellite imagery combined with operator summaries are possible, but increase uncertainty and will be explicitly called out in deliverables.

Appendix A (detailed copy/paste checklist) is repeated in the back of this report for convenience.

---

## 4. Proposed analytical approach & deliverables (owners & timeline)

This section expands the phased plan to include sub‑tasks, key assumptions, sample deliverable templates and acceptance criteria.

Phase 0 – Kickoff and data confirmation (next 48h)
- Objectives:
  - Align owners, confirm folder structure and secure access routes.
  - Agree data confidentiality and communication protocols.
- Activities:
  - 30–45 minute kickoff meeting: confirm schedule, access and immediate blockers.
  - Creation of central secure folders: BlueHarbor/Technical, BlueHarbor/Procurement, BlueHarbor/Stakeholder with RBAC as per section 8.
  - Quick wins: client to upload one month of recent 15‑min load to confirm formats.
- Deliverable: dataset receipt log and list of blockers.
- Owner: Oscar (invite), Marcos (confirm client participants), Alex & Lisa (dataset log).

Kickoff meeting agenda (30–45 min)
1. Introductions and roles (5 min)
2. Objectives of the 6‑week engagement and expected outputs (5 min)
3. Data needs and upload process (10 min)
4. Project schedule and key milestones (10 min)
5. Q&A and next actions (10–15 min)

Phase 1 – Rapid diagnostic (Day 1–5)
- Activities:
  - Data validation and cleaning tasks (see Section 2).
  - Preliminary load/diesel exposure, outage clustering and high‑level siting constraints.
  - Quick stakeholder interviews with operations and procurement to confirm constraints.
- Deliverable: 1‑page diagnostic per island + consolidated data appendix.
- Acceptance criteria:
  - All islands have a completed template and a data quality score.
  - Top 3 candidate pilot sites identified.
- Owners: Alex (analysis), Oscar (technical notes), Lisa (compile/report).

Phase 2 – Modelling & scenarios (Week 2–3, ~days 6–21)
- Objectives:
  - Produce scenario analysis for three modular options per candidate site: Small (partial battery/inverter), Medium (hybrid with genset control) and Full (diesel displacement to target %).
  - Quantify CAPEX/OPEX tradeoffs, energy and capacity savings, reliability improvements and financial metrics (NPV / IRR / payback bands).
- Activities:
  - Demand scenario construction: baseline, low growth, high growth and DSM‑enabled scenario.
  - Technical simulation: simplified dispatch modelling (hourly) capturing genset characteristics, battery cycling, roundtrip efficiency, minimum genset loading constraints, and reserve requirements.
  - Financial model: CAPEX (equipment + installation + contingency), OPEX (fuel, maintenance, inverter losses), financing scenarios (grant/subsidy levels, debt cost, tenor).
  - Sensitivity analysis across fuel price, FX, vendor lead time, permitting delay and demand growth.
- Deliverables:
  - Scenario deck summarising quantified outcomes, option‑level CAPEX/OPEX bands and sensitivity tables.
  - Preliminary NPV/IRR/payback ranges and an investor‑facing summary of financing conditions required.
- Owners: Lisa (modelling lead), Alex (data & demand models), Oscar (technical feasibility), Sara (procurement inputs).

Modelling assumptions (examples to be refined with data)
- Battery round trip efficiency: 88–92%
- Minimum genset loading: 30–40% rated for common models
- Fuel price base case: historical mean delivered price (client data) — sensitivities at ±20%, ±40%
- Discount rate: base 8% (blended), sensitivity at 6% (grant enhanced) and 12% (pure commercial debt)

Phase 3 – Recommendations & implementation plan (Week 4)
- Objectives:
  - Convert the modelling outcomes into a pragmatic implementation plan, procurement approach and regulatory checklist for pilot deployment(s).
- Activities:
  - Prioritise sites based on technical feasibility, financial attractiveness and deliverability (lead times, permitting).
  - Produce procurement strategy: RFP template, vendor shortlists, evaluation criteria and recommended contractual approach (supply + installation or supply + EPC).
  - Develop a 30/60/90 day implementation timeline for pilot(s), including civil works, interconnection schedule, testing and commissioning.
- Deliverable:
  - Recommendation memo with implementation sequencing and procurement annex.
- Owners: Lisa (report lead), Marcos (client liaison), Sara (procurement lead), Oscar (technical input).

Phase 4 – Investor‑grade business case (Week 5–6)
- Objectives:
  - Finalise assumptions and produce documentation suited to lenders/donors including sensitivity tables, technical specifications and proposed term‑sheet.
- Activities:
  - Refine CAPEX/OPEX, produce final LCOE ranges, update NPV and investor pack with risk allocation matrix.
  - Draft term‑sheet / financing memo aligned to likely financiers (donor grant for partial capital, concessionary debt for balance).
  - Prepare procurement/spec annex with technical acceptance criteria and test procedures for commissioning.
- Deliverable:
  - Investor‑grade business case and term‑sheet ready package; procurement annex with spec templates.
- Owners: Lisa, Sara, supported by Alex/Oscar.

Detailed Gantt (6 week view)
- Week 0 (48h): Kickoff; folder setup; initial dataset upload.
- Week 1 (Days 1–5): Rapid diagnostic; one‑page island briefs.
- Week 2 (Days 6–10): Scenario modelling start — baseline and low complexity options.
- Week 3 (Days 11–15): Scenario modelling complete; sensitivity analysis.
- Week 4 (Days 16–21): Draft recommendations; procurement approach; client review.
- Week 5 (Days 22–28): Business case refinement; term‑sheet draft.
- Week 6 (Days 29–35): Final deliverables; presentation to BlueHarbor and draft lender/donor pack.

(Exact dates to be set in kickoff).

Acceptance criteria for final deliverables
- Investor pack must include: technical spec annex, CAPEX/OPEX tables, sensitivity matrices, term‑sheet draft, procurement RFP templates, 30/60/90 day implementation plan, and M&E / KPI table.
- All calculations must be reproducible from source files in BlueHarbor/Technical.
- A final presentation to BlueHarbor (60–90 minutes) with Q&A.

---

## 5. Owners & primary team contacts (quick list)

Primary team
- Lisa Carter (Wild Advice) — Stakeholder & comms owner; overall report lead; responsible for stakeholder map, scoping pack and client-facing deliverables. (Owner: report consolidation, client deck)
- Alex [last name] (Wild Advice) — Data ingestion, demand & financial model lead. (Owner: modelling, data ingestion)
- Oscar [last name] (Wild Advice) — Technical siting, modular design and equipment lead. (Owner: technical feasibility, siting)
- Sara [last name] (Wild Advice) — Procurement, vendor prioritisation and lead-time assessments. (Owner: procurement strategy)
- Marcos [last name] (Wild Advice) — Client liaison and schedule coordination with BlueHarbor. (Owner: client alignment & approvals)

Suggested communications cadence
- Daily standup (10–15 min) internally during week 1 (data ingestion).
- Twice weekly syncs with BlueHarbor technical lead during week 2–3.
- Weekly steering call with BlueHarbor senior management (30 minutes) from week 3 onwards.

Contact list template (please populate)
- CEO/MD:
- Technical Director:
- CFO/Treasury:
- Head of Procurement:
- Regulator liaison:
- Lead donor contact (if applicable):

---

## 6. Key levers we will evaluate (expanded)

We will quantitatively and qualitatively evaluate the following levers for each candidate site:

1. Pack sizing & productisation
   - Options: containerised prefabricated microgrid (plug & play), site‑built hybrid system, staged modular build.
   - Considerations: transport & crane constraints, local installation skills, future expandability, OPEX implications of modularity.

2. Fuel & operational optimisations
   - Improved dispatch strategies (battery first for peak shaving, genset spin‑up thresholds).
   - Genset maintenance optimisation and life extension through load sharing and base loading.
   - Fuel contract renegotiation opportunities: volume discounts, price indexing, delivery frequency and contingency clauses.
   - Fuel theft mitigation and metering upgrades.

3. Procurement & local supply options
   - Regional vs global vendor trade‑offs (lead time vs cost).
   - Availability of spares, local maintenance capacity and warranties.
   - Local content requirements and customs clearance times.

4. Financing structures (blended finance)
   - Possible structures:
     - Grant + concessional debt (donor covers % CAPEX to improve investor returns).
     - Vendor financing + local bank refinance.
     - Performance contracting with O&M provider; availability payments for reliability improvements.
   - We will model the effect of different grant shares (10%, 25%, 50%) on payback and debt service coverage.

5. Demand side measures (DSM)
   - Targeted DSM where feasible: water pumping schedules, demand response for large consumers, LED retrofit programs.
   - DSM can have low CAPEX and immediate impact on peak exposure.

6. Hybrid technical levers
   - Use of used/overhauled gensets where cost effective but with careful O&M considerations.
   - PV plus battery integration where siting and insolation allow; prioritise where daytime loads are high.
   - Microgrid controls: integrate supervisory controller for optimized dispatch and islanding functionality.

---

## 7. Risks & mitigations (high-level with probability and impact bands)

We present risks with recommended mitigation and clear owners. For each risk we include probability (Low/Medium/High) and impact (Low/Medium/High).

Risk matrix (summary)

| Risk | Probability | Impact | Mitigation | Owner |
|---|---:|---:|---|---|
| Missing/late data | High | High | Use fallbacks (satellite + operator summaries), run conservative scenarios, flag uncertainty. Establish daily data escalation with client. | Lisa (flag), Alex (technical) |
| Vendor lead‑times >2 weeks (supply chain delays) | High | Medium | Prioritise vendors with regional stock; identify alternatives; split procurement into parallel tracks. | Sara, Oscar |
| Regulatory/permitting delays | Medium | High | Early regulator engagement; include permit buffer in timeline; prepare standard permit docs to accelerate review. | Lisa, Marcos |
| Single‑vendor dependency | Medium | Medium | Shortlist multiple vendors; prequalify second‑source; include termination/escrow protections in contracts. | Sara |
| Fuel price volatility | High | High | Sensitivity scenarios; recommend hedging/forward purchase where available; consider contractual indexation clauses review. | Alex, Lisa |
| Security of installation (theft/vandalism) | Medium | Medium | Site security assessment; include physical barriers and local engagement; insurance clauses. | Oscar |
| Local workforce skill gap (O&M) | Medium | Medium | Training packages in procurement annex; temporary vendor O&M with knowledge transfer schedules. | Sara, Oscar |
| FX risk for imported equipment | High | Medium | Model multiple FX scenarios; agree financing in local currency where possible; include contingency in CAPEX. | Lisa, Alex |
| Environmental / social constraints | Low/Medium | Medium | Early screening; environmental & social management plan (ESMP) template included in annex. | Lisa, Oscar |

Escalation process
- Any "High" probability × "High" impact issues must be escalated to BlueHarbor MD and the Wild Advice steering lead within 24 hours of identification. Lisa will maintain the master risk register.

---

## 8. Data governance & security

All client data must follow Wild Advice Partners security and privacy procedures.

Folder & access policy
- Folder structure (BlueHarbor account):
  - BlueHarbor/Technical — time series, asset registers, modelling inputs (restricted)
  - BlueHarbor/Procurement — vendor contacts, lead‑time tables, procurement templates (restricted)
  - BlueHarbor/Stakeholder — contact lists, term sheets, donor comms (restricted)
- Access:
  - Access will be granted via secure SSO invited to corporate emails. Shared links must be set to 'restricted' and limited to named team members.
  - Do not copy sensitive datasets to personal drives. No external cloud sharing without prior approval from BlueHarbor.
- Data handling:
  - All extracted datasets must be stored with filename conventions and a version history in the dataset receipt log.
  - Any personal data (names, phone numbers, email addresses) must be handled per client privacy requirements and redacted from public materials.

Security checklist (to be completed by client IT)
- Confirm secure SFTP or shared drive credentials for ingestion (Owner: BlueHarbor IT).
- Provide contact for secure transfer of large files (>10 GB).
- Confirm encryption at rest (Y/N) and MFA requirement for account access.

---

## 9. Next steps (immediate actions & responsibilities)

Action list (immediate, for copy/paste into email to client)
1. Lisa: circulate this scoping report as a draft to the Wild Advice team and ask the client to upload/enable access to the requested datasets to BlueHarbor/Technical and BlueHarbor/Procurement in the next 24–48h.
2. Alex: confirm ETA for dataset uploads (load profiles, outage logs, diesel history, tariff schedules) and flag any expected remediation actions.
3. Sara: populate BlueHarbor/Procurement with vendor contacts and lead-times, calling out any single‑vendor exposures; prepare an initial vendor short‑list format.
4. Oscar: upload preliminary siting notes and the technical folder within ~12 hours and flag any immediate equipment lead-times or constraints.
5. Team: confirm availability for the kickoff tomorrow at the agreed slot (Oscar/Marcos time) or propose alternatives.

Immediate action schedule (first 72 hours)
- T+0: Lisa sends this report and schedules kickoff. Marcos confirms client participants.
- T+6 hours: Alex posts initial dataset receipt log with any immediate format issues.
- T+12–24 hours: Oscar posts siting notes and initial vendor lead time flags.
- T+24–48 hours: Kickoff meeting; upload of at least one month of load data for format validation.

---

## 10. Detailed appendices & templates

Appendix A – Detailed 24–48h data checklist (for copy/paste)
- 12–24 months of load profiles (15‑min preferred) – BlueHarbor/Technical (Owner: Alex)
- Outage/event logs (time‑stamped) – BlueHarbor/Technical (Owner: Alex)
- Diesel consumption history & recent fuel contracts – BlueHarbor/Technical (Owner: Alex)
- Genset specifications & asset registers – BlueHarbor/Technical (Owner: Alex/Oscar)
- Network/GIS shapefiles & candidate site notes – BlueHarbor/Technical (Owner: Oscar)
- Tariff schedules & customer segmentation – BlueHarbor/Technical (Owner: Alex)
- Vendor contacts & lead-times (batteries, inverters, containers) – BlueHarbor/Procurement (Owner: Sara)
- Lender/donor pre‑conditions or term‑sheet templates – BlueHarbor/Stakeholder (Owner: Lisa)
- Primary client contacts (CEO/MD, Technical Director, CFO/Treasury, Procurement, regulator) – BlueHarbor/Stakeholder (Owner: Lisa)

Appendix B – Data templates & sample headers

Sample file: islandname_load_15m_YYYYMM.csv
- Columns:
  - timestamp_utc (YYYY-MM-DD HH:MM:SS)
  - feeder_id
  - customer_class (residential/commercial/industrial/other)
  - measured_kW
  - measured_kVar (optional)
  - meter_id (optional)
- Notes:
  - Preferred timezone: UTC. If local timezone used, specify offset and daylight savings conventions.

Sample file: islandname_outage_log_YYYYMM.csv
- Columns:
  - event_id
  - start_timestamp_utc
  - end_timestamp_utc
  - affected_feeder
  - cause_code (planned/unplanned/fuel shortage/maintenance/other)
  - estimated_customers_affected
  - notes

Sample file: genset_asset_register.csv
- Columns:
  - genset_id
  - manufacturer
  - model
  - rated_kW
  - date_commissioned
  - last_maintenance_date
  - fuel_consumption_curve (link to CSV or table)
  - typical_efficiency_at_50pct_load (%)
  - location_coordinates

Appendix C – Example calculation: diesel exposure and savings (illustrative)

Input assumptions (example)
- Monthly generation: 540,000 kWh
- Diesel burn: 65,000 litres/month
- Delivered fuel price: USD 1.30/litre
- Baseline fuel cost: 65,000 * 1.30 = USD 84,500/month

If a medium microgrid reduces diesel burn by 50%:
- New diesel burn: 32,500 L/month
- Fuel cost savings: (65,000 - 32,500) * 1.30 = USD 42,250/month
- Annual savings: USD 507,000
- Simple annualised fuel saving payback for an installation CAPEX of USD 1.2M: 1.2M / 507k ≈ 2.4 years (ignores financing, O&M changes and replacement cycles).

Appendix D – Vendor evaluation & scoring matrix (sample)

Scoring scale: 1 (poor) – 5 (excellent)

| Criteria | Weight | Vendor A | Vendor B | Vendor C |
|---|---:|---:|---:|---:|
| Technical fit (spec compliance) | 30% | 4 | 5 | 3 |
| Lead time (weeks) | 20% | 3 | 4 | 2 |
| Warranty & support | 15% | 4 | 3 | 5 |
| Local spares availability | 10% | 2 | 5 | 3 |
| Price (CAPEX) | 15% | 4 | 3 | 5 |
| References / past projects | 10% | 5 | 4 | 2 |
| Total (weighted) | 100% | 3.6 | 4.1 | 3.4 |

Appendix E – Procurement RFP high‑level contents (for each candidate site)
- Project overview and objectives
- Scope of supply (technical specs for containers, batteries, inverters, BESS management system)
- Scope of installation and integration (connection to existing switchgear, earthing, cabling)
- Testing & commissioning requirements (factory acceptance test, site acceptance test)
- Performance guarantees (minimum efficiency, roundtrip, degradation schedule)
- Warranty and spares obligations
- Delivery timeframe and penalties for delay
- Pricing schedule and payment milestones
- Evaluation criteria and scoring methodology
- Clarification & submission instructions

Appendix F – Draft term‑sheet outline (for lenders/donors)
- Borrower / counterparty
- Facility size (USD)
- Purpose (CAPEX for microgrid installation, associated civil & interconnection)
- Capital structure:
  - Grant amount / concessional tranche (USD & %)
  - Senior debt (USD, tenor, interest rate)
  - Equity (if any)
- Use of proceeds
- Key covenants (DSCR thresholds, reporting cadence)
- Security package (assignment of O&M contract cashflows or lien on assets)
- Conditions precedent
- Drawdown schedule
- Reporting and audit requirements

Appendix G – Environmental & Social screening checklist
- Checklist items:
  - Land tenure and affected parties identified?
  - Sensitive receptors (schools, water wells, cultural heritage) within 300 m?
  - Noise modelling required for genset operations?
  - Hazardous materials / fuel storage risk and secondary containment?
  - Waste management and battery recycling pathways?
- Deliverable: rapid ESMP template for pilot sites.

Appendix H – Commissioning & acceptance checklist (sample)
- Pre‑installation checks: site grading, power availability, crane and access verified.
- Factory Acceptance Tests (FATs): vendor to provide FAT reports for battery, inverter and control systems.
- Site Installation: mechanical & electrical installation checked vs drawings.
- Protection & control: relay settings verified, islanding tests completed.
- Functional tests: battery charge/discharge cycles, genset seamless transition tests.
- Performance acceptance: proof of anticipated diesel reduction profile over 7 days.
- Final sign‑off: signatures from BlueHarbor technical lead and Wild Advice.

Appendix I – KPIs & Monitoring for pilot operation (sample)
- Fuel consumption (L/month)
- Fuel cost per kWh (USD/kWh)
- Average outage frequency (events/month)
- Average outage duration (minutes/event)
- Battery state of health (SOH %)
- Availability of installed system (% uptime)
- Customer complaints related to quality (count/month)

Appendix J – Training and O&M knowledge transfer plan
- Training modules:
  - Basic system overview and safety (1 day)
  - Operation & daily checks (1 day)
  - Basic troubleshooting & firmware updates (1 day)
  - Monthly maintenance activities and spare part replacement (half day)
- Deliverable: training slides, quick reference guides and a schedule for on‑site shadowing during first 30 days of operation.

---

## 11. Estimated resource & cost envelope (high level)

This section provides Wild Advice’s estimate of the internal resource allocation and a high‑level consulting fee envelope for the 6‑week rapid engagement (for client budgeting; final SOW to follow).

Estimated internal team days
- Lisa – Project lead & stakeholder engagement: 12 days
- Alex – Data & modelling: 18 days
- Oscar – Technical & siting: 12 days
- Sara – Procurement & vendor engagement: 8 days
- Marcos – Client liaison & admin: 4 days
- Total consultant person‑days: 54 days

Indicative fee estimate (excluding travel, taxes and vendor costs)
- Daily rate assumptions (example):
  - Senior lead (Lisa) USD 1,200/day
  - Technical lead / modeller (Alex / Oscar) USD 900/day
  - Procurement specialist (Sara) USD 700/day
  - Project coordinator (Marcos) USD 500/day
- Indicative total consulting fee: USD 54k – 75k (range depends on seniority mix and client onsite requirements). Final quote to be issued following a quick SOW sign‑off.

Travel & expenses
- If site visits are required for pilot assessment in Week 2–4, separate travel estimate will be provided. We recommend at least one on‑site assessment for the top candidate pilot to validate siting constraints prior to RFP issuance.

---

## 12. Closing & ask to BlueHarbor

We are ready to start immediately upon receipt of the data and confirmation of client participants for the kickoff. To maintain the 6‑week delivery schedule we require:

Immediate asks (again, succinctly):
- Secure access to the datasets in Appendix A within 24–48 hours.
- Confirmation of primary contacts for operations, treasury, procurement and the regulator.
- Availability for a 30–45 minute kickoff in the next 24 hours (proposed time: [propose time based on client timezone]; please confirm or propose alternative).

If any of the above is not feasible, please indicate timings and blockers in the shared issue log so we can replan.

We aim to produce tangible, bankable outcomes — not just concepts. Our focus will be on actionable pilot(s) with clear procurement and financing paths so BlueHarbor can significantly reduce diesel exposure and improve supply reliability with minimal disruption.

Prepared by: Lisa Carter (Wild Advice Partners)