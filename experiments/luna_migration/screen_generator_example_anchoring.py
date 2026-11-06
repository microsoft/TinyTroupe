"""Screen unrelated biography-example anchoring without targeting survey ratings."""

import copy
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from tinytroupe import config_manager
from tinytroupe.agent import CognitiveActionsModel
from tinytroupe.clients import client, force_api_cache
from review_notebook_evidence import cost_for_run
from model_case_study import decode_key

OUTPUT = ROOT / "generator-example-ablation-json-mode"
RESUME_ACTORS = "--resume-actors" in sys.argv
OUTPUT.mkdir(exist_ok=RESUME_ACTORS)
CASES = [
    json.loads((ROOT / "population-scope-trial" / name).read_text(encoding="utf-8"))
    for name in ["Diego.json", "Marco.json", "Gabriel.json"]
]
ACTORS = {
    row["name"]: row
    for row in json.loads(
        (ROOT / "population-scope-actor-replays" / "results.json").read_text(
            encoding="utf-8"
        )
    )
    if row["condition"] == "regenerated_biography"
}
expected = {case["name"]: case["before"] for case in CASES}
captured_options = {}
source_cache = json.loads((ROOT / "cf5-gaz" / "api.cache.json").read_text(
    encoding="utf-8"
))
for key, response in source_cache.items():
    if "- Name, demographics and other characteristics:" not in key:
        continue
    request, schema = decode_key(key)
    if schema is not None:
        continue
    biography = json.loads(response["choices"][0]["message"]["content"])
    name = biography.get("name")
    if name not in expected:
        continue
    normalized = lambda p: {k: v for k, v in p.items() if v is not None}
    if normalized(biography) != normalized(expected[name]):
        continue
    assert request["model"] == "gpt-6-luna"
    assert request["reasoning_effort"] == "xhigh"
    assert request["response_format"] == {"type": "json_object"}
    captured_options[name] = {
        option: request[option]
        for option in [
            "temperature", "max_completion_tokens", "response_format",
            "frequency_penalty", "presence_penalty",
        ]
        if option in request
    }
assert set(captured_options) == set(expected)
OLD_FORMAT = "The format for this JSON response is as described in the examples."
NEW_FORMAT = (
    "The response is one JSON object with the fields listed below. Complex fields "
    "may use nested JSON objects, arrays, or descriptive strings, as appropriate."
)
TEMPLATE = REPO / "tinytroupe" / "factory" / "prompts" / "generate_person.mustache"
original = TEMPLATE.read_text(encoding="utf-8")
assert original.count(OLD_FORMAT) == original.count("## Examples") == 1
candidate = original.split("## Examples", 1)[0].replace(OLD_FORMAT, NEW_FORMAT).rstrip() + "\n"
(OUTPUT / "candidate.mustache").write_text(candidate, encoding="utf-8")

jobs = []
for case in CASES:
    messages = case["messages"]
    text = messages[-1]["content"]
    assert text.count(OLD_FORMAT) == text.count("## Examples") == 1
    assert "Cold foods like salads." in text
    assert "Warm, comforting foods like soup." in text
    changed = text.split("## Examples", 1)[0].replace(OLD_FORMAT, NEW_FORMAT).rstrip() + "\n"
    for condition, prompt in [
        ("examples_retained_replication", text),
        ("unrelated_examples_removed", changed),
    ]:
        request = copy.deepcopy(messages)
        request[-1]["content"] = prompt
        jobs.append({
            "name": case["name"], "condition": condition, "messages": request,
            "sampled_characteristics": case["draws"], "historical_scoped_persona": case["after"],
            "generation_options": captured_options[case["name"]],
        })

plan = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "hypothesis": "Two fixed unrelated example biographies may anchor generated food "
                  "preferences: one dislikes cold foods; the other likes warm soup.",
    "design": "Three previously selected observed generator requests, one fresh replication "
              "with examples retained and one with examples removed per person, followed "
              "by the corresponding six frozen first-turn actor replays.",
    "constants": "All supplied characteristics, population eligibility, general generation "
                 "rules, required output fields, actor instructions, chronological stimuli, "
                 "schema, model gpt-6-luna, effort xhigh and captured output-token limits.",
    "intervention": "Remove unrelated worked biographies and replace only their output-format "
                    "cross-reference with a description of permitted JSON structures.",
    "acceptance": "Preserve identity, eligibility and supplied traits; inspect generated "
                  "preferences and actual public speech. Neither a higher rating nor "
                  "a closer human mean is an acceptance criterion.",
    "limitations": "Small stochastic screen, not a population calibration. New biography "
                   "elaborations are not unchanged-persona comparisons. Raw actor turns "
                   "do not exercise quality correction or a complete notebook.",
    "production_changed": False,
    "generator_response_format": {"type": "json_object"},
    "prior_harness_correction": "The earlier generator-example-ablation screen omitted "
                                "production JSON mode in both generator arms. Preserve its "
                                "eleven returned responses and one malformed output as an "
                                "out-of-contract diagnostic; this new folder contains the "
                                "paired rerun with captured production generation options.",
    "production_template_sha256": hashlib.sha256(TEMPLATE.read_bytes()).hexdigest(),
    "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
}
if RESUME_ACTORS:
    recorded = json.loads((OUTPUT / "plan.json").read_text(encoding="utf-8"))
    assert recorded["production_template_sha256"] == plan["production_template_sha256"]
    assert recorded["candidate_sha256"] == plan["candidate_sha256"]
else:
    (OUTPUT / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )

config_manager.update("model", "gpt-6-luna")
config_manager.update("reasoning_model", "gpt-6-luna")
config_manager.update("reasoning_effort", "xhigh")
config_manager.update("timeout", 600)
force_api_cache(True, str(OUTPUT / "api.cache.json"))


def generate(job):
    reply = client().send_message(
        job["messages"], dedent_messages=False,
        **job["generation_options"],
    )
    if reply is None:
        raise RuntimeError(f"No biography for {job['name']}/{job['condition']}.")
    persona = json.loads(reply["content"])
    expected = job["historical_scoped_persona"]
    assert persona["name"] == job["name"] and persona["age"] == expected["age"]
    required = {
        "name", "age", "gender", "nationality", "residence", "education",
        "long_term_goals", "occupation", "style", "personality", "preferences",
        "beliefs", "skills", "behaviors", "health", "relationships", "other_facts",
    }
    assert required <= persona.keys(), required - persona.keys()
    job["persona"] = persona
    key = f"{job['name'].split()[0]}-{job['condition']}"
    (OUTPUT / f"{key}-biography.json").write_text(
        json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "stage": "generation", "name": job["name"], "condition": job["condition"],
        "characters": len(json.dumps(persona)), "preferences": persona["preferences"],
    }, ensure_ascii=False), flush=True)
    return job


def act(job):
    captured = ACTORS[job["name"]]
    messages = copy.deepcopy(captured["messages"])
    system = messages[0]["content"]
    prefix, section = system.split("## Persona", 1)
    match = re.search(r"```json\s*(.*?)```", section, re.S)
    previous = match[1]
    assert json.loads(previous) == job["historical_scoped_persona"]
    trailing = previous[len(previous.rstrip()):]
    section = (
        section[:match.start(1)] + json.dumps(job["persona"], indent=4) + trailing
        + section[match.end(1):]
    )
    messages[0]["content"] = prefix + "## Persona" + section
    assert messages[1:] == captured["messages"][1:]
    reply = client().send_message(
        messages, dedent_messages=False, response_format=CognitiveActionsModel,
        max_completion_tokens=captured["max_completion_tokens"],
        frequency_penalty=0.0, presence_penalty=0.0,
    )
    if reply is None:
        raise RuntimeError(f"No actor response for {job['name']}/{job['condition']}.")
    result = json.loads(reply["content"])
    CognitiveActionsModel.model_validate(result)
    actions = result["actions"]
    assert actions[-1]["type"] == "DONE"
    assert len({(a["type"], a["target"]) for a in actions}) == len(actions)
    talks = [i for i, a in enumerate(actions) if a["type"] == "TALK"]
    thinks = [i for i, a in enumerate(actions) if a["type"] == "THINK"]
    assert talks and thinks and min(thinks) < min(talks)
    row = {
        "name": job["name"], "condition": job["condition"],
        "messages": messages, "result": result,
    }
    key = f"{job['name'].split()[0]}-{job['condition']}"
    (OUTPUT / f"{key}-actor.json").write_text(
        json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "stage": "actor", "name": job["name"], "condition": job["condition"],
        "public": [a["content"] for a in actions if a["type"] == "TALK"],
    }, ensure_ascii=False), flush=True)
    return row


if RESUME_ACTORS:
    generated = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(OUTPUT.glob("*-biography.json"))
    ]
    assert len(generated) == 5
    expected_cases = {(job["name"], job["condition"]) for job in jobs}
    complete_cases = {(job["name"], job["condition"]) for job in generated}
    missing = expected_cases - complete_cases
    assert missing == {("Diego Andrés Quintana", "unrelated_examples_removed")}
    failures = []
    initial_cache = json.loads((OUTPUT / "api.cache.json").read_text(encoding="utf-8"))
    assert len(initial_cache) == 6
    for key, response in initial_cache.items():
        request, schema = decode_key(key)
        assert schema is None
        content = response["choices"][0]["message"]["content"]
        try:
            json.loads(content)
        except json.JSONDecodeError as error:
            failures.append({
                "name": "Diego Andrés Quintana",
                "condition": "unrelated_examples_removed",
                "error": str(error),
                "finish_reason": response["choices"][0]["finish_reason"],
                "raw_content": content,
                "request": request,
            })
    assert len(failures) == 1
    (OUTPUT / "generation-failures.json").write_text(
        json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT / "execution-deviation.json").write_text(json.dumps({
        "reason": "The original six-call generator stage returned one syntactically invalid "
                  "JSON response (stop, not truncation), aborting strict parsing.",
        "handling": "Retain the failed raw response and cost. Do not repair, redraw, or replace "
                    "it. Replay only the five complete biographies; report the missing "
                    "candidate as an error rather than inferring its rating.",
        "completed_generator_responses": 6,
        "valid_biographies": 5,
        "observed_generation_failures": 1,
        "planned_actor_turns": 6,
        "executed_actor_turns": 5,
        "actor_outcomes_not_examined_before_this_amendment": True,
    }, indent=2), encoding="utf-8")
else:
    with ThreadPoolExecutor(max_workers=3) as executor:
        generated = list(executor.map(generate, jobs))
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(act, generated))

cache = json.loads((OUTPUT / "api.cache.json").read_text(encoding="utf-8"))
assert len(cache) == len(jobs) + len(results)
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(
    encoding="utf-8"
))["models"]["gpt-6-luna"]
usage = cost_for_run(OUTPUT, {
    "started_at": "1970-01-01T00:00:00+00:00",
    "elapsed_seconds": max(r["created"] for r in cache.values()) + 1,
}, prices)
(OUTPUT / "receipt.json").write_text(json.dumps({
    "status": "Screen completed with one observed JSON generation failure; five valid "
              "biographies and five actor turns require semantic review."
              if RESUME_ACTORS else "Twelve responses returned; semantic review remains required.",
    "generator_responses": len(jobs),
    "observed_generation_failures": 1 if RESUME_ACTORS else 0,
    "generated_biographies": len(generated), "actor_turns": len(results),
    "returned_usage_estimate": usage,
    "production_template_unchanged": hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()
        == json.loads((OUTPUT / "plan.json").read_text(encoding="utf-8"))[
            "production_template_sha256"
        ],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("Example-ablation screen finished.", flush=True)
