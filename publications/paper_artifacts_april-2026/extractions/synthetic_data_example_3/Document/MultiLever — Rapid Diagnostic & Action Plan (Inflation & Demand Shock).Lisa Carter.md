# Executive summary

MultiLever experienced approximately 10% input-price inflation and an approximately 20% decline in consumer demand in the most recent quarter. The demand decline is concentrated in three categories: food, home appliances, and toys. This document proposes a prioritized, time‑boxed engagement to rapidly diagnose the drivers, quantify impacts under plausible scenarios, and deliver short‑to‑ and medium‑term actions that protect revenue while maintaining margin integrity.

Key short‑term objective: deliver a rapid diagnostic within 5 business days to identify the top 2–3 demand drivers per category and recommend immediate mitigations that can be tested or deployed within 2–4 weeks.

Summary of recommendations (high level)
- Run a 5‑business‑day rapid diagnostic to produce a one‑page executive finding and a data appendix with preliminary elasticity estimates and top drivers by SKU/segment/channel.
- Follow with 2–3 weeks of scenario modelling using hierarchical/segment‑level elasticity models, promotion and pack‑size simulations, and margin tradeoff analysis.
- Deliver a week‑4 prioritized playbook with pilot designs, owners, KPIs, and quantified ROI to guide 2–4 week pilots and subsequent scaling.

This plan balances speed and robustness: early work focuses on high‑signal aggregates and quick wins; modelling then refines results for strategic pilots and scale.

---

# Situation & key facts (expanded)

Observed metrics (company‑reported)
- Input cost increase: ~ +10% YoY on weighted average COGS across SKUs (documented by Procurement and Finance).
- Demand change: ~ −20% in aggregate sales revenue for the quarter vs the previous comparable quarter (seasonally adjusted), concentrated in three categories:
  - Food: −22% revenue; unit sales down −18%.
  - Home appliances: −25% revenue; unit sales down −23%.
  - Toys: −18% revenue; unit sales down −20%.
- Geographic concentration: greatest declines in Region East and Region South (retail partner channels), comparatively smaller declines in Direct Online channels but lower traffic.

Operational constraints and client context
- R&D capacity exists but is limited: core R&D team can reallocate 20–30% capacity to rapid feasibility studies; large reformulations will require longer timelines.
- Commercial/Analytics has access to transactional data but recent BI snapshots are incomplete for promotions and returns.
- Time pressure: client needs implementable options within 2–4 weeks for peak trading windows and to preserve FY targets.
- Regulatory or procurement constraints (to be confirmed) may limit maximum allowable discounts or bill‑of‑materials changes for certain SKUs (notably food).

Category snapshots (initial observations)
- Food: high frequency purchase, relatively low unit price; high sensitivity to price increases and smaller pack options historically perform well in price‑sensitive cohorts.
- Home appliances: higher‑ticket items, longer purchase cycles; demand appears sensitive to financing terms and promotional bundles rather than unit price alone.
- Toys: seasonal and gift‑driven; demand drop correlates with decreased promotional activity and fewer product launches.

---

# Core diagnostic questions (expanded and operationalized)

1. What share of the observed demand decline is explained by:
   - Pure price elasticity (pass‑through of input inflation to consumer prices)?
   - Income effects / macro consumer pressure (household income declines or sentiment)?
   - Channel shifts (customers moving from one channel to another, causing lower conversion or measurement issues)?
   - Competitor actions (aggressive pricing, bundle offers, new SKUs)?
   - Other factors (supply out‑of‑stocks, negative product sentiment, seasonality variance)?
   For each, produce approximate contribution estimates (e.g., % of total demand decline attributable).

2. Which SKUs, segments, channels, or cohorts are most sensitive (high elasticity) and which are resilient?
   - Produce an ordered SKU list per category by estimated price elasticity, margin contribution, and strategic importance.
   - Highlight SKUs that are “margin protectors” (low elasticity, high margin), candidate “volume drivers” (high elasticity, high share), and “strategic losses” (high elasticity, low margin — avoid heavy discounts).

3. What low‑effort, high‑impact levers are immediately available to test and implement within 2–4 weeks?
   - Rank levers by expected impact (demand lift), cost (margin erosion or implementation cost), time‑to‑implement, and risk.

4. What pilot designs and KPIs will give rapid, statistically meaningful results for the most promising levers?

5. Under plausible competitor reaction scenarios, what guardrails should the business apply to discounting or pack changes to protect long‑term margin?

---

# Recommended engagement structure & timeline (detailed)

Overall timeline: 4 weeks (time‑boxed phases), with clear deliverables and owners.

Phase 1 — Rapid diagnostic (5 business days)
- Deliverable: 1‑page diagnostic summary + data appendix (CSV & visuals).
- Objectives:
  - Identify top 2–3 demand drivers per impacted category (food, appliances, toys).
  - Estimate preliminary price elasticities at SKU or segment level using log‑linear regressions and simple fixed effects where possible.
  - Flag quick wins: 3–6 interventions per category that could be piloted within 2–4 weeks.
- Activities (day‑by‑day):
  - Day 0 (kickoff): confirm data access, nominate client analytics/R&D contacts, finalize scope and out‑of‑scope SKUs.
  - Day 1: ingest sales, pricing, promo calendar, COGS, and channel data; run data quality checks (missingness, out‑liers).
  - Day 2: descriptive analytics — time series of revenue, units, price, promos by SKU/channel/region; identify large discontinuities and OOS events.
  - Day 3: preliminary elasticity estimates (log(price) -> log(quantity) with SKU or category fixed effects), promo lift estimates, and quick segmentation by cohort (loyal vs trial).
  - Day 4: synthesize findings, draft the one‑page executive diagnostic, prepare data appendix and reproducible code.
  - Day 5: review with client, hand off detailed appendix.
- Team & roles:
  - Owner: Lisa (lead analyst & author).
  - Support: Alex (data ingestion, ETL, QA).
  - Client lead: named contact in Commercial/Analytics (TBD).
- Outputs:
  - One‑page diagnostic (top 3 drivers per category + confidence levels).
  - Data appendix: CSV of cleaned aggregated series (SKU x week x channel), model code snippets, and initial elasticity priors.

Phase 2 — Modelling & scenarios (2–3 weeks)
- Deliverable: scenario deck with quantified outcomes and recommended interventions.
- Objectives:
  - Build more refined elasticity models (hierarchical Bayesian or mixed effects models) to estimate elasticity by SKU, channel, and cohort.
  - Simulate interventions: pricing changes, pack size introductions, targeted promotions, and loyalty offers.
  - Margins: run COGS and cost‑to‑serve scenarios to show profit/revenue tradeoffs.
- Activities:
  - Expand feature set (promotional mechanics, pack sizes, competitor price series, marketing exposures).
  - Build hierarchical models that pool information across SKUs within a category to improve estimates for low‑volume SKUs.
  - Run scenario simulations for 3 business cases (Base, Recession‑deep, Competitor price war).
  - Feasibility check with R&D for product variant options (list of candidate SKUs with estimated COGS delta and expected timeline).
- Team & roles:
  - Owner: Lisa (modelling & scenario lead).
  - Support: Alex (feature engineering & validation), Client R&D (feasibility inputs), Sara (engagement sponsor/PM).
- Outputs:
  - Scenario deck with tables showing revenue, margin, and ROI under candidate tactics and competitor responses.
  - Ranked list of pilot candidates with estimated demand uplift, margin change, and time‑to‑implement.

Phase 3 — Recommendations & implementation plan (week 4)
- Deliverable: prioritized playbook + quantified ROI and owners for pilot/scale.
- Objectives:
  - Prioritize tactics by expected demand lift / margin impact / time‑to‑implement.
  - Provide pilot designs with statistical power calculations, KPIs, monitoring dashboards, and escalation rules.
  - Communication templates for internal stakeholders and retail partners.
- Activities:
  - Finalize prioritization using agreed decision criteria.
  - Produce playbooks and estimated budgets/owners for each pilot.
  - Schedule rolling implementation plans and performance review cadence.
- Team & roles:
  - Owner: Lisa (report author).
  - Partner: Sara (client engagement & approvals).
  - Client Ops/Retail: implementation owners for pilots.
- Outputs:
  - Implementation playbook with owners, timelines, and KPIs.
  - Monitoring dashboard templates and reporting cadence for pilot governance.

High‑level timeline (condensed)
Week 0: Kickoff and data access (0–48 hours)
Week 1 (days 1–5): Rapid diagnostic deliverable
Week 2–3: Scenario modelling and R&D feasibility
Week 4: Recommendations, playbook, and pilot readiness

---

# Tactical levers to evaluate (expanded, with deployment notes)

For each lever we provide: short description, deployment time estimate, implementation complexity, expected impact direction, and sample KPIs.

1. Pricing & pack-sizing
- Description: Introduce lower‑priced formats (smaller SKUs), multi‑packs, and psychological price points. Consider tiered price anchoring and value SKUs.
- Time to pilot: 2–4 weeks for pack‑size promos through retail partners (if shelf space not required); 4–8 weeks for permanent pack SKU launches.
- Complexity: medium (packaging, SKU codes, distribution updates).
- Expected impact: increases purchase incidence in price‑sensitive cohorts; potential margin compression depending on COGS.
- KPIs: unit sales change, revenue per household, margin per unit, frequency of purchase, uplift vs control stores.

2. Targeted promotions
- Description: Redirect promotional spend to cohorts with highest expected ROI — loyal customers, price‑sensitive segments, or high LTV prospects.
- Time to pilot: 1–2 weeks to set up targeted digital promos; 2–4 weeks for retailer coupon arrangements.
- Complexity: low to medium (depends on segmentation availability).
- Expected impact: higher conversion and more efficient promo spend.
- KPIs: promo redemption rate, incremental units, promo ROI (incremental margin / promo cost).

3. Cost‑to‑serve & supply chain
- Description: Quick wins by optimizing distribution (e.g., consolidation of pick batches, alternate fulfillment nodes) to reduce cost‑to‑serve and free margin for targeted discounts.
- Time to pilot: 1–3 weeks to change fulfillment routes or packing rules.
- Complexity: medium (operations coordination).
- Expected impact: margin protection enabling selective discounts without net margin loss.
- KPIs: cost‑to‑serve per order, fulfillment lead time, stock‑out rate.

4. Product reformulation / lower‑cost variants
- Description: Use R&D to identify substitutions or simplifications that keep perceived quality but reduce ingredient or BOM costs.
- Time to pilot: 4–12 weeks for rapid feasibility and small‑batch trials; longer for regulatory approvals if needed.
- Complexity: high (R&D, regulatory, procurement).
- Expected impact: permanent margin improvement if accepted by customers.
- KPIs: COGS reduction per unit, sensory acceptance score, pilot sell‑through.

5. Loyalty & subscriptions
- Description: Pilot subscription programs, auto‑replenishment discounts, and bundled value packs to stabilize demand among high‑LTV customers.
- Time to pilot: 2–6 weeks depending on platform readiness.
- Complexity: medium (CRM, billing).
- Expected impact: demand smoothing and retention uplift.
- KPIs: churn rate, ARPU, lifetime value change.

6. Channel mix optimization
- Description: Prioritize channels by conversion and acquisition cost. Increase share in direct channels if margins allow and acquisition costs are favorable.
- Time to pilot: 1–3 weeks for tactical shifts.
- Complexity: low to medium.
- KPIs: CAC, conversion rate, gross margin contribution per channel.

Each lever will be quantified in the modelling phase (Phase 2) with expected demand lift and margin impact under multiple scenarios.

---

# Data needs (expanded and precise schema)

To run the diagnostic quickly we require the following, ideally in the specified formats. For each item we indicate minimum acceptable quality, preferred file format, and example headers.

1. SKU‑level sales and units by day/week for the last 12 months (including returns)
- Minimum: weekly aggregation per SKU for 12 months, with units, revenue, returns.
- Preferred: transactional (order line) CSV with headers:
  - order_id, order_date, sku, units, gross_price, net_price, channel, customer_id (nullable), region, return_flag, promo_code
- Note: include timezone and calendar conventions.

2. SKU listed price, promotional price, promotion calendar and promo mechanics
- Preferred: promo_calendar.csv
  - sku, promo_start_date, promo_end_date, promo_type (discount, BOGO, coupon), promo_mechanics (e.g., 20% off, 2 for 1), trade_spend_allocated
- Include effective displayed price per promo day if possible.

3. Channel & region breakdowns (online, retail partner, direct), including traffic and conversion where available
- Preferred: channel_metrics.csv
  - date, channel, sku (optional), sessions (if digital), clicks, adds_to_cart, checkouts, orders, units, revenue, conversion_rate
- If partner data is limited, provide aggregated weekly KPIs by channel.

4. Cost and margin at SKU level (COGS, cost-to-serve)
- Preferred: sku_costs.csv
  - sku, cogs_per_unit, packaging_cost, freight_alloc_per_unit, cost_to_serve_per_unit, current_list_price, net_margin
- If only BOM available, provide BOM and master cost assumptions.

5. Loyalty / customer‑level panels or cohort metrics if available
- Preferred: customer_purchases.csv (delivered as hashed IDs)
  - customer_id, order_id, order_date, sku, units, price, channel, cohort_tag (if available)
- Also include segment definitions or churn flags.

6. Competitor price data (if available) or top‑5 competitor pricing snapshots
- Preferred: competitor_prices.csv
  - sku_or_competitor_sku, competitor, date, listed_price, promo_flag, source
- If not available, note data collection constraints and whether scraping or syndicated data purchase is possible.

7. Consumer or macro data on household income or consumer sentiment
- Examples: regional unemployment, disposable income indices, consumer confidence indices aligned to the last 12 months.

8. R&D inputs: bill‑of‑materials at SKU level, current formulation specs, and a named R&D contact
- Preferred: bom_sku.xlsx and formulation_specs.pdf
  - bom_sku: sku, ingredient_code, ingredient_name, qty_per_unit, unit_cost, supplier, lead_time
- Provide contact name, email, and best times for rapid calls.

Data access: provide an API key, BI account, SFTP link, or shared folder (e.g., secure S3 bucket). If credentials cannot be shared, plan a 1‑hour screen share to run queries with client analysts.

---

# Rapid diagnostic: technical approach (concrete)

Analytical methods to be used in the 5‑day diagnostic (keep computations simple and reproducible)

1. Descriptive analytics
- Time series decomposition at weekly granularity: baseline trend, seasonality, and noise.
- SKU concentration analysis: Pareto (top 20% SKUs by revenue), volatility index (coefficient of variation of weekly units).
- Channel conversion funnel analysis using available digital metrics.

2. Preliminary price elasticity estimation
- Model: log(quantity_t) = alpha + beta * log(price_t) + gamma * promo_t + SKU_FE + region_FE + epsilon_t
  - Interpret beta as elasticity. For aggregated data, run per category and pooled SKU models.
- Where price endogeneity is a concern (e.g., price changed in response to demand), use instrumental variables if a valid instrument is available (e.g., cost shock, supplier price index) — flagged as low confidence in rapid diagnostic.
- Output: elasticity point estimates with standard errors and an elasticity prior table for modelling phase.

3. Promo lift estimation
- Estimate immediate incremental units attributable to promotions using regression with promo dummies and lag terms to capture post‑promo effects.

4. Quick segmentation
- Segment customers into high‑LTV and price‑sensitive cohorts if customer data exists. If not, use proxy (repeat purchase rate, average basket value).

5. Out‑of‑stock detection
- Using sales velocity and inventory data (if available) to flag potential OOS confounders.

Deliverables from Phase 1 include the code notebook (R/Python), key SQL queries, and clean aggregated CSVs.

Example quick SQL extraction (pseudo)
- Sales by SKU/week:
  SELECT sku, DATE_TRUNC('week', order_date) AS week, SUM(units) as units, SUM(net_price * units) as revenue
  FROM orders
  WHERE order_date >= DATEADD(month, -12, CURRENT_DATE)
  GROUP BY sku, week
  ORDER BY sku, week;

---

# Scenario modelling (Phase 2) — sample scenarios and assumptions

We recommend modelling at least three scenarios to bound outcomes and stress test recommendations.

Scenario definitions (example)
- Scenario A: Base case — assume current competitor pricing stable, household income continues at recent levels. Model elasticities as estimated in Phase 1.
- Scenario B: Downside macro — further 3–5% drop in disposable income; forecasted demand contraction baseline −10% relative to Base.
- Scenario C: Competitor price war — competitors reduce prices by 8–12% in key SKUs; assume partial pass‑through and estimate share loss.

Sample tactic simulations (illustrative; values to be replaced with model outputs)
- Tactic 1: Introduce 20% smaller pack priced at −12% price per unit
  - Expected: +8–12% units among price‑sensitive cohort, net margin per unit change −3% (due to packaging cost).
- Tactic 2: Targeted 10% off for loyalty segment (digital coupon)
  - Expected: +10–15% incremental purchase rate in the targeted cohort; incremental promo cost vs incremental margin to be evaluated.
- Tactic 3: Cost‑to‑serve reduction of $0.50 per order via fulfillment optimization
  - Expected: margin improvement directly additive to pilot economics; allows for limited targeted discounting without net margin loss.

Sample scenario table (format)

| Scenario | Assumption | Revenue impact (12 weeks) | Margin impact | Confidence |
|---|---:|---:|---:|---|
| Base | No competitor reaction; elasticities per Phase 1 | −10% | −6% points | Medium |
| Downside | −5% disposable income | −18% | −9% points | Low |
| Price war | Competitors −10% price | −22% (market share loss) | −12% | Low |

Note: These are illustrative. Phase 2 will produce precise scenario tables per SKU and category.

---

# Pilot design & statistical considerations

For each prioritized tactic we provide a template pilot design with sample sizes and expected detection windows.

A/B test design (example)
- Objective: measure the incremental uplift in weekly units from a 10% targeted discount to loyalty customers.
- Population: loyalty cohort (n = 50,000 customers).
- Randomization: at customer level.
- Treatment: 10% digital coupon valid for 2 weeks.
- Control: no coupon.
- Outcome metric: weekly units per customer (primary), conversion rate (secondary).
- Power calculation (example):
  - Baseline weekly purchase rate = 1.2% for cohort.
  - Want to detect a 20% relative uplift (to 1.44%).
  - Required sample per arm ≈ 20,000 customers (assume alpha=0.05, power=0.8).
- KPI dashboard elements: cumulative lift, cumulative incremental units, ROI, redemption by channel.

Retail partner pilot (example)
- Objective: measure SKU sell‑through lift from introducing a new 20% smaller pack at price P.
- Design: 20 matched stores (10 treatment, 10 control), matched by historical sales and footfall.
- Duration: 6 weeks (includes 2‑week run‑in and 4‑week measurement).
- Outcome: units per store per week, sell‑through %, margin per store.
- Statistical notes: use difference‑in‑differences with store fixed effects controlling for seasonality.

Monitoring & governance
- Daily monitoring for OOS and supply constraints.
- Weekly steering calls with named owners; immediate pause rules for margin erosion beyond agreed guardrails.

---

# Deliverables & owners (expanded)

Explicit deliverables, owners, and timelines. Include escalation path and sign‑off roles.

Deliverables (with owners)
- 48–72h: Data request and ingestion checklist (Owner: Alex). Escalation: Sara if data delays >72h.
- 5 business days: One‑page diagnostic + appendix with top drivers and elasticity priors (Owner: Lisa; Support: Alex).
- 2–3 weeks: Scenario modelling deck (quantified demand/margin outcomes) (Owner: Lisa; Partner: Client R&D).
- Week 4: Prioritized recommendations + implementation playbook with owners & KPIs (Owner: Lisa & Sara).

Client responsibilities (to enable delivery)
- Primary analytics contact (name & contact details): to be confirmed by client within 24–48h.
- R&D contact (name & contact details): to be confirmed within 48h for feasibility inputs.
- Sign‑off owner for pilots: a single delegated decision maker for rapid approvals during pilot execution (name required within 48h).

Escalation path
- Day‑to‑day: Lisa (analytical questions) / Alex (data access technical issues).
- Programme sponsor: Sara (commercial/engagement sponsor).
- Executive escalation: Client leadership (TBD) if decisions require executive authority.

---

# Immediate asks (expanded checklist with templates)

To unblock work in the next 48 hours we need the following items from the client:

1. Confirm primary client contact for analytics & R&D and provide contact details (email & phone).
   - Provide name, role, email, phone, and best times for calls.

2. Share or provide access to SKU‑level sales + price + promo data (see Data needs #1–3).
   - Preferred: SFTP link or BI credentials; if not possible, schedule a 1‑hour screen‑share to run extractions.

3. Confirm whether any SKUs/categories are out‑of‑scope for analysis.
   - Provide list of SKUs or categories (and reason: regulatory, discontinued, contractual).

4. Confirm procurement or implementation constraints (e.g., maximum discounting allowed, regulatory limits).
   - Provide any internal discount ceilings, supplier minimum order quantities, permitted pack sizes, or packaging restrictions.

5. Identify a single sign‑off owner for fast decisions during the pilot (name & delegate).
   - Include backup delegate.

6. Share any customer segmentation definitions used internally (if available).
   - Attach segmentation mapping or definitions: e.g., "Loyal customers = 3+ purchases in last 12 months and >$200 spend".

Suggested email subject and brief template to request items (editable by client)
- Subject: Urgent: Data & contact requests to enable 5‑day rapid diagnostic for MultiLever
- Body (one paragraph): [Insert brief ask for direct attachments/credentials and confirm a 30‑minute kickoff to review access.]

---

# Risks & mitigations (detailed risk register)

We list major risks, likelihood, impact, and mitigation actions.

1. Risk: Low‑quality or delayed data
- Likelihood: High (initial assessment).
- Impact: High (delays diagnostic).
- Mitigation:
  - Focus Phase 1 on robust aggregates (weekly SKU x channel) which are easier to extract.
  - Provide a prioritized data request: minimum viable dataset to start.
  - Use plausible priors and document confidence bands.

2. Risk: Slow R&D feasibility approvals
- Likelihood: Medium.
- Impact: Medium–High for reformulation tactics.
- Mitigation:
  - Include fallback tactics that do not require R&D (pack sizing, promotions, channel shifts).
  - Ask R&D to commit to initial handwritten feasibility notes within 72 hours.

3. Risk: Price wars / competitor responses
- Likelihood: Medium.
- Impact: High (could drive margin erosion).
- Mitigation:
  - Model competitor reaction scenarios and build guardrails (e.g., maximum aggregate discounting exposure, duration limits).
  - Prioritize tactics less likely to trigger price war (targeted coupons, loyalty bundles).

4. Risk: Operational constraints for pilots (shelf space, packaging lead time)
- Likelihood: Medium.
- Impact: Medium.
- Mitigation:
  - Engage Ops/Procurement early and prioritize pilots that require minimal packaging changes (promos, shelf displays, digital bundling).
  - Use digital channels and direct fulfillment to test concepts.

5. Risk: Statistical insignificance due to small samples or short pilot windows
- Likelihood: Medium.
- Impact: Medium.
- Mitigation:
  - Conduct power calculations before pilot launch and adjust sample sizes or durations.
  - Use matched store tests and hierarchical pooling to increase power.

Risk matrix (summary table)

| Risk | Likelihood | Impact | Primary mitigation |
|---|---:|---:|---|
| Data delays/quality | High | High | Prioritized MVSD; data runbook |
| Slow R&D approvals | Medium | Medium | Fallback tactics; R&D 72h commitment |
| Competitor price war | Medium | High | Scenario modelling; discount guardrails |
| Operational pilot constraints | Medium | Medium | Early Ops alignment; digital pilots |
| Insufficient power | Medium | Medium | Power calc & hierarchical pooling |

---

# Success metrics & pilot KPIs (expanded)

Primary success metric (pilot)
- Change in weekly sales volume and revenue vs baseline for pilot SKUs (measured as incremental lift and expressed in absolute units and percentage).

Secondary metrics
- Margin impact: change in contribution margin and gross margin percentage for pilot SKUs.
- Promo ROI: incremental gross profit attributable to promo divided by promotional spend.
- Conversion lift by channel: percentage improvement in conversion post‑intervention for online channels.
- Retention: change in repeat purchase rate for loyalty/subscription pilots.
- Cost metrics: change in cost‑to‑serve or fulfillment cost per order.

Suggested KPI dashboard structure
- Top row: campaign status, start/end dates, pilot lead, decision date.
- Time series charts: weekly units vs baseline, revenue, margin.
- Table: SKU / store / cohort level summary with columns: baseline units/week, treatment units/week, incremental units, incremental revenue, incremental gross margin, ROI.
- Alerts: OOS rate > 5%, margin erosion beyond pre‑approved threshold, competitor price change > 5%.

Decision criteria for scaling
- Positive incremental units and positive incremental margin (or acceptable margin erosion within guardrails) for at least 4 consecutive weeks AND statistical significance per pre‑agreed alpha level OR clear commercial justification.

---

# Implementation plan & resource estimate (week‑by‑week)

Sample resource allocation and estimated time required for core activities. All hours are cumulative estimates for MultiLever engagement.

Week 0 (0–48h)
- Activities: kickoff, data access, scoping call.
- Resources: Lisa (2hrs), Alex (6hrs), Client analytics (2–4hrs).

Week 1 (Rapid diagnostic)
- Activities: data ingestion, cleaning, descriptive analytics, preliminary elasticity estimates, one‑page report.
- Resources: Lisa (30hrs), Alex (30hrs), Sara (3hrs client sync), Client analytics (assistance 10–15hrs).

Week 2 (Modeling start)
- Activities: feature engineering, hierarchical model development, R&D feasibility calls.
- Resources: Lisa (40hrs), Alex (20hrs), R&D (5–10hrs), Sara (5hrs).

Week 3 (Scenario simulations)
- Activities: run scenarios, refine ROI, design pilots.
- Resources: Lisa (30hrs), Alex (10hrs), Client Ops (5–10hrs).

Week 4 (Recommendations & playbook)
- Activities: finalize playbook, pilot sign‑offs, communications.
- Resources: Lisa (20hrs), Sara (10hrs), Client leadership (decision meeting 2–4hrs).

Estimated total consulting effort: ~200–250 person‑hours across team over 4 weeks (adjust based on data quality and scope).

Gantt (textual)
- Week 0: Kickoff, data access
- Week 1: Rapid diagnostic (deliverable at end of week)
- Week 2–3: Modelling & scenarios; R&D feasibility
- Week 4: Recommendations, playbook, pilot readiness

---

# Communication templates (samples)

1. Internal executive one‑page (to be delivered at end of Day 5)
- Title: Rapid Diagnostic — Top Findings & Immediate Actions
- Sections: Key findings (bulleted), Top 3 drivers per category, 3 immediate recommended pilots (with owner & time‑to‑implement), Data caveats and next steps.

2. Retail partner outreach (sample email)
- Subject: Proposal: 4‑week promotional test for [SKU] – MultiLever
- Body: Short pitch describing test, proposed timing, support offered, data sharing needs, and expected outcomes. Include pilot metrics, reporting cadence, and incentive sharing.

3. Pilot onboarding note (for internal teams)
- Contents: Objectives, start/end dates, roles & responsibilities, data collection plan, monitoring cadence, go/no‑go decision rules.

(Full editable templates will be included in Phase 3 deliverable.)

---

# Appendix A — Required file formats & access notes (detailed)

Preferred files and sample headers:

1) Transactional sales (CSV)
- Headers:
  - order_id, order_date, sku, units, price_per_unit, net_price_per_unit, promo_flag, promo_code, channel, store_id, region, customer_id_hashed, return_flag

2) Promo calendar (CSV)
- Headers:
  - sku, promo_start_date, promo_end_date, promo_type, promo_description, trade_spend, channel, distributor

3) SKU cost & BOM (XLSX)
- Sheets: sku_costs, bom
- sku_costs headers: sku, cogs_per_unit, packaging_cost, overhead_alloc, freight_alloc, cost_to_serve
- bom headers: sku, component_id, component_name, qty, unit_cost, supplier

4) Channel metrics (CSV)
- Headers:
  - date, channel, sessions, clicks, adds_to_cart, checkouts, orders, units, revenue

5) Competitor price snapshots (CSV)
- Headers:
  - date, competitor, competitor_sku, category, listed_price, promo_flag, source_url

Access notes
- Provide credentials for SFTP or secure cloud storage (S3 preferable).
- If data cannot leave client systems, designate a client analyst to run extraction queries; provide a 1‑hour window for screen share to expedite.

---

# Appendix B — Example elasticity summary table (format to be filled in Phase 1)

| Category | SKU | Baseline weekly units | Avg price | Elasticity (log‑log) | StdErr | Elasticity band | Notes |
|---|---|---:|---:|---:|---:|---|---|
| Food | SKU‑A | 1,200 | $2.50 | −1.20 | 0.15 | High sensitivity | Promo confounding flagged |
| Home appliances | SKU‑B | 120 | $89.00 | −0.30 | 0.12 | Low sensitivity | Consider financing offers |
| Toys | SKU‑C | 600 | $15.00 | −0.85 | 0.20 | Medium sensitivity | Seasonality strong |

This table will be produced as a CSV in the diagnostic appendix and used to prioritize pilots.

---

# Appendix C — R&D feasibility checklist (for quick triage)

For each SKU being considered for reformulation or pack resizing:
- Regulatory constraints: any ingredient or label restrictions?
- Supplier timeline: can suppliers deliver alternative ingredients within 4 weeks?
- Packaging availability: are alternate package sizes in stock or require tooling?
- Sensory risk: can sensory testing be done in <2 weeks for initial acceptability?
- Cost delta estimate: expected COGS change per unit and per 1,000 units.
- Pilot batch minimums and lead times.

Requested R&D response format (quick table)
- sku, proposed_change, feasibility (Y/N), estimated_cogs_delta, estimated_time_to_pilot, comments, contact_name

---

# Next steps (this week — expanded)

1. Lisa to circulate this expanded report to internal team (Sara, Alex, Oscar) and to client contact when approved. (Owner: Lisa; timeframe: today).
2. Alex to confirm data access ETA and start ingestion. (Owner: Alex; ETA: 24–48h).
3. Client to confirm primary analytics & R&D contacts and provide access per Data needs (Owner: Client; timeline: 24–48h).
4. Rapid diagnostic analytics to commence on receipt of sufficient data; deliverable due in 5 business days. (Owner: Lisa).

Contact list (internal)
- Lisa Carter — Lead Analyst / Report Author — email: lisa.carter@[company].com — mobile: +1 (xxx) xxx‑xxxx
- Alex [surname] — Data Lead — email: alex.[surname]@[company].com
- Sara [surname] — Engagement Sponsor/PM — email: sara.[surname]@[company].com
- Oscar [surname] — Ops Liaison — email: oscar.[surname]@[company].com

(Replace with client names and contacts once provided.)

---

Author: Lisa Carter
Version: 1.0 (expanded diagnostic & engagement plan)
Date: (draft)

If you approve this plan we will issue the 48–72h data request sheet and schedule the kickoff call. Once we have the minimum viable dataset we will begin the 5‑business‑day rapid diagnostic and deliver the one‑page executive summary with data appendix.