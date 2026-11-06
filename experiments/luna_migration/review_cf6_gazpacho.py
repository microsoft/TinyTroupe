"""Review the fresh complete gazpacho run without equating higher scores with quality."""

import argparse
import html
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from audit_notebook_runs import audit
from model_case_study import decode_key
from review_notebook_evidence import public_actions, summarize, table_rows

NAME = "Bottled Gazpacho Market Research 5 (with behavior correction).ipynb"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--folder", choices=["cf6-gaz", "cf7-gaz"], default="cf6-gaz")
args = parser.parse_args()
FOLDER = ROOT / args.folder
STEM = FOLDER / Path(NAME).stem


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


execution = audit(REPO / "examples", ROOT, {Path(NAME).stem: FOLDER.name},
                  "gpt-6-luna", "xhigh")
assert execution["runs"][0].get("execution_audit_passed") is True
record = load(STEM.with_suffix(".run.json"))
prices = load(ROOT / "model-study" / "study-prices.json")["models"]["gpt-6-luna"]
metrics = summarize(FOLDER, NAME, prices)
talks = public_actions(load(STEM.with_suffix(".agents.json")))
traits = load(STEM.with_suffix(".traits.json"))
rows = table_rows(load(STEM.with_suffix(".tables.json")))
assert len(rows) == len(talks) == len(traits) == 50
assert len({row["name"] for row in rows}) == 50
assert {row["name"] for row in rows} == set(talks)
cache = load(FOLDER / "api.cache.json")
actor_personas, generated, sampling_responses = {}, [], []
marker = "- Name, demographics and other characteristics:"
for key, response in cache.items():
    request, schema = decode_key(key)
    if "messages" not in request:
        continue
    assert request["model"] == "gpt-6-luna"
    assert request.get("reasoning_effort") == "xhigh"
    if schema == "tinytroupe.agent.CognitiveActionsModel":
        persona_text = request["messages"][0]["content"].split("## Persona", 1)[1]
        persona = json.loads(re.search(r"```json\s*(.*?)```", persona_text, re.S)[1])
        name = persona["name"]
        if name in actor_personas:
            assert actor_personas[name] == persona
        actor_personas[name] = persona
    prompt = request["messages"][-1]["content"]
    if isinstance(prompt, str) and marker in prompt:
        draws, _ = json.JSONDecoder().raw_decode(
            html.unescape(prompt.split(marker, 1)[1]).lstrip()
        )
        generated.append((json.loads(response["choices"][0]["message"]["content"]), draws))
    response_format = request.get("response_format") or {}
    if response_format.get("json_schema", {}).get("name") == "sampling_plan_by_identifiers":
        sampling_responses.append(response["id"])
assert set(actor_personas) == set(talks)
assert len(sampling_responses) == 1

population_evidence = []
for name, persona in actor_personas.items():
    matches = [(p, d) for p, d in generated
               if {**({"country_of_residence": None}
                       if "country_of_residence" not in p else {}), **p} == persona]
    assert matches, name
    assignments = {json.dumps(d, sort_keys=True, ensure_ascii=False) for _, d in matches}
    assert len(assignments) == 1, name
    biography, draws = matches[0]
    assert biography["name"] == draws["name"] == name
    assert biography["age"] == draws["age"] == traits[name]["age"]
    population_evidence.append({
        "name": name, "age": persona["age"], "draws": draws, "persona": persona,
        "generated_fields_match_actor_visible_persona": True,
    })

evidence = []
for row in rows:
    speech = "\n".join(action["text"] for action in talks[row["name"]])
    justification = row.get("justification")
    evidence.append({
        **row, "age": traits[row["name"]]["age"], "public_speech": speech,
        "justification_verbatim_or_null": (
            justification is None or
            isinstance(justification, str) and justification in speech
        ),
        "manual_review": "Pending: confirm score, rationale and developmental coherence.",
    })

numeric = [int(str(row["response"])) for row in rows
           if str(row["response"]) in {"1", "2", "3", "4", "5"}]
adult = [int(str(row["response"])) for row in rows
         if traits[row["name"]]["age"] >= 18
         and str(row["response"]) in {"1", "2", "3", "4", "5"}]
summary = {
    "execution": execution, "metrics": metrics,
    "public_response_counts": dict(Counter(str(row["response"]) for row in rows)),
    "numeric_mean": statistics.mean(numeric) if numeric else None,
    "numeric_sample_sd": statistics.stdev(numeric) if len(numeric) > 1 else None,
    "adult_numeric_counts": dict(Counter(adult)),
    "adult_numeric_mean": statistics.mean(adult) if adult else None,
    "adult_numeric_sample_sd": statistics.stdev(adult) if len(adult) > 1 else None,
    "exact_actor_visible_biography_matches": len(population_evidence),
    "exact_drawn_name_and_age_matches": len(population_evidence),
    "biography_normalization": "Only the documented country_of_residence=None default "
                               "may be added to a generated biography; no fields are discarded.",
    "sampling_response_ids": sampling_responses,
    "verbatim_or_null_justifications": sum(e["justification_verbatim_or_null"] for e in evidence),
    "manual_quality_review": "Pending; execution and increased variation are not quality approval.",
    "scope": "A new independent full run, not the same cohort as earlier runs. Neither a higher mean "
             "nor additional 4/5 ratings alone establishes empirical calibration. Human-panel "
             "recruitment eligibility remains unknown.",
}
for name, value in [
    (f"{args.folder}-execution-review.json", summary),
    (f"{args.folder}-public-evidence.json", evidence),
    (f"{args.folder}-population-evidence.json", population_evidence),
]:
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
