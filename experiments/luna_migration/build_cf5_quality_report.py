"""Publishable comparison separating complete simulations, postprocessing repair and empirical validity."""

import html
import json
import statistics
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def table(headers, rows):
    return "<table><thead><tr>" + "".join(
        f"<th>{html.escape(str(value))}</th>" for value in headers
    ) + "</tr></thead><tbody>" + "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in row) + "</tr>"
        for row in rows
    ) + "</tbody></table>"


lineage = load("cf5-validation-lineage.json")
assert lineage["current_source_core"]["status"] == "Passed"
assert lineage["postprocessing_replay"]["public_responses_semantically_unchanged"] == 100
scope_path = ROOT / "population-scope-validation.json"
scope = load(scope_path.name) if scope_path.exists() else None
if scope:
    assert scope["status"] == "Passed"
latest_core = scope["current_source_core"] if scope else lineage["current_source_core"]
latest_hash = scope["current_library_sha256"] if scope else lineage["current_library_sha256"]
integration_path = ROOT / "sampling-coverage-integration-validation.json"
integration = load(integration_path.name) if integration_path.exists() else None
if integration:
    assert integration["status"] == "passed", "Do not publish an unvalidated integration."
fresh_plan_path = ROOT / "integrated-coverage-plan" / "structural-audit.json"
fresh_plan = load(str(fresh_plan_path.relative_to(ROOT))) if fresh_plan_path.exists() else None
if fresh_plan:
    assert fresh_plan["request_and_exact_reconstruction"] == "passed"
    fresh_semantics = load(r"integrated-coverage-plan\semantic-review.json")
    fresh_receipt = load(r"integrated-coverage-plan\receipt.json")
budget_reviews = []
for folder in ["demographic-coverage-budget", "demographic-coverage-budget-r2"]:
    path = ROOT / folder / "review.json"
    if path.exists():
        budget_reviews.append(load(str(path.relative_to(ROOT))))
cf6_path = ROOT / "cf6-gaz-manual-quality-review.json"
cf6 = load(cf6_path.name) if cf6_path.exists() else None
final_path = ROOT / "comprehension-options-validation.json"
final_stage = load(final_path.name) if final_path.exists() else None
if final_stage:
    assert final_stage["status"] == "passed", "Do not publish an unvalidated final stage."
marginal_path = ROOT / "marginal-choices-validation.json"
marginal_stage = load(marginal_path.name) if marginal_path.exists() else None
if marginal_stage:
    assert marginal_stage["status"] == "passed", "Do not publish an unvalidated marginal stage."
audit = load("cf5-execution-audit.json")
assert len(audit["runs"]) == 3 and all(r["execution_audit_passed"] for r in audit["runs"])
metrics = {Path(row["folder"]).name: row for row in load("cf5-current-metrics.json")}
review = load("cf5-manual-quality-review.json")
usage = load("cf5-returned-usage-audit.json")
frame = load("gazpacho-human-control-frame.json")
gaz = review["gazpacho"]["counts"]
scores = [value for value in range(1, 6) for _ in range(gaz[str(value)])]
prior_gaz = {"1": 3, "2": 39, "3": 5, "4": 0, "5": 0, "N/A": 3}
rows = [
    ["Investment Firm", "Complete: 20 steps / 3 participants",
     "Better factual retention; mixed conversation",
     "Final customer summary retains earlier financial facts. 23 public utterances versus CF4's 11; early repetition and deferred valuation remain.",
     usage["runs"]["inv"]["usd"]],
    ["Children's storytelling study 2", "Complete: 50 parents",
     "Better than original unanimity; narrower than CF4",
     "First choices A0 / B31 / C10 / D0 / E9. Earlier repaired run: A1 / B20 / C16 / D1 / E12. Cost/privacy/screen-time themes remain repetitive.",
     usage["runs"]["kids"]["usd"]],
    ["Gazpacho study 5, behavior correction", "Complete: 50 people; 47 ratings",
     "Empirical compression unresolved",
     "1:4 / 2:37 / 3:6 / 4:0 / 5:0; three genuine infant nonanswers. Same mean as CF4, and still no high-end ratings.",
     usage["runs"]["gaz"]["usd"]],
]
rollout_table = table(["Notebook", "Execution", "Quality", "Findings", "Returned-usage USD"], rows)
distribution_table = table(
    ["Rating", "Prior Luna CF4", "Current Luna CF5", "Human control"],
    [[key, prior_gaz[key], gaz[key], frame["vote_counts"].get(key, 0) if key != "N/A" else 0]
     for key in ["1", "2", "3", "4", "5", "N/A"]],
)
full_cost = sum(Decimal(usage["runs"][name]["usd"]) for name in ["inv", "kids", "gaz"])
extraction_trials_cost = sum(
    Decimal(row["usd"]) for row in usage["extraction_prompt_trials"].values()
)
example_path = ROOT / "generator-example-ablation-review.json"
example_review = load(example_path.name) if example_path.exists() else None
if example_review:
    example_audit = load(example_review["protocol_audit"])
    assert example_audit["protocol_status"] == "Passed"
    assert not example_review["production_changed"]
coverage_path = ROOT / "realized-behavior-coverage-review.json"
coverage_review = load(coverage_path.name) if coverage_path.exists() else None
if coverage_review:
    assert not coverage_review["production_changed"]
    assert load(coverage_review["protocol_audit"])["protocol_status"] == "passed"
cost_table = table(["Scope", "Returned-usage estimate USD"], [
    ["Three complete CF5 notebooks", str(full_cost)],
    ["21 bounded gazpacho prompt/transport/effort conditions", "0.659406800"],
    ["Two exact Investment retention replays", "0.005904725"],
    ["13 responses across three extraction-prompt candidates", str(extraction_trials_cost)],
    ["100 real-history extractions with final production prompt", usage["runs"]["reextraction"]["usd"]],
] + ([
    ["Three population-scope generator replays",
     scope["returned_usage_estimates"]["population-scope-trial"]["usd"]],
    ["Six frozen actor replays across two population-scope conditions",
     scope["returned_usage_estimates"]["population-scope-actor-replays"]["usd"]],
    ["Two assertion-development diagnostics",
     scope["returned_usage_estimates"]["population-scope-test-diagnostics"]["usd"]],
] if scope else []) + ([
    ["Example-ablation screen with production JSON mode: 12 responses",
     example_review["corrected_screen"]["returned_usage_usd"]],
    ["Earlier out-of-contract example screen: 11 responses, including malformed JSON",
     example_review["earlier_harness_mismatch"]["returned_usage_usd"]],
] if example_review else []) + (
    [[row["scope"], row["usd"]] for row in coverage_review["costs"]]
    if coverage_review else []
) + ([
    ["Independent fresh integrated production plan: one returned response",
     fresh_receipt["returned_usage_estimate"]["usd"]],
] if fresh_plan else []))
if budget_reviews:
    cost_table += table(["Additional diagnostic", "Returned-usage estimate USD"], [
        [f"Demographic-budget prompt revision {index}", review["returned_usage_usd"]]
        for index, review in enumerate(budget_reviews, 1)
    ])
if cf6:
    cost_table += table(["Fresh full run", "Returned-usage estimate USD"], [
        ["CF6 gazpacho 5, independent cohort; 50 people", cf6["returned_usage_usd"]],
    ])
if final_stage:
    comprehension_receipt = load(r"cf6-comprehension-screen\receipt.json")
    coherent_audit = load(r"cf6-coherent-dimensions\audit.json")
    coherent_receipt = load(r"cf6-coherent-dimensions\receipt.json")
    assert coherent_audit["status"] == "passed"
    cost_table += table(["Bounded final diagnostic", "Returned-usage estimate USD"], [
        ["Six frozen biographies through action correction and extraction",
         comprehension_receipt["returned_usage_estimate"]["usd"]],
        ["Original full-population dimension request with coherent options",
         coherent_receipt["returned_usage_estimate"]["usd"]],
    ])
if marginal_stage:
    cost_table += table(["Structural marginal diagnostic", "Returned-usage estimate USD"], [
        ["Revision 3: weighted alternatives, compatibility follow-up withheld",
         load(r"demographic-coverage-budget-r3\review.json")["returned_usage_usd"]],
        ["Revision 4: weighted alternatives plus qualification compatibility",
         load(r"demographic-coverage-budget-r4\review.json")["returned_usage_usd"]],
    ])
scope_repair = """
<li>Individual biography generation now separates population-planning instructions from
personal characteristics. It retains eligibility requirements and asks for the person's
selected traits, not catalogs of alternative population values.</li>
""" if scope else ""
scope_section = ""
if scope:
    scope_section = """
<h2>Additional upstream repair: population catalogs are not individual traits</h2>
<p>Inspection found biographies containing ten-value population spectra in addition to
the individual's selected traits. The original population description was correctly
retained for eligibility, but it also contained instructions to construct sampling
dimensions. The generator prompt now explicitly scopes those instructions to planning,
not the biography. No filtering heuristic discards arbitrary persona fields.</p>
<p>Three captured generator cases returned catalog-free biographies while retaining
their names, ages and the reviewed food/adoption preferences. Two new real-factory core
cases additionally check opposed food preferences and current parent eligibility using
the exact production template. These are fidelity checks, not proof of representative
joint sampling or preservation of every originally sampled dimension.</p>
<p>Replay-harness correction: those three exploratory generator calls omitted the
factory's JSON-output setting. They are not exact-production request replays.
The two real-factory core cases independently exercise the production template
and JSON mode; the completed core result is unaffected.</p>
""" + table(
        ["Person", "Original rating", "Only catalogs removed", "New scoped biography"],
        [[name, row["original"], row["catalog_only_removed"], row["regenerated_biography"]]
         for name, row in scope["actor_replays"]["manual_public_scores"].items()],
    ) + """
<p>All six frozen first-turn replies were read directly. Ratings did not change.
Removing catalogs preserves the existing individual trait descriptions; regenerating
a biography permits new life details under the same supplied characteristics. Neither
condition establishes a calibration solution. These raw actor replays were not new
complete simulations and were not passed through action-quality correction.</p>
<p>A separate audit of the full CF5 trajectory found 53 actor calls for 50 people.
Only Hazel, Wyatt and Clara, all infants, were regenerated. No adult purchase rating
was selected by a correction loop, so disabling correction is not supported as a remedy
for those observed adult ratings. Production quality thresholds remain unchanged.</p>
"""
scope_lineage = f"""
<p>A later generator-only paragraph repair produced the next validated implementation,
<code>{latest_hash}</code>, which passed <strong>{latest_core["passed"]} core cases</strong>
({latest_core["deselected"]} deselected; {latest_core["warnings"]} warnings). A second
read-only reconstruction exactly recovers the 432-case implementation by undoing only
that generator paragraph. The actor/runtime and extraction implementation are unchanged
from the 432-case stage. The original full notebooks have not been regenerated with
this later generator repair; the small generator and actor diagnostics are reported
separately rather than represented as another full 50-person study.</p>
""" if scope else ""
example_section = ""
if example_review:
    example_section = """
<h2>Additional rejected hypothesis: unrelated biography examples</h2>
<p>The generator's two fixed worked biographies include a dislike of cold foods
and a preference for warm soup. A paired diagnostic removed these unrelated examples
and clarified the permitted JSON structures, without requesting different tastes
or a preferred rating. The corrected screen used production JSON mode, the same
sampled traits and six frozen first-turn actor requests. All six biographies were
valid JSON and retained names and ages; their culinary elaborations and all public
replies were reviewed.</p>
""" + table(
        ["Person", "Examples retained", "Examples removed"],
        [[name, row["examples_retained"], row["examples_removed"]]
         for name, row in example_review["corrected_screen"]["manual_public_scores"].items()],
    ) + """
<p>The candidate was not adopted. Responses remained cautious, and the change
from 1 to 2 for one person is not evidence of improved calibration. Three paired
people and new stochastic life details do not identify a precise causal effect;
this does not prove that examples have no influence. These are raw actor diagnostics,
not another full study or a held-out human comparison.</p>
<p>The first screen accidentally omitted production JSON mode: six generator
responses included one malformed output, followed by five valid actor turns.
That failure and its cost were preserved without replacement. It is not evidence
of a production regression. The corrected twelve-response comparison was run
separately with captured production generation settings; its protocol audit passed.
The earlier population-scope generator replay has the same documented harness
caveat, while its real-factory core cases and the 434-case core result remain valid.</p>
"""
coverage_section = ""
if coverage_review:
    coverage_section = """
<h2>Further iteration: permitted alternatives are not realized contrast coverage</h2>
<p>The original 79-dimension vocabulary includes behavioral extremes, but allowing an
option in a mixed list does not ensure the randomly drawn cohort contains it. A new
baseline and candidate were assessed against four contrast endpoints defined before
the calls: traditional versus adventurous food preferences, and strongly resistant
versus extreme novelty-seeking product attitudes. No survey scores were used to
choose those endpoints.</p>
""" + table(
        ["Condition", "Valid returned plan", "Guaranteed contrast endpoints", "Finding"],
        [[row["condition"], row["valid_plan"], row["guaranteed_endpoints"], row["finding"]]
         for row in coverage_review["conditions"]],
    ) + """
<p>The first prompt revision did not meet the predefined requirement. A stricter
revision first timed out, then returned an all-false categorical selection that the
unchanged production validator correctly rejected. That invalid response was retained,
not repaired into null or replaced. A separate experimental representation used nonempty
lists of option identifiers instead of repeated boolean membership slots. Its returned
plan passed reconstruction, guaranteed all four endpoints across 100 sampling seeds,
and allocated ages 9/7/20/6/8. This does not establish reliability over independent
model replications. Compact output did not demonstrate lower total completion usage:
reasoning tokens still dominate.</p>
<p>The six-person integration screen below selected people by the predefined traits,
then included the youngest remaining draw and the first remaining adult. It exercised
the actual generator, original questionnaire, correction threshold and extractor.
It is a contrast-selected diagnostic, not another full notebook rerun or an estimate
of population purchase propensity.</p>
""" + table(
        ["Person", "Age", "Preselected role", "Public rating", "Review"],
        [[row["name"], row["age"], row["role"], row["response"], row["review"]]
         for row in coverage_review["pipeline"]["rows"]],
    ) + "<p>" + html.escape(coverage_review["pipeline"]["verdict"]) + "</p>" + (
        "<p>Additional returned-usage subtotal for this follow-up: <strong>US$"
        + html.escape(coverage_review["additional_returned_usage_subtotal_usd"])
        + "</strong> across 49 returned responses.</p>"
    ) + """
<p>At the time of this six-person screen, no candidate had been integrated. The supplied
demographic source explicitly identifies itself as GPT-4o-synthesized; approximate
allocation to its figures is not authoritative census validation. Behavioral singleton
quotas represent illustrative contrasts, not measured prevalence. The cost of the
unreturned timeout is unknown and excluded from returned-usage estimates.</p>
"""
integration_section = ""
if integration:
    integrated_core = integration["tests"]["sampling-coverage-core"]
    integrated_targeted = integration["tests"]["sampling-coverage-targeted"]
    integration_section = f"""
<h2>Integrated reliability repair: compact, nonempty categorical selections</h2>
<p>The compact selection representation and the screened final coverage-check paragraph
are now integrated. The model returns nonempty lists of local integer option identifiers;
the public plan still contains the original complete option strings. Empty lists,
duplicates, booleans, noninteger identifiers and out-of-range values are rejected rather
than repaired. Optional dimensions remain explicitly null in the intermediate response
and omitted in the restored plan.</p>
<p>The exact integrated messages and schema match the experimental 79-dimension request,
and its saved 50-person native response reconstructs directly to the same public plan.
This is a compatibility check, not an independent full survey. Targeted validation passed
<strong>{integrated_targeted["passed"]} cases</strong>, including real factory calls,
preserved age allocations and deterministic singleton coverage across 100 sampling seeds.</p>
<p>The new implementation, <code>{integration["current_library_sha256"]}</code>,
passed <strong>{integrated_core["passed"]} core cases</strong>
({integrated_core["deselected"]} deselected; {integrated_core["warnings"]} warnings).
Restoring only the two snapshotted pre-change library files in memory exactly recovers
the preceding 434-case implementation. Documentation and directly related tests were
updated; actor, extractor, model, effort and quality thresholds are unchanged.</p>
<p>This is adopted as a selection-validity and requested-coverage repair, <strong>not</strong>
as a demonstrated cure for gazpacho response compression. The earlier six-person screen
predates integration and retains its own source lineage. No new full notebook result
is implied by the core suite or the saved-response compatibility check.</p>
"""
fresh_plan_section = ""
if fresh_plan:
    fresh_plan_section = """
<h2>Independent production replication: coverage survives, demographic caveats remain</h2>
<p>A fresh 79-dimension request through the actual integrated production method
returned 18 directives totaling 50 people. All four prospectively defined contrasts
had singleton allocations and survived 100 fixed drawing seeds. Age totals were
9/7/20/6/8, numeric ages matched their labels, explicit U.S. residence was preserved,
and integer age support covered 0 through 110. The request audit applies exactly
the production client's dedent preprocessing before comparing template and wire messages.</p>
<p>Review did <strong>not</strong> treat these checks as full population fidelity:
two fixed multiracial cultural-profile allocations were added to otherwise weighted
race draws. Across the 100 seeds, the multiracial mean was 3.34 of 50, compared with
the source-weight expectation of 1.45. All eight older-adult allocations also required
a bachelor's degree or higher, although the supplied marginals establish no such
age-education relationship. Uniform draws across age 65–110 preserve support but do
not establish a realistic within-band age distribution.</p>
<p>Two further prompt candidates explained fixed allocations, residual budgets,
conditional-weight renormalization, and nominal versus ordinal categories. Both
preserved the four contrasts and permitted more educational variation, but neither
passed the original expected-marginal-error criterion: race total-variation errors
were 1.5924 and 1.8197 people against a maximum of 1.0. Neither was integrated.
Permitted educational variety alone does not establish compatibility with every
simultaneously selected learning profile. No survey rating was used to choose a plan.</p>
<p>The fresh complete gazpacho 5 notebook described below uses the validated integrated
source, original source cells and thresholds, and no reused simulation cache.</p>
"""
cf6_section = ""
if cf6:
    cf6_section = f"""
<h2>Fresh complete CF6 gazpacho 5: execution succeeds, compression persists</h2>
<p>A new independent population of 50 completed all original notebook cells in
6,404.86 seconds, using <code>{cf6["full_rollout_library_sha256"]}</code>.
Model and effort were Luna/xhigh; the library remained unchanged during execution.
All 50 actor-visible biographies matched the saved generation outputs and drawn names
and ages. These are new people, not a paired comparison against CF5.</p>
""" + table(["Metric", "CF5", "Fresh CF6", "Human control"], [
        ["1 / 2 / 3 / 4 / 5", "4 / 37 / 6 / 0 / 0", "5 / 31 / 13 / 0 / 0",
         "11 / 9 / 13 / 10 / 7"],
        ["N/A", "3", "1", "0"],
        ["Mean among numerical answers", "2.0426", "2.1633", "2.8600"],
        ["Sample SD among numerical answers", f"{statistics.stdev(scores):.4f}",
         f"{cf6['sample_sd']:.4f}", f"{frame['vote_sd']:.4f}"],
    ]) + """
<p>All 49 numerical extractions match public speech; the infant nonanswer remains N/A.
Forty-nine explanations are verbatim or null. The remaining explanation merely adds
quotation marks around an exact public substring. No private-thought substitution or
rationale reversal was found. All 50 public responses and explanations were reviewed.</p>
<p>The adult subset still contains no 4/5 ratings (1:3 / 2:22 / 3:13; mean 2.2632).
The small overall mean increase is not evidence that the repair improves empirical
accuracy across different cohorts. Warm/familiar-food objections and regular-purchase
qualifications remain repetitive. The human panel is not eligibility-matched.</p>
<p>Two additional concrete defects were identified. The newly generated product-attitude
vocabulary includes one option saying the person strongly rejects novelty <em>or</em>
adopts products impulsively. A singleton allocation to that option cannot guarantee
either actual end. Separately, children aged two and three stated purchase-rating
digits despite not understanding the task; those digits were genuine speech, not an
extraction error. A four-year-old's score is likewise not validated as an adult purchase
judgment.</p>
<p>The 117-year-old persona preserves its exact drawn age inside this fresh vocabulary's
0–120 range. It does not violate the earlier frozen vocabulary's 0–110 bounds, because
that is a different request. The uniform within-band sampling assumption does not encode
the rarity of such ages. No arbitrary cutoff, age edit, or invented age distribution
was introduced to hide this population-model limitation.</p>
"""
final_section = ""
if final_stage:
    core = final_stage["core"]
    final_section = f"""
<h2>Bounded repairs: comprehension and coherent categorical options</h2>
<p>The actor now distinguishes demanded response formatting from the person's actual
knowledge and abilities; it does not invent a caregiver to answer for them. The rule is
task-specific, not an age cutoff: children's counting and capable adults' numerical
preferences remain available. Dimension-generation instructions now require opposing
ends to be separately selectable rather than joined in one disjunctive option.</p>
<p>Four live comprehension/capability regressions passed, as did a live dimension-vocabulary
regression. This comprehension/coherence source, <code>{final_stage["current_library_sha256"]}</code>,
passed <strong>{core["passed"]} core cases</strong>
({core["deselected"]} deselected; {core["warnings"]} warnings). Removing only the three
new actor lines and four dimension-method docstring lines in memory reconstructs the
exact full-CF6/444-core source. README guidance and five related core cases were added.</p>
<p>Six exact saved biographies were then exercised through the original gazpacho
questionnaire, thought stimulus, quality-correction settings and extractor. The
age-zero infant remained unscored; the two- and three-year-olds now gave unscored
concrete reactions; adult controls retained public 2/3 responses. The four-year-old
still gave a public 2, which is not presented as repaired or an adult propensity judgment.
This is a bounded improvement, not a full new population survey or calibration cure.</p>
<p>The six-person command exited at its final whole-library fingerprint assertion because
the dimension-method docstring was edited while it ran. All actor and extractor outputs
had already been saved. A separate audit recovered the receipt without repeating any
model calls and proved that removing that four-line docstring delta restores the exact
screen-start fingerprint. Every actor request contains the unchanged new actor rule;
dimension generation is never called in this frozen-biography screen. The source-drift
exception is disclosed rather than calling that command an unqualified pass.</p>
<p>A separate real call repeated the original full-population dimension request through
the production method and JSON mode. Its wire audit proves the original population input
and all non-message model options are unchanged; removing only the four new instruction
lines recovers the original system message exactly. The new vocabulary has 12 adoption
options, with impulsive trend buying and strong rejection separately selectable.
Traditional food and unfamiliar-cuisine exploration also remain distinct.
This supports the specific option-coherence repair, not comprehensive demographic
validity or a new survey-calibration result.</p>
"""
marginal_section = ""
if marginal_stage:
    marginal_core = marginal_stage["core"]
    marginal_replay = load(r"marginal-choices-integration\receipt.json")
    assert marginal_replay["status"] == "passed"
    assert marginal_replay["library_sha256"] == marginal_stage["current_library_sha256"]
    marginal_section = f"""
<h2>Further sampling repair: preserve weighted alternatives, not invented demographic profiles</h2>
<p>Rather than repeat the unsuccessful residual-budget arithmetic instructions, two
new candidates retain complete compatible weighted demographic alternatives within
behavioral directives. Both pass the original frozen numerical criteria: expected
race, gender, region and settlement proportions match the supplied weights to
floating-point precision, age allocations remain 9/7/20/6/8, all four predefined
singleton contrasts survive, and both older bands allow multiple attainments.
Neither candidate was selected using downstream survey ratings.</p>
<p>Revision 3 was withheld for a qualification/occupation compatibility follow-up.
Revision 4 adds that generic guard and was integrated exactly as tested. All 25
directives were manually reviewed. They retain the full integer age support and
explicit U.S. residence, avoid independently sampled race-specific cultural profiles
and credential-dependent occupations, and pair the specialist learning contrast
with advanced attainment. A request/reconstruction audit and 100 fixed draw seeds
confirm age compatibility. These are two model calls, not 100 model replications;
the seed audit concerns the deterministic drawing stage.</p>
<p>The actual integrated factory method replays the accepted original-input response
with exactly matching messages and schema, without a new saved API response.
A separate live core case checks weighted marginals, culinary endpoints and explicit
medical-license compatibility on a synthetic diagnostic population.
Current library source <code>{marginal_stage["current_library_sha256"]}</code>
passed <strong>{marginal_core["passed"]} core cases</strong>
({marginal_core["deselected"]} deselected; {marginal_core["warnings"]} warnings).
Removing only the tested planner paragraph reconstructs the preceding 449-case source.</p>
<p>This preserves expected marginals, not exact realized quotas, measured demographic
correlations, or empirical representativeness. Optional redundant details are left
open rather than invented. Uniform within-band ages and independently drawn opinion
and personality alternatives remain assumptions, not a fully validated joint model.
No new full survey under this source is claimed; gazpacho response compression remains
unresolved.</p>
"""
research_section = """
<h2>Next scientific gate, not an implemented workaround</h2>
<p>A broader study should cross fixed population-generation conditions with fixed
response-model conditions using the same concrete draws, survey wording and simulated
time. Freeze the conditions and population-sampling seeds before examining outcomes;
repeat independent model runs and retain the existing validation thresholds. No
unsupported deterministic model-seed parameter is assumed. Unknown recruitment eligibility must remain
unknown, rather than assuming an age-25 filter. Quantitative validation needs eligible
human comparison data and product-level holdouts, not further tuning to this one
gazpacho distribution. Mean, dispersion, ordinal distribution distance and, across
multiple products, relative appeal must be assessed together; more varied numbers
alone are not an acceptance criterion.</p>
<p>Published survey-method research documents over-precise synthetic responses:
<a href="https://www.cambridge.org/core/journals/political-analysis/article/synthetic-replacements-for-human-survey-data-the-perils-of-large-language-models/B92267DC26195C7F36E63EA04A47D2FE">
Bisbee et al., Synthetic Replacements for Human Survey Data? (2024)</a>.
An explicitly different measurement protocol is discussed in the preprint
<a href="https://arxiv.org/abs/2510.08338v3">Maier et al., LLMs Reproduce Human Purchase
Intent via Semantic Similarity Elicitation of Likert Ratings</a>: free-text
responses are mapped through embedding similarities to rating distributions.
Its 57-survey, 9,300-response personal-care evaluation is not evidence that the method
works for Luna or gazpacho. Crucially, the authors state that their reference anchors
were manually optimized for those same 57 surveys and that transfer to other surveys
remains unclear. Their reported correlation attainment is not individual-response accuracy.</p>
<p>No such measurement change has been implemented. Any future experiment must keep
derived probabilities distinct from publicly stated ratings, preserve the original
extraction contract, freeze anchors without gazpacho outcome tuning, and test unseen
products. Replacing a spoken 2 with an embedding-derived higher score would not repair
extraction fidelity or establish behavioral realism.</p>
"""
before_after = table(["Observed defect", "Before", "After"], [
    ["Nonanswer explanation cites a private turn boundary",
     "Wyatt's correct N/A explanation quotes DONE: 'I can't give a meaningful purchase rating.'",
     "Uses his actual public babble and absence of a numeric answer, or leaves an absent justification null; does not quote DONE as speech."],
    ["An extraction reverses the reason for a preference",
     "Tiana: 'B is last because she would not leave a 3-to-5-year-old unsupervised with it.'",
     "Preserves: 'B is last because I'm open to seeing a sample and trying something new' together with her separate supervision qualification."],
])
report = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Luna notebook quality follow-up</title>
<style>
body{{font:15px/1.55 system-ui,sans-serif;max-width:1180px;margin:32px auto;padding:0 20px;color:#20262e}}
table{{border-collapse:collapse;width:100%;margin:16px 0;font-size:14px}}
th,td{{border:1px solid #d5dce3;padding:10px;text-align:left;vertical-align:top}}
th{{background:#edf1f5}}.warning{{padding:16px;background:#fff2dc;border-left:5px solid #b87500}}
code{{overflow-wrap:anywhere}}h2{{margin-top:30px}}li{{margin:6px 0}}
</style>
<h1>Luna notebook quality follow-up</h1>
<p class="warning"><strong>Not fully solved.</strong> All three requested complete notebook reruns
finished, and concrete runtime and extraction repairs have been implemented. Gazpacho's
quantitative response compression remains unresolved; these results do not justify calling
Luna a validated drop-in replacement for this empirical survey.</p>
<p>Generated {html.escape(datetime.now(timezone.utc).isoformat())}.
All complete rollouts used <code>gpt-6-luna</code> / <code>xhigh</code>.
Only the most complete gazpacho variation was rerun, not its alternative notebooks.</p>
<h2>Complete notebook results</h2>{rollout_table}
<p>All source cells executed without recorded cell or simulation errors. Exact biographies
match the previous CF4 cohorts; reused local API responses were not treated as fresh generation
or newly billed calls. No questionnaire, sample size or quality threshold was relaxed.
These are individual rollouts, not statistically established model rankings.</p>
<h2>Repairs supported by the evidence</h2>
<ul>
<li>Actor system instructions and turn cues remain plain text; structured stimuli and image
resolution retain their existing handling.</li>
<li>Actual middle-memory omissions are visible; complete histories no longer carry false gap
warnings. The finite Investment meeting has a local 100-event lookback, without changing global
retention defaults. Its final summaries now retain the supplied sales, cost, price, EBITDA
and cash figures; inaccessible market prices and independent valuation inputs remain unavailable.</li>
<li>Extraction boundaries now apply to every field, including explanations of missing answers.
Justifications favor the person's actual public clauses, keeping reasons, conditions and choices
connected rather than composing a new rationale.</li>
{scope_repair}
</ul>
{before_after}
<p>The final extraction repair was checked on all 100 real survey histories: all original
ratings/rankings and their types were preserved. Ninety justifications were verbatim public
substrings or null; the remaining ten were manually reviewed as faithful summaries, quotation
wrappers or a public nonanswer explanation.</p>
<h2>Gazpacho: the remaining empirical problem</h2>{distribution_table}
<p>Current simulated mean: <strong>{statistics.mean(scores):.4f}</strong>, sample SD
<strong>{statistics.stdev(scores):.4f}</strong>, n={len(scores)}. Human control mean:
<strong>{frame["vote_mean"]:.4f}</strong>, sample SD <strong>{frame["vote_sd"]:.4f}</strong>,
n=50. The current simulated mean equals the previous repaired run's mean.
The absence of 4/5 responses remains the central unresolved issue, not an execution error.</p>
<p>The original PickFu report verifies 50 US-based respondents, completed July 5, 2025,
in 27 minutes, with matching rating-question and product-description substance. The export
filename date is not the completion date. Exact targeting, an age-25 eligibility filter and
national representativeness remain unknown. The simulation includes 13 minors and is not an
eligibility-matched reproduction of that human panel; age-restricted earlier comparisons
also retained compression. No private report link or poll identifier is included here.</p>
<p>Twenty-one bounded prompt, transport, framing, season and effort conditions were investigated.
The combined decision rules did not establish a calibration fix on either the development
panel or an independent eight-person holdout. Separately, a genuinely minimal actor template
failed to resolve compression on the development panel. Neither was adopted. An explicitly
isolated low-effort diagnostic reduced native actor reasoning tokens from 4,325 to 829 but still
produced only 2/3 responses on its eight-person panel. The production default remains
<code>xhigh</code>. Synthetic favorable/unfavorable controls are diagnostics, not human observations.
No rating distribution was forced toward the control.</p>
<h2>Validation lineage</h2>
<p>The three full simulations and the earlier 429-case core suite used
<code>{lineage["full_rollout_library_sha256"]}</code>. The first subsequent change was
confined to the extraction template. A read-only reconstruction of that one file recovers the prior whole-library
fingerprint; all actor/runtime code is unchanged.</p>
<p>The extraction-repair implementation, <code>{lineage["current_library_sha256"]}</code>,
passed <strong>{lineage["current_source_core"]["passed"]} core cases</strong>
({lineage["current_source_core"]["deselected"]} deselected;
{lineage["current_source_core"]["warnings"]} warnings). The 100-history replay used the final
production extraction template. It is postprocessing of the actual completed studies, not
a second full simulation under the later source hash. The corrected CSVs supersede extraction
justifications in the attached frozen-run notebooks.</p>
{scope_lineage}
{scope_section}
{example_section}
{coverage_section}
{integration_section}
{fresh_plan_section}
{cf6_section}
{final_section}
{marginal_section}
<h2>Returned-usage costs</h2>{cost_table}
<p>Saved standard list rates and returned API usage, not invoices or project-wide spending.
Full-run estimates reconcile exact new cache entries against the copied CF4 caches; the final
extraction estimate includes all 100 owned saved responses after process completion, rather
than the earlier 94-response in-process snapshot. Core-suite usage and failed/unreturned
request charges are not included. Elapsed times were affected by concurrent work and are not
performance benchmarks.</p>
{research_section}
<h2>Conclusion</h2>
<p>The factual-retention and extraction repairs are supported by actual end-to-end execution
and targeted source-fidelity checks. The parents study is no longer uniformly rejecting the
product, but remains repetitive and is not empirically validated. Investment is better grounded,
not uniformly better conversationally. Gazpacho still needs a defensible research solution:
neither successful execution, higher mean ratings nor more varied answers alone would establish
one. A broader population/response calibration design would be a separate scientific and
engineering decision, not an undisclosed prompt trick or silent model fallback.</p>
</html>"""
(ROOT / "cf5-quality-report.html").write_text(report, encoding="utf-8")
print("Report written; overall quality objective remains unresolved.")
