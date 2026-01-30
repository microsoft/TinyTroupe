# Executive Summary

MultiLever is facing an acute demand shock driven by elevated inflation (~10% year-over-year) and a ~20% contraction in demand in the most recent quarter. The impact is concentrated in food, home appliances, and toys per the client brief. This document is an expanded, client-ready action plan and playbook that:

A. Defines a rapid analytics diagnostic to identify where declines are concentrated and to quantify price and promotional sensitivities (deliverable within 3–5 business days after receiving data).  
B. Recommends immediate, low-risk commercial interventions and carefully instrumented pilots (0–14 days) designed to stabilize demand and protect margin.  
C. Outlines medium-term R&D/product and go-to-market moves (4–12 weeks) to preserve value while addressing consumer price sensitivity.

We recommend two parallel tracks:
- A rapid analytics diagnostic (3–5 business days after data arrival) to surface high-impact SKUs, elasticities, customer cohort sensitivities, and channel dynamics; and
- An R&D/product ideation and pilot design track (1–3 weeks) to convert analytics findings into testable offers and operationally-feasible pilots.

Immediate ask of MultiLever: provide the data listed in Appendix A within 72 hours so we can deliver the rapid diagnostic within 3–5 business days of receipt.

This brief expands the original plan with concrete methods, sample outputs, measurement plans, pilot designs, success thresholds, risk mitigation, and operational checklists to make this immediately actionable.

---

# Situation & Objectives (detailed)

Context and observed signals
- Macroeconomic: Inflation running ~10% Y/Y. Consumer price sensitivity is elevated, especially for discretionary and frequently-purchased categories.
- Demand shock: Company-wide volume down ~20% last quarter. Declines are concentrated in three categories: food, home appliances, and toys.
- Operational signal: Anecdotal reports indicate shifts to lower pack sizes, increased couponing, and higher online/discount channel share.

Primary objectives (0–14 days)
- Arrest or materially slow demand deterioration with focused, ROI-positive interventions.
- Identify 3–5 high-impact, executable pilots that can be launched quickly and measured rigorously.

Secondary objectives (4–12 weeks)
- Launch R&D/product changes (smaller pack sizes, value sub-brands, modular features for appliances) and implement pricing/promo cadence changes that preserve brand value while reducing price friction for target segments.

Constraints and assumptions
- Data availability: Rapid diagnostic contingent on receiving adequate SKU-level sales, pricing, promos, and CRM data within the 72-hour window.
- Supply: Some SKUs may have limited inventory; recommended pilots favor agility and small region rollouts where supply constraints exist.
- Regulatory: Any product formulation or packaging changes in food require legal/regulatory checks which must be prioritized in pilot feasibility.

---

# Rapid Diagnostic Plan (Analytics) — deliverable in 3–5 business days after data arrival

Goal
- Identify top drivers of demand decline and prioritize SKUs/categories for intervention based on expected volume lift, impact on gross margin, operational feasibility, and strategic fit.

High-level deliverable
- A concise diagnostic report (10–15 pages) and an appendix of data tables that includes:
  - Ranked list of top 10 SKUs or SKU clusters where interventions are likely to yield the best balance of volume lift and margin retention.
  - Elasticity estimates (own-price and short-run promotional uplift) with confidence intervals.
  - Channel shift summary and customer segment sensitivity matrix.
  - Three recommended pilot concepts with detailed measurement plans and feasibility notes.

Priority analyses and methodology (in priority order)

1) Descriptive time series (SKU x week over last 52 weeks)
Purpose: identify where declines are concentrated across SKUs, channels, and regions; detect seasonality and recent breakpoints.
Method:
- Aggregate weekly volume and revenue by SKU, channel, region.
- Compute YoY and QoQ percent change, 4-week rolling averages, and contribution to company-level volume decline.
- Detect breakpoints (Bai-Perron / structural break detection) and flag weeks with outlier events (holidays, supply disruptions).
Deliverables:
- Heatmap of percent change by SKU category x region.
- Table: top 25 SKUs by absolute volume decline and percent decline.

2) Price & promo elasticity estimation
Purpose: quantify short-run responsiveness of demand to price and promotions to prioritize discounts and promotional treatments.
Method:
- Panel regressions at SKU x week level:
  - Base model (fixed effects): log(units) = α_sku + γ_week + β_price * log(price) + Σδ_promo_types + ε
  - Where α_sku controls for time-invariant SKU attributes, γ_week for common shocks and seasonality.
- For sparse SKUs or when cross-SKU pooling is sensible, employ hierarchical (mixed-effects) models or Bayesian shrinkage to borrow strength across SKUs in the same category.
- Control variables: marketing spend (channel-level), stockouts (inventory ratio), holidays, competitor promotions (if available), and macro price index (to give real vs nominal context).
Deliverables:
- Elast. table: SKU, estimated own-price elasticity (point estimate + 95% CI), promo uplift estimate (percent incremental sales under promo), model diagnostics (R^2, RMSE).
- Guidance: flag elasticities by category (e.g., food fundamentals vs discretionary toys).

3) Promotion ROI and cannibalization analysis
Purpose: identify promotions that are truly incremental vs those that merely shift demand across SKUs or time.
Method:
- Use difference-in-differences where possible: compare treated stores/SKUs with control stores/SKUs in the same time window.
- Calculate incremental quantity = observed treated sales – expected control sales (scaled for baseline differences).
- Estimate cannibalization matrix: incremental sales on promoted SKU vs decline in sales for related SKUs (adjacencies) during same period.
- Compute promo ROI = incremental profit / promo cost (including trade funds and marketing).
Deliverables:
- Promo ROI table with net margin impact, cannibalization rate (% of promo lift that came from within-brand cannibalization).
- Recommendations for promo types with positive ROI.

4) Channel shift analysis
Purpose: quantify movement of demand across retail, e-commerce, and distributors and how this affects observed declines.
Method:
- Compute channel share changes by category and SKU over last 12 months.
- Test whether channel-specific declines explain national patterns using mediation analysis: does channel shift account for X% of volume decline?
- Detect price differentials across channels and compute elasticity by channel.
Deliverables:
- Channel shift dashboard: percent change in channel volume, top SKUs with channel-specific declines.
- Recommendation: channel-specific tactics (e-commerce bundles, in-store demos, distributor incentives).

5) Margin impact simulation
Purpose: translate volume-change scenarios and pilot promo mechanics into gross margin and contribution margin implications.
Method:
- For each SKU, compute baseline gross margin (price – COGS), incremental margin under promo scenarios (e.g., 5%, 10% discount), and net margin after trade funds and variable promo costs.
- Scenario simulations: 3 scenarios per SKU (conservative, expected, aggressive) with volume uplift assumptions derived from estimated elasticities.
Deliverables:
- Simulation table: SKU, baseline margin, scenario volume, net margin, breakeven promo depth (discount that maintains margin neutrality given estimated uplift).
- Recommendation: list of SKUs where targeted discount preserves net margin or where mix-shifting will be necessary.

6) Customer segment analysis
Purpose: identify cohorts (CRM or loyalty segments) most sensitive to price/promotions and prioritize targeted offers.
Method:
- Use RFM segmentation and cohort analysis to identify highest-value cohorts at retention risk. Build uplift models to estimate incremental response to targeted discounts.
- For loyalty cohorts, estimate LTV impact from short-term promotions, and forecast retention lift from successful pilots.
Deliverables:
- Cohort sensitivity matrix: cohorts x elasticity or uplift.
- Target list: top 3 loyalty cohorts for targeted pilots.

7) Competitor/market scan (if data available)
Purpose: contextualize own-chain moves vs competitors and identify opportunities to differentiate.
Method:
- Ingest competitor price and promo history (if provided).
- Highlight competitor-led price cuts or pack-size moves.
Deliverables:
- Competitor heatmap and recommended defensive/offensive responses.

Data quality & processing steps (quick checklist for analytics team)
- Standardize SKUs, map to master catalogue.
- Impute missing prices using median transaction price per SKU-week or nearest-neighbor interpolation for short gaps.
- Flag and exclude weeks with stockouts for elasticity estimation (or include inventory as a control).
- Inflation-adjust pricing to real terms where comparing across longer time windows.

Primary outputs
- Ranked list (Top 10 SKUs or SKU clusters) prioritized by expected volume lift × probability of margin retention × operational feasibility score.
- Elasticity estimates summary table with confidence bounds.
- Three pilot designs for high-priority opportunities with measurement plans.

Sample "Top SKUs" output (illustrative)

| Rank | SKU ID | Category | 12-mo % Volume Change | Estimated Elasticity | Promo Uplift | Baseline Margin | Feasibility Notes |
|------|--------|----------|-----------------------:|---------------------:|-------------:|----------------:|-------------------|
| 1    | F-2134 | SnackBars | -28% | -1.35 (±0.25) | +40% (promo) | 28% | High inventory, e-comm strength |
| 2    | T-4021 | Toy-Car | -33% | -1.78 (±0.40) | +70% | 35% | Seasonal; packaging cost low |
| 3    | A-1102 | Mid-Range Kettle | -22% | -0.95 (±0.15) | +25% | 32% | Higher COGS, consider bundling |
| ...  | ...    | ...      | ... | ... | ... | ... | ... |

(These are sample synthetic numbers to illustrate the report format.)

---

# Immediate Recommendations (0–14 days) — prioritized, test-first approach

Principles
- Target the interventions where demand is most elastic or where small price/package changes can unlock substantial volume without catastrophic margin loss.
- Preference for targeted, measurable pilots over broad, deep discounts.
- Preserve brand by framing offers as limited-time value packs, bundles, or loyalty-exclusive offers rather than permanent list-price cuts.

A. Targeted Promotional & Pricing Moves (0–14 days)

1. Precision discounts
- Tactic: Apply limited-duration, targeted discounts to high-elasticity SKUs and/or to high-value customer cohorts (identified from CRM).
- Implementation notes:
  - Use loyalty channel for first wave — loyalty customers typically have higher conversion and measurable response.
  - Limit discount depth to the breakeven level suggested by margin simulations.
- KPI: incremental revenue, incremental margin, promotional ROI.
- Success threshold (example): net incremental margin ≥ 3% AND ROI of promo spend ≥ 1.5x within pilot window.

2. Bundles & value packs
- Tactic: Create temporary bundles (e.g., snack multipacks, toy accessory+toy, small appliances + cleaning accessory) positioned as "value combos".
- Implementation notes:
  - Price bundles to be perceived as saving (e.g., 10–20% versus buying items separately) while preserving or improving margin through mix-shift.
  - Use existing SKUs to avoid manufacturing changes; use co-packaging where possible.
- KPI: units per basket, basket AOV, bundle attach rate.

3. Pack-size downshift
- Tactic: Offer smaller pack sizes at lower absolute prices but with messaging focused on affordability (price-per-unit perception is key).
- Implementation notes:
  - Operational check: packaging capacity, SKU proliferation risk, and SKU labeling/regulatory needs (food).
  - Short-run options: re-sleeving, multi-packs sold as “mini” or “single-serve” without full package redesign.
- KPI: conversion rate among price-sensitive cohorts, price-per-unit trends, margin per transaction.

4. Trade promotions with retailers
- Tactic: Negotiate co-funded discounts, temporary feature placements, or slotting for prioritized SKUs.
- Implementation notes:
  - Ask retailers for metrics: predicted uplift, shelf display timing, and share-of-voice.
  - Use performance-based co-funding rather than deep flat funding where possible.
- KPI: sell-through, net margin after trade funds, incremental sell-through vs baseline.

5. Channel-specific offers
- Tactic: Tailor offers to where demand has moved — e.g., e-commerce exclusive bundles, click-and-collect value SKUs for retail, distributor volume incentives.
- Implementation notes:
  - Ensure price parity considerations and MAP policy compliance.
  - Use channel-specific promo codes / couponing to track response.
- KPI: channel conversion, channel share change, ROI by channel.

B. Margin-preserving tactics

- Focus on product mix: Promote higher-margin SKUs and profitable adjacencies rather than deep discounting low-margin staples.
- Use shallow, broad discounts (e.g., 5–10% across a wider audience) if that yields higher aggregate incremental margin than deep discounts on small segments.
- For perishable categories, use time-limited “smart markdowns” based on inventory aging to avoid waste while protecting margin.

C. Rapid Pilots — design & measurement

Each pilot must include: hypothesis, treatment, target population, duration, sample size/power (where relevant), KPIs, and predefined success thresholds. Below are three concrete pilot examples:

Pilot 1 — Elastic SKUs Promo Pilot (Targeted loyalty cohort)
- Hypothesis: Targeted 10% discount to loyalty cohort on the top 10 elastic SKUs will increase units sold enough to produce a positive net incremental margin after promo costs.
- Treatment: 10 SKUs, 10% discount, targeted to top 5% of loyalty base via email/push, 14-day campaign.
- Target population: Top 5% loyalty customers (by LTV) across two test regions; control group = matched loyalty customers in two matched control regions with no discount.
- Duration: 14 days + 7 days post-campaign observation.
- Data/KPIs: incremental units, incremental revenue, net incremental margin, ROI of promo spend, retention lift for the cohort at 30 days.
- Success thresholds: net incremental margin ≥ 3% and ROI ≥ 1.5x; incremental units ≥ 15% vs baseline.

Pilot 2 — Value Pack Pilot (Food)
- Hypothesis: Offering smaller/multi-packs at a 7–12% lower absolute price will increase purchase frequency and conversion among price-sensitive shoppers without eroding per-transaction margin.
- Treatment: Repackage 3 high-velocity food SKUs into smaller packs and a “3-for-2” bundle; price to yield perceived savings ~10%.
- Target population: Two metropolitan retail regions + e-commerce site (A/B test by region/channel).
- Duration: 21 days.
- Data/KPIs: units sold, price-per-unit behavior, basket AOV, gross margin per transaction.
- Success thresholds: lift in units sold ≥ 12% and basket AOV change ≥ 0% (no decrease), net incremental margin neutral or positive.

Pilot 3 — Appliance Bundling Pilot
- Hypothesis: Bundling a mid-tier appliance with a low-cost accessory increases conversion at a lower effective entry price while preserving attach rate and margin.
- Treatment: Bundle kettle (A-1102) with a standard descaler sample; bundle priced 8% lower than kettle list price but with higher perceived value.
- Target population: National e-commerce test with randomized on-site visitor assignment (50/50) and a matched in-store regional test with co-funding from retailer.
- Duration: 14 days.
- Data/KPIs: conversion rate, attach rate for accessory, incremental basket AOV, net incremental margin.
- Success thresholds: conversion uplift ≥ 20% and net incremental margin ≥ 2%.

Measurement & stats guidance (quick)
- Use randomized assignment where possible (e-commerce A/B testing). Where randomization is infeasible (store-level), use matched controls (propensity score matching) and difference-in-differences.
- Predefine primary KPI for success and statistical significance (e.g., 95% CI) and minimum detectable effect (MDE). Example power calc: For baseline conversion 2% to detect +0.4pp uplift (~20% relative) at 80% power and alpha=0.05, need ~40,000 visitors per arm. We'll compute precise sample sizes per SKU based on baseline volumes.
- Pre-register analysis plan: endpoints, window length, and handling of outliers.

---

# Medium-Term Product & R&D Moves (4–12 weeks)

Objective
- Develop sustainable offering variants and structural cost/packaging changes that meet price-sensitive demand while protecting brand and margin.

Strategic product options

1) Value-line products (rapid-develop)
- Concept: Lower-cost variants of existing products via simplified feature set or alternate materials; position as a separate sub-brand to avoid diluting core brand equity.
- Example: For home appliances, a “MultiLever Basics” line with fewer frills (e.g., single heat setting, lighter materials) sold at ~15–25% lower price.
- Owners: Oscar (R&D ideation) and Supply Chain (sourcing).
- Timeline: 6–10 weeks to concept -> pilot SKU; 12–20 weeks to scaled production depending on lead times.

2) Pack-size & format innovation
- Concept: Create smaller pack sizes and modular packaging to reduce absolute transaction price and align with cash-constrained consumers.
- Design considerations:
  - Material cost per unit often increases for smaller pack size — target re-engineering to keep per-unit cost increase ≤ 15% OR achieve compensating increase in purchase frequency.
  - Maintain regulatory labeling and shelf compatibility.
- Owners: Oscar + Procurement.

3) Faster, lower-cost manufacturing options
- Concept: Review BOMs for alternative suppliers, simplify features to lower cost, standardize components across product families to realize economies of scale.
- Actions:
  - Run BOM cost reduction workshops with Supply Chain and Engineering.
  - Solicit quotes from alternate suppliers with shorter lead times and smaller MOQs.
- Owners: Supply Chain.

4) Promotional calendar redesign
- Concept: Shift from infrequent deep promotions to shallower, more frequent, targeted offers to maintain demand while protecting margin. Use loyalty-driven cadence and localized events.
- Implementation:
  - Build monthly promo calendar with targeted campaigns, rotating focused SKUs, and retailer-aligned events.
- Owners: Commercial/Marketing + Finance.

Feasibility and productization checklist
- Regulatory: food formulations and labeled pack changes must be reviewed by legal; include regulatory lead in pilot feasibility step.
- Packaging: evaluate capacity for new SKU packing; if constrained, use retail/fulfilment partners for co-pack.
- Supply & MOQ: model required MOQ vs expected pilot volumes; if MOQ mismatch, start with smaller, higher-priced pilot pack to validate before scale.

R&D concept pipeline (example three concepts per prioritized product line)
- For each prioritized product family (e.g., SnackBars, Toy-Cars, Mid-Range Kettle), Oscar will produce:
  1. Quick-win concept: repackaging or bundling using existing components.
  2. Mid-term concept: simplified feature variant (distinct SKU/line).
  3. Longer-term cost engineering concept: BOM rework and supplier change.

Deliverable expected within 4–12 weeks: product concept deck (3 concepts per line), technical feasibility memo, cost/price simulations, and pilot kit.

---

# Implementation Roadmap & Owners (high-level, detailed timeline)

Immediate (0–72 hours)
- Send data request and secure transfer template to client (owner: Lisa Carter). Target: full or partial data access within 72 hours.
- Confirm internal owners: Pricing Lead, Supply Chain Lead, Finance/Pricing Analyst, Project Manager; solicit nominations from Wild Advice Partners and client.
- Prepare kickoff agenda and secure NDA/secure transfer channel details.

Once data received (Day 0 = data receipt)
- Day 0–3/5: Rapid diagnostic (owner: Lisa + analytics support). Deliverable: prioritized SKU list, elasticity estimates, top 3 pilot recommendations and a slide deck summary.
- Day 4–7: Pilot design & feasibility (owner: assigned PM + Finance/Pricing + Supply Chain) — finalize pilot mechanics, vendor/retailer approvals, packaging feasibility, and KPI targets; draft internal SOP for pilot operations.
- Day 7–14: Pilot execution (staged rollouts per channel) and ongoing monitoring (owner: PM + Analytics). Daily or every-other-day dashboards for pilot metrics.
- Day 14–28: Analyze pilot outcomes, iterate and scale successful pilots. Parallel R&D concept testing (owner: Oscar + R&D + Supply Chain).
- Week 4–12: Medium-term productization activities, supplier selection, initial production runs for value lines; align with promotional calendar redesign.

Detailed Gantt (illustrative)

| Time Window | Key Activity | Owner |
|-------------|--------------|-------|
| 0–3 days | Data request sent, secure channels set up | Lisa |
| 0–5 days | Rapid diagnostic (analytics & prioritized list) | Lisa + Analytics |
| 4–7 days | Pilot design & feasibility (detailed mechanics) | PM + Finance + Supply Chain |
| 7–14 days | Pilot launch & monitoring (staged) | PM + Channel Leads |
| 14–28 days | Pilot analysis & iterate, scale winners | PM + Analytics |
| 28–84 days | R&D/product concept test & production readiness | Oscar + Supply Chain + Marcos |
| 6–12 weeks | Launch value-line/productized pilots & promo calendar | Commercial + Marketing |

Suggested owners (please confirm names)
- Client-facing lead & analytics: Lisa Carter (Wild Advice Partners) — responsible for data request, diagnostic, and report.
  - Role summary: lead analyst and client liaison, owns analytics model selection, visualization, and diagnostic delivery.
- R&D/Product concepts: Oscar (lead)
  - Role summary: ideation owner, will produce 3 concepts per prioritized product line and coordinate feasibility.
- Technical/R&D feasibility input: Marcos
  - Role summary: engineering/technical feasibility, BOM analysis, supplier liaison.
- Pricing Lead: [TBD — client nomination requested]
- Supply-Chain Lead: [TBD — client nomination requested]
- Finance/Pricing analyst: [TBD — internal nomination requested]
- Project Manager: [TBD — internal nomination requested]
Please confirm or replace proposed owners immediately to lock schedule.

---

# KPIs & Success Criteria (detailed)

Diagnostic deliverables
- Data completeness: key required data in Appendix A received within 72 hours (binary pass/fail metric).
- Diagnostic delivery: prioritized SKU list and elasticity estimates delivered within 3–5 business days after data receipt.

Pilot KPIs (examples and measurement windows)
- Incremental units: absolute additional units sold attributable to pilot during pilot window.
- Incremental revenue: additional revenue net of discounts.
- Net incremental margin: incremental profit after promo cost, trade funds, and any added logistics/packaging cost.
- ROI of promotional spend: (net incremental margin) / (incremental promotional cost + trade funds).
- Conversion uplift (e-commerce): percent relative uplift in conversion.
- Attach rate: accessory attach rate in bundling pilots.
- Retention lift (CRM): lift in repeat purchases or reduced churn within targeted cohort over 30/60 days.

Suggested pass/fail thresholds (examples; tailor per SKU/pilot):
- Net incremental margin >= 2–5% (category-dependent) and ROI >= 1.2–1.5x.
- Conversion uplift >= 10–20% for bundling pilots.
- Units uplift >= 10–25% for targeted discounts on high-elasticity SKUs.
- Retention lift >= 3% for loyalty-targeted pilots measured at 30 days.

Statistical thresholds
- Use 95% confidence interval for primary KPI; power calculations pre-specified to ensure pilot durations/sample sizes are sufficient to detect MDE.

Financial metrics & dashboard
- Include a pilot P&L with:
  - Baseline revenue & margin.
  - Promo costs (discounts + trade funds + packaging).
  - Incremental revenue & margin.
  - Net incremental margin and payback period (if applicable).

---

# Risks & Mitigations (expanded)

1) Brand dilution risk (over-discounting)
- Risk: Frequent or deep discounts may reposition brand as low-cost, eroding long-term pricing power.
- Mitigation:
  - Use limited-time offers, loyalty-only deals, value packs with different SKU codes, or sub-brand positioning for value-line SKUs.
  - Carefully cap discount depth and duration; track brand health metrics via NPS or brand lift surveys during pilot.

2) Regulatory constraints (food)
- Risk: Reformulation or pack-size labeling changes may trigger regulatory review or require re-certification.
- Mitigation:
  - Include legal/regulatory team in pilot feasibility step.
  - Use interim tactics (repackaging or multi-packs) that do not change formulation while regulatory reviews run in parallel.

3) Supply constraints
- Risk: Insufficient inventory or long lead times hamper scale-up or lead to stockouts.
- Mitigation:
  - Validate inventory & lead times before committing to wide rollouts.
  - Prefer small regional pilots and staged rollouts.
  - Use distributor/third-party co-packers for packaging flexibility.

4) Margin erosion
- Risk: Promotions increase volume but reduce net margin below acceptable thresholds.
- Mitigation:
  - Run margin simulations prior to launch and set stop-loss thresholds during pilots (e.g., auto-stop if net incremental margin < target).
  - Prioritize mix-promotion that focuses on high-margin adjacencies.

5) Cannibalization within portfolio
- Risk: Promotions on one SKU cannibalize higher-margin SKUs.
- Mitigation:
  - Include cannibalization analysis in promo ROI calculations.
  - Design promos to encourage incrementality (e.g., new-customer acquisition, cross-sell bundles).

6) Data & measurement issues
- Risk: Missing or low-quality data leads to biased elasticity estimates or unmeasurable pilots.
- Mitigation:
  - Rapid data QA and imputation strategy; if crucial data missing, use synthetic benchmarking and conservative assumptions.
  - Pre-define primary and secondary KPIs and have fall-back metrics.

Risk matrix (example — simplified)

| Risk | Likelihood | Impact | Mitigation |
|------|------------:|-------:|-----------|
| Brand dilution | Medium | High | Use sub-brand/value packs, limit-time offers |
| Regulatory delay (food) | Low-Med | High | Legal/Reg review in feasibility; use non-formulation tactics first |
| Supply constraints | Medium | Medium | Regional pilots, co-packers, inventory checks |
| Margin erosion | High | High | Margin simulation and stop-loss thresholds |
| Data gaps | Medium | Medium | QA script & fallback assumptions |

---

# Appendix A — Detailed Data Request (expanded; please provide within 72 hours if possible)

Preferred format: CSV or Parquet files with UTF-8 encoding. If sensitive, use secure SFTP or encrypted cloud share with appropriate ACLs. Include data dictionary and codebook for any proprietary fields.

Primary required datasets (minimum):

1) SKU-level weekly sales (last 12 months; ideally 24 months if available)
- Required fields (example CSV schema):
  - week_start_date (YYYY-MM-DD)
  - sku_id (string)
  - sku_name (string)
  - units_sold (integer)
  - gross_revenue (decimal)
  - channel (enum: retail, e-commerce, distributor)
  - region (string — standardized)
  - store_id / fulfillment_center_id (optional)
  - promotion_id (nullable)
  - inventory_on_hand (end-of-week integer)
  - returns_units (optional)
- Provide sample rows (example):
  - 2025-01-05, F-2134, "Snack Bar - Cocoa", 1245, 18675.00, e-commerce, NYC-region, FC-03, PROMO-001, 320, 12

2) SKU-level weekly price & promotion flags
- Required fields:
  - week_start_date
  - sku_id
  - list_price (decimal)
  - avg_transaction_price (decimal)
  - promo_flag (boolean)
  - promo_type (enum: percent_discount, bogo, bundle, coupon, shelf_price, other)
  - promo_depth (numeric: percent or absolute discount)
  - promo_detail (text: short description)
- Notes: If transaction-level data is available, include sample transaction detail.

3) Promotion history (granular)
- Required fields:
  - promo_id
  - sku_id (or SKU list)
  - promo_start_date
  - promo_end_date
  - promo_type
  - promo_depth
  - trade_funds_amount (decimal)
  - retailer (if co-funded)
  - channel
  - expected uplift (if known)
  - creative/campaign_id (if applicable)

4) Marketing spend (channel-level weekly)
- Required fields:
  - week_start_date
  - channel (digital, TV, radio, OOH, in-store)
  - spend_amount (decimal)
  - campaign_id (text)
  - geo_scope (national/region/store)
- Notes: Campaign IDs should crosswalk to SKU targeting if possible.

5) Inventory & lead times
- Required fields:
  - sku_id
  - date
  - inventory_on_hand (units)
  - replenishment_lead_time_days (typical)
  - safety_stock (units)
  - supplier_lead_time (days)
  - outstanding_po_qty (units)

6) SKU-level cost / BOM
- Required fields:
  - sku_id
  - unit_material_cost (decimal)
  - unit_labor_cost (decimal)
  - overhead_allocated_per_unit (decimal)
  - packaging_cost_per_unit (decimal)
  - unit_cogs_total (decimal)
  - current_sku_weight/volume (for shipping cost modeling)
  - any variable costs per channel (e.g., pick-pack fees)

7) Customer / CRM segments (anonymized)
- Required fields:
  - customer_id (anonymized)
  - customer_segment (RFM buckets or loyalty tier)
  - recency_days
  - frequency_12mo
  - monetary_12mo
  - avg_basket_value
  - channel_preference (if known)
- Optional: transaction-level purchase history (anonymized) with datetime, sku_id, units, transaction_price.

8) Channel mapping & definitions
- Required: canonical definitions for channels and mapping table from store_id/fulfillment_id to channel and region.

9) Competitor price/promotions (if available)
- Fields:
  - store/competitor_name
  - sku_proxy (if direct SKU mapping not possible)
  - date
  - price
  - promo_flag
  - promo_detail

10) R&D capability note
- Fields:
  - current_projects (text)
  - typical lead_times_by_change_type (small packaging change, reformulation, new SKU)
  - regulatory_constraints (country-level)
  - packaging capacity constraints (units/day)
  - contact for R&D lead and supply chain.

11) Contact list
- Fields:
  - role (R&D lead, head commercial, head pricing, supply chain)
  - name
  - email
  - phone
  - preferred secure transfer method (SFTP/cloud link)

Optional but helpful
- SKU-level returns and reasons.
- Customer-level purchase histories (full transactions, anonymized).
- Historic A/B tests or uplift experiments and their results.
- Retailer merchandising calendars and planned promotions.

Data delivery checklist (to confirm)
- [ ] Data dictionary included
- [ ] Date ranges specified and complete
- [ ] SKU master table included (sku_id, description, category, subcategory)
- [ ] Currency and units standardized across files
- [ ] Secure transfer mechanism confirmed

Sample data request email (template)
- See section “Communications & Kickoff” below for a ready-to-send template.

---

# Measurement & Analytics Implementation Details

Modeling approaches (technical but practical)
- Elasticity modeling:
  - Panel OLS with SKU and week fixed effects for high-volume SKUs.
  - Bayesian hierarchical shrinkage models for low-volume SKUs within categories.
  - Log-log specification for elasticity estimation (elasticities are interpretable as percent change).
- Promo incremental analysis:
  - Difference-in-differences for store-level promotions.
  - Synthetic control for national-level promotional events when a natural control group is not present.
  - Propensity-score matched controls for non-random assignments.
- Cannibalization mapping:
  - Build SKU adjacency matrix based on co-purchase frequencies and category taxonomy.
  - Run multivariate regression to assess cross-price effects among related SKUs.
- Uplift modeling for personalization:
  - Train uplift (two-model or direct uplift) models on historical campaign data if available to identify best target cohorts for future promos.

Data treatment & adjustments
- Price deflation/inflation adjustment: deflate nominal prices using CPI or internal price index when comparing across periods.
- Stockout handling: Exclude or control for stockouts and low inventory weeks to avoid underestimating price sensitivity.
- Holiday/seasonal controls: Include week indicators for major holidays; use Fourier terms or seasonal dummies if needed.
- Outlier treatment: Winsorize extreme values or apply robust regression.

Dashboarding and reporting
- Daily pilot monitoring dashboard (Key metrics updated daily):
  - Units sold (treatment vs control)
  - Revenue (gross & net)
  - Promo cost & trade funding burn
  - Net incremental margin
  - Conversion rate (e-comm)
  - Inventory on hand for pilot SKUs
- Weekly analytic report:
  - KPI trends, short statistical test results, and any immediate operational red flags.

Analytic deliverables (package)
- One-page executive summary slide deck.
- 6–10 page diagnostic report with methodologies and prioritized SKU list.
- Analytics appendix including full elasticity tables and model code snippets (R or Python scripts).
- Data QA report documenting assumptions, missing data, and any imputation steps.

---

# Communications & Kickoff

Kickoff meeting (proposed agenda, 60–75 minutes)
- Introductions and confirmation of owners (10 mins)
- Overview of situation, objectives, and scope (10 mins)
- Data requirements and transfer process (10 mins)
- Diagnostic approach and timeline (10 mins)
- Pilot concepts overview and measurement approach (10 mins)
- Risks, constraints, and next steps (10 mins)
- Q&A and action item assignment (10–15 mins)

Suggested kickoff time window: within 48 hours of this brief confirmation. Please confirm availability of client R&D lead, head of commercial/marketing, head of pricing, and supply-chain lead.

Sample data request email (ready-to-send; edit as needed)
Subject: Urgent — Data Request for Rapid Diagnostic (please provide within 72 hours)

Body:
Hello [Client Contact],

As discussed, to run the rapid diagnostic and deliver prioritized SKU insights within 3–5 business days, we need the following data files (CSV/Parquet) and schema details attached in Appendix A. Please upload to [secure SFTP / cloud link] or provide instructions for secure transfer.

Priority — please provide:
- SKU-level weekly sales and prices (last 12 months)
- Promo history and marketing spend (last 12 months)
- SKU master table and BOM (costs)
- CRM segment file (anonymized)
- Inventory & lead times
- R&D capability note and contact list

If any file cannot be provided within 72 hours, please send a partial extract or a sample for the top-selling SKUs. Once we receive data, we will commence the diagnostic immediately.

Best,
Lisa Carter
Wild Advice Partners

---

# Financial & Resource Estimates (indicative)

Estimated effort (Wild Advice Partners)
- Rapid diagnostic analytics: 2 analysts (full-time) + 1 senior analyst for review; 3–5 business days from data receipt.
- Pilot design & feasibility: 1 PM + 1 Pricing analyst + 1 Supply Chain lead; 3–7 days.
- Pilot operations & monitoring: 1 PM (part-time), analytics support for dashboards (ad-hoc).
- R&D concepting: Oscar + 1 design engineer + Marcos for technical notes; 4–12 weeks depending on pilot complexity.

Indicative cost ranges (professional services; estimate only)
- Rapid diagnostic (one-off): $25k–$45k depending on data complexity and scope.
- Pilot design & execution (single pilot, two-week): $15k–$35k including analytics and PM support (excludes marketing/promo spend and trade funds).
- R&D concepting (3 product lines): $20k–$60k depending on number of concept iterations and supplier engagement.

Note: These are indicative and will be refined after scoping call and confirmation of owners.

---

# Annexes

A. Example pilot statistical power calculation (simplified)
- Suppose baseline weekly units sold per SKU (to target cohort) = 1,000. Desired detectable relative uplift = 10% (i.e., +100 units). Assume standard deviation of weekly units ~ sqrt(1000) ≈ 32 (Poisson-ish) but practical SD observed ~ 150 due to variability. For alpha=0.05 and power=0.8, sample size per arm for continuous outcome:
  - n = ( (Z_α/2 + Z_β)^2 * 2 * σ^2 ) / Δ^2
  - Where Z_α/2 = 1.96, Z_β = 0.84, σ = 150, Δ = 100.
  - n ≈ ( (2.8)^2 * 2 * 22500 ) / 10000 ≈ (7.84 * 45000) / 10000 ≈ 352,800 / 10000 ≈ 35.28 → 36 weeks (not feasible).
  - Interpretation: For small per-week sample per SKU with high variance, need aggregation across SKUs, longer durations, or larger target populations. Hence pilot design should either A) target more SKUs simultaneously, B) extend duration, or C) target cohorts with higher baseline volumes.

B. Example pilot P&L template (columns)
- SKU_ID | Baseline units | Baseline revenue | Baseline gross margin | Promo discount % | Promo cost $ | Estimated incremental units | Estimated incremental revenue | Incremental gross margin | Net incremental margin | ROI

C. Example data QA checks
- SKU de-duplication, missing weeks, negative prices, inconsistent currency, inconsistent unit-of-measure.

D. Technical feasibility checklist for packaging change
- Regulatory approval needed? Y/N, expected duration.
- Packaging machinery compatibilities (line speeds, changeover time).
- Label approval timelines.
- Cost per unit impact and expected change in per-unit margin.

---

# Next Steps & Asks

From Client
- Provide data in Appendix A within 72 hours (or partial extract if delay expected).
- Nominate client R&D and head-of-commercial contacts.
- Confirm availability for kickoff within 48 hours.

From Wild Advice Partners team
- Nominate Pricing Lead, Supply-Chain Lead, Finance/Pricing analyst, and Project Manager.
- Confirm internal resource availability and readiness to commence on data arrival.

Immediate action items (summary)
1. Client: upload data or indicate timeline for data transfer (owner: client) — due within 72 hours.
2. Wild Advice Partners: confirm internal owners for Pricing, Supply Chain, Finance, and PM — due within 24 hours.
3. Schedule kickoff (virtual, 60–75 mins) within 48 hours of confirmation (owner: Lisa) — send calendar invite and preliminary agenda.
4. On data receipt: analytics begin (owner: Lisa) — deliverable within 3–5 business days.

Contact & Ownership
- Prepared by: Lisa Carter — lead analyst & client contact (Wild Advice Partners)
- R&D/Product ideation: Oscar (lead)
- Technical/R&D feasibility input: Marcos
- Please confirm or revise suggested owners for Pricing, Supply Chain, Finance/Pricing analyst, and Project Manager.

We will deliver the rapid diagnostic within 3–5 business days after data receipt and pilot designs within 7–14 days (from data receipt) as described above. Once owners are confirmed, we will: 1) send the formal data-request, 2) schedule the kickoff within 48 hours, and 3) commence the rapid diagnostic upon secure data transfer.

---

Prepared and ready to proceed upon your confirmation and data transfer.