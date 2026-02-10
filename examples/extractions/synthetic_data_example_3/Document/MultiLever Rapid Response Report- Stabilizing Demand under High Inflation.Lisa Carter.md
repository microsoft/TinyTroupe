# MultiLever — Rapid Response Plan to Demand Contraction and Elevated Inflation
Prepared by: Wild Advice Partners  
Author / Analytics lead: Lisa Carter, Data Scientist  
Date: [Insert date]

Executive summary (expanded)
- Situation: MultiLever is facing a material demand contraction of ~20% in the last quarter coincident with sustained elevated inflation (~10%). The contraction is concentrated in food, home appliances, and toys, with discretionary categories showing higher elasticity and greater volume declines.
- Objective: Rapidly diagnose which SKUs, channels, and regions are driving the decline, quantify short-run elasticities and promotional effectiveness, and implement prioritized short- and medium-term interventions that preserve value and margins while addressing consumer price sensitivity.
- Recommended approach: Two parallel tracks running in concert:
  A. Rapid analytics-driven diagnostic (48–72 hours) to identify concentration of declines, compute elasticity estimates and promo uplift, and produce a prioritized SKU list (impact score = revenue exposure * elasticity) for targeted intervention.
  B. Operational + R&D/portfolio interventions (immediate to 12+ weeks) including short-term price-pack and promotional reallocations, inventory prioritization, targeted coupons and bundling, and medium-term cost-down, value-tier product development and supplier/packaging optimization.
- Immediate priorities (next 48–72 hours; see Owners and deliverables below):
  - Deliver a rapid descriptive diagnostic by SKU/channel/region to localize declines and margin pressure. Owner: Lisa — 48 hours.
  - Run high-level own-price elasticity and promotion-uplift analyses for prioritized SKUs/categories using weekly data over the last 12 months. Owner: Lisa — 72 hours.
  - Prepare targeted short-term interventions (price-pack changes, promo reallocation, channel prioritization) for high-impact SKUs. Owners: Lisa + Oscar — 72 hours.

Contents
1. Background & context
2. Primary findings and supporting evidence
3. Data & inputs required (detailed)
4. Rapid diagnostic plan (analytics) — expanded methodology
5. Deliverables and templates (what you will receive)
6. Short-term operational recommendations (0–8 weeks) — execution playbook
7. Medium-term R&D & portfolio recommendations (2–12 months) — roadmap & hypotheses
8. Measurement & KPIs (dashboards, cadence, experiments)
9. Implementation timeline, owners, and resource plan (detailed Gantt and dependencies)
10. Risks & mitigations (expanded risk matrix)
11. Supplier RFQ & repackaging checklist (template)
12. Communication & governance (approval gates, decision rubric)
13. Appendices
    A. Example prioritized SKU CSV layout and sample rows
    B. Elasticity estimation technical note (models, priors, equations)
    C. Promo uplift & cannibalization model technical note
    D. Sample SQL queries & data checks
    E. Experiment design sample (A/B test) and analysis plan

1. Background & context
- Macro environment: Inflation has remained elevated at approximately 10% y/y. Historically, inflation spikes of this magnitude reduce discretionary spending and compress demand for non-essential goods. Consumers respond through substitution to lower-priced alternatives, downtrading to smaller pack sizes or private label, and cutting discretionary items.
- MultiLever context: MultiLever has strong R&D capabilities and a broad SKU portfolio spanning staples and discretionary lines. Current constraints include limited visibility into certain retailer procurement terms/price floors, potential supply-side bottlenecks, and incomplete city-level budget/affordability segmentation.
- Strategic aim: Protect topline where possible, prevent unnecessary margin erosion, and design experiments/portfolio changes that can be scaled if successful, while minimizing risk to brand equity.

2. Primary findings and supporting evidence (expanded)
Summary of headline observations, their implications, and suggested first-order responses.

- Observation 1 — Macroe link: Inflation ~10% correlated with a ~20% demand decline last quarter.
  - Evidence: Preliminary top-line sales vs prior-year shows volume drop concentrated in Q3→Q4 correlating with CPI spikes and rising food price indices. Possible confounders: seasonality, channel shifts; diagnostic must control for week fixed effects.
  - Implication: Consumers are actively reducing spend; price sensitivity is elevated. Short-term actions should focus on preserving unit economics while supporting demand via targeted offers.

- Observation 2 — Category-level concentration: Food, home appliances, toys most affected; discretionary categories appear more elastic.
  - Evidence: Category-level revenue shares and decline rates indicate food and discretionary durable goods suffered steeper drops versus staples like hygiene products. Elasticities (to be formally estimated) are expected to be higher in toys and small appliances.
  - Implication: Prioritize interventions for high-revenue, high-elasticity SKUs using targeted price-pack and promo strategies; avoid across-the-board discounting.

- Observation 3 — Capabilities: Strong R&D but limited quick-turn options for some changes.
  - Evidence: Internal R&D notes show capacity for reformulation and pack redesign but lead times vary (some SKUs need 3–6 months).
  - Implication: Pair short-term operational tactics (price packs, coupons) with medium-term R&D (value tier, cost-downs).

- Observation 4 — Constraints: Possible supply-side constraints and limited visibility into retailer budget bands.
  - Evidence: Procurement has indicated supplier lead times have lengthened for some components; retailer contracts unknown.
  - Implication: Include local or short-lead suppliers in RFQ; secure retailer POC for promo and price discussions.

3. Data & inputs required (detailed)
To execute the rapid diagnostic and elasticity estimates accurately, provide the following datasets with the specified formats and quality expectations. Faster access yields faster and higher-quality outputs.

Core data (required immediately)
- Weekly_sales_by_SKU.csv
  - Required fields: date (ISO week or YYYY-MM-DD week start), SKU_ID, SKU_Name, channel (retail/ecommerce/wholesale), region (city/area), units_sold, revenue, returns_units, returns_value.
  - Time span: last 52 weeks (rolling 12 months). Preferred frequency: weekly. Acceptable alternative: daily aggregated to week.
- SKU_price_catalog.csv
  - Required: SKU_ID, date_effective, list_price, net_price (to retailer / consumer price), currency, pack_size (qty/unit), unit_price_per_base_unit, price_type (MAP, regular, promotional).
- Promotions_history.csv
  - Required: SKU_ID, promo_id, promo_type (percent_off, fixed_amount_off, bogo, coupon, trade_fund), start_date, end_date, promo_mechanic_details, channel_applicability, trade_fund_amount, retailer_contribution_flag, redemption_rate (if coupons).
- Channel_distribution.csv
  - Required: SKU_ID, distribution_channel, store_id (if available), outlet_type, geography (region/city), store_chain (retailer), share_of_sales_by_channel, on_shelf_availability (if available).
- SKU_costs_and_margins.csv
  - Required: SKU_ID, COGS_per_unit, transport_cost_per_unit, historical_margin_pct, typical trade_fund_allocation_pct, gross_margin_history (weekly or monthly if available).
- Inventory_and_leadtimes.csv
  - Required: SKU_ID, warehouse_id, inventory_on_hand_units, weeks_of_supply, supplier_lead_time_days, supplier_contact, reorder_point.
- Marketing_campaigns.csv
  - Required: campaign_id, channel, start_date, end_date, spend, creative_id, target_segment, SKUs_affected, attribution_method.
- R&D_capabilities_note (document or spreadsheet)
  - Content: For each SKU (or product family) list feasible changes (reformulation, ingredient substitutions, pack-size changes), expected time-to-implement, regulatory/labeling implications, estimated cost impact per unit, minimum viable order quantities for repackaging.
- Retailer_contracts (document repository)
  - Required: Any retailer-specific contract terms, MAP policies, mandated minimum price guidelines, promotional constraints, invoicing/procurement format.
- Optional but highly useful:
  - Loyalty_program_data.csv (customer_id masked, cohort, redemption, CLTV estimates)
  - Competitor_price_index.csv (competitor SKU mapping and weekly prices)
  - Consumer_panel_survey (if available)

Data quality expectations and format
- Prefer S3 or secure FTP. Use folder structure described in Appendix D.
- Provide a data dictionary for each CSV and examples of typical rows.
- If fields are missing, flag them and provide a fallback mapping table (e.g., SKU grouping to category).

4. Rapid diagnostic plan (analytics) — expanded methodology
Objective: Deliver actionable diagnostic to identify high-leverage intervention points. The diagnostic has three analytic pillars: Descriptive, Elasticity & Promo Models, and Segmentation & Experiment design.

A. Descriptive analytics (48 hours)
Goal: Provide a crisp portrait of where revenue and volume losses are concentrated by SKU / category / channel / region.

Key outputs:
- Time-series plots (weekly) of revenue and volume by SKU and category with year-on-year % change. Callouts for SKUs with > 10% absolute drop in revenue > 1 month sustained.
- Waterfall of topline decline attribution: percent contribution of each category/region/SKU to overall decline.
- Margin analysis: correlation of margin compression with volume decline; identify margin-at-risk SKUs where margin decline > x% points.
- Concentration table: top 50 SKUs by revenue exposure, showing their share of total revenue and percent decline.

Methodology / Steps:
1. Data ingestion and validation (Lisa): schema checks, missing values, duplicates; produce data quality log.
2. Time normalization: align weeks across datasets with ISO-week.
3. Baseline vs current: compute 52-week moving averages and yoy comparisons; highlight anomalies and potential seasonality.
4. Visualization: summary deck with 10-15 slides and CSVs with prioritized SKU lists.

B. Elasticity estimates (72 hours)
Goal: Estimate short-run own-price elasticity and promo-lift for prioritized SKUs or categories.

Models:
- Primary model: Panel OLS with SKU fixed effects and week fixed effects:
  log(Q_it) = alpha_i + beta * log(P_it) + gamma * Promo_it + delta * X_it + weekFE_t + epsilon_it
  where Q_it = quantity of SKU i in week t, P_it = consumer price, Promo_it = promo indicator(s), X_it = marketing spend and other controls (seasonal dummies, holidays).
- If price endogeneity suspected (e.g., price changes targeted to demand), instrument price with lagged cost or competitor price index where available (2SLS specification).
- For sparse SKUs: Hierarchical (multilevel) model pooling across SKUs within a category:
  beta_i ~ N(mu_beta_category, sigma_beta_category^2)
  This borrows strength from category-level data to estimate SKU elasticities.

Implementation details:
- Use log-log specification to interpret beta as elasticity.
- Include promo dummies and promo-depth variables (percent_off, trade_fund) to separate price vs promotional drivers.
- Where limited data: compute category-level elasticities and apply to SKUs based on price position and pack size.

Quality checks:
- Check for implausible elasticities (e.g., > -20 or > 0); flag for manual review.
- Report standard errors and confidence intervals; provide scenario elasticity ranges (conservative, base, aggressive).

C. Promo effectiveness and cannibalization (72 hours)
Goal: Estimate incremental uplift from promotions and identify cannibalization across SKUs and channels.

Approach:
- Difference-in-differences where promotional windows can be compared vs similar weeks without promo controlling for seasonality and store effects.
- When store-level data available: use synthetic control / matched stores to estimate lift.
- Estimate intra-brand cannibalization by comparing uplift on promoted SKUs and effect on non-promoted SKUs in the same portfolio: cross-elasticities matrix where feasible.
- Compute promo ROI = incremental_revenue / promo_spend (trade_fund + retailer funds + marketing costs).

Deliverables for analytics track (48–72h)
- Diagnostic slide deck (PDF/PPT): 10–20 slides with executive summary, key charts, prioritized SKU list, recommended short-term interventions.
- Prioritized_SKU_list.csv: columns: SKU_ID, category, baseline_weekly_revenue, percent_decline, estimated_elasticity, impact_score (revenue_exposure * |elasticity|), recommended_action (pack_size/promo/bundle), owner.
- Analytics notebook / script (R/Python) and model outputs (coefficients, standard errors).
- Data quality log and assumptions list.

5. Deliverables and templates (what you will receive)
- 48-hour deliverable (by end of Day 2)
  - Diagnostic deck (PDF/PPT) with top-line findings.
  - CSV: Prioritized SKU list (top N SKUs by impact, default N=50 but configurable).
  - Data intake checklist and mapping file.
- 72-hour deliverable (by end of Day 3)
  - Elasticity estimation outputs and model diagnostics.
  - Promo uplift estimates and recommended top-10 SKU interventions (price-pack/promo/channel).
  - Short-term tactical plan: proposed coupons, pack-size candidates, and promo reallocation schedule.
- 2-week deliverable
  - RFQs to suppliers and repackaging supplier shortlist.
  - Pilot designs and testing calendar for promos/pack-size pilots.
- 2–8 week deliverables
  - Pilot execution reports, weekly KPIs.
  - Iteration plan and scale recommendation.

Templates included:
- Prioritized SKU CSV template (see Appendix A).
- RFQ template and supplier evaluation matrix.
- Promo ROI template (incremental revenue, costs, net margin impact).
- Experiment analysis plan template.

6. Short-term operational recommendations (0–8 weeks) — execution playbook
Principles
- Prioritize low-friction, low-risk changes that can be reversed.
- Avoid broad across-the-board price cuts.
- Target promotions to cohorts or channels with higher measured elasticity and better ROI.
- Protect brand equity—avoid degrading product quality or misleading communications.

Tactics (detailed with decision rules, owners, and timeline)

1. Targeted price-pack and pack-size strategy
- Tactic: Introduce smaller (value) pack sizes for price-sensitive SKUs and offer multi-pack “value packs” for households wanting savings per purchase.
- Decision rule: For SKUs with elasticity magnitude > 0.8 and margin buffer > 15% after pack-costs, pilot smaller pack sizes where unit economics maintain at least 80% of baseline margin.
- Owner: Oscar + R&D + Procurement.
- Steps:
  a. Identify candidate SKUs (from prioritized SKU list).
  b. R&D feasibility check (lead time, packaging, regulatory).
  c. Minimal pack-size prototypes (consult BOM & cost impact).
  d. Local supplier RFQ for repackaging (short-lead capacity prioritized).
  e. Launch pilot in 1–3 regions or selected retailers/channels for 4–8 weeks.
- Example: A snack SKU priced at $2.00 for 150g could be repacked into a 100g pack with headline price of $1.49, preserving per-gram margin while lowering headline price; measure sell-through and margin.

2. Reallocate promotional spend to high-ROI formats and channels
- Tactic: Move promotional funds away from blanket discounts to targeted digital coupons, loyalty offers, and retailer-specific high-ROI mechanics.
- Decision rule: Only fund promotions with projected promo ROI > 2x and limited cannibalization (<20% displacement from other SKUs).
- Owner: Marketing lead, advised by Lisa analytics.
- Steps:
  a. Recalculate current promo ROI per SKU and channel.
  b. Reassign trade funds to top decile of SKUs by expected incremental volume and margin preservation.
  c. Reduce or pause low-ROI promotions; reinvest into digital targeted coupons and e-com support (free shipping thresholds, bundling).
- Example channels: loyalty in eCommerce for repeat shoppers and targeted emails containing unique coupon codes.

3. Prioritize essential SKUs in distribution and ensure stock for fast-moving items
- Tactic: Use weeks_of_supply and historical velocity to prioritize replenishment for SKUs with low elasticity (inelastic) and high revenue exposure.
- Decision rule: SKUs in top 20 by impact score and with >4 weeks of sell-through remaining get priority allocation.
- Owner: Ops / Supply Chain.
- Steps:
  a. Weekly re-order plan aligned with prioritized SKU list.
  b. Re-route shipments to high-performing regions; consider temporary increases in local safety stock.
  c. If supplier lead times block repackaging, consider third-party co-packer options.

4. Pilot targeted price promos or coupons to segmented cohorts rather than blanket discounts
- Tactic: Use loyalty and digital channels to deploy targeted coupons tied to consumer segments (price-sensitive cohorts identified by RFM or loyalty behavior).
- Decision rule: Deploy to segments where predicted incremental lift > threshold; cap total coupon redemptions to defined budget.
- Owner: eCom/Promo teams.
- Steps:
  a. Select 3–5 SKUs to pilot targeted coupons.
  b. Define control groups and lift measurement windows (4–8 weeks).
  c. Monitor redemption rates, incremental sales, cannibalization, and net margin.

5. Bundling / cross-sell with staples
- Tactic: Bundle discretionary SKU with staple SKU at modest incremental price to increase perceived value.
- Decision rule: Ensure bundle margin > baseline weighted margins and that cannibalization of full-price SKU is limited.
- Owner: Category managers.
- Steps:
  a. Identify logical bundle pairs (e.g., toy + snack; small appliance + consumable).
  b. Launch time-limited bundles on e-commerce platforms and selected retailers.
  c. Track bundle lift, attach rate, and abandonment.

Operational playbook checklist (for each recommended action)
- Feasibility check (R&D/packaging)
- Margin re-calculation and approval (Finance)
- Supplier quotes and lead time confirmation (Procurement)
- POS / retail compliance check (Commercial)
- Pilot design (Marketing + Analytics)
- Launch and weekly monitoring (Ops + Analytics)

7. Pricing governance & decision rules
- All price changes or trade fund reallocations above threshold X (e.g., $50K) require Finance sign-off.
- Temporary price packs priced below MAP require written retailer permission.
- Trades: Redirect trade funds toward high-ROI targeted promotions; require ROI forecast and ex-post reconciliation.

7. Medium-term R&D & portfolio recommendations (2–12 months)
Principles
- Build a lower-priced, value-focused tier while maintaining core brand equity.
- Reduce COGS where feasible through materials optimization, pack redesign, and alternative sourcing.
- Use experiments to validate consumer acceptance before large-scale reformulation.

Recommendations (detailed)

1. Fast-track reformulation or cost-down initiatives (2–12 months)
- Action: For SKUs where ingredient or packaging cost reduction is feasible without perceived quality loss, initiate cost-down projects.
- Owner: R&D + Procurement.
- Steps:
  a. Shortlist SKUs with highest margin sensitivity and where COGS reduction > 5% is feasible.
  b. Rapid lab testing for reformulation alternatives with blind consumer panels (if necessary).
  c. Regulatory review and labeling updates.
  d. Pilot production runs, monitor quality metrics.
- Expected outcomes: 3–7% unit cost reduction per SKU on pilot list; scale targets defined per SKU.

2. Develop a 'value tier' product line
- Action: Create simplified features, reduced pack sizes, or base-ingredient variants under a sub-brand or clearly labeled value tier to preserve premium brand architecture.
- Owner: R&D + Brand + Legal.
- Steps:
  a. Brand architecture mapping to determine naming conventions and packaging differentiators.
  b. Prototype packaging that reduces material use or simplifies design.
  c. Test in selected markets; measure adoption and cannibalization.
- Decision rule: Launch value-tier broadly only when net contribution margin is acceptable and cannibalization < threshold.

3. Pack-material optimization and alternative suppliers
- Action: Review bill-of-materials and switch to cost-effective materials where feasible; qualify alternate suppliers including local co-packers.
- Owner: Procurement + Oscar (BOM design).
- Steps:
  a. BOM review for top 30 SKUs by impact score.
  b. Supplier RFQ and cost-savings analysis.
  c. Pilot few SKUs to validate quality & line compatibility.

4. Behavioral pricing experiments: price-anchoring and decoy SKUs
- Action: Introduce decoy SKUs or price anchors that steer consumers toward mid-tier options.
- Owner: Marketing + Analytics.
- Steps:
  a. Design decoy products and anchor price points.
  b. Run randomized tests in eCommerce and select stores.
  c. Measure shifts in SKU mix and average basket value.

8. Measurement & KPIs (dashboards, cadence, experiments)
Short-run KPIs (weekly cadence)
- Weekly revenue and volume by prioritized SKU.
- Estimated price elasticity (weekly rolling update for top SKUs).
- Promo ROI per SKU and channel (incremental revenue / promo spend).
- Promo cannibalization (%) (promotion lift less net portfolio change).
- Weeks of supply and out-of-stock events for prioritized SKUs.
- Unit margin and gross margin trend by SKU.

Medium-run KPIs (monthly / quarterly)
- Margin by SKU and portfolio.
- Sell-through rates for new pack sizes and value-tier SKU adoption.
- Net revenue impact of portfolio changes (2–3 month lag).
- Customer retention and segment adoption (for value-tier).

Experimentation KPIs (for each pilot)
- Primary metric: Incremental weekly revenue (vs control) within 4–8 week measurement window.
- Secondary metrics: Promotion redemption rate, gross margin impact, cannibalization rate, CLTV impact (if loyalty tracked), customer satisfaction/returns.
- Analysis approach: Intent-to-treat and per-protocol lift estimates; Bayesian sequential monitoring recommended for rapid decision-making.

Dashboard & reporting cadence
- Daily ingestion logging and basic health checks.
- Weekly tactical dashboard for Ops, Marketing, Finance (KPIs + callouts).
- Bi-weekly steering update deck for executive approvals and decision gates.

9. Implementation timeline, owners, and resource plan (detailed)
High-level timeline (weeks)

Week 0–1 (0–72 hours)
- Confirm data transfer and client POC. Owner: Lisa.
- Deliver descriptive diagnostic and prioritized SKU list. Owner: Lisa.
- Elasticity estimation and promo uplift initial runs. Owner: Lisa.
- Prepare short-term intervention proposals. Owners: Lisa + Oscar.

Week 1–2
- RFQs to packaging suppliers and local co-packers. Owner: Procurement + Oscar.
- Finalize pilots for 3–10 SKUs (promo, pack-size, bundling). Owners: Marketing, Ops, Lisa.
- Set up experiment tracking and analytics pipelines. Owner: Lisa/Analytics.

Weeks 2–8
- Execute pilots. Owners: Marketing, Ops, R&D (for pack changes).
- Weekly monitoring and iteration. Owner: Lisa.
- Procurement negotiate lead times and pilot runs.

Weeks 8–12+
- Scale successful pilots across regions and channels. Owners: Product, R&D, Procurement.
- Begin medium-term reformulation and supplier qualification projects. Owners: R&D, Procurement.

Detailed Gantt-style table (example)

| Task | Week 0 | Week 1 | Week 2 | Week 3 | Week 4 | Week 5 | Week 6 | Week 7 | Week 8–12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Data transfer & validation | X |  |  |  |  |  |  |  |  |
| Descriptive diagnostic | X | X |  |  |  |  |  |  |  |
| Elasticity & promo models |  | X | X |  |  |  |  |  |  |
| Prioritized SKU list |  | X |  |  |  |  |  |  |  |
| Supplier RFQs |  | X | X |  |  |  |  |  |  |
| Pilot design |  | X | X |  |  |  |  |  |  |
| Run pilots |  |  | X | X | X | X |  |  |  |
| Weekly pilot reporting |  |  | X | X | X | X | X | X |  |
| Scale-up plan |  |  |  |  |  | X | X | X | X |
| R&D reformulation projects |  |  |  |  |  |  |  | X | X+ |

Resource & budget estimates (indicative)
- Analytics & diagnostic (Wild Advice): 0.5 FTE analytics lead + 0.5 FTE data engineer for 2 weeks (includes model runs and decks). Estimated fee: [TBD per contract].
- Pilot marketing spend: depends on promo scale; recommend initial test budget $25–100K for targeted coupons and digital promos.
- Packaging RFQ & co-packer pilot cost: One-time setup + unit costs; estimate $5–20K depending on tooling and run sizes.
- R&D reformulation: prototyping and regulatory testing per SKU: $10–50K per SKU.

10. Risks & mitigations (expanded risk matrix)
Summary table

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---:|---:|---|---|
| Data delays / poor quality | High | High | Provide fallback top-down analysis, request minimal required datasets first, provide imputation & conservative scenario ranges. | Lisa |
| Price endogeneity bias in elasticity | Medium | High | Use IV approach (costs or competitor price) and hierarchical pooling; report ranges & robustness checks. | Lisa |
| Supplier lead time prevents repackaging | High | Medium | Include local/short-lead suppliers in RFQ; consider temporary co-packers; use promo/coupon alternatives. | Oscar + Procurement |
| Poor promo targeting leads to margin erosion | Medium | High | Require ROI forecasts and Finance approval; restrict blanket discounts; pilot targeted coupons initially. | Finance + Marketing |
| Brand equity damage from low-quality value-tier | Low | High | Rigorous consumer testing; clear sub-brand differentiation; limit initial rollouts. | Brand + R&D |
| Cannibalization within portfolio | Medium | Medium | Estimate cross-elasticities and monitor lift metrics; limit scale until cannibalization acceptable. | Lisa + Marketing |

11. Supplier RFQ & repackaging checklist (template)
Key items to include in RFQ:
- SKU_ID and description for repackaging.
- Requested pack sizes and sample quantities.
- Minimum order quantities and lead times.
- Tooling and setup fees (if any).
- Quality control processes and acceptance criteria.
- Regulatory compliance statements.
- Pricing per unit at pilot and scale volumes.
- Capacity to produce short runs and scale-up timelines.

Supplier evaluation matrix (example)
- Cost per unit (30%)
- Lead time (25%)
- Quality & compliance (20%)
- Local presence (10%)
- Flexibility for design changes (10%)
Score each supplier 1–5 and compute weighted score.

12. Communication & governance (approval gates, decision rubric)
Steering committee composition (recommended)
- Commercial Lead (MultiLever) — approvals on retail engagements
- Finance Lead (MultiLever) — approves margin impacts and trade-fund reallocations
- Analytics (Lisa) — provides diagnostic and model outputs
- R&D Lead — signs off on reformulation and packaging feasibility
- Procurement — supplier negotiations
- Marketing Lead — approves promo creatives and pilot launches

Decision gates
- Gate A (post-diagnostic): Approve top-10 SKUs for immediate pilot testing. Requires sign-off from Commercial and Finance within 48 hours.
- Gate B (pilot results): After 4–8 week pilot, approve scale-up based on pre-specified success criteria (min incremental revenue and min margin threshold).
- Gate C (medium-term): Approve reformulation & national roll-out if pilot shows acceptable economic and brand metrics.

13. Appendices

Appendix A — Example prioritized SKU CSV layout and sample rows
Columns:
- SKU_ID, SKU_Name, Category, Baseline_weekly_revenue, Percent_decline_YoY, Estimated_elasticity, Elasticity_confidence_interval, Revenue_exposure_pct, Impact_score, Recommended_action, Owner, Notes

Sample rows (illustrative)
- SKU_ID: ML-SK-0001 | Name: "Everyday Flour 1kg" | Category: Food | Baseline_weekly_revenue: 45,000 | Percent_decline_YoY: -22% | Estimated_elasticity: -0.45 (CI: -0.35 to -0.55) | Revenue_exposure: 3.2% | Impact_score: 144 | Recommended_action: Protect distribution; targeted coupon to low-income cohorts | Owner: Marketing

Appendix B — Elasticity estimation technical note (summary)
- Preferred specification: log-log panel with SKU and week fixed effects. Add promo depth, marketing spend controls, and store or channel fixed effects when available.
- Identification and endogeneity: Price may be endogenous when used tactically. Use instruments:
  - 2SLS instrument candidate 1: Lagged input cost / COGS per SKU (if weekly).
  - 2SLS instrument candidate 2: Competitor price index (where mapping exists).
- Hierarchical Bayesian approach (when SKU-level N sparse):
  - Model: log(Q_it) ~ Normal(alpha_i + beta_i * log(P_it) + gamma*Promo_it + weekFE_t, sigma)
  - Priors: beta_i ~ Normal(mu_beta_category, tau_beta)
  - Implementation: Stan or PyMC3; yields posterior distributions and predictive intervals.

Appendix C — Promo uplift & cannibalization technical note
- Uplift estimate: For promo windows, estimate counterfactual baseline with regression-adjusted approach controlling for time, store, and other marketing activity.
- Cannibalization: Evaluate cross-SKU effects within same brand; compute net incremental revenue = uplift_on_promoted - lost_revenue_on_other_SKUs.
- Promo ROI formula:
  - Incremental gross profit = incremental_units * (unit_price - COGS) - promo_costs
  - Promo ROI = incremental_revenue / promo_costs (or incremental_profit / promo_costs depending on preference).

Appendix D — Sample SQL queries & data checks
- Example: Compute weekly revenue by SKU
  SELECT sku_id, date_trunc('week', sales_date) AS week_start,
         SUM(units) AS units_sold, SUM(revenue) AS revenue
  FROM sales
  WHERE sales_date BETWEEN '{{start_date}}' AND '{{end_date}}'
  GROUP BY sku_id, week_start;

- Example: Basic data quality checks
  - Check for missing price data join:
    SELECT s.sku_id, COUNT(*) AS missing_price_weeks
    FROM sales s
    LEFT JOIN price p ON s.sku_id = p.sku_id AND s.week_start BETWEEN p.start_date AND p.end_date
    WHERE p.unit_price IS NULL
    GROUP BY s.sku_id
    ORDER BY missing_price_weeks DESC;

Appendix E — Experiment design sample (A/B test) and analysis plan
- Example pilot: Targeted coupon for 5 SKUs via loyalty channel
  - Randomize at customer level into treatment (coupon) vs control.
  - Pre-specify primary outcome: incremental units sold per customer over 4-week window.
  - Secondary outcomes: average order value, repeat purchase within 30 days, redemption rate, margin impact.
  - Analysis: Difference-in-means with ANCOVA controlling for pre-period spend; estimate uplift and 95% CI; perform subgroup analysis by cohort (value shoppers vs premium).

Immediate asks / Next steps (action items to initiate work — please action now)
1. Provide the datasets listed in Section 3 into a secure shared folder (preferred: S3 with read-only bucket for Wild Advice; SFTP acceptable). Please include data dictionary and sample rows.
2. Confirm a single MultiLever point-of-contact for approvals and a retail/commercial contact for promo negotiation.
3. Nominate a Finance lead to approve margin/trade-fund reallocations (or confirm Lisa may run provisional modeling for up to 72 hours).
4. Provide R&D capability note and any retailer MAP or contract constraints available.
5. Confirm access timeline and preferred communication cadence for the first 72 hours.

Contacts (Wild Advice Partners recommended owners)
- Analytics lead / Report author: Lisa Carter (Wild Advice Partners) — analytics, elasticity estimation, diagnostics — lisa@wildadvice.example / +44 7700 000001
- Design / pack & BOM: Oscar Martins (Wild Advice Partners) — thumbnails, BOMs, supplier-neutral specs — oscar@wildadvice.example / +44 7700 000002
- Vendor outreach / procurement liaison: Marcos Almeida (Wild Advice Partners) — vendor quotes and local capacity — marcos@wildadvice.example / +44 7700 000003
- Client approvals / data owner: MultiLever (please nominate)
- Finance owner: MultiLever Finance Lead (TBD) / Wild Advice provisional cover (Lisa up to 72h)

Acceptance criteria for rapid diagnostic deliverable
- Diagnostic deck with clear top-10 actionable SKUs and recommended interventions.
- Prioritized SKU CSV with elasticity estimates and impact scores for top N SKUs.
- Data ingestion completed and documented with data quality log.
- Agreement on pilot SKUs and budget for initial promotions.

Conclusion (call to action)
We are ready to commence immediately. If you can confirm data access and a client point-of-contact by [insert target time], Wild Advice Partners will prioritize the rapid SKU prioritization and elasticity estimates with an objective to present the 48–72 hour diagnostic and recommended short-term interventions. The combined analytics and operational approach is designed to be surgical—targeting where demand and margin risk are highest—while preserving long-term brand equity.

— Lisa Carter  
Data Scientist, Wild Advice Partners

(End of document)