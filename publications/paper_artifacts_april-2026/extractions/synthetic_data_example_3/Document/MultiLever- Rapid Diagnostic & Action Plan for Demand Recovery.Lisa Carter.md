```
SELECT sku_id, week_start_date,
       SUM(units_sold) as units,
       SUM(net_sales) / NULLIF(SUM(units_sold), 0) as avg_price
FROM weekly_sales
GROUP BY sku_id, week_start_date
HAVING SUM(units_sold) > 0
ORDER BY sku_id, week_start_date;
```

---

# Owners & timeline (proposed)

Team and responsibilities
- Lisa Carter (Wild Advice) — Project lead
  - Deliverables: Day-5 diagnostic, Scenario deck, consolidated recommendations, client presentation.
  - Responsibilities: analysis oversight, hypothesis synthesis, stakeholder communications.
- Alex (Data Engineer / Analyst)
  - Deliverables: ingestion pipelines, elasticity estimates, measurement pipeline for pilots.
  - Responsibilities: data extraction, cleaning, feature engineering, producing model-ready data.
- Oscar (R&D & Prototyping)
  - Deliverables: feasibility reports for pack-sizing changes, prototype packaging, supplier liaison.
  - Responsibilities: quick-turn prototypes, estimating MOQ, lead times, packaging cost impacts.
- Sara (Client Sponsor)
  - Responsibilities: prioritize client resources, unblock cross-functional delays, escalate to executive as needed.
- Marcos (Client Liaison / Domain SME)
  - Responsibilities: scheduling, subject-matter insights, validation of assumptions with market context.

RACI snapshot (example)
- Diagnostic memo: Responsible = Lisa; Accountable = Lisa; Consulted = Alex, Oscar; Informed = Sara, Marcos.
- Scenario modelling: Responsible = Lisa & Alex; Accountable = Lisa; Consulted = economist (if contracted); Informed = Sara.
- Pilots execution: Responsible = Oscar & Alex & Lisa; Accountable = client commercial lead & Sara; Consulted = supply chain, store ops; Informed = Marcos.

Timeline (detailed Gantt overview)
- Day 0–2:
  - Action: send formal data request, lock 60-minute kickoff; confirm roles and access.
- Day 1–5:
  - Rapid diagnostic: 1-page memo + data appendix delivered by EOD Day 5.
- Week 2 (days 6–12):
  - Begin modelling & scenario building; start pilot procurement/creative if approved.
- Week 3 (days 13–19):
  - Deliver scenario deck; finalize pilot designs and pre-register analysis plans.
- Week 2–6 (days 8–40):
  - Pilot execution window (2–6 weeks depending on pilot).
- Week 4:
  - Consolidated recommendations & implementation roadmap (including scale-up costing and resourcing).
- Week 6:
  - Pilot results, final recommendations and scaled rollout plan.

Communication cadence
- Daily stand-ups internally (15 minutes) for first 2 weeks, then 3x weekly.
- Weekly steering call with client sponsor and key stakeholders to report progress and blockers.
- Rapid Slack/email updates for critical issues (data access, execution delays).

Milestone acceptance criteria (examples)
- Diagnostic accepted: client signs off that the one-page memo captures the top drivers and pilot concepts.
- Scenario deck accepted: models validated on holdout SKUs and client accepts assumptions list.
- Pilot go/no-go: pilots meet pre-registered criteria for sample size and operational readiness.

---

# Deliverables (expanded)

1) Day 5 — Diagnostic memo (1 page) + data appendix
   - One-page memo structured: Headline → Evidence summary → Top drivers (with estimated impacts) → Recommended pilots (3) → Next steps.
   - Data appendix: sample files, data quality issues, missing fields and request list, sample SQL queries used for checks.

2) Week 3 — Scenario deck with quantified outcomes
   - 10–20 slides per category with:
     - Problem framing
     - Modelling approach & assumptions
     - Elasticity estimates and visualizations
     - Scenario matrix with quantitative outcomes (volume, margin, ROI)
     - Recommended pilot candidates with measurement and operational notes.

3) Week 4 — Prioritized recommendations and implementation plan
   - Prioritized list of interventions with RACI, resource estimate, cost to implement, and timeline.
   - Go/no-go criteria and a staged scale-up plan (pilot → regional → national).
   - Change management considerations (e.g., trade fund negotiations, pricing policy, IT changes for checkout offers).

4) Week 6 — Pilot results & scaled rollout recommendations
   - Pilot analysis: causal estimate, confidence intervals, margin implications, and incremental ROI.
   - Scaled rollout plan: sequence, capacity constraints, procurement plan, inventory/infrastructure implications.
   - Implementation checklist and monitoring dashboard templates (KPIs and ownership).

Deliverable formats
- PDF/PowerPoint for decks and memos.
- CSV/Parquet for datasets and appendices.
- Jupyter notebooks or RMarkdown for reproducible analysis (if desired).
- Dashboard prototype (PowerBI/Tableau) for ongoing monitoring (if requested).

---

# Risks & mitigation strategies

High-level risk matrix (probability × impact), proposed mitigations

1) Delayed or poor-quality SKU data
- Probability: High | Impact: High
- Mitigation:
  - Request 4–6 week sample extracts immediately to unblock diagnostic work.
  - Use aggregated category-level proxies and external benchmark data if SKU-level missing.
  - Implement quick data-quality scoring and escalate to sponsor within 24 hours of discovery.

2) Limited R&D capacity to create new pack-sizes or SKUs
- Probability: Medium | Impact: Medium-High
- Mitigation:
  - Prioritize low-effort, high-impact prototypes (temporary packaging or relabel existing SKUs).
  - Consider co-packing or limited-run pilot SKUs with third-party co-packers.
  - Hire short-term contractor resources for packaging/label design.

3) Client alignment issues (unclear contacts / slow approvals)
- Probability: Medium | Impact: Medium
- Mitigation:
  - Escalate to sponsor (Sara) and request a single point of contact per function.
  - Provide a decision calendar and pre-approved templates to accelerate approvals.

4) Regulatory or compliance constraints (especially financing offers)
- Probability: Low-Medium | Impact: High for appliance financing pilot
- Mitigation:
  - Early legal/compliance review; pre-clear offers with finance/legal team.
  - Consider alternative offers (gift cards, rebates) if financing unworkable.

5) Operational execution failures (inventory stockouts during pilot)
- Probability: Medium | Impact: High
- Mitigation:
  - Coordinate forecasting with supply chain; secure buffer inventory for pilot SKUs.
  - Daily inventory checks and quick restock protocols.

6) Unintended cannibalization across SKUs
- Probability: Medium | Impact: Medium
- Mitigation:
  - Measure cross-price elasticities and include cannibalization in pilot analysis.
  - Pre-specify acceptable cannibalization thresholds; include substitution adjustments in ROI calculations.

Risk register example (prioritized)
| Risk | Likelihood | Impact | Mitigation action | Owner |
|---|---:|---:|---|---|
| SKU data missing critical fields | High | High | Request sample extracts; use aggregated proxies; escalate to sponsor | Alex / Lisa |
| Supplier cannot support new pack size | Medium | Medium-High | Use alternative packaging or third-party co-packer; adjust pilot to promotion instead | Oscar |
| Financing offer blocked by compliance | Low | High | Pre-clear with legal; prepare alternative offers | Lisa / Legal |

---

# Privacy & compliance

Minimum standards
- All handling of consumer-level data must comply with applicable data protection laws (GDPR, local privacy regulations) and client internal policies.
- Use hashed/pseudonymized customer identifiers when consumer-level data is required for analysis. Keep mapping keys separate and under client control.
- Limit access to raw files to named project members; use role-based access control for storage.
- Use secure transfer protocols (SFTP, signed AWS S3 presigned URLs) and encryption-at-rest.

Retention & disposal
- Agree on retention period for project extracts; typical policy: retain for the duration of the engagement + 90 days unless otherwise specified.
- After the retention period, purge raw files and document deletion steps with receipts.

Data sharing & third parties
- Any engagement of contractors (economist, external co-packer) requires a data processing agreement (DPA) and NDA.
- Provide only the minimum necessary data to third parties; prefer aggregated data where possible.

Audit & documentation
- Maintain an access log for data extracts and transformations.
- Provide documentation of pseudonymization steps, encryption keys handling and data deletion.

---

# Next steps (first 72 hours)

1) Finalize and send the data request
   - Action: Lisa/Alex to send the prioritized file list (as detailed above) to data owners; include target formats (parquet/CSV), sample extract request (4–6 weeks) and contact details.
   - Target: within 24 hours (Day 0).
2) Lock a 60-minute kickoff within 48–72 hours
   - Proposed slot: tomorrow 19:00 CET (please confirm with Marcos and client sponsor).
   - Kickoff agenda (60 minutes):
     - 0–5 min: introductions and objectives
     - 5–20 min: client context and constraints (finance, R&D, fulfillment)
     - 20–35 min: data availability & handover plan
     - 35–45 min: pilot feasibility constraints and quick wins
     - 45–60 min: next steps, milestone confirmations and Q&A
3) Begin data ingestion and request sample extracts
   - Alex to set up ingestion pipelines for sample files; run initial data quality checks within 24–48 hours of receipt.
4) Deliver Day-5 diagnostic and propose 2–3 pilot concepts for rapid approval
   - Lisa to draft diagnostic; Oscar to validate pilot feasibility; Alex to include data appendix.

Checklist for first 72 hours (owner + due date)
- [ ] Send formal data request with sample extract instructions (Owner: Alex; Due: Day 0 + 8 hours)
- [ ] Schedule kickoff meeting and confirm attendees (Owner: Marcos; Due: Day 0 + 12 hours)
- [ ] Confirm legal/compliance guardrails for data sharing (Owner: Sara; Due: Day 0 + 24 hours)
- [ ] Ingest first sample files and run data health checks (Owner: Alex; Due: Day 1)
- [ ] Draft Day-5 diagnostic outline (Owner: Lisa; Due: Day 2)

Sample kickoff email (template)
Subject: MultiLever Demand Recovery — Kickoff & Data Request (Tomorrow 19:00 CET)
Body:
- Brief intro, objectives, requested attendees, attach dataset schema and sample request, ask for confirmation of slot, include link to SFTP bucket or upload instructions.

---

# Appendix A — Pilot measurement plan (expanded)

Primary and secondary metrics (definitions)
- Primary:
  - Incremental volume lift vs control: (Units_treatment − Units_control) adjusted for pre-trend (difference-in-differences).
  - Incremental gross margin: (Gross margin_treatment − Gross margin_control) after accounting for promo/trade spend and product BOM.
  - ROI: Incremental gross margin divided by incremental promo or operational cost (including trade funds).
- Secondary:
  - Retention: percent of customers who repurchase within N weeks.
  - Repeat purchase rate: repeat purchase counts per customer over a defined horizon.
  - Price elasticity estimates: local elasticity computed from pilot outcomes to update model priors.
  - Channel-specific lift: change in channel share (in-store vs online).

Statistical analysis plan (SAP) — key points
- Predefine the analysis window: pre-period (4 weeks baseline), treatment window (pilot duration), post-period (4 weeks if applicable).
- Primary estimator: difference-in-differences with covariate adjustment for store/geography fixed effects and time trends.
- Model specification example:
  - Outcome_it = α + β*TreatmentGroup_i*Post_t + γ_i + δ_t + ε_it
    - β is the causal treatment effect estimate.
- Adjust standard errors for clustering at the unit of randomization (store or geo).
- Multiple testing correction: if running multiple pilots or many SKUs, use Benjamini-Hochberg FDR or Bonferroni as appropriate for hypothesis control.

Power calculations (illustrative)
- Food pilot example:
  - Baseline per-store weekly units = 100, SD = 20
  - Expected uplift = 8 units/week → Cohen's d = 8/20 = 0.4
  - For α=0.05, power=0.8 → required n ≈ 50 stores total; but with weekly repeated measures and fixed effects, effective n reduces; estimate 20 stores per arm likely sufficient (see sample calc).
- Provide exact power calcs when actual baseline means and variances are received.

Data engineering & measurement notes
- Ensure promo flags are normalized across data tables and aligned to the promo calendar.
- Synchronize timestamps across pos/online/inventory systems; convert to a standard timezone and week definition.
- Build a “pilot table” that maps store_id/geo_id to treatment/control and contains planned start/end dates to feed dashboards and analyses.
- Track inventory separately to ensure observed changes are demand-driven and not supply-constrained.

Sample analysis SQL (difference-in-difference)
```
WITH sales_week AS (
  SELECT store_id, week_start, SUM(units_sold) AS units
  FROM weekly_sales
  WHERE sku_id IN ('SKU_A','SKU_B') AND week_start BETWEEN '2025-06-01' AND '2025-08-31'
  GROUP BY store_id, week_start
),
treatment_map AS (
  SELECT store_id, treatment_flag
  FROM pilot_store_map
)
SELECT s.store_id, s.week_start,
       s.units,
       t.treatment_flag,
       CASE WHEN s.week_start >= '2025-07-01' THEN 1 ELSE 0 END AS post,
       AVG(s.units) OVER (PARTITION BY s.store_id ORDER BY s.week_start ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS rolling_mean_units
FROM sales_week s
LEFT JOIN treatment_map t ON s.store_id = t.store_id;
```