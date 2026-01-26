# IronCliff Emergency Stabilisation & Community Protection Plan — Draft (Expanded)

Author: Lisa Carter (Wild Advice Partners)  
Status: Draft — internal use. Do NOT send externally until legal and community liaison (Marcos) have reviewed and approved.  
Prepared: Immediate (0–3 week) triage plan and asks.  
Version: 1.0 (Expanded)  
Date prepared: [Immediate — update timestamp when used]

---

Contents (quick navigation)
- 1) Executive summary (expanded)
- 2) Safety-first immediate actions (0–24 hours) — detailed tasks, checklists, and templates
- 3) 48-hour deliverables (0–2 days) — outputs and acceptance criteria
- 4) 3-week engineer-verified plan — detailed day-by-day schedule, decision gates, and deliverables
- 5) Communications and legal considerations — stakeholder mapping, approval workflow, draft templates
- 6) Roles & primary owners (summary + deputies & contact fields)
- 7) Immediate data & access requirements (detailed ask & file/spec formats)
- 8) Procurement guidance & FX mitigation — supplier table template, equipment specs, ballpark lead-times
- 9) Risks, assumptions & mitigations (risk register with ratings and owners)
- 10) Proposed immediate next steps (6-hour checklist + sign-off template)
- Appendix A — Suggested deliverables & owners (milestone/Gantt table)
- Appendix B — Technical annex: temporary stabilisation options, construction methods, monitoring plan, lab tests, safety checklist, sample messages/forms

---

1) Executive summary (expanded)

Situation summary — high level:
- Extreme rainfall events over the last 48–72 hours have resulted in overtopping, seepage, and observed movement at the tailings containment embankment at IronCliff quarry. Reports from site personnel and recent satellite/drone imagery indicate zones of erosion at the downstream toe, sediment-laden discharge into the natural drainage channel, and water accumulation behind the crest. Downstream receptors include three small villages (approx. population total 2,100), agricultural land, a primary school, and a community water intake located ~4.2 km downstream along the main drainage path.
- Regulators and lenders have issued an urgent request: provide an engineer-verified emergency stabilisation and community protection plan acceptable to them within approximately three weeks. This plan must be defensible, show a clear evidence chain (data, tests, monitoring), and identify staged measures to protect people and critical infrastructure.

Key constraints and complicating factors:
- Limited pre-existing geotechnical data (few shallow borings, incomplete lab datasets). No recent cross-sections produced within the last 5 years.
- Site access is remote; existing access road is partially washed out and may require temporary works (bridge/culvert bypass) to move 20–30 tonne equipment.
- Heavy equipment procurement faces international FX and customs delays; local rental fleet is limited to small and medium class machines.
- Active Indigenous land claims and culturally sensitive areas within a 1.5 km radius from the site. Community liaison and legal review are essential before any external engagement or on-site activities on Indigenous land.
- Weather forecasts indicate intermittent heavy showers, with one 48-hour window of more intense rainfall expected within the next 7 days (monitor closely).

Our role and scope:
- Wild Advice will provide rapid triage: coordinate remote sensing and mapping, recommend priority in-field borings and monitoring installations, define concept-level temporary stabilisation options, produce an engineer-ready package for regulators/lenders, and lead initial stakeholder liaison until on-site engineers (firm(s) contracted) can verify and implement the recommended works.
- We will not sign off on permanent engineering works — Wild Advice will coordinate emergency geotechnical consultancies who will provide engineer-signed deliverables for regulator/lender submission.

Immediate objective:
- Deliver a defensible, timeboxed 3-week plan that: (a) protects people and downstream receptors; (b) documents short-term stabilisation options capable of immediate implementation (temporary, reversible where possible); (c) identifies required data, supplier options, permits, and community consent steps necessary for engineered works and mobilization.

Success criteria (how we will know the plan is acceptable):
- Regulator and lenders confirm receipt of the submission package and indicate the plan is sufficient to avoid enforcement action within the immediate triage period; or provide a clear list of required clarifications.
- Temporary measures implemented within 72 hours reduce immediate downstream release risk (as measured by discharge observation and monitoring points).
- Community safety protocols and evacuation mapping verified by local leaders and Marcos.
- Geotechnical borings and baseline monitoring completed within the first 7 days to enable final engineer verification in week 3.

---

2) Safety-first immediate actions (0–24 hours) — detailed tasks, checklists, and templates

Top-line instruction: Safety of people first. Any deployment or engagement must follow the on-site safety plan, including work permits, PPE, traffic and access control, and specific community consent requirements. Do NOT send external comms until legal and Marcos have reviewed.

For each numbered action below we provide: objective, step-by-step tasks, deliverables, acceptance criteria, and quick templates where relevant.

Action 1. Issue internal acknowledgement to regulator/lender (Owner: Lisa) — draft only
- Objective: Acknowledge awareness of incident, confirm Wild Advice support and that an engineer-verified plan is in progress, request any data the regulator/lender may hold, and request preferred format for future submissions. Keep factual and conservative.
- Tasks:
  1. Draft one-paragraph acknowledgement (see template below).
  2. Tag legal (cc) and Marcos; mark "HOLD — do not send externally" until legal and community liaison approve final wording.
  3. Post draft to internal ops channel for rapid review by lead owners (Oscar, Alex, Sara) within the 6-hour deadline.
- Deliverable: Internal draft message (email & secure copy in Ops channel) within 6 hours.
- Acceptance criteria: Draft reviewed and no critical factual errors flagged within 3 hours of posting.

Internal draft template (for internal circulation only):
- Subject: IronCliff tailings containment — acknowledgement of incident and Wild Advice support (DRAFT — DO NOT SEND)
- Body (short): "Wild Advice acknowledges receipt of the incident notification regarding the IronCliff tailings containment basin and understands the potential downstream safety and environmental implications. We are mobilising rapid triage support — remote sensing, emergency engineering coordination and community liaison — and will deliver a 3-week engineer-verified stabilisation and community protection plan. We request any existing geotechnical files, monitoring data, and incident imagery you can provide to support rapid assessment. Legal/community liaison/land-claim considerations are being reviewed and we will provide a formal submission once sign-off is received. Please advise any preferred submission format for engineer-signed documentation."
- Include instructions: "Legal: please advise constraints; Marcos: please advise community engagement constraints."

Action 2. Rapid remote-sensing & change-detection (Owner: Alex)
- Objective: Quickly characterise extent of inundation, erosion, slope movement, and downstream flow path using SAR, optical, and drone imagery where safe.
- Tasks:
  1. Immediately task SAR imagery (if available within 24 hours) — specify minimum 3 m resolution where possible; request acquisitions for pre-event baseline (last cloud-free pass), event imagery, and task a new overpass if possible.
  2. Task high-resolution optical imagery (50–80 cm) and multispectral if available.
  3. If weather allows and regulatory permits permit, task a local BVLOS/line-of-sight drone operator (safer to use local operator with existing permits). Drone objectives: orthomosaic (5–10 cm GSD if safe), DEM (from photogrammetry), visible signs of cracking, seepage, surface piping, and downstream sediment plumes.
  4. Generate change-detection products (date1 vs date2) and produce a hazard overlay showing: high/medium/low risk zones, downstream population centers, primary water intakes, and access routes.
- Deliverable: Initial hazard overlay + DEM + orthomosaic (or lower-res substitute) within 12–24 hours.
- Acceptance criteria: Hazard overlay georeferenced (EPSG clearly specified), DEM resolution documented, and initial list of 3 priority borehole locations recommended.

Remote-sensing product specs (minimum):
- Orthomosaic: geotiff, <10 cm/pixel if drone, <50 cm if satellite; include metadata (acquisition time, sensor, sun angle).
- DEM: 1 m or better if drone; include vertical datum reference.
- Change-detection: raster diff + annotated PDF map with lat/long grid.
- Output coordinate reference: WGS84 / EPSG:4326 and local CRS if available.

Action 3. Mobilise emergency engineering cell (Owner: Oscar)
- Objective: Set up an operational cell for engineering coordination and outreach to two emergency geotechnical consultancies.
- Tasks:
  1. Establish an ops Slack/MS Teams channel with named owners and 24/7 contact for the triage period.
  2. Contact two emergency geotech consultancies with immediate capacity (preferably those with experience on tailings / mining waste dams). Provide a concise brief (attach initial imagery and hazard overlay when available).
  3. Prepare a short list of temporary reversible stabilisation options (toe buttress, controlled diversion, staged dewatering, temporary sediment barriers) with conceptual sketches and materials.
  4. Draft initial concept-level Health & Safety Protocol for any temporary work (PPE list, exclusion zones, observer roles, emergency extraction routes).
- Deliverable: Supplier/equipment list + concept-level temporary measures + engineering-cell roster in 24 hours.
- Acceptance criteria: Two consultancies confirmed on-call, ops channel active, and concept sketches ready for review.

Action 4. Community liaison & consent (Owner: Marcos)
- Objective: Immediately identify community and Indigenous contacts, flag culturally sensitive areas and establish an engagement protocol that respects local consent processes.
- Tasks:
  1. Compile a contact list by priority (Indigenous leadership, village chairs, health centre leads, school principal, local NGOs).
  2. Prepare an initial engagement protocol: who speaks, when, message frames, no-commitment listening sessions, safe spaces for complaint.
  3. Identify any cultural monitors required and list cultural sites (avoid detailed public disclosure of sensitive locations).
  4. Prepare a community vulnerability map (households by distance to drainage, vulnerable cohorts: children, elderly, mobility-impaired).
- Deliverable: Contact list + engagement protocol + vulnerability map within 24–48 hours.
- Acceptance criteria: Community leads contacted (where safe) and agreement on an initial liaison approach documented.

Action 5. Emergency procurement shortlist (Owner: Sara)
- Objective: Identify local/regional suppliers and rental houses able to provide machinery and materials at short notice; assess lead times and FX/import risk.
- Tasks:
  1. Build an initial shortlist of equipment: excavator (20–30 t), 14–16 t dozer or tracked loader, 8–12 t dump trucks (or articulated equivalents), drill rig for 2–4" borings, pumps (submersible, 6" and 3"), geotextiles (AOS spec), sandbags, silt curtains, cofferbing materials, and temporary sheet piling if available.
  2. For each supplier record: contact, location, estimated mobilization time to site (hrs/days), equipment hours/day rates, deposit/FX requirements, and any customs lead time if imported.
  3. Identify standby pricing and any conditional hold/option pricing to enable quick commit once geotech confirms.
- Deliverable: initial supplier shortlist and lead-time/Fx notes in 24–48 hours.
- Acceptance criteria: At least two options per critical equipment type with mobilization ETA.

Action 6. Data & contacts request to IronCliff (Owner: Lisa)
- Objective: Secure any existing site data to accelerate interpretation.
- Ask (inline template provided in Section 7): site coordinates (lat/long), bore logs, piezometer and inclinometer data (timeseries), surveys, photos, plant/ops contacts, emergency contacts, permits, and permission for drone flights. Request delivery within 6 hours where possible.
- Deliverable: Data request email draft and logged follow-up calls.
- Acceptance criteria: Data received or firm ETA provided within the 6-hour window.

Safety and immediate field rules (generic, to be adapted on-site)
- No boots-on-the-ground (no on-site entry) without:
  - Community consent where required;
  - Engineer or delegated safety officer present;
  - Site-specific risk assessment and permit-to-work signed;
  - Communications check-in/out and evacuation plan.
- All field staff MUST have: high-visibility clothing, hard hat, safety boots, lifejackets (if working near open water), two-way radio, GPS, first-aid kit, and a buddy system.
- Any observed serious cracking, seepage, bulging or new springs must be reported immediately in the ops channel with GPS coordinates and photos.

---

3) 48-hour deliverables (0–2 days) — outputs and acceptance criteria

This section lists the essential deliverables to be produced within 48 hours, with the expected content, owner, and minimum acceptance criteria.

Deliverable 1: Hazard overlay, DEM, and recommended priority boring locations (Owner: Alex) — 24 hours
- Content:
  - Orthomosaic (geotiff) and high-resolution DEM with metadata.
  - Annotated hazard map (PDF + GIS shapefile) showing zones of observed erosion, active seepage, likely failure planes inferred from imagery, downstream receptor buffer zones (200 m / 500 m / 1,000 m).
  - Recommended 3–6 priority boring locations with rationale, access notes and GPS coordinates.
- Acceptance criteria: Map georeferenced and loaded on shared drive; recommended borings include safety/access notes and estimated depth.

Deliverable 2: Supplier/equipment shortlist with lead times and FX notes (Owners: Sara + Oscar) — 24–48 hours
- Content:
  - Supplier table (see template below in Section 8) including contact, mobilization ETA, equipment specs, daily/hourly rates, and FX/import comments.
  - Standby options and conditional hold prices if available.
- Acceptance criteria: At least two suppliers for each critical equipment type, with contact verification call logs.

Deliverable 3: Preliminary stabilisation concept sketches and on-site safety protocol (Owners: Oscar + emergency geotech consultancies) — 48 hours
- Content:
  - Concept sketches (PDF) of temporary measures: toe buttress plan and section, controlled diversion channel alignment, staged dewatering scheme with pump locations, temporary sediment barrier cross-section.
  - On-site safety protocol: exclusion zones, traffic management, plant safety distances, and emergency extraction plan.
- Acceptance criteria: Concepts are reviewed by a geotechnical consultant and include material lists and estimated quantities.

Deliverable 4: Community contact list and vulnerability map (Owner: Marcos) — 48 hours
- Content:
  - Contact table: names, roles, phone/WhatsApp, languages, cultural considerations.
  - Vulnerability map overlay in GIS format and PDF with household clusters and low-literacy outreach plan.
- Acceptance criteria: Key community leaders contacted and aware that engagement will follow legal review.

Deliverable 5: Draft regulator/lender acknowledgement + legal contact (Owner: Lisa) — 6 hours draft; legal to review within 12 hours
- Content:
  - Draft acknowledgement email (internal only) and an elevated submission template for the 3-week plan (format options requested).
- Acceptance criteria: Legal review requested and expected turnaround time documented.

---

4) 3-week engineer-verified plan (deliverable to regulator/lenders) — detailed schedule, tasks, decision gates

Goal: Final engineer-signed plan delivered to regulator and lenders within ~3 weeks with supporting data, monitoring plan, supplier confirmations and community safety procedures.

High-level structure of the 3-week plan deliverable:
- Executive summary & immediate measures
- Site description and hazard summary
- Data collected and QA/QC logs
- Geotechnical interpretation (stability analysis, seepage assessment)
- Temporary stabilisation measures and mobilisation plan
- Monitoring and instrumentation plan (piezometer/inclinometer schedule, thresholds, alarm levels)
- Community liaison & protection plan (evacuation mapping, communication protocol)
- Schedule and cost estimates for works
- Permitting and Indigenous consent record
- Appendices: raw data, lab results, drawings, supplier confirmations, chain-of-custody, safety plans
- Engineer declarations and signature pages

Detailed timeline and tasks (Day-by-day):

Week 1 — Rapid data collection and initial stabilisation (Days 0–7)
- Day 0 (immediate):
  - Complete internal acknowledgement draft; ops channel live; geotech consultancies engaged on-call.
  - Remote-sensing tasking initiated. Drone tasking where safe and permitted.
  - Procurement shortlist started.
- Day 1–2:
  - Field reconnaissance (safety permitting) to establish safe vantage points; installation of temporary observation posts; baseline photography log.
  - Priority borings mobilized — aim for minimum 3 borings targeting zones identified from hazard overlay (trial pits if possible for near-surface characterization).
  - Install temporary piezometers and inclinometers (where feasible) at critical locations. If full inclinometer installation not possible, install standpipe piezometers and subsurface vibrating wire piezometers for baseline pore pressure.
- Day 3–4:
  - Begin sample shipment to nominated labs; commence preliminary laboratory testing (natural moisture content, particle size distribution, Atterberg limits, specific gravity).
  - If necessary, implement immediate temporary measures: toe buttress (imported or locally placed rockfill), temporary berms, diversion channels to redirect surface flow away from compromised sections, and temporary pump stations to reduce ponding. Record all as-built field notes with photos and GPS.
- Day 5–7:
  - Rapid laboratory interpretation and preliminary slope stability runs based on field data; refine temporary measures into concept-level drawings.
  - Obtain preliminary cost and mobilization confirmations from suppliers for short-listed options.

Decision Gate 1 (end Week 1): Enough confidence to proceed to detailed analysis and staged measures?
- Criteria:
  - At least 3 borings completed with representative samples and initial lab results available.
  - Piezometer readings show trends consistent with drainage or rising phreatic surface (documented).
  - Temporary measures in place and reducing immediate hazard indicators.
  - Community safety measures implemented (notifications to community contacts logged).

Week 2 — Detailed analysis & staged solutions (Days 8–14)
- Day 8–10:
  - Full suite of lab tests returned (unconsolidated undrained triaxial where required, consolidation tests, grain-size, Atterberg limits, unit weight).
  - Detailed slope stability modelling performed (limit equilibrium analyses and rapid finite-element seepage modelling as required).
  - Water-table and seepage assessments completed with recommended drainage and toe stabilization measures modelled.
- Day 11–13:
  - Engineering works sequenced and method statements drafted for each temporary measure and for the interim stabilized configuration.
  - Identify permits required for in-channel works, temporary diversions, drilling, and heavy-equipment movement. Initiate permit workflow and Indigenous consent check.
  - Confirm supplier availability with mobilization dates and conditional pricing. Arrange hold/standby agreements if required.
- Day 14:
  - Finalize draft of engineer-stamped interim stabilization plan (concept-level), monitoring thresholds, and emergency response actions (triggered by instrument readings or observed signs).
  - Prepare regulator/lender submission package outline and submit internal draft for legal and Marcos review.

Decision Gate 2 (end Week 2): Proceed to final verification and regulator submission?
- Criteria:
  - Stability modelling demonstrates acceptable factor of safety with proposed temporary measures or demonstrates specific residual risk with proposed mitigations.
  - Permits identified and earliest submission timelines documented.
  - Community engagement steps agreed (with Marcos and legal input).
  - Supplier confirmations for mobilization in Week 3.

Week 3 — Final engineer verification and submission (Days 15–21)
- Day 15–17:
  - Implement any remaining temporary measures where safe, and validate their effectiveness via monitoring (piezometer readings, visual inspection).
  - Final checks on mobilization logistics, traffic management and community notifications for on-site activities.
  - Final engineer site visit if regulator/lender require on-site verification (coordinate visitor safety and community agreement).
- Day 18–20:
  - Compile final report: all data, analyses, monitoring plan, drawings (plan and sections), supplier confirmations, mobilization schedule, and cost estimates. Obtain engineer signatures and declarations.
  - Review final submission internally — legal, Marcos, and Wild Advice leads sign off.
- Day 21:
  - Deliver final engineer-verified stabilization and community protection plan to regulator/lenders in agreed format.
  - Prepare for follow-up Q&A and potential site visit scheduling.

Decision Gate 3 (end Week 3): Submission complete and follow-up plan agreed.
- Criteria:
  - Engineer-signed plan submitted.
  - Regulator/lenders confirm receipt and list any clarifications.
  - Mobilization of full engineered works proceeds following regulator acceptance and any permit constraints.

Monitoring and alarm thresholds (recommended initial values — to be refined by geotech consultant)
- Piezometer thresholds:
  - Green: stable, within baseline ±5% of initial reading.
  - Amber: rising trend >10% of baseline within 24 hours — increase monitoring frequency and prepare mobilization.
  - Red: sudden rise >20% or sustained rising trend over 48 hours — consider evacuation and emergency stabilization actions.
- Visual indicators:
  - New cracks >10 mm width, bulging, sudden seepage, or slope acceleration — immediate "Red" report to operations channel and potential local evacuation.

Deliverables for regulator/lender submission
- Cover letter and executive summary
- Engineer-signed report and drawings (PDF + original CAD/GIS files)
- All raw data and lab certificates (chain-of-custody documented)
- Monitoring plan and instrument logs
- Supplier confirmations and mobilization plan
- Community engagement summary and consent documentation
- Permitting status and next steps

---

5) Communications and legal considerations

Principles:
- Do not send any external communications without legal counsel confirmation regarding Indigenous land-claims and permitting risks, and without Marcos' confirmation on community engagement approach.
- All public-facing or regulator-facing messaging must be factual, conservative, clear about uncertainty, and avoid speculative language about liability or root cause until adequate data exists.
- Maintain a single source of truth — Wild Advice will host the official package; only designated spokespersons (Lisa and/or an agreed company representative) may speak to regulators/lenders. Marcos leads local community communications.

Stakeholder mapping (initial)
- Regulators (primary): National Environmental Agency (NEA) — primary contact: [insert contact when available]; Regional Mines Inspectorate — backup.
- Lenders: Senior Credit Officer (Bank/Institution) — contact to be provided by lender.
- IronCliff operations: Site Manager — name, phone, email (request from IronCliff).
- Community/Indigenous: Chairpersons, Elders, Health Centre Leader, School Principal.
- Media: local outlets (to be managed only by corporate comms and legal).
- Local emergency services: Fire, EMS, Police.

Approval workflow (internal)
1. Draft message prepared by Lisa -> posted to ops channel.
2. Legal reviews for legal risk and Indigenous land-claim implications (timeline: 12 hours).
3. Marcos reviews for cultural and community engagement implications (timeline: 12 hours).
4. Wild Advice leads (Lisa and Oscar) sign off; external send only after step 3 complete.

Suggested immediate regulator/lender draft language (internal draft for approval)
- Keep to 3–5 brief paragraphs: acknowledgement of incident, brief description of actions Wild Advice is undertaking, expected timeline for engineer-verified plan, and request for any available data and preferred submission format. Example (internal draft):
  - "We acknowledge the incident at IronCliff tailings containment and confirm that Wild Advice has initiated emergency triage and coordination with geotechnical specialists. Our immediate priorities are to secure people and downstream receptors, rapidly collect and interpret data (remote sensing, borings, monitoring), and deliver an engineer-verified stabilization and community protection plan within approximately three weeks. We request any existing geotechnical and monitoring data you hold, and we would appreciate guidance on preferred submission format for engineered plans. Please note legal and Indigenous-consultation steps are being followed and external communications will be coordinated."

Rapid Q&A and escalation matrix
- All urgent field incidents: immediate alert to ops channel -> on-call engineer and Marcos -> decide on evacuation if necessary.
- Media enquiry: refer to legal / corporate communications — no staff to comment to media.
- Regulator request for immediate data not in our possession: escalate to Lisa to request from IronCliff and copy regulator to avoid time delays (retain legal pre-clear).

Community messaging (principles and templates)
- Principles: short, clear, non-technical; focus on safety, what is known, what is being done, and what people should do (phone numbers, meeting points).
- Template (to be used only after legal + Marcos approval):
  - "We are aware of conditions at the IronCliff site and are working with engineers and your community leaders to ensure your safety. At this time, please avoid the river/stream and low-lying areas downstream of the quarry. If you notice unusual discoloured water, new springs, or cracks near the ground, please report immediately to [local contact]. We will hold a community meeting at [time/place] to explain next steps and answer questions."

Recordkeeping and confidentiality
- All communications, data transfers, and decisions must be logged in the project folder with time stamps and owner IDs. Sensitive cultural or legal material must be marked CONFIDENTIAL and access restricted.

---

6) Roles & primary owners (expanded summary)

Primary leads (with placeholders for contact fields — to be filled by team):

- Lisa Carter (Wild Advice) — Lead: report drafting, regulator & lender comms, legal loop-in, coordination across owners. Contact: lisa.carter@[email-placeholder] | +[phone placeholder]
  - Deputies: [Name], [Contact]
  - Responsibilities: final submission coordination, regulator liaison, legal engagement, acceptance criteria sign-off.

- Oscar [Surname] — Lead: stabilisation engineering & logistics (temporary measures, supplier coordination, mobilization plans). Contact: oscar.[email-placeholder] | +[phone placeholder]
  - Deputies: On-call geotech consultancy lead
  - Responsibilities: technical lead, concept sketches, supplier technical spec, safety protocols.

- Alex [Surname] — Lead: remote sensing, DEM, change detection, and geospatial hazard overlays; recommend boring locations. Contact: alex.[email-placeholder] | +[phone placeholder]
  - Deputies: GIS analyst, drone operator
  - Responsibilities: hazard mapping, imagery processing, change detection reporting.

- Sara [Surname] — Lead: procurement & supplier fast-track, local rental houses, FX and lead-time assessment. Contact: sara.[email-placeholder] | +[phone placeholder]
  - Deputies: procurement assistant
  - Responsibilities: supplier outreach, hold pricing, logistics.

- Marcos [Surname] — Lead: community liaison & Indigenous consent; engagement protocol and contacts. Contact: marcos.[email-placeholder] | +[phone placeholder]
  - Deputies: community liaison officer(s)
  - Responsibilities: community meeting facilitation, consent recording, cultural monitoring.

Ops & support roles:
- Legal counsel (internal/external) — name & contact to be provided by Lisa; must review communications and advise on land-claim risk.
- Health & Safety Officer — responsible for field safety permits and PPE compliance.
- Logistics lead — responsible for access route repair contractor if required.
- Data manager — maintain project data repository and access control.

Escalation path
- Immediate life-safety incident -> Marcos & Oscar -> Lisa -> legal & regulator as required.
- Procurement blockage or FX delays -> Sara -> Lisa -> client finance for emergency FX approvals.
- Community complaint or cultural issue -> Marcos & legal -> pause field works if advised.

---

7) Immediate data & access requirements (ask IronCliff now) — detailed

To accelerate analysis, we require the following files/data from IronCliff with format guidance and expected priority:

Priority A (urgent — request now; desired within 6 hours if possible)
- Exact site coordinates (lat/long for key features): crest points, toe points, intake/overflow point, nearest community centroids. Format: CSV with decimal degrees (WGS84/EPSG:4326).
- Any existing geotechnical logs: borehole logs, depths, sample IDs, field descriptions, lab test references. Format: PDF + original log CSV or spreadsheet if available.
- Monitoring records: piezometer and inclinometer timeseries (raw and plotted), including instrument IDs, depths, installation dates, and last calibration. Format: CSV or Excel timeseries.
- Recent photos and time-stamped videos from site staff (with GPS metadata preferred).
- Emergency contacts: site manager, plant operations lead, security, local road & bridge contact, and local emergency services.

Priority B (important — within 24–48 hours)
- Historical surveys and cross-sections for the tailings basin (CAD, DXF/DWG preferred, or PDF with scale).
- Design reports for the tailings basin, including original geotechnical design criteria, construction records, and as-built documentation.
- Environmental monitoring data (surface water quality samples if available; turbidity logs).
- Drone/licensing contacts for imagery if IronCliff prefers to task imagery directly through its provider.

Priority C (as available)
- Anything on previous incidents, settlement monitoring data, maintenance records (clearing of drains), or past remedial works.

Data formatting and metadata checklist
- CRS: clearly state coordinate reference system. If local CRS used, provide transformation parameters.
- Time zone and format for timeseries.
- Sample chain-of-custody documentation for any soil/water samples.
- Lab test certificates and method references (e.g., ASTM/ISO numbers).

Sample data request email (internal draft — DO NOT SEND externally until approved):
- Subject: Data request — IronCliff tailings containment (URGENT)
- Body: concise list of items requested (as above), specification of formats, preferred delivery method (secure file share link), and request for data delivery timeline (now / within 6 hours / within 24 hours).
- Attach: brief justification for urgent data (support triage and engineer assessment).

Access / permissions for drone flights
- Confirm whether site has no-fly restrictions; if so provide contact for applying for exemptions.
- Provide any required local permits or points of contact for airspace coordination.

---

8) Procurement guidance & FX mitigation — supplier table template and equipment specs

Procurement principles:
- Prioritise local/regional suppliers to minimize customs/FX risk and mobilization delays.
- Prepare conditional hold/standby options for long-lead items (drill rigs, specialized pumps).
- Quote in local currency where possible; if FX exposure unavoidable, identify client-led FX mechanisms for rapid payments.
- Ensure suppliers have appropriate insurance and safety documentation.

Sample supplier / equipment template (fill per supplier)
| Equipment/Item | Supplier | Contact (name/phone/email) | Location | Mobilization ETA (days/hours) | Daily Rate (local currency) | Deposit / FX notes | Comments / Capacity |
|---|---|---:|---|---:|---:|---:|---|
| Excavator 20–30t | Supplier A | John Doe / +xx / j.doe@ | 120 km | 2 days | 1,200 / day | Local currency; requires 30% deposit | Can mobilize tracked or wheeled |
| Drill rig (geotech, truck-mounted) | Supplier B | ... | 2–3 days | 6,000 / day | Import if local rigs unavailable | Standby rate possible |
| Submersible pump 6" | Supplier C | ... | 12 hours | 800 / day | Local stock available | Two units available immediately |

Note: Populate with local supplier names and contact details once Sara completes outreach.

Equipment and material specifications (minimum)
- Toe buttress rockfill: crushed rock or imported quarry rock, nominal D50 = 100–300 mm, well-graded angular material, placed in layers with compaction as directed by engineer.
- Geotextile: non-woven separation fabric, tensile strength per engineer spec, filtration properties to be confirmed.
- Sandbags: polypropylene (UV-stabilized), filled on-site using local sand where appropriate.
- Silt curtain: floating polypropylene with weighted skirt, rated for expected flow velocities.
- Pumps: diesel-driven submersible pumps with flow capacity to lower ponding within acceptable timeframe (engineer to confirm required flow rate; preliminary assumption: 100–300 L/s cumulative).

Ballpark mobilization lead-times (assumptions, to be validated)
- Local small excavator: 12–48 hours if within 200 km.
- Large excavator (>30 t) or heavyweight bulldozer: 3–7 days (depending on availability).
- Drill rig: 24–72 hours if local; >7 days if requiring relocation from capital city or import.
- Geotextiles and specialist materials: 24–72 hours if local/regional stock; 7–21 days if importing.

Procurement checklist
- Verify supplier insurance and safety certifications.
- Confirm equipment operator competency and licensing.
- Confirm fuel logistics and site refuelling plan.
- Document supplier standby pricing and cancellation terms.

---

9) Risks, assumptions & mitigations (expanded risk register)

The table below lists principal risks, likelihood and impact ratings (High/Medium/Low), mitigations, and owners.

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---:|---|---:|---:|---|---|
| R1 | Missing or poor-quality geotechnical data delays model confidence | High | High | Prioritise borings Day 0–3; use conservative assumptions; document uncertainty in report | Oscar / Alex |
| R2 | Community consent / Indigenous claims prevent access or works | Medium | High | Legal review before external comms; Marcos to lead culturally appropriate engagement; plan non-intrusive monitoring options | Marcos / Legal |
| R3 | FX/import delays for heavy equipment / materials | High | Medium | Prioritise local suppliers; obtain standby pricing; client finance to pre-authorise emergency FX clearance | Sara |
| R4 | Worsening weather causing further destabilisation | Medium | High | Integrate weather windows; pre-install temporary containment (sandbags, berms); plan for accelerated mobilization | Oscar / Logistics |
| R5 | Unexpected subsurface pockets leading to rapid failure during field works | Low | High | Conservative excavation/support plan; engineer on-site during critical works; emergency extraction zones | Oscar / H&S |
| R6 | Regulatory rejection of plan due to insufficient engineer-signed data | Medium | High | Ensure geotech consultants sign final plan; provide full data appendix and QA/QC | Lisa / Oscar |
| R7 | Media or social unrest leading to misinformation | Medium | Medium | Centralize communications; Marcos to hold community meetings; legal to prepare holding statements | Lisa / Marcos |
| R8 | Supply chain fraud or unreliable suppliers | Low | Medium | Use pre-vetted suppliers; require references; small initial payments; hold payment on delivery | Sara |

Assumptions (explicit)
- Assume availability of at least one local drill rig within 72 hours.
- Assume access to satellite imagery with appropriate revisit within 24 hours.
- Assume IronCliff will provide basic site coordinates and at least partial geotechnical records within 24 hours.
- Assume community leaders will engage in good faith but that cultural consent may require delays to certain activities.

Contingency triggers and actions
- If borings cannot be completed in Week 1 due to access or consent, prepare contingency: use additional remote sensing, trial pits, and increased conservative temporary measures (larger toe buttress).
- If weather event forecast shows >100 mm rainfall within 48 hours, escalate to emergency pumping and temporary diversion immediately.

---

10) Proposed immediate next steps (for the team, next 6 hours)

Action checklist to be completed within the next 6 hours; owners to note progress and post status updates to the ops channel.

1. Lisa: Draft regulator/lender acknowledgement (6 hours). Post to ops channel and tag legal and Marcos. Attach initial hazard overlay if available.
2. Alex: Begin SAR/optical tasking and contact drone operators; start initial change detection processing (12–24 hours deliverable).
3. Oscar: Establish engineering-cell roster and outreach to two emergency geotech consultancies (deliver contacts list & initial options within 24 hours).
4. Sara: Start sourcing local rental houses and prepare initial procurement shortlist (24–48 hours).
5. Marcos: Share community/Indigenous contact list and recommended initial engagement protocol (24–48 hours).
6. IronCliff (requested now): provide site coords, any geotech/monitoring files, ops contacts, and drone/satellite access details.
7. Legal: confirm availability for review and expected turnaround for initial communications (Lisa to loop legal).
8. Ops: create secure shared project folder with restricted access and upload initial draft outputs.

Sign-off template (internal)
- Name / Role / Time / Status (Complete / In progress / Blocked) / Notes
- All lead owners to post completion status in ops channel and confirm no external messages posted without required sign-offs.

---

Appendix A — Suggested deliverables & owners (milestone table / simplified Gantt)

Milestone list with target dates (Day counts relative to Day 0):

| Milestone | Owner(s) | Target (Day) | Dependencies |
|---|---|---:|---|
| Draft regulator/lender acknowledgement (internal) | Lisa | 0–0.25 | Legal review pending |
| Hazard overlay + DEM + recommended borings | Alex | 0.5–1 | Satellite/drone acquisitions |
| Emergency engineering-cell roster & ops channel | Lisa / Oscar | 0.5–1 | N/A |
| Supplier/equipment shortlist & procurement notes | Sara | 1–2 | Supplier outreach |
| Initial borings & baseline monitoring installed | Oscar / Geotech | 1–3 | Site access & consent |
| Preliminary stabilisation concept sketches | Oscar + geotech | 2 | Borings / DEM results |
| Community contact list & vulnerability map | Marcos | 1–2 | Local outreach |
| Initial lab test results & geotech interpretation | Geotech labs | 4–7 | Sample delivery |
| Interim temporary measures implemented | Oscar / Suppliers | 0–7 | Procurement & safety permits |
| Detailed slope stability & seepage analysis | Geotech | 7–14 | Lab results |
| Draft engineer-verified plan for review | Oscar + Lisa | 14–18 | Analyses & permit checks |
| Final engineer-signed plan submission | Lisa + Geotech signatory | 21 | Legal & Marcos sign-off |

Gantt notes:
- Critical path: borings (Day 1–3) -> lab tests (Day 4–7) -> engineering analysis (Day 8–14) -> final review and sign off (Day 15–21).
- Overlap tasks where feasible (e.g., procurement and community engagement) to compress schedule.

---

Appendix B — Technical annex (detailed guidance and templates)

B1. Temporary stabilisation options — descriptions, pros/cons, material estimates

1. Toe buttress
- Description: Add mass at the downstream toe to increase resisting forces and reduce driving forces; typically rockfill or compacted fill keyed into existing embankment.
- Materials: Rockfill, geotextile separation, filter layer as required.
- Pros: Immediate effect on stability; relatively simple to place.
- Cons: Requires heavy machinery and safe access; may be disruptive to downstream environment if not contained.
- Ballpark material estimate: For a 50 m long compromised segment requiring a 5 m wide 2 m thick buttress: Volume ~500 m3 rock (subject to engineer confirmation).

2. Controlled diversion (surface water management)
- Description: Temporary diversion channel or flap to route surface runoff away from compromised sections and reduce inflow to the basin.
- Materials: Sandbags, temporary culverts, geotextile-lined channels, silt fences.
- Pros: Low-cost, rapid; reduces surface inflow.
- Cons: May be overtopped during extreme rainfall; requires good design to prevent erosion at diversion outlet.

3. Staged dewatering (pumping)
- Description: Use of submersible pumps to lower ponded water and reduce pore pressures; must be staged to avoid rapid drawdown that could destabilize slopes.
- Materials: Pumps, fuel, pipes, manifolds, containment for discharged water (sediment traps).
- Pros: Rapid reduction of ponded water.
- Cons: Requires careful control; dewatering may lead to differential settlement or uncontrolled seepage unless accompanied by drainage works.

4. Temporary sediment & filter barriers
- Description: Deploy silt curtains and coffer dams to reduce downstream turbidity and limit suspended solids transport.
- Pros: Protects downstream water users; simple to deploy in low-flow conditions.
- Cons: Limited efficacy in high flows; needs anchoring and maintenance.

B2. Geotechnical field sampling and lab tests — protocol summary

Minimum sample types and lab tests required for interim stability analysis:
- Disturbed samples: particle size distribution (sieve + hydrometer), natural moisture content, Atterberg limits, specific gravity.
- Undisturbed samples (where possible): unit weight, consolidation test (oedometer), undrained triaxial test (UU or CU depending on sample quality).
- Index properties reported with method references (ASTM/ISO numbers).
- Chain-of-custody form to accompany each sample (template below).

Chain-of-custody sample form (brief)
- Sample ID | Date/Time | Collector | Location (lat/long) | Depth | Sample type | Preservation | Lab sent to | Signature

B3. Monitoring plan — instrumentation and frequency

Instrumentation recommended (initial)
- Standpipe piezometers (3–6): daily readings for first 7 days, then twice daily if unstable.
- Vibrating wire piezometers (2–3): continuous loggers where available — set alarm thresholds.
- Inclinometer (1–2) in critical slope if feasible: weekly readings unless accelerated movement detected.
- Surface benchmarks/GPS points: daily for first 7 days (monitor settlement and major movement).

Data reporting cadence
- Daily monitoring report (24–hr): key instrument readings, visual observations, summary of actions.
- Immediate incident report: any reading exceeding red thresholds or sudden visual changes.

B4. Sample field safety and permit forms (templates)

Permit-to-work (quick checklist)
- Work description (boring, dewatering, earthworks).
- Date/time, personnel names, emergency contact, equipment planned.
- Safety controls (PPE, exclusion zones, traffic management).
- Community consent confirmation (where on Indigenous land).
- Signatures: Site manager, H&S officer, community monitor (where applicable).

B5. Drone flight plan template (for operator)
- Flight ID, operator name and license, UAV make/model, planned takeoff/landing coordinates, survey area polygon, GSD target, altitudes, mission duration, AVLOS/BVLOS status, emergency contingency, permission attachments.

B6. Sample regulator submission checklist
- Cover letter
- Executive summary
- Full engineer report (PDF)
- Supporting data folder (raw and processed)
- Instrumentation logs and QC certificates
- Supplier confirmations and method statements
- Community engagement summary and consent evidence
- Signature and stamp pages

B7. Sample internal incident reporting format (for ops channel)
- Time / Reporter / Location (lat/long) / Short description / Photos attached? Yes/No / Immediate action taken / Recommended next step / Owner

B8. Cost estimate template (high-level, provisional)
- Temporary stabilisation materials (rockfill, geotextile, sandbags): $XX,XXX
- Equipment rental (excavator, pumps, trucks) for initial 7 days: $XX,XXX
- Drilling and lab tests: $XX,XXX
- Specialist consultancy fees (emergency geotech): $XX,XXX
- Logistics and fuel: $X,XXX
- Contingency (20%): $XX,XXX
(Note: Provide client with a detailed cost estimate once suppliers confirm pricing. All numbers to be updated to local currency and approved by client finance.)

B9. Community engagement suggested contents for first meeting
- Purpose of meeting and introduction of team
- Plain-language summary of current situation and what we are doing
- Safety measures and immediate actions requested of community
- Opportunity for questions and to record local knowledge or concerns
- Reporting channels and times for next meetings
- Request for permission areas and cultural site identification (handled sensitively)

B10. Map symbology legend for hazard overlay (recommended)
- Red shading: High immediate failure risk
- Orange shading: Moderate risk of erosion/transport
- Yellow shading: Low risk / monitor
- Blue line: Main drainage channel
- Crosses: recommended boring locations
- House icons: community receptor centroids
- Star: community water intake

---

End of expanded plan.

Next immediate action: Lisa will post the regulator/lender draft into the ops channel and tag legal and Marcos for approval before any external messaging. All owners to update status on the ops channel within the next 2 hours with any critical blockers (access, equipment, legal availability).

Prepared by: Lisa Carter (Wild Advice Partners)  
For internal distribution only — DO NOT SEND externally until legal and Marcos have approved.