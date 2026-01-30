# MultiLever — Rapid Diagnostic & Recommendations

Author: Lisa Carter, Data Scientist, Wild Advice Partners  
Contact: team channel or lisa.carter@wildadvice.example

Version: Rapid response draft — intended for immediate operationalization.

---

## Executive summary

Background and context
- MultiLever is operating in an environment characterized by elevated inflation (~10% reported) and a meaningful decline in consumer demand (~20% reported in the most recent quarter). The initial impact is concentrated in discretionary categories (notably toys and small home appliances), while staples and food categories are showing greater volume resilience but early signs of margin pressure due to rising input costs.
- The organization requires an immediate analytics-driven diagnostic to identify where demand declines and margin pressure are concentrated, estimate price and promotion elasticities at SKU-level, and produce concrete, prioritized interventions that can be executed quickly to stabilize revenue and protect margins.

High-level recommendation — two-track approach executed in parallel
1. Rapid analytics-driven diagnostic (track A)
   - Deliver SKU- and channel-level diagnostics (sales, margins, stockouts, promos) and estimate short-run price elasticities and promo uplifts for the top revenue-driving SKUs.
   - Produce a prioritized list of SKU-level interventions (3–10 SKUs per category) including targeted price/promo levers, pack-size experiments, and fulfillment priorities.

2. Near-term operational & R&D/portfolio actions (track B)
   - Short-term (0–7 days): tactical actions to stem ongoing revenue loss — targeted promos, geo-limited pilot packs, supply prioritization, and vendor financing measures to avoid production stoppages.
   - Medium-term (1–6 months): cost-engineering/reformulation, SKU rationalization, introduction of value-tier SKUs, and strategic bundling.

Timing and urgency
- Immediate actions (0–7 days) aimed at stabilizing sales and preventing avoidable stockouts.
- Medium-term actions (1–6 months) for portfolio adjustments and product modifications to protect long-run margins and customer perception.

Key expected outcomes (targeted)
- Stabilize or improve weekly sales for pilot SKUs within 6–8 weeks of action.
- Demonstrable positive ROI on targeted promotions and pack-size pilots within the same period (measured as incremental contribution margin).
- Reduced exposure to margin erosion through targeted reformulation/cost engineering and SKU rationalization.

Deliverables
- Rapid diagnostic Power BI dashboard with SKU/channel filters and pre-built views for elasticity, promo lift, margin deltas, and inventory status.
- Short award recommendation memo (T+24 decision) with prioritized SKU-level interventions and recommended experimental designs.
- RFQ/SOW package for short-lead items and vendor rebids.
- NGO LOI/MOU draft for conditional supplier finance support (if applicable).

---

## Key diagnostic observations (pending full data)

Preliminary findings
- Reported demand drop is uneven both by category and within categories at the SKU level. Discretionary categories (toys, small appliances) show the largest declines by revenue contribution and units sold. Food and basic household consumables exhibit higher resistance to volume declines but show margin squeeze due to raw material cost increases.
- Geographic and channel heterogeneity is likely material: preliminary client brief indicates urban modern trade channels may be more price-sensitive than rural traditional channels; e-commerce shows mixed results depending on assortment and digital promotion intensity.

Critical unknowns (to be resolved with data)
- SKU-level short-run price elasticities — how quantity demanded responds to small price changes for each SKU, by channel and geography.
- Promo uplift and cannibalization — incremental sales and margin from promotions, and whether promotions on some SKUs cannibalize sales of other SKUs or tiers.
- Margin trends — SKU-level contribution margin changes over time (gross margin, COGS breakdown, promotion-related margin pressure).
- Inventory and fulfillment constraints — stockouts, lead times, and allocation issues that may be artificially depressing sales.
- Customer heterogeneity — whether specific cohorts (e.g., loyalty customers, high-frequency buyers) are holding vs. churning.

What we will deliver once data is received
- A prioritized list of 3–5 SKU-level interventions per affected category, including estimated revenue/margin impact and implementation complexity.
- Quantified elasticities and promo lift estimates for the top ~80% revenue SKUs per category, with confidence intervals and sensitivity checks.
- A small set of A/B test or geo-pilot designs for promotions and pack-size variations, including power calculations and pre-specified success criteria.

---

## Immediate (0–7 days) recommendations — tactical and operational

Overview
The near-term objective is to stop avoidable revenue decline and secure supply lines while building a data-driven foundation for medium-term portfolio changes. Actions are grouped by analytics, marketing/pricing, product/packaging, supply/procurement, and finance.

1) Rapid diagnostic analytics (Owner: Lisa) — priority
Objective: Produce crisp, actionable diagnostic outputs within 48–96 hours of receiving required datasets.

Core analytic tasks (deliver in two waves)
- Wave 1 (Day 0–2): Descriptive diagnostics
  - Compute weekly and rolling 4-week volume and revenue trends at SKU × channel × geography slices.
  - Identify top 80% revenue SKUs per category and top decile of margin contributors.
  - Flag SKUs with sudden drop-offs (>20% WoW decline), high return rates (> benchmark), or persistent out-of-stock flags.
- Wave 2 (Day 2–4): Short-run causal estimates and prioritization
  - Estimate short-run price elasticities using week fixed-effects log-log models and cross-sectional variation where available.
  - Estimate promo uplift using difference-in-differences or event-study frameworks; where randomization is absent, leverage matched control cohorts (propensity-score matching).
  - Compute contribution-margin impact under alternate pricing/promotion scenarios for each candidate SKU.

Deliverables
- Power BI diagnostic dashboard with pre-built filters for category, region, channel, SKU, and time windows. Key tabs: Overview, Elasticities, Promo Lift, Margin Impact, Inventory & Fulfillment, Recommended Actions.
- Short memo (2–4 pages) with 3–5 prioritized SKU-level interventions, estimated short-run revenue/margin impact, and recommended test design for each.

Sample analytic pipeline (high level)
- Data ingestion → Quality checks → Time series aggregation → Regression models and uplift estimation → Prioritization algorithm (score = [elasticity rank] × [revenue weight] × [implementability penalty]) → Dashboard & memo.

2) Targeted pricing & promotion (Owners: Client Marketing; execution owner: Oscar)
Principles
- Avoid across-the-board discounts; instead, apply targeted, short-duration offers where elasticity indicates price sensitivity and where incremental margin from uplift is positive.
- Preserve brand equity for core SKUs: keep flagship SKUs out of deep discounting; use secondary SKUs or limited-time bundles as primary experiment subjects.

Tactics (examples)
- High-elasticity discretionary SKU: short-duration 10–15% discount combined with free-shipping threshold reduction in a geo-limited pilot (urban metro areas).
- High-frequency staple SKU showing margin pressure: test a temporary coupon targeted to loyalty customers to preserve volume without broad price cuts.
- Use "economy" price framing (smaller pack sizes priced proportionally higher per unit but lower absolute spend) to reduce consumer spend resistance.

Execution checklist
- Define pilot geos/channels and control groups.
- Pre-approve margin loss threshold and stop-loss rules.
- Monitor daily to detect early signs of cannibalization or brand risk.

3) Pack-size & value-pack pilots (Owners: R&D & Product; RFQ owner: Oscar)
Rationale
- Smaller pack sizes lower the entry ticket for consumers facing budget pressure; value packs can increase perceived value while protecting ASPs.

Pilot design
- Select 4–6 SKUs across affected categories (mix of staples and discretionary where appropriate).
- Offer two pack-size variants: (A) smaller size priced to preserve unit margin (higher per-unit price but lower absolute spend) and (B) value pack (multi-pack) with slight per-unit discount but higher basket value.
- Pilot duration: 4 weeks (with 1-week ramp + 3 weeks full test), measured against matched geo-controls.

Metrics to track
- Sales (units, revenue), conversion rate, average basket size, margin per transaction, repeat purchase rate for the test window and 4 weeks post-promo.

Sample pack experiment table

| SKU | Baseline weekly units | Variant A (small pack) price | Variant B (value pack) price | Channel | Geo | Pilot length (weeks) |
|-----|-----------------------:|-----------------------------:|-----------------------------:|--------:|----:|---------------------:|
| SKU-1001 | 8,500 | $1.25 (per unit equiv) | $0.95 (per unit equiv) for 3-pack | Modern Trade | Metro A | 4 |
| SKU-2042 | 4,200 | $3.00 | $2.75 (2-pack) | E-commerce | Geo B | 4 |

4) Supply prioritization & staged fulfillment (Owners: Ops / Procurement)
Objective
- Avoid stockouts for high-contribution SKUs and prioritize short-lead SKUs to meet immediate demand and avoid lost sales.

Actions
- Implement short-term allocation rules: prioritize core SKUs and pilot SKUs, de-prioritize low-contribution SKUs or slow-movers for constrained capacity.
- Stage fulfillment: deliver partial shipments to key markets to maintain presence, with clear communications to customers about expected delivery timing.
- Implement a daily supply dashboard for operations with flags for SKUs approaching safety stock threshold and expected fill rates by region.

5) Procurement / vendor financing approach (Owners: Procurement; Marcos to coordinate NGO assurances)
Problem
- Vendors may face liquidity pressure; conditional financing or revised award structures can keep them operational and able to execute.

Recommended approaches
- Conditional award with reduced bond and contractual holdback (suggested +5% retention): reduces vendor upfront capital requirement while protecting buyer via retention.
- Bank or parent guarantees + mobilization milestone: release initial partial payment on proof of mobilization and escrow the remainder.
- NGO or development partner LOI/MOU to provide partial bridge financing or guarantees where public-good rationale applies.

Sample template language (high-level)
- “Buyer shall retain 5% of contract value as retention for up to 90 days post-delivery. Vendor may request an initial mobilization advance of up to 20% subject to provision of [bank/parent] guarantee or confirmed NGO bridging instrument. Partial release of retention will occur upon achieving agreed delivery milestones.”

---

## Medium-term (1–6 months) recommendations — product, portfolio, and R&D

Objective
- Move from tactical firefighting to structural adjustments that sustain margins and customer loyalty over the medium term.

1) Reformulation / cost engineering (Owner: R&D)
Scope
- Target ingredients, processing steps, and packaging components with the highest dollar impact on COGS that can be altered without materially changing product perception or regulatory status.

Process
- Rapid cost opportunity assessment: quantify cost contribution by ingredient and packaging for top 30 SKUs using Pareto analysis.
- Prioritize low-risk substitutions (e.g., alternate sourcing, minor recipe tweaks) and packaging changes (thinner-gauge film, optimized box sizes).
- Pilot reformulations with sensory testing and limited market release to validate acceptance.

Financial target
- Aim for 2–5% unit COGS reduction across prioritized SKUs, with sensitivity scenarios modeled for potential perception or quality impacts.

2) SKU rationalization and portfolio optimization (Owner: Product & Analytics)
Rationale
- Eliminate/merge low-contribution, high-complexity SKUs to reduce working capital, manufacturing complexity, and procurement overhead.

Approach
- Data-driven SKU scoring (example criteria): revenue contribution, margin contribution, frequency of purchase, SKU complexity cost (setups, packaging tooling), inventory days, and strategic importance.
- Establish a cutoff rule (e.g., SKUs below median for revenue and margin while above 75th percentile for complexity become candidates for rationalization).
- Develop migration paths for customers (substitute SKUs, communication plans, promo offers to shift demand).

3) New value-tier products and strategic bundling (Marketing + R&D)
Opportunity
- Introduce lower-priced value tiers or bundle existing SKUs to increase perceived value while protecting average selling price (ASP) across core lines.

Examples
- “Value” reformulation with modest ingredient change but lower price point targeted at budget-constrained segments.
- Bundles: pair slower-moving accessory SKUs with core SKUs at a small discount, preserving overall margin but improving turnover.

Go-to-market
- Use targeted campaigns to test response among price-sensitive segments, measure cannibalization, and iterate.

---

## Implementation plan, owners & timelines (concrete)

High-level milestones and owners

| Activity | Owner | Timeline (from data availability) | Deliverable |
|---------|-------|------------------------------------:|------------|
| Receive datasets & run QA | MultiLever Data Team | 0–24 hours | Cleaned dataset + data quality report |
| Rapid diagnostic analytics (Wave 1 & 2) | Lisa (Analytics) | 48–96 hours | Power BI dashboard + 2–4 page memo |
| RFQ / Vendor rebids (short-lead items) | Oscar | 0–12 hours (upload) + 12 hours (rebids) | RFQ/SOW uploaded + vendor responses |
| NGO LOI/MOU draft | Marcos | 24 hours | Draft LOI/MOU |
| Procurement confirm guarantee acceptance | Procurement | 12 hours | Confirmation + legal template |
| Finance provide SKU-level COGS | Client Finance | 24 hours | SKU-level COGS file |
| Pack-size pilot design | R&D & Product | 48–72 hours | Pilot protocol + creatives |
| Promotional pilot launch | Marketing/Oscar | 72–120 hours | Live pilot + monitoring dashboard |

Gantt-style view (indicative)
- Day 0: Data request issued; RFQ uploaded; Procurement legal check initiated.
- Day 1: Data received & ingested (if available); Lisa begins Wave 1 diagnostics; Marcos posts LOI draft.
- Day 2–4: Elasticity estimates completed; memo prepared; RFQ rebids reviewed; procurement decisions finalized; pilots queued.
- Week 1–2: Pilots run; monitoring daily; preliminary KPI checks on Day 7 and Day 14.
- Weeks 4–8: Evaluate pilots and make go/no-go decisions on scaling.

Decision gates and timelines
- T+24 (24 hours after diagnostics complete): decision on immediate SKU-level interventions and vendor awards (recommend for fast-moving items).
- 6–8 weeks: review pilot results and decide scaling strategy for promotions, packs, and new SKUs.

Budget and resource outline (indicative)
- Analytics effort (Lisa + 1 analyst, 48–96h): estimated internal cost or pro-bono hours as per engagement.
- Promotion spend (pilot-level): dependent on SKU and channel — recommended capped test budgets per SKU (e.g., $5–15k per SKU for digital/ecomm pilots; sample allocation table available on request).
- RFQ mobilization/guarantees: contingent on supplier proposals; expected short-term working capital requirement if advances are used.

---

## Data requirements & assumptions

Required datasets, owners & suggested deadlines
- Weekly SKU-level sales (last 12 months) — Owner: MultiLever Data Team — preferred deadline: within 24 hours.
- Price history, promotion history, channel & geography flags, returns, inventory and lead times — Owner: MultiLever Data Team — 24 hours.
- SKU-level cost/COGS and margin breakdown — Owner: Finance — 24 hours.
- Marketing campaign calendar and spend by channel (last 12 months + planned) — Owner: Marketing — 24 hours.
- Production capacity, supplier lead times, and current open purchase orders — Owner: Procurement / Ops — 24 hours.
- Loyalty/customer cohort data and customer-level transaction history (opt-in/hashed IDs) — Owner: CRM/Customer Analytics — 24–48 hours (if available).

Minimum acceptable data quality
- Weekly granularity for time-series analysis (daily where possible).
- SKU-level identifiers consistent across datasets (single primary key).
- Accurate timestamps for promotions and price changes (start/end dates).
- COGS detail at SKU level (ingredient and packaging cost breakdown preferred).

Data dictionary (minimum fields, sample)
- sku_id (string) — unique SKU code
- sku_description (string)
- category (string)
- channel (string) — e.g., ModernTrade, TraditionalTrade, E-commerce
- geo_region (string) — e.g., MetroA, RegionB
- week_ending (date) — week granularity
- units_sold (int)
- gross_revenue (decimal)
- unit_price (decimal) — net of coupons
- promo_flag (bool) — whether on-promo
- promo_type (string) — e.g., price_discount, coupon, bogo
- returns_units (int)
- inventory_on_hand (int)
- lead_time_days (int)
- cogs_per_unit (decimal)
- contribution_margin (decimal) — optional if finance provides

Assumptions and caveats
- Client-reported inflation and demand metrics are treated as directionally accurate. Elasticity and uplift estimates will have uncertainty proportional to data granularity and history length.
- Short-run elasticity estimates assume other factors (stockouts, substitution, marketing) are adequately controlled for in models; we will explicitly test for stockout-induced drops.
- Missing or late data will delay diagnostic outputs and reduce confidence intervals; the recommended 24–48 hour data window is critical for the compressed timeline.

Data quality checklist (to be completed by data owner)
- Are SKU identifiers consistent across all files? Y/N
- Are price and promo timestamps accurate? Y/N
- Are returns accurately attributed to original order week? Y/N
- Are inventory and lead-time fields populated for >90% SKUs? Y/N
- Known data anomalies (list): e.g., price decimals missing, negative sales after returns.

---

## KPIs and success metrics

Primary operational KPIs
- Weekly sales (units and revenue) by SKU and channel — tracked daily and summarized weekly.
- SKU-level price elasticity — estimated short-run elasticity (∆logQ / ∆logP) with confidence intervals.
- Promo uplift — incremental sales and margin attributable to promotions (in units and contribution margin).

Financial KPIs
- Contribution margin impact by SKU and pilot cohort (baseline vs. pilot).
- Gross margin delta vs. baseline on a rolling 4-week window.
- ROI on promotional spend (incremental contribution margin / promo cost).

Pilot targets and thresholds
- For pack-size and promo pilots: target stabilization or improvement in weekly units sold for pilot SKUs within 6–8 weeks. Example numeric target: at least +5% unit sales vs. matched-control with non-negative contribution margin impact.
- Minimum acceptable ROI for promotion pilots: incremental contribution margin ≥ 1.5 × promotional cost (or a positive breakeven based on strategic prioritization).
- Stockout mitigation: maintain fill rate >95% for prioritized SKUs during the pilot window.

Reporting cadence
- Daily: dashboard for critical live pilots — units sold, promo redemptions, stockouts, and contribution margin burn rate.
- Weekly: consolidated status update with top signals and recommended adjustments.
- T+24 decision memo: prioritized list and recommended awards/changes.

Definitions (to avoid ambiguity)
- Short-run price elasticity: % change in units demanded for a 1% change in price over a short time horizon (weeks), controlling for promo and seasonality.
- Promo uplift: incremental units sold attributable to promotional activity relative to an appropriate control.
- Fill rate: share of customer demand satisfied from available inventory (units shipped / units ordered).

---

## Risks & mitigations

1) Data & analytics risk
- Risk: Missing, inconsistent, or late data prevents accurate elasticity or uplift estimation.
- Mitigation: Prioritize delivery of minimal required fields (SKU-week sales, price history, promo flags). Use conservative imputation for short gaps; flag estimates with uncertainty bands. Use business rules for immediate prioritization if models cannot be estimated.

2) Supply constraints
- Risk: Vendors cannot supply prioritized SKUs on time, leading to stockouts and lost promotional ROI.
- Mitigation: Short-lead prioritization, phased fulfillment plans, conditional vendor financing and mobilization milestones, sourcing alternate suppliers where feasible. (Owner: Ops / Procurement)

3) Margin erosion
- Risk: Broad discounting reduces margins more than the incremental volume can compensate.
- Mitigation: Use targeted offers with pre-specified margin loss thresholds, prefer pack-size and bundling approaches, require finance sign-off for any promotion exceeding X% margin hit per SKU. (Owner: Finance / Marketing)

4) Brand perception and cannibalization
- Risk: Deep discounts or widespread promotion may dilute brand positioning or cannibalize higher-margin SKUs.
- Mitigation: Keep core branded SKUs out of deep discounting; restrict experiments geographically and by channel; pre-specify cannibalization checks; cap promotional duration and scope. (Owner: Marketing)

5) Vendor liquidity risk
- Risk: Vendor failure due to liquidity constraints could disrupt supply.
- Mitigation: Offer conditional awards, retention-based contracts, mobilization guarantees, or facilitate NGO/partner bridge assurances. (Owner: Procurement / Marcos)

6) Regulatory or compliance issues (if applicable)
- Risk: Packaging or reformulation changes could trigger regulatory review.
- Mitigation: R&D will coordinate with regulatory/compliance teams on any formulation/pack-size changes prior to launch.

Risk register (sample entries)

| Risk | Likelihood | Impact | Mitigation Owner | Mitigation actions |
|------|-----------:|-------:|-----------------:|-------------------|
| Missing SKU-level COGS | High | High | Finance | Provide minimal cost allocations; accept proxies for rapid work |
| Vendor inability to rebid | Medium | High | Procurement/Oscar | Expand RFQ pool; use conditional awards with mobilization |
| Promo cannibalization | Medium | Medium | Marketing/Analytics | Pre-specified control geos; daily monitoring; adjustable stop rules |

---

## Governance, roles & RACI (sample)

RACI for immediate program

| Activity | Responsible | Accountable | Consulted | Informed |
|----------|-------------|-------------|-----------|---------|
| Rapid analytics | Lisa (Analytics) | Lisa | Data Team, Finance | Exec Sponsor |
| Promo design & launch | Marketing | Head of Marketing | Lisa, Finance | Ops, Sales |
| Pack-size pilots | R&D & Product | Head of Product | Marketing, Finance | Ops |
| RFQ upload & vendor communication | Oscar | Oscar | Procurement | Suppliers |
| NGO LOI negotiation | Marcos | Marcos | Legal, Finance | Exec Sponsor |
| Procurement guarantee acceptance | Procurement | Head Procurement | Legal, Finance | Oscar, Ops |
| Implementation monitoring | Ops | Head Ops | Analytics | Marketing, Finance |

Escalation path
- Day 0–3 issues: escalate to project lead (Lisa) for triage.
- Vendor or procurement impasse: escalate to Marcos and Head Procurement within 24 hours.
- Material deviation from financial thresholds: escalate to Client Finance Lead and Head of Commercial.

---

## Next steps (immediate, concrete)

1) Within 12 hours
- Oscar uploads RFQ/SOW and short-lead components list to shared folder (Owners: Oscar, Procurement). Provide supplier list and contact details.
- Procurement confirms acceptable guarantee language and uploads legal template. If guarantees unacceptable, propose alternative conditional payment terms.

2) Within 12–24 hours
- Vendors submit rebids per RFQ (Owners: Vendors, managed by Oscar).
- Data team provides initial dataset (Owners: MultiLever Data Team). If not available, supply earliest possible ETA.

3) Within 24 hours
- Marcos posts NGO LOI/MOU draft confirming potential bridge support and proposed escrow/direct payment mechanisms (Owner: Marcos).
- Finance uploads SKU-level COGS and margin file (Owner: Client Finance).

4) Within 24–48 hours
- Lisa runs a FEMA (financial, ethics, market access) compliance pass on rebids and prepares award recommendation memo for T+24 decision (Owner: Lisa).
- Analytics finalizes elasticity estimates for top 80% revenue SKUs and shares dashboard access.

5) Decision points
- T+24 decision: Approve immediate SKU-level interventions and vendor awards for short-lead items.
- T+6–8 weeks: Review pilot results and decide on scale-up or termination.

Action checklist (interactive)
- [ ] RFQ uploaded (Oscar)
- [ ] Procurement legal template confirmed (Procurement)
- [ ] Data received & QA completed (Data Team)
- [ ] SKU-level COGS received (Finance)
- [ ] NGO LOI drafted (Marcos)
- [ ] Analytics dashboard live (Lisa)
- [ ] Pack-size pilot protocol approved (R&D/Product)

---

## Appendix A: analytic approach (detailed)

Overview
The analytic approach focuses on robust, fast-turnaround methods to estimate short-run elasticities and promo lift while providing clear uncertainty quantification and sensitivity checks. We combine descriptive time-series diagnostics with quasi-experimental causal inference where feasible.

1) Descriptive diagnostics
- Aggregations: Weekly time-series for units, revenue, average price, and margin for SKU × channel × geo.
- Outlier detection: Identify anomalous weeks (e.g., returns spikes, data dumps) and flag for manual review.
- Seasonality and holiday flags: incorporate calendar controls for known demand events.

2) Price elasticity estimation (short-run)
Primary model: Week fixed-effects log-log regression (example)

ln(Q_ijkt) = α_jk + β ln(P_ijkt) + γX_ijkt + δ_t + ε_ijkt

Where:
- Q_ijkt = units sold for SKU i in channel j and geography k at week t
- P_ijkt = observed price per unit (net)
- α_jk = SKU × channel/site fixed effects (or SKU fixed effects if enough time variation)
- X_ijkt = vector of control variables (promo_flag, inventory_on_hand, marketing_spend)
- δ_t = week fixed effects (controls for macro trends)
- β = short-run price elasticity estimate

Notes
- In presence of endogeneity (price changes correlated with unobserved demand shocks), exploit exogenous price variation (manufacturer-driven list price changes, geo-specific price differences, or instrument with cost shocks if available).
- Provide clustered standard errors at SKU × region level.

3) Promo uplift estimation
- Preferred: randomized controlled trials (geo or customer-level) where feasible.
- If not randomized: difference-in-differences (DiD) or event-study with matched controls.
  - DiD specification example:

Q_it = α + τ Promo_it + θ Post_t + λ (Promo_it × Post_t) + φControls + ε_it

Where λ captures incremental lift relative to controls.

Matching
- Propensity-score matching on pre-treatment sales trends, category, price, and channel to construct credible control groups.

4) Cannibalization and cross-price effects
- Where SKUs in the same category have sufficiently rich variation, estimate cross-price elasticities in a system of demand equations (e.g., logit or Almost Ideal Demand System (AIDS) where practical).
- Simpler approach: regressions including competitor SKU prices and promo flags as regressors to detect substitution.

5) Power calculations for pilots
- Use historical variance in weekly sales to compute minimum detectable uplift (MDU) for a given sample size and test duration.

Sample power calc (illustrative)
- Baseline weekly mean units per geo = 1,000, SD = 250
- Desired detectable increase = 5% (50 units)
- With α=0.05 and power=0.8, required sample geos ~ 16 (8 treatment, 8 control) for 4-week test. (Precise numbers computed once variance is known.)

6) Prioritization scoring algorithm (example)
- Score_i = w1*(revenue_share_i) + w2*(elasticity_rank_i) + w3*(margin_impact_i) - w4*(implementation_complexity_i)
- Normalize weights to session priorities (default: w1=0.4, w2=0.3, w3=0.2, w4=0.1). Allows rapid triage of top candidate SKUs.

7) Robustness checks
- Heterogeneity: estimate elasticities by channel and geo.
- Sensitivity: re-estimate excluding weeks with known stockouts or promotional confounders.
- Placebo tests: apply identical models to pre-treatment placebo windows to check for spurious effects.

8) Example SQL queries (for data team)
- Aggregate weekly sales:

SELECT sku_id, channel, geo_region, DATE_TRUNC('week', order_date) AS week_ending,
       SUM(units) AS units_sold, SUM(revenue) AS gross_revenue,
       AVG(unit_price) AS avg_price
FROM sales_table
WHERE order_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY sku_id, channel, geo_region, week_ending;

- Join price & promo history:

SELECT s.*, p.promo_flag, p.promo_type, f.cogs_per_unit
FROM weekly_sales s
LEFT JOIN price_promo_history p
  ON s.sku_id = p.sku_id AND s.week_ending = p.week_ending
LEFT JOIN finance_cogs f
  ON s.sku_id = f.sku_id

9) Dashboard mock-up & views
Key tabs and metrics:
- Overview: total revenue trend, units trend, average price, margin trend.
- Top SKUs: sortable table (revenue, margin, elasticity, promo lift).
- Elasticities: heatmap by category × channel.
- Promo lift: cumulative uplift vs. control.
- Inventory & Fulfillment: fill rates, lead times, stockouts.
- Recommendations: actionable SKUs and estimated impact.

Visuals descriptions (for Power BI)
- Line chart: weekly revenue and units with promo shading bands.
- Heatmap: elasticity values (red = high elasticity, green = inelastic).
- Waterfall: contribution margin change decomposition (price, cost, promo effect).

---

## Appendix B: sample templates & artifacts

1) Short award recommendation memo (T+24) — template (content guidance)
- Background & problem statement (1 paragraph)
- Data and analytic summary (one-page): datasets used, key diagnostics, top signals
- Top recommended awards/interventions (table): SKU, intervention type, expected impact, estimated margin effect, owner, and implementation time.
- Risks & stop-loss rules (e.g., if observed cannibalization > X% or margin < threshold).
- Appendices: elasticity table and promo uplift estimates.

2) RFQ / SOW checklist
- Item description and SKU mapping
- Required volumes and lead times
- Quality/specification documents and acceptance criteria
- Payment terms and conditional guarantees
- Mobilization milestones and delivery milestones
- Penalties and retention terms

3) NGO LOI / MOU outline (sample clauses)
- Purpose: provide bridging guarantees or partial payment support to key local vendors to ensure continuity of supply for essential products.
- Scope: limited to identified SKUs/vendors for defined period.
- Financial modalities: guarantee cap, milestones for release.
- Reporting & audit: vendor must provide production and shipment documentation.
- Term & termination: clear exit clauses and dispute resolution.

4) Pack-size pilot protocol (example)
- Objective: test whether smaller pack variants increase conversion among budget-constrained consumers without materially eroding per-transaction margin.
- Hypothesis: Variant A (smaller pack) will achieve +6% units sold in target geos with non-negative contribution margin impact.
- Design: Geo A/B test — 8 treatment geos vs 8 matched control geos.
- Duration: 4 weeks.
- Metrics & success criteria: units sold, revenue per transaction, margin per transaction, repeat purchase within 30 days.
- Stopping rules: stop early if margin loss exceeds pre-approved threshold or if brand complaints exceed threshold.

---

Prepared by: Lisa Carter

For questions, clarifications, or scheduling the kickoff call, please contact the team channel or lisa.carter@wildadvice.example

---