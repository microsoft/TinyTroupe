# Port Aurora — Rapid Flood Resilience Plan (Initial Report)

Prepared by: Lisa Carter, Data Scientist, Wild Advice Partners  
Lead: Analytics & Report Author

Date: Day 0

---

Contents
1. Executive summary  
2. Situation and scope  
3. Key findings (expanded)  
4. Immediate (0–6 week) recommendations (expanded)  
   A. Rapid diagnostic (owner: Lisa; support: Alex)  
   B. Quick operational measures (owner: Marcos, with City contacts)  
   C. Shelter typologies & prototype work (owner: Oscar)  
   D. Finance & eligibility modelling (owner: Alex)  
   E. Procurement and supply-chain actions (owner: Marcos / Oscar)  
5. FEMA grant submission approach (owner: Marcos; support: Lisa & Alex)  
   - Draft narrative outline and scoring mapping  
   - Required attachments and templates  
6. Proposed milestone timeline (owners & partners) — detailed Gantt-style table  
7. Roles, responsibilities and RACI matrix  
8. Short-term risks & mitigations (detailed risk register)  
9. Immediate asks for the team (action checklist)  
10. Next steps (today) — expanded operational checklist  
11. Appendix A — Focused data request (for City; fallback-first) with templates  
12. Appendix B — Example shelter typologies, BOMs, cost ranges and lead-times  
13. Appendix C — Finance model sample inputs & worked examples  
14. Appendix D — Sample emails, letters of support, and community outreach templates  
15. Appendix E — Monitoring, evaluation and post-deployment plan  
16. Appendix F — Data schemas and sample CSV/GeoCSV formats

---

1. Executive summary

Port Aurora faces recurring and increasing flood events that regularly strain available shelter capacity. Municipal budgets are constrained and usual procurement timelines are long. To achieve rapid, equitable improvements to shelter capacity and FEMA-eligibility for funding, we propose a two-track approach:

- Track A — Rapid analytics-driven diagnostic (0–2 weeks): gather the minimum viable data set, run descriptive and prioritized site-selection analytics, and output a 1-page dashboard (hotspots) plus ranked candidate sites for surge capacity interventions. This diagnostic is designed to produce evidence that directly supports FEMA scoring criteria (equity, risk reduction, short-term deployability).
- Track B — Near-term operational and shelter interventions (0–6 weeks): deploy short-lead-time operational measures (retrofit of existing public buildings, pre-staging supplies), deliver three modular shelter typologies and two retrofit kits with BOMs and cost/lead-time flags, and prepare a FEMA grant package within a 6-week window.

This report provides immediate recommendations, a detailed owner-assigned timeline for deliverables, technical annexes (typologies, BOMs, finance inputs), a full risk register, templates to accelerate City engagement, and a plan for FEMA submission aligned to anticipated scoring criteria.

Key near-term objective: Submit a FEMA grant application within ~6 weeks that documents prioritized interventions, cost estimates, site maps (using fallback coordinates if shapefiles are delayed), and municipal commitments.

---

2. Situation and scope

Problem statement (expanded)
- Port Aurora experiences repeated flooding across coastal and low-lying inland neighborhoods. Events generate localized inundation and major events that require temporary sheltering.
- Current shelter capacity (official and ad-hoc) is likely insufficient to meet simultaneous displacement needs during major flood events.
- Drainage infrastructure is aging; stormwater conveyance capacity and maintenance records are incomplete.
- There is a need to balance fast deployment with equity: ensure shelters are sited where vulnerable populations (seniors, mobility-limited, low-income households) can access them.

Goal
- Produce an evidence-backed, FEMA-aligned plan to increase near-term surge shelter capacity (0–6 weeks), prioritize equitable siting decisions, and submit a FEMA-eligible grant package.

Scope (what this report covers)
- Rapid diagnostic methods, prioritized site-selection criteria and immediate candidate list.
- Operational measures for rapid capacity increases (retrofits, pre-staging supplies).
- Design and costing for modular shelter typologies and retrofit kits suitable for rapid procurement and local manufacture.
- Municipal finance modelling for capital and operating costs and FEMA-eligibility mapping.
- A six-week project plan to produce a complete FEMA submission package.

Constraints and assumptions
- Data availability is variable; shapefiles/LiDAR may be delayed. Fallback formats must be used.
- Procurement timelines may preclude full modular deployments within 2 weeks; retrofits of existing buildings are fastest.
- Budget constraints: we will present low, mid, and high capital cost scenarios.
- FEMA rules may require municipal match or particular procurement/contracting language — we will coordinate with City Grants Officer.

---

3. Key findings (based on brief & constraints)

Demand pressure and equity
- Preliminary municipal inventory (summary inputs) indicates shelter capacity concentrated in central/municipal zones; peripheral high-exposure neighborhoods show high counts of at-risk populations (seniors, limited mobility).
- Likely gap: surge capacity shortfall of approximately 25–40% (estimate range to be refined with data) for a moderate flood event.

Data risk and fallback pathways
- Primary data risk: GIS exports (shapefiles, LiDAR) may be delayed beyond our 72-hour target.
- Fallback plan: immediately request shelter coordinate CSV, building addresses and capacity tables, scanned emergency plans (PDFs), and historical incident logs.

Rapid-intervention opportunities
- Low-cost modular shelters and rapid retrofit kits exist and can add capacity quickly when combined with retrofits of schools/gyms.
- Short-lead items: inflatable partitions, privacy screens, portable toilets, ADA ramps, floor coverings — many available within 0–6 weeks via national distributors or local manufacturers.

FEMA-eligibility window
- FEMA tends to favor projects demonstrating immediate risk reduction, equity-focused site selection, and cost-effectiveness. Short lead-time, municipal-implemented projects with clear deliverables are competitive — our approach emphasizes these.

---

4. Immediate (0–6 week) recommendations (expanded)

A. Rapid diagnostic (owner: Lisa; support: Alex)

Objective: Within 10 business days deliver a one-page dashboard + hotspot list and prioritized candidate sites for surge capacity intervention with supporting datasets and assumptions documented.

Actions and method
1. Data request (send within 24–72 hours). Prioritize fallback CSVs/PDFs (see Appendix A).
2. Ingest available data into an established analytic pipeline (Python/R scripts + QGIS if shapefiles available). Use fallback coordinate CSV to create quick GeoCSV.
3. Produce the following analytics deliverables:
   - Descriptive summary table: shelter count, capacity, utilization (% typical), distance to high-exposure areas.
   - Heat map of flood exposure (historic incidents) overlaid with vulnerable-population density (seniors, mobility-limited).
   - Accessibility matrix for each candidate site: ADA compliance, transit access, parking, access routes during flood.
   - Priority scoring for candidate sites using weighted criteria (see site-selection criteria below).
4. Output materials (Day 10):
   - 1-page dashboard PDF (hotspots, top 10 candidate sites, quick stats).
   - Ranked candidate site list (Excel/CSV) with scoring breakdown.
   - Short methods writeup: data used, assumptions, fallback data notes.

Site-selection criteria (proposed weights — adjust if City provides constraints)
- Vulnerable population proximity (age, disability, poverty): 25%
- Flood exposure reduction potential (ability to reduce travel/exposure): 20%
- Accessibility (ADA, transit, road access during flood): 15%
- Existing infrastructure condition (sanitation, electricity, HVAC): 15%
- Feasibility (ownership, municipal control, legal constraints): 10%
- Time-to-operational (lead time for retrofit/modules): 10%
- Community support / equity considerations: qualitative overlay

Deliverables and outputs
- Dashboard, ranked candidates, data package with metadata, and recommended immediate interventions.

B. Quick operational measures (owner: Marcos, with City contacts)

Objective: Provide immediate shelter capacity and safe spaces using existing public buildings and rapid retrofits.

Operational checklist (first 72 hours to 2 weeks)
1. Activate temporary use of large, accessible public buildings (gyms, municipal auditoria, community centers, schools during non-instruction times).
   - Minimum retrofit actions: clear signage, accessible ramps, basic sanitation, space demarcation for distancing/privacy, basic bedding and floor coverings.
2. Pre-stage basic supplies at identified hubs in or adjacent to vulnerable neighborhoods:
   - Bedding kits (cots + blankets), hygiene packs, PPE, portable heaters/coolers as needed, sanitation supplies.
3. Staffing and operations:
   - Identify staffing rosters (volunteer + municipal staff). Prepare a simple SOP for intake, registration, triage, medical needs and accommodations for mobility-limited.
4. Accessibility and transportation:
   - Pre-contract accessible transport (paratransit) for residents with mobility impairments; identify pickup/handoff points.
5. Safety and infection control:
   - Include basic infection prevention (hand sanitizer stations, signage), especially if sheltering for prolonged periods.
6. Pre-deploy communications:
   - Alert templates, community hotlines, shelter maps, and route guidance to be pre-drafted for activation.

Quick SOP outline (shelter activation)
- Activation trigger (threshold rainfall, flood advisory, municipal declaration)
- Lead contact: Emergency Manager (City) + interim PM (Marcos)
- Triage and intake steps: registration, medical needs, accessibility needs
- Shelter operations hours and nightly capacity management
- Demobilization and re-stocking schedule

C. Shelter typologies & prototype work (owner: Oscar)

Objective: Deliver three modular typologies and two retrofit kits with one-pager sheets, 2–3 thumbnails each, full BOMs, cost ranges and lead-time flags.

Deliverables (by Day 10)
- Three modular typologies: Type A (Short-stay modular pods for low-cost rapid deployment), Type B (Medium-capacity modular pods with enclosed sleeping areas), Type C (Durable community modular shelter units with climate control).
- Two retrofit kits: Retrofit Kit 1 (Minimal rapid retrofit for gyms/schools) and Retrofit Kit 2 (Advanced retrofit with partitioning, improved sanitation, accessibility ramps).
- For each: one-pager, 2–3 thumbnails, detailed BOM, installation footprint, electricity and sanitation needs, rough lifecycle cost ranges, and lead time classification.

Lead-time classification (label all items):
- Short (0–6 weeks) — items commonly available from national distributors or local suppliers.
- Medium (6–12 weeks) — items requiring custom orders or limited manufacturing.
- Long (>12 weeks) — bespoke structures, large-volume orders, or items requiring extensive permitting.

Quality/safety requirements
- Minimum ventilation and HVAC guidance for enclosed spaces.
- ADA requirements: ramp gradients, circulation spaces, toilet access.
- Fire safety: egress routes, number of exits, portable fire-fighting equipment.

D. Finance & eligibility modelling (owner: Alex)

Objective: Rapid municipal finance model to estimate capital and operating costs, map costs to FEMA-eligible line items, and provide cost ranges for typologies and retrofits.

Deliverables
- Rapid finance spreadsheet (low/mid/high scenarios) covering:
  - Capital costs: modular purchases, retrofit materials, one-time site work.
  - Operating costs: staff, utilities, maintenance for the projected operational period (assume initial 6-month horizon).
  - FEMA-eligibility mapping: which cost items are likely FEMA-eligible (e.g., emergency repairs, temporary facilities) vs. municipal match requirements.
- Short narrative on funding gap and suggested municipal match strategies (in-kind labor, municipal materials, volunteer mobilization).

Worked example (sample numbers — to be refined)
- Example: Retrofit Kit 1 applied to 3 gym sites
  - Capital per site: $18,000 — includes partitions, portable toilets (2), ADA ramp, signage, basic bedding.
  - Operating (6 months): $9,000 per site — staffing, utilities, supplies.
  - Total per site: $27,000
  - For 3 sites: $81,000
- Example: Modular Type A (10 pods)
  - Capital: $6,000 per pod (short-lead solution) = $60,000
  - Shipping & installation: $10,000
  - Operating (6 months): $12,000
  - Total: $82,000

E. Procurement and supply-chain actions (owner: Marcos / Oscar)

Actions
- Immediately identify local/regional suppliers for short-lead components. Create a prioritized vendor list (national distributors for urgent items, local manufacturers for medium-term).
- Identify emergency procurement pathways with City Procurement and Grants Officer (pre-approved vendors, sole-source justifications, cooperative purchasing agreements).
- Prepare a draft procurement package (SOW + sample PO) for short-lead items to accelerate contracting upon City approval.

---

5. FEMA grant submission approach (owner: Marcos; support: Lisa & Alex)

Objective: Prepare a competitive FEMA application emphasizing equity, vulnerability reduction, short lead time, and rapid deployability.

Strategy and narrative outline
- Cover letter: municipal commitment, high-level summary of need, and intended use of funds.
- Technical narrative: present diagnostic findings (hotspots), prioritized sites, expected reductions in exposure for vulnerable populations, and operational plan for shelters.
- Cost appendices: detailed cost estimates for each intervention (Alex).
- Site maps: preferred shapefiles or fallback coordinate maps (Lisa).
- Letters of support / municipal commitment: Mayor, Emergency Manager, School District, Community Organizations (draft templates in Appendix D).

Mapping to FEMA scoring
- Demonstrate: (1) risk reduction (measurable reduction in exposure or improved capacity) (2) operational readiness (supply chain, procurement plan) (3) equity (priority to high-vulnerability neighborhoods) (4) cost-effectiveness (low capex per sheltered person) (5) partnerships & municipal commitment (letters).
- Provide explicit mapping table that references each scoring criterion and where in the application evidence can be found.

Required attachments (typical — confirm with City Grants Officer and FEMA rubric)
- Technical narrative and project description
- Cost estimate spreadsheet and supporting quotes/pro-forma invoices
- Site maps and photos
- Letters of support and municipal resolutions/commitments
- Project schedule / milestones (this timeline)
- Procurement plan and vendor lists
- Environmental & historical preservation compliance statements (as applicable)

Deliverable timeline
- Week 3: Draft technical narrative & cost appendices
- Week 4: Draft client report & internal review
- Week 5: Finalize grant package and obtain City sign-offs
- Week 6: Submission

Scoring-focused attachments to prioritize
- Evidence of vulnerability reduction: maps showing populations served within 1 mile of sites, before/after capacity calculations.
- Short-lead procurement plan: vendor quotes/letters of intent for items within 0–6 weeks.
- Equity-focused letters: statements from community organizations representing seniors, disability advocates.

---

6. Proposed milestone timeline (owners & partners) — detailed

Gantt-style milestone table (relative days)

| Milestone | Owner | Start | Target Complete | Key Outputs |
|---|---:|---:|---:|---|
| Day 0 — Send data request to City | Lisa | Day 0 | Day 0 | Data request email + checklist |
| Day 0 — Confirm roles & kickoff | Lisa | Day 0 | Day 0 | Kickoff invite & role confirmations |
| Day 0–3 — Vendor identification for short-lead items | Oscar/Marcos | Day 0 | Day 3 | Vendor list + preliminary quotes |
| Day 3 — Receive initial data or fallback | City → Team | Day 0 | Day 3 | CSVs/PDFs/GeoCSV |
| Day 5 — Oscar submits typology one-pagers + thumbnails | Oscar | Day 0 | Day 5 | 3x one-pagers + BOM summaries |
| Day 7 — Alex delivers initial cost & finance inputs | Alex | Day 0 | Day 7 | Finance model skeleton & mapping |
| Week 2 (Day 10–14) — Rapid diagnostic report | Lisa / Alex | Day 0 | Day 14 | 1-page dashboard + hotspot list |
| Week 3 (Day 15–21) — Draft FEMA narrative & cost appendices | Marcos / Alex / Lisa | Day 15 | Day 21 | Narrative draft + cost appendices |
| Week 4 (Day 22–28) — Draft client report & review | Lisa | Day 22 | Day 28 | Draft report |
| Week 5 (Day 29–35) — Finalize grant package & City sign-offs | Marcos / City | Day 29 | Day 35 | Final grant package |
| Week 6 (Day 36–42) — Submit to FEMA | Marcos / City | Day 36 | Day 42 | Submission |

Notes:
- If shapefiles arrive late, mapping tasks pivot to coordinate-based mapping (GeoCSV).
- Critical decision point is Day 14: finalize candidate sites for immediate retrofits vs modular procurement.

---

7. Roles, responsibilities and RACI matrix

Primary team roles
- Lisa Carter — Data & analytics lead; report author; produces diagnostic deliverables.
- Marcos [Last name TBD] — Interim PM; public-health lead; responsible for City engagement and FEMA submission.
- Oscar [Last name TBD] — Shelter typology & design lead; BOMs; vendor liaison.
- Alex [Last name TBD] — Finance & municipal-modelling lead; provides cost estimates and FEMA-eligibility mapping.

RACI (example for key deliverables)

| Deliverable | Responsible | Accountable | Consulted | Informed |
|---|---:|---:|---|---|
| Data Request Sent | Lisa | Lisa | Marcos / Alex | City contacts |
| Rapid Diagnostic (dashboard, hotspot list) | Lisa | Lisa | Alex | Marcos / Oscar |
| Typologies + BOMs | Oscar | Oscar | Lisa / Alex | Marcos |
| Finance model & cost appendices | Alex | Alex | Lisa / Marcos | Oscar |
| Procurement plan | Marcos | Marcos | Oscar / City Procurement | Lisa / Alex |
| FEMA narrative | Marcos | Marcos | Lisa / Alex | City leadership |

Communication cadence
- Daily standup (15 min) during first 2 weeks (owners + City rep if available).  
- Weekly progress review with City Grants Officer (30–45 min).  
- Milestone reviews at Day 14 and Day 28 for sign-offs.

---

8. Short-term risks & mitigations (detailed risk register)

Risk register — key entries

| # | Risk | Likelihood | Impact | Mitigation | Residual Risk |
|---:|---|---:|---:|---|---:|
| 1 | GIS/LiDAR delay | High | High | Use fallback CSVs, PDFs; generate GeoCSV; prioritize coordinate-level mapping; document assumptions clearly | Medium |
| 2 | Procurement timelines prevent modular deliveries within target | High | High | Prioritize retrofits of public buildings; identify local manufacturers; prepare emergency procurement SOW | Medium |
| 3 | Supply-chain disruption for key components | Medium | Medium | Oscar to flag short-lead items; maintain vendor redundancy; consider rental/borrow options for equipment | Low-Medium |
| 4 | Insufficient municipal match or unresolved procurement requirements (FEMA) | Medium | High | Early engagement with Grants Officer; identify in-kind match options; prepare procurement justification | Medium |
| 5 | Community resistance to selected shelter locations | Low-Medium | Medium | Early outreach with community organizations; transparent criteria; offer community hearing or letter templates | Low |
| 6 | Staffing shortages for operating shelters | Medium | High | Pre-identify volunteer partnerships (Red Cross, NGOs); use municipal staff surge rosters; train staff quickly on SOP | Medium |
| 7 | Legal/ownership constraints on candidate sites | Low | High | Verify ownership early; prioritize municipal-owned buildings; prepare lease/MOU templates | Low-Medium |

Each mitigation should be documented with responsible owner and timeline. For example, Risk 1 mitigation is Lisa sending fallback request within 24 hours.

---

9. Immediate asks for the team (action checklist)

- Alex: Confirm availability to act as Finance Lead and produce initial municipal modelling inputs (target: confirm within 3 hours). If unavailable, nominate alternate.
- Oscar: Produce 2–3 thumbnails + one-pager assumptions before the kickoff if possible. Label hypotheses and lead times.
- Marcos: Confirm acceptance of interim PM responsibilities for City engagement and FEMA submission ownership.
- City Contacts: Provide requested data within 72 hours; at minimum provide fallback items (shelter coordinates + budget ranges).
- All team: Join Day 0 kickoff call; ensure calendars blocked for core milestone reviews.

---

10. Next steps (today) — expanded operational checklist

1. Lisa: Send data-request email to City (within 3 hours if Alex confirms; otherwise proceed provisionally after 3 hours). Use template in Appendix D.
2. Lisa: Circulate this initial report and attach the data request and kickoff calendar invite (Saturday 09:00 São Paulo timezone as proposed).
3. Oscar: Begin drafting typologies with assumptions; label short lead-time components.
4. Alex: Begin assembling finance model inputs upon confirmation of availability; populate sample cost rows (see Appendix C).
5. Marcos: Reach out to City Emergency Manager and Grants Officer to confirm key municipal contacts and procurement pathways.
6. All: Confirm availability for daily standups and Day 14 review.

---

11. Appendix A — Focused data request (for City; fallback-first) with templates

Priority (fallback-friendly). Please provide, ideally within 72 hours. If shapefiles are not possible, provide equivalent CSV/PDF items.

Requested datasets and minimal formats
- Shelter coordinate list and capacities (CSV) [FALLBACK - highest priority]  
  - Minimum fields: shelter_id, name, address, latitude, longitude, capacity_total, capacity_accessible, current_condition_summary, contact_name, contact_phone, ownership_type (municipal/private), typical_staffing_levels
- Approximate budget ranges / recent capital allocations for shelter and emergency response [FALLBACK] (PDF or Excel)
- GIS flood layers:
  - Preferred: shapefile / GeoJSON for historic inundation polygons, floodplain extents, FEMA flood maps
  - Fallback: PDF or GeoPDF maps with legend; or table of affected census blocks with dates
- LiDAR/elevation or contour data (DEM tiles preferred; fallback: contour PDFs)
- Historical flood incident records (last 10 years) with dates and extents (CSV with incident_id, date, extent_description, affected_addresses or polygon reference)
- Drainage/stormwater asset inventory (locations, condition, capacity) (CSV: asset_id, type, location_lat, location_lon, condition_score, last_maintenance_date)
- Emergency shelter list & operational notes (accessibility, staffing, current condition; PDF manual OK)
- Evacuation routes and known traffic constraints (PDF map or CSV list of critical routes)
- Demographic/vulnerable-population mapping (seniors %, disability %, low-income % by small geography) — CSV or shapefile
- FEMA grant criteria & scoring rubric, required attachments, deadlines (PDF)
- Primary municipal contacts with emails/phone and preferred availability for rapid calls

Sample email template (send from Lisa — full body available in Appendix D)

Data delivery checklist (for municipal contact)
- If sending shapefiles: include projection (EPSG), readme file describing layers, attributes and update date.
- If sending CSVs: include column headers, units, and a short metadata file describing each field.

---

12. Appendix B — Example shelter typologies, BOMs, cost ranges and lead-times

Note: Numbers below are initial estimates for planning and should be refined once vendor quotes and City data are available.

Typology: Type A — Short-stay modular pods (10-person cluster)
- Purpose: Rapidly increase capacity for transient sheltering during immediate events.
- Footprint: 6 pods per 100 m2 clear space (each pod ~1.5 x 2.5 m sleeping area).
- Key components / BOM (short lead items flagged *):
  - Inflatable or rigid-frame pod units * (10 units): $4,000 total ($400/unit) — Short lead
  - Privacy curtains & partitions *: $1,500 total
  - Modular floor coverings (waterproof mats) *: $1,200
  - Lighting (battery or plug-in) *: $600
  - Bedding kits (10) *: $2,000 ($200 each)
  - Temporary power & extension cords: $1,000
  - Shipping & installation: $3,000
  - Total capital (approx): $13,300
- Operating (per 3 months): staff, utilities ~$5,000
- Lead-time: Most components short (0–6 weeks)

Typology: Type B — Medium-capacity modular pods (20-50 persons)
- Purpose: Provide enclosed sleeping areas with basic amenities for multi-day stays.
- BOM highlights:
  - Modular frame shelters (20 units) — $20,000
  - Partition systems & privacy screens — $6,000
  - Portable toilets (4) with service agreements — $8,000
  - HVAC/ventilation units (temporary) — $10,000
  - Bedding kits (50): $10,000
  - Installation & site prep — $12,000
  - Total capital (approx): $66,000
- Lead-time: Mix of short and medium (some HVAC equipment lead 6–12 weeks)

Typology: Type C — Durable community modular shelter (100+ persons)
- Purpose: Provide more robust sheltering solution with climate control and improved services.
- BOM highlights:
  - Containerized units / heavy modular units (4 units) — $125,000
  - Sanitation block (plumbed toilets & showers) — $40,000
  - Power generation / connections — $20,000
  - Accessibility ramps, flooring — $10,000
  - Total capital (approx): $195,000
- Lead-time: Medium to long (>6 weeks)

Retrofit Kit 1 — Minimal retrofit for gyms/schools (per site)
- Purpose: Quick conversion of existing gym/auditorium to surge shelter.
- Contents:
  - Portable ADA ramp (if steps present) *: $1,200
  - Privacy partitions (20 sets) *: $4,000
  - Portable toilets (2) & handwashing stations *: $4,000
  - Signage, wayfinding, registration desk kit *: $1,000
  - Bedding kits (50) *: $10,000
  - Cleaning & sanitation supplies (initial stock): $1,000
  - Installation & labor (local) : $2,800
  - Total capital (approx): $24,000
- Lead-time: All items short (0–6 weeks)

Retrofit Kit 2 — Advanced retrofit with improved hygiene & accessibility
- Contents:
  - All items from Kit 1
  - Portable shower modules (2) — $12,000
  - Temporary partitioned recovery/medical space — $3,500
  - HVAC filtration units (portable) — $6,000
  - Additional staffing & training budget — $5,000
  - Total capital (approx): $50,500
- Lead-time: Some items medium (shower modules may be lead 6–12 weeks)

Cost-efficiency metrics (examples)
- Cost per person (Type A example): $13,300 capital / 10 persons = $1,330 per person (short-stay pod)
- Cost per person (Gym retrofit): $24,000 / 50 persons = $480 per person (rapid, cost-effective)
- Use cost-per-person and lead-time as primary decision axes: prioritize low cost-per-person + short lead-time where possible.

---

13. Appendix C — Finance model sample inputs & worked examples

Finance model structure (spreadsheet tabs)
- Inputs: inflation, contingency %, labor rates, utility rates, municipal cost assumptions.
- Capital costs: itemized BOM lines with unit cost, quantity, lead-time.
- Operating costs: staffing (FTE), per diem volunteer costs, utility per month estimates.
- FEMA mapping: tag each cost row with FEMA-eligible Y/N/Conditional and note required documentation.
- Outputs: Total project cost (capital + operating), municipal match requirement, scenario analyses.

Sample worked scenario (3 gym retrofits + 20 Type A pods)
- Gym retrofits (3 x $24,000) = $72,000
- Type A pods (20 pods, capital as per earlier $13,300 for 10 pods -> scale to 20) = $26,600
- Installation and contingency (10%) = $9,860
- Operating for initial 6 months = $5,000 (gyms) + $5,000 (pods) = $10,000
- Total project = $118,460
- FEMA-eligible estimate: 85% (assume FEMA can cover emergency retrofit & temporary shelters; municipal match 15%) -> FEMA request = $100,691; municipal match = $17,769
- Municipal match options: in-kind staff time, municipal materials, or local fundraising commitments.

FEMA-eligibility notes
- Document all quotes and procurement SOWs for eligible costs.
- Keep contingency in line with FEMA rules (often allowable up to a % but must be justified).
- Track match sources with signed forms or council resolution.

---

14. Appendix D — Sample emails, letters of support, and community outreach templates

A. Data request email (Lisa to City Grants Officer / Emergency Manager)

Subject: Urgent — Data Request for Rapid Flood Shelter Diagnostic (Port Aurora) — 72-hour requested response

Body:
Dear [Name],

Wild Advice Partners is preparing an immediate Rapid Flood Resilience diagnostic for Port Aurora to support near-term shelter capacity improvements and a potential FEMA application. To complete the diagnostic within the required timeline, please provide the following items within 72 hours (fallback formats acceptable):

[List the items from Appendix A]

If shapefiles are not available, a simple CSV of shelter coordinates and capacities, recent budget allocations, and PDF maps will allow us to proceed. Please also share the best contact for Procurement and the Grants Officer for any required procurement questions.

We are available for a call at your convenience today to clarify any item.

Best regards,  
Lisa Carter  
Wild Advice Partners — Data & Analytics Lead  
[lisa.email@example.com] | +1 (XXX) XXX-XXXX

B. Draft letter of municipal commitment (Mayor)
[Template language confirming municipal match, operational support, and commitment to timely procurement steps. Include signature line for Mayor and date.]

C. Community outreach flyer (plain text)
- When to go to shelters, how to access accessible transport, phone hotline, what to bring.

D. Vendor pre-qualification email template
- Request for short-lead quotes with 72-hour turnaround.

---

15. Appendix E — Monitoring, evaluation and post-deployment plan

Monitoring indicators (initial)
- Number of additional shelter beds added (target per intervention).
- Percent of additional capacity sited within high-vulnerability neighborhoods.
- Time from activation notice to operational readiness (hours).
- Number of sheltered persons served per event.
- Accessibility compliance (number of accessible units per shelter).
- Cost per sheltered person (capital + operating).

Evaluation plan (post-deployment)
- After first activation: conduct a hot wash within 72 hours to capture operational lessons.
- 30-day and 90-day after-action reports: occupancy rates, supply chain performance, staffing sufficiency, community feedback.
- Integrate lessons into a resilient shelter playbook for City use.

Sustainability and reuse
- Consider durable modules for reuse in future events and convert temporary investments into longer-term community assets (e.g., storage, community centers) where allowed.

---

16. Appendix F — Data schemas and sample CSV/GeoCSV formats

A. Shelter inventory CSV sample header
shelter_id, name, address, latitude, longitude, capacity_total, capacity_accessible, current_condition, owner_type, contact_name, contact_phone, notes

B. Historical incident CSV
incident_id, date, incident_type, affected_addresses, estimated_duration_hours, damage_estimate_usd, description

C. Drainage asset CSV
asset_id, asset_type, latitude, longitude, capacity_m3_s, condition_score_1_5, last_inspection_date, maintenance_notes

D. GeoCSV sample note
- Use EPSG:4326 (WGS84) coordinates for latitude/longitude columns.
- Include README with projection and data provenance.

---

Closing notes and commitments

We will iterate rapidly on the diagnostics and typology concepts once the City data arrives. Immediate next actions are critical: Lisa to send the data request, Alex to confirm availability, Oscar to start typology sketches, and Marcos to confirm PM role and engage municipal contacts.

This initial report and timeline are designed to produce actionable recommendations and a FEMA-eligible grant package within the 6-week constraint. Please confirm role acceptances and reply to the data request at your earliest convenience so we can start the diagnostic pipeline.

Prepared by:  
Lisa Carter  
Data Scientist, Wild Advice Partners  
Lead: Analytics & Report Author

(Contact list and signature block to be appended once City and team confirmations are received.)