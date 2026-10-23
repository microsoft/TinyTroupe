# GreenRiver Rapid-Response — 48h Needs Assessment & Pilot Plan (Draft)

Version: 0.1 (Draft)  
Prepared by: Lisa Carter (Lead/PM)  
Date: [Insert date/time]

---

## Executive summary

GreenRiver requests urgent operational support to restore safe vaccination delivery capacity in priority localities experiencing cold-chain and service delivery constraints. This document is a working 48-hour needs-assessment and pilot plan intended to:

- Define the minimum data, files, and named contacts required immediately from the client to proceed (see "Immediate data & named contacts requested").
- Assign team owners and explicit deliverables with timelines and milestones (see "Team owners & roles" and "Deliverables & timeline").
- Propose a practical pilot design for rapid mobile/modular clinic deployment including cold-chain options, shelter concepts, staffing models, and procurement priorities (see "Pilot design (recommended baseline)" and annexed equipment BOMs).
- Provide a clear site selection and scoring framework, operational checklists, monitoring & evaluation metrics (including calculation definitions), and a risk register with mitigations.

This draft is actionable: once the requested data and a named RHA operations contact are provided, the team will finalize the 48-hour memo, produce a prioritized shortlist of three candidate pilot sites, complete GIS overlays, and be prepared to run pilots within the timelines below. The objective is to return safe, verifiable vaccination capability to communities quickly while minimizing cost and assembly time.

Key immediate ask: supply the ten files/contacts listed in the "Immediate data & named contacts requested" section. With those inputs we can finalize the 48h outputs and mobilize procurement and field teams.

---

## Background & objective

Context
- Recent briefings and initial field reports indicate urgent cold-chain failures and constrained service-delivery capacity across several local health catchments. Challenges reported include intermittent electricity at storage nodes, broken or absent cold-chain equipment, lack of validated vaccine carriers for outreach, insufficient staffing for surge delivery, and local access/security limitations.
- The aim is a rapid technical/operational diagnostic to identify candidate pilot sites and deploy scalable pilot interventions (mobile or modular clinics) to re-establish safe vaccine delivery at scale while minimizing cost and time.

Primary objective (48 hours)
- Produce a rapid needs-assessment memo summarizing data-driven site prioritization, a shortlist of three candidate pilot sites with constraints and immediate actions, a community engagement script for safe rollout, and a minimal specification (BOM) for mobile/modular clinic piloting (cold-chain, shelter, staffing, essential consumables).

Scope (within 48 hours)
- Data ingestion & validation from client-provided datasets.
- Rapid GIS overlay and site-constraints analysis.
- Shortlisting of three candidate pilot sites with preliminary feasibility scores.
- Draft technical note on cold-chain and shelter options (Oscar — 24h).
- Draft clinical SOP and outreach checklist (Marcos — 48h).
- Community engagement script and basic IEC (information, education, communication) materials for immediate use.
- A prioritized procurement/fill list for immediate sourcing (passive cold boxes, vaccine carriers with temp loggers, PCM packs, small solar fridges if required).

Out of scope (initial 48h)
- Full procurement and delivery of larger fixed cold-chain equipment beyond immediate passive and small solar options.
- Full community mobilization beyond scripts and CHW briefing materials — this will begin once pilot sites are finalized.
- Extensive training beyond a concise, field-focused orientation for pilot staff (training package to be developed if pilots proceed to week 2).

---

## Immediate data & named contacts requested from GreenRiver (required now)

Providing these files is essential to run the 48-hour diagnostic and prioritize pilot sites by cold-chain verifiability and operational feasibility. Please attach files to the shared folder and copy the named RHA operations contact into the kickoff meeting invitation.

Requested items (priority order)

1) Weekly case counts by locality (CSV) — last 12 weeks.
   - Required columns (CSV header template):
     locality_code, locality_name, admin1, admin2, week_start_date, week_end_date, vaccine_type, doses_administered, age_group, source
   - Purpose: rapid demand mapping and to identify high-need catchments.

2) Cold-chain inventory (CSV + photos where available)
   - Required columns:
     facility_id, facility_name, gps_lat, gps_lon, fridge_model, fridge_capacity_l, installation_date, last_maintenance_date, power_source (grid/solar/generator), onsite_temp_logs_attached (Y/N), temp_log_filename
   - Attach recent temperature logs for each storage node (CSV or logger exports). If logs are in proprietary formats, export as CSV with timestamps and temperatures.

3) Clinic list & capacities (CSV + site notes)
   - Required columns:
     clinic_id, clinic_name, gps_lat, gps_lon, hours_of_operation, typical_daily_visits, catchment_population_est, lead_contact_name, lead_contact_phone, lead_contact_email
   - Note operational hours, staff count per shift, cold-chain equipment at site.

4) Transport assets & availability
   - Inventory of available vehicles (type, capacity, fuel range), drivers, and restrictions.
   - Suggested format:
     vehicle_id, type (truck/4x4/van/motorbike), cargo_volume_m3, fuel_type, fuel_autonomy_km, availability_window (dates/times), driver_name, driver_contact

5) Population estimates or catchment proxies per candidate site
   - Sources (census, projections, CHW lists) and estimated population by age group relevant to scheduled vaccines.

6) Shapefiles or a location list (CSV with GPS coordinates)
   - Candidate clinics, storage nodes, district boundaries, roads (if available). GeoJSON acceptable.
   - If shapefiles not available, provide CSV with facility_name, latitude, longitude, admin1, admin2.

7) Security/permit constraints and any known access restrictions by site
   - Brief notes per site: restricted hours, permits required, known safety incidents, local community tensions.

8) Emergency budget envelope and any procurement flexibilities
   - Available budget for the pilot (immediate 1–2 week envelope), procurement thresholds, approved vendors or procurement lead times.

9) Named RHA operations contact (required now)
   - Provide name, role, mobile phone, secure channel (WhatsApp/Signal), email, and delegated decision authority for operational approvals.

10) Local NGO/CHW contact list (if available)
    - Names, organizations, phone numbers, geolocated if possible. These contacts are critical for community engagement and outreach.

Data delivery formats and minimum metadata
- Preferred formats: CSV (UTF-8), GeoJSON or Shapefile, JPEG/PNG for photos, and PDFs for existing SOPs. Please include date collected and data source for each file.
- If elements are missing, flag in file and provide the best available estimate with provenance.

If any of the above cannot be provided within 24 hours, indicate partial availability and the expected delivery time so that the team can adjust the plan.

---

## Team owners & roles (detailed responsibilities)

- Lisa Carter — Lead/Project Manager & Report owner
  - Overall coordination, final deliverable consolidation, scenario analysis, client communications, and approval gating.
  - Responsible for compiling the 48h memo, site shortlist and coordinating rapid review cycles.
  - Escalation point for procurement decisions beyond stated thresholds.

- Marcos Almeida — Clinical Lead & Community Engagement
  - Clinical SOPs and sign-off on outreach scripts.
  - AEFI (Adverse Events Following Immunization) guidance and emergency response checklist.
  - Responsible for clinical training brief (on-site orientation) for vaccinators and CHWs.

- Oscar (Surname) — Modular/Mobile Clinic Design & Cold-chain Lead
  - Technical note on passive cold boxes, PCM options, validated vaccine carriers with temp-loggers, solar-fridge options, and shelter concepts.
  - Produce 24h technical note (target within 24 hours) and contribute to the 72h finalized rapid needs-assessment.
  - Provide BOMs and quick procurement lists for immediate equipment.

- Alex (Surname) — Mapping & GIS Specialist
  - Rapid GIS overlay, site-constraints analysis, distance-to-hub calculations, travel-time isochrones (drive/walk), and risk exposure mapping.
  - Responsible for uploading overlays and producing annotated maps for each candidate site within 48 hours of receiving shapefiles.

- Sara (Surname) — Project Sponsor / Client Liaison
  - Help secure client approvals, unblock access to restricted files, and assist with high-level sponsor communications.
  - Escalation channel for approvals if RHA contact is delayed.

- Field/local partners (to be confirmed): CHWs, local NGO leads, and contracted drivers/assemblers.
  - Local team responsibilities: community engagement, site prep, vaccine handling at point-of-service, and reporting.

Contact matrix (example)
- For operational approvals: RHA operations contact -> Sara -> Lisa
- For clinical sign-off: Marcos
- For technical equipment decisions: Oscar (with Lisa and Marcos)

---

## Deliverables & timeline (detailed, draft)

All times are referenced to local BRT/CET as noted in planned kickoff. This timeline assumes receipt of the requested inputs within 2 hours of kickoff.

High-level timeline
- T+0–6 hours: Data intake, quick validation, and assign site initial feasibility (Lisa/Alex).
- T+6–24 hours: Oscar delivers 24h technical note; Alex begins GIS overlay; Marcos drafts clinical SOPs.
- T+24–48 hours: Lisa produces 48h needs-assessment memo, site shortlist (3 candidate pilots), community engagement script; Marcos completes clinical SOP/AEFI checklist; Alex delivers final GIS overlay.
- T+48–72 hours: Oscar & Lisa finalize rapid needs-assessment, site-constraints table and two concept directions with rough BOMs and assembly time estimates.
- Week 2: scenario modeling for scale (costs, staff cadence, supply needs) and pilot implementation planning.

Detailed deliverable list (with owners and target hours)
| Deliverable | Owner(s) | Target delivery |
|---|---:|---|
|Kickoff meeting facilitation and agenda | Lisa | 07:30 BRT (primary), backup 18:30 BRT |
|Data ingestion & minimal validation | Lisa & Alex | Within 2–6 hours of receiving files |
|24h technical note — cold-chain & shelter options | Oscar | Within 24 hours |
|Rapid GIS overlay & access map | Alex | Within 24–48 hours after shapefiles |
|48h needs-assessment memo & site shortlist (3) | Lisa | Within 48 hours |
|Clinical SOPs & AEFI checklist | Marcos | Within 48 hours |
|Community engagement script (CHW brief) | Marcos | Within 48 hours |
|Pilot site constraints table & concept sketches | Oscar & Lisa | Within 72 hours |
|Procurement priority list & quick-BOM | Oscar & Lisa | Within 48 hours |
|Finalized rapid needs-assessment package | Lisa (with Oscar/Marcos/Alex) | Within 72 hours |

Daily (hourly approx.) schedule for T+0 to T+48 (example)
- 07:30–08:30 — Kickoff call: confirm inputs, roles, and communication channels.
- 08:30–10:00 — Lisa/Alex ingest files, basic QA; Marcos reviews clinical implications; Oscar reviews cold-chain inventory.
- 10:00–14:00 — Oscar drafts technical note; Alex runs initial GIS overlays; Lisa synthesizes early findings.
- 14:00–17:00 — Team review (internal): site shortlist candidate selection; assign field verification tasks.
- 17:00–18:30 — Draft deliverables circulated for internal sign-off.
- 18:30 — Handover/standby for overnight inputs from client or local partners.

Proposed kickoff: primary — tomorrow 07:30 BRT (11:30 CET); backup — 18:30 BRT (22:30 CET). Please confirm client availability and named RHA operations contact to lock the slot.

---

## Pilot design (recommended baseline)

Design principles
- Speed: solutions prioritized by lead time and easy assembly.
- Verifiability: cold-chain must be demonstrably within 2–8°C via temp-logger records.
- Scalability: choices should be replicable at low cost and with short procurement lead times.
- Safety: clinical and biosafety controls must meet minimum immunization standards including AEFI readiness.

Site selection guardrails (detailed)
- Must have verifiable cold-chain: recent temp logger data within last 30 days OR capacity to install validated temp-logger and record 24–48h verification before vaccine delivery.
- Access: drive/walk time within 2 hours of a hub capable of restocking or support; road passability documented.
- Local partner presence: CHW or NGO contact able to support mobilization and provide crowd-control/community messaging.
- Security: acceptable safety profile (no active conflict), or security mitigations in place.
- Minimum catchment: site should serve a catchment where pilot is meaningful (e.g., >1,000 target-age population or high unmet need as per case data).

Cold-chain baseline (technical)
- Short-lead solutions:
  - Passive cold boxes (WHO PQS-recommended) for fixed-site buffer and outreach storage.
  - Validated vaccine carriers with temperature loggers (continuous recording loggers; ideally single-use or ruggedized with multiple-day battery life).
  - PCM (Phase Change Material) packs for outreach to maintain carriers at target temperature for extended outreach windows.
  - Small solar-powered refrigerator (50–100 L) for fixed pilot sites where mains power is unreliable (for storage of multi-dose vials).
- Temperature monitoring protocol (quick):
  - Deploy at least one temperature logger per vaccine storage point; set sampling interval to 5–15 minutes.
  - Define in-range as 2–8°C; compute % time-in-range for each 24h period.
  - For outreach sessions, loggers should accompany vaccine carriers and be downloaded at end of day.
  - If out-of-range events occur, stop use of affected vials pending clinical guidance from Marcos.

Shelter & layout
- Options:
  - Lightweight insulated tents (rapid deploy; 3x3m or 6x3m) with raised flooring and hard surfaces for cold boxes.
  - Quick-container conversion (shipping container modified with insulation and battery-powered fridge) where turnover time allows.
  - Vehicle-based outreach (van with built-in cold boxes) if roads permit.
- Assembly:
  - Modular assembly target: 2–4 hours with 3 trained assemblers.
  - Minimal footprint guidance: 6–12m2 per pilot point (vaccination, registration, observation).
- Layout recommendations:
  - Entrances/exits separated to manage flow, registration station before vaccination station, separate observation area (3–5 minutes observation) with seating and emergency kit nearby.

Minimal staffing mix per pilot shift (example)
- Shift length: 6–8 hours (adjust as needed).
  - 2 vaccinators (trained and certified per schedule) — administer vaccines, manage AEFI immediate care.
  - 1 registrar/recorder — records doses, logs batch numbers, maintains cold-chain documentation.
  - 1 CHW/outreach mobilizer — community engagement, queuing control, pre-screening for eligibility.
  - 1 logistics/driver — responsible for transport of vaccines, equipment, waste management, and cold-chain maintenance.
- Supervisory oversight: remote clinical lead (Marcos) with on-call availability; local supervisor if multiple sites are operated.
- Rotations and capacity:
  - Throughput estimates: assuming 2 vaccinators, expected throughput 40–100 doses per day depending on including outreach and demand; refine once local demand estimates provided.

PPE & consumables checklist (pilot-level)
- Vaccine carriers (validated) — quantity = number of outreach teams + 1 spare.
- Passive cold boxes — 1–2 per fixed site depending on throughput.
- Temp-loggers (minimum 2 per site: one in storage and one in carrier).
- PCM packs — number depends on outreach window; calculate from BOM.
- Syringes & safety boxes/sharps containers.
- PPE for staff (masks, gloves, hand sanitizer, aprons).
- Waste disposal bags and supply for safe disposal.
- Basic emergency kit: adrenaline ampoules (as per AEFI protocol), epipen if locally approved, clinical gloves, blood pressure cuff, stethoscope, and first aid.
- Documentation: vaccine batch records, consent forms, tally sheets, IEC materials.

Cold-chain equipment options and lead times (summary table)

| Item | Typical capacity | Use-case | Typical lead-time (procurement) | Priority |
|---|---:|---|---:|---|
|WHO PQS passive cold box (e.g., 16–40L) | 16–40 L | Outreach & short-term storage | Off-the-shelf local supply (0–7 days) | High |
|Vaccine carrier with temp-logger | 5–10 L | Outreach | 3–14 days (loggers may require import) | High |
|PCM packs (pre-conditioned) | N/A | Keeps carriers stable | 7–14 days | High |
|Small solar fridge (50–100 L) | 50–100 L | Fixed pilot sites | 7–21 days (depending on local stock) | Medium |
|Portable generator (small) | 1–2 kW | Backup power for fridge | 3–7 days | Medium |
|Insulated tent (3x3, 6x3) | N/A | Shelter | 1–7 days local supplier | High |

Note: Prioritize passive solutions and vaccine carriers with validated temp-loggers for speed. Solar fridges are higher effectiveness but longer lead times.

Consumables BOM (sample short-list with unit costs estimate - provisional, to be refined with procurement team)
| Item | Unit | Est. unit cost (USD)* | Qty (pilot x1) | Est. total |
|---|---:|---:|---:|---:|
|Validated vaccine carrier w/ temp-logger | each | 150–350 | 3 | 450–1,050 |
|Passive cold box 16–40L | each | 80–200 | 2 | 160–400 |
|PCM pack | each | 10–25 | 10 | 100–250 |
|Small solar fridge 50L | each | 1,200–2,500 | 1 | 1,200–2,500 |
|Temp-logger spare units | each | 80–200 | 2 | 160–400 |
|Insulated tent (6x3) | each | 300–900 | 1 | 300–900 |
|Sharps disposal box (5L) | each | 8–15 | 2 | 16–30 |
|Syringes (0.5 ml) | box 100 | 5–10 | 2 | 10–20 |
|PPE kit (per staff/day) | kit | 8–15 | 5 | 40–75 |

*Costs indicative and vary by supplier and locality; final procurement requires local quotation.

Throughput modeling (simple example)
- If 2 vaccinators deliver 10 minutes per vaccination including registration and observation is rotated to separate space, then per vaccinator assuming 6 productive hours = 36 vaccinations per vaccinator = 72 per day. Adjust for travel, outreach downtime, and breaks; realistic range 40–70 per day.

Cold-chain monitoring & temperature incident protocol (detailed)
- Requirement: continuous temp logging at storage point and carrier during outreach.
- Logger settings: sample interval 5–15 minutes; alarms set at <2°C and >8°C.
- Daily process:
  1. At start of day, confirm temp loggers are functioning and within 2–8°C.
  2. Pre-condition PCM and carriers as per manufacturer instructions.
  3. Record vaccine batch, dose counts, and times removed from cold-chain for each carrier.
  4. End-of-day: download and attach temp logs to site record; calculate % time-in-range.
- Out-of-range handling:
  - If temp breach occurs, isolate affected vials, consult Marcos for risk assessment and safe disposal or use decision.
  - If breach >2 hours or sustained above 8°C, treat vials as compromised unless manufacturer guidance indicates tolerance (document decision).

Waste management
- Sharps containers should be present and not overfilled.
- Segregation of medical waste and safe disposal arrangement with local authorities or contracted waste handlers.
- Burning pits or incineration only if permitted and done per local environmental guidance.

---

## Site selection & scoring framework

Proposed scoring criteria (0–5 scale per criterion; higher = more favorable). Weighting shown as percent; adjust as needed.

| Criterion | Weight | Scoring notes |
|---|---:|---|
|Cold-chain verifiability (recent temp logs) | 25% | 5 = logs within 30 days and in-range; 0 = no logs |
|Access & travel time to hub (road access) | 20% | 5 = <30 min; 1 = 90–120 min |
|Local partner/CHW presence | 15% | 5 = active CHW team and NGO support |
|Population need (case counts/vaccination gap) | 15% | 5 = high unmet need; 0 = low |
|Security & permitting | 10% | 5 = unrestricted; 0 = active security risk |
|Onsite staffing capacity | 10% | 5 = existing vaccinators available |
|Physical site suitability (space, water) | 5% | 5 = full suitability |

Scoring method
- For each candidate site, compute weighted score out of 100. Shortlist top 3 sites subject to quick verification visit or remote verification call.

Site constraints table (example template)
| Site ID | Name | Score | Key constraints | Recommended immediate action |
|---|---|---:|---|---|
|S01 | Community Health Post A | 82 | No recent temp logs; power intermittent | Verify with temp-logger, deploy carriers with loggers, pre-position PCM |
|S02 | Primary Clinic B | 74 | Road access limited in rainy season | Consider motorbike outreach team; pre-deploy extra carriers |
|S03 | Market Outreach Site C | 69 | No fixed storage; strong CHW network | Use mobile outreach with vehicle and passive cold boxes |

---

## Monitoring & Evaluation — Key metrics (pilot)

Define metrics, calculation, and target ranges for pilot evaluation.

1) Doses delivered per day and per site
   - Definition: total number of vaccine doses administered at the pilot site in a calendar day.
   - Target: pilot-dependent (e.g., 40–100/day for mobile site).

2) Cold-chain compliance: % time-in-range (2–8°C)
   - Definition: percent of recorded temperature samples in the 2–8°C band for storage and carrier during operations.
   - Calculation: (count_in_range / total_samples) * 100.
   - Target: >95% for storage; >90% for carriers during outreach.

3) Service uptime: % of scheduled clinic hours delivered
   - Definition: actual hours of service delivered divided by scheduled hours.
   - Target: >90%.

4) Community uptake: attendees per outreach vs target population
   - Definition: attendees per outreach event / (planned eligible population) * 100.
   - Target: context-specific (initial target: 5–15% capture per outreach event depending on campaign).

5) Adverse events reported and % appropriately handled
   - Definition: number of AEFIs reported; percent meeting reporting and response SOP steps.
   - Target: 100% of AEFIs reported and documented, 100% receive initial evaluation, severe events referred according to SOP.

6) Cost per dose delivered (pilot-level)
   - Definition: pilot total cost (equipment, consumables, per diem/staff, fuel) / doses delivered.
   - Target: to be modeled in week 2 for scale comparisons.

Reporting cadence and formats
- Daily site-level brief (one-page) with: doses administered, temp logger % time-in-range snapshots, service uptime, AEFIs, stock on hand and re-order needs.
- Weekly consolidated dashboard with trend charts (doses/day, temp compliance trend, cost per dose estimates).

Data collection templates
- Tally sheet (paper or digital) with fields: date, site, vaccinator name, vaccine type, dose number, batch/expiry, dose count, adverse events.
- Cold-chain logger export README with sampling interval and timezone.

---

## Clinical SOP highlights (rapid orientation)

This section provides the core clinical SOP points that Marcos will expand into a 48-hour clinical SOP document. This is intended for immediate field use.

Pre-deployment
- Confirm cold-chain integrity using logger data or 24h pre-verification if logs missing.
- Ensure all staff have required immunization training and AEFI rapid response orientation.

Vaccination session flow (concise)
1. Registration: confirm eligibility, obtain verbal consent, record unique identifier/tally.
2. Screening checklist: contraindications, allergy history, current illness.
3. Vaccination: vaccinator follows aseptic technique, uses proper reconstitution if required, documents batch & expiry.
4. Observation: 15 minutes for routine sessions unless clinical reason requires longer.
5. AEFI management: immediate mild reactions managed on-site; severe anaphylaxis — administer intramuscular adrenaline per weight-based dosing and arrange urgent transfer.

AEFI documentation & reporting
- Immediate documentation on AEFI form with time, event, management action and referrals. Marcos will provide a simple AEFI reporting template.
- All suspected severe AEFIs to be communicated immediately to RHA ops contact and Marcos.

Waste management and infection control
- Single-use syringes only; immediate disposal in sharps container.
- Clean surfaces and hand hygiene between clients.

Cold-chain handling at point of care
- Remove vials only at last possible moment, track time out of cold-chain; discard vials if temp breach indicates compromise per guidance.

Informed consent & communication
- Use locally appropriate language; keep messages concise and respectful; provide clear advice on when to return for next dose and how to report AEFIs.

Marcos will circulate a one-page field SOP and an AEFI action sheet for vaccinators to carry.

---

## Communications & community engagement

Objectives
- Inform communities of the pilot, reduce misinformation, ensure safe queuing and high uptake.
- Mobilize CHWs to pre-register and direct eligible people according to catchment.

Community engagement script (quick field script)
- Greeting and brief introduction of the team and purpose.
- Explain which vaccines are being offered, eligibility criteria, and safety information.
- Explain the observation period and what to report (dizziness, breathing difficulty, swelling).
- Invite questions and provide contact for follow-up.

Example short CHW script for community door-to-door mobilization
- "Hello, my name is [CHW name] with [organization]. On [date], we will be offering [vaccine name] at [site/time]. If you are [eligibility], please come between [hours]. We will observe you for 15 minutes after vaccination. If you can't attend, we will visit your area on [date]. For any concerns contact [CHW phone]."

IEC materials (minimum)
- One-page flyer (in local language): what vaccine, who can receive it, where/when, what to bring, what to expect.
- Poster for site entrance with flow diagram and COVID-safety basics (if applicable).

Community acceptance and rumor management
- Engage local leaders early; brief on objectives and expected duration.
- CHWs as first-line rumor monitors; have simple FAQ responses prepared.
- Rapid escalation path: any significant resistance or protests escalate to RHA contact and Sara.

---

## Principal risks & mitigations (expanded)

Comprehensive risk register (selected items)

| Risk | Likelihood | Impact | Mitigation |
|---|---:|---:|---|
|Missing or incomplete temperature logs | High | High | Prioritize sites with recent logs; if missing, do 24h pre-verification with temp loggers and do not open vaccine vials until verified. |
|Delayed client contact/approvals | High | High | Request named RHA ops contact now; Sara to escalate for approvals; prepare three contingency sites with existing local NGO partners. |
|Procurement delays for critical equipment | Medium | High | Prioritize passive carriers/PCM (local suppliers), rent where possible, and identify local suppliers for tents and basic items. |
|Security incidents at site | Medium | High | Obtain security/permit notes, avoid high-risk locations, coordinate with local authorities and CHWs; do not deploy until security mitigations agreed. |
|Transport breakdowns / fuel constraints | Medium | Medium | Pre-position spare vehicles or motorbikes; secure fuel allowances; schedule sessions to minimize travel. |
|Low community uptake due to misinformation | Medium | Medium | Use CHWs and local leaders for pre-engagement; provide FAQs and rumor response; hold small community info sessions before campaign. |
|AEFI incidents causing reputational risk | Low | High | Ensure AEFI SOP and emergency kit onsite; immediate reporting to Marcos and RHA; transparent communication to community. |
|Data quality issues for candidate site selection | Medium | Medium | Use conservative approach and on-site verification for ambiguous sites; use satellite imagery and CHW confirmation to supplement missing data. |

Each mitigation item must be assigned an owner and an expected completion time.

---

## Procurement & logistics (quick action plan)

Immediate procurement priorities (within 48 hours)
- Vaccine carriers with validated temp-loggers (quantity for outreach teams and spares).
- Passive cold boxes for fixed sites.
- PCM packs (sufficient for outreach windows).
- Temp loggers spare units.
- Basic PPE, syringes, sharps boxes, and waste bags.
- Lightweight tents or local shade shelter alternatives.

Procurement path
- Check existing GreenRiver-approved suppliers first for speed.
- Local suppliers for tents, fuel, and small items to reduce lead time.
- If import required for specific equipment (solar fridge, loggers), prioritize items that can be procured within procurement flex thresholds and expedite through emergency procurement channels.

Logistics notes
- Consolidate pick-up points; assign owner for last-mile logistics (recommended: logistics/driver per pilot).
- Cold-chain transport planning: pre-condition PCM packs, check carrier temperatures before loading.

Customs/special permits
- If importing solar fridges or temp-loggers, confirm customs lead times and whether duty waivers apply under emergency procurement.

---

## Next steps (immediate, for the client & team)

Immediate actions (priority)
1) Client: Provide the ten requested files and named RHA operations contact now via the shared folder or secure email.
2) Oscar: Prepare and circulate the 24h technical note on cold-chain & shelter options; cc Marcos for clinical input.
3) Alex: Confirm shapefile readiness and stand by to run GIS overlay once files arrive.
4) Marcos: Draft the 48h clinical SOP and community engagement checklist and circulate for review.
5) Sara: Confirm sponsor status and help expedite client provisioning of files/contacts.
6) Lisa: Upon receipt of inputs, finalize the 48h memo and circulate for rapid review (target: within 6 hours of receiving inputs).

Communications plan for kickoff
- Kickoff call invite to include: RHA operations contact, Sara, Lisa, Marcos, Oscar, Alex, local NGO/CHW leads (if available).
- Shared folder created with version-controlled naming: GR_48h_Input_[date] and GR_48h_Deliverables_[date].

Decision points and sign-off
- Site shortlist finalized by Lisa with clinical sign-off from Marcos.
- Equipment orders approved by Lisa after consultation with Oscar; procurement exceeding emergency thresholds to be escalated to Sara.

---

## Annex (attachments to be circulated when available)

- Oscar: 24h technical note (cold-chain options, vaccine carriers, PCM calculation, solar fridge spec sheets).
- Alex: GIS overlays and site-constraints table (upon receipt of shapefiles).
- Marcos: Minimal clinical SOP & outreach script (AEFI checklist, quick vaccinator orientation).
- Templates (to be circulated):
  - CSV templates for case counts, cold-chain inventory, clinic list, transport assets.
  - Daily site brief template (Excel/PDF).
  - AEFI reporting form (PDF/printable).
  - Consent/tally sheets (paper and digital formats).
  - Procurement quick-BOM with supplier contacts where known.

Sample attachments list (placeholder filenames)
- GR_CaseCounts_template.csv
- GR_ColdChainInventory_template.csv
- GR_ClinicList_template.csv
- GR_TransportAssets_template.csv
- Oscar_24h_TechnicalNote_v0.1.pdf
- Marcos_ClinicalSOP_48h_draft_v0.1.pdf
- Alex_GIS_Overlay_Initial.geojson

---

Prepared by: Lisa Carter (Lead/PM)  
For questions and to provide the requested files, please contact:

- Lisa Carter — [email], +[phone], availability: 06:00–20:00 BRT  
- Sara — sponsor contact: [email], +[phone]  
- Marcos Almeida — clinical lead: [email], +[phone]  
- Oscar — technical lead: [email], +[phone]  
- Alex — GIS lead: [email], +[phone]

---

This is a working draft intended for rapid iteration. Please provide the requested files and confirmations so we can finalize the 48h needs-assessment and move quickly to pilot selection and implementation planning.

[End of main document]

Appendix A — Quick templates & checklists (copy-paste ready)

1) Case counts CSV header:
locality_code,locality_name,admin1,admin2,week_start_date,week_end_date,vaccine_type,doses_administered,age_group,source

2) Cold-chain inventory CSV header:
facility_id,facility_name,gps_lat,gps_lon,fridge_model,fridge_capacity_l,installation_date,last_maintenance_date,power_source,onsite_temp_logs_attached,temp_log_filename

3) Clinic list CSV header:
clinic_id,clinic_name,gps_lat,gps_lon,hours_of_operation,typical_daily_visits,catchment_population_est,lead_contact_name,lead_contact_phone,lead_contact_email,notes

4) Daily site brief (fields)
date,site_id,site_name,team_lead,doses_administered,temp_log_%in_range_storage,temp_log_%in_range_carrier,service_uptime_hours,AEFIs_reported,stock_on_hand(next_day),immediate_needs,notes

5) Quick AEFI immediate response checklist
- Identify reaction and vitals; stop vaccination.
- For mild symptoms: monitor, provide symptomatic care, document.
- For anaphylaxis: give IM adrenaline, call for urgent transfer, document, notify Marcos and RHA.
- Collect contact details for follow-up and report within 24 hours.

Appendix B — Quick PCM conditioning and carrier loading steps
1. Freeze/condition PCM according to manufacturer (solid-state phase change temperature).
2. Pre-cool vaccine carrier interior as per guidance.
3. Place PCM packs around vaccine vials but not in direct contact with vials if manufacturer warns; use insulating spacer as directed.
4. Insert temp-logger centrally; record time loaded, expected time out-of-cold-chain, and staff initials.

Appendix C — Example short community flyer (text)
"Free vaccination at [site] on [date]. Eligible: [eligibility]. Bring [ID if required]. Open [hours]. For questions call [CHW phone]. Vaccines provided are safe and free. You will be observed for 15 minutes afterwards."

---

Please confirm availability for the proposed kickoff slot and provide the ten requested files plus the named RHA operations contact as soon as possible so the team can proceed on the 48-hour plan.