"""Match actual actor-visible biographies to saved generation evidence, including API reuse."""

import html
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "model-study"))
from model_case_study import decode_key


def normalized(persona):
    """Ignore only absent versus null top-level optional persona fields."""
    return {key: value for key, value in persona.items() if value is not None}


for study in ["kids", "gaz"]:
    folder = ROOT / f"cf5-{study}"
    record_path = next(folder.glob("*.run.json"))
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["status"] == "completed"
    start = datetime.fromisoformat(record["started_at"]).timestamp()
    finish = start + record["elapsed_seconds"]
    expected_names = set(json.loads(record_path.with_name(
        record_path.name.removesuffix(".run.json") + ".traits.json"
    ).read_text(encoding="utf-8")))
    cache = json.loads((folder / "api.cache.json").read_text(encoding="utf-8"))
    actual, generated = {}, []
    marker = "- Name, demographics and other characteristics:"
    for key, response in cache.items():
        request, schema = decode_key(key)
        if schema == "tinytroupe.agent.CognitiveActionsModel" and start <= response["created"] <= finish:
            assert request["model"] == "gpt-6-luna"
            assert request["reasoning_effort"] == "xhigh"
            text = request["messages"][0]["content"].split("## Persona", 1)[1]
            persona = json.loads(re.search(r"```json\s*(.*?)```", text, re.S)[1])
            name = persona["name"]
            if name in actual:
                assert normalized(actual[name]) == normalized(persona), name
            actual[name] = persona
        if marker in key:
            prompt = request["messages"][-1]["content"]
            assert marker in prompt
            draws, _ = json.JSONDecoder().raw_decode(
                html.unescape(prompt.split(marker, 1)[1]).lstrip()
            )
            generated.append((json.loads(response["choices"][0]["message"]["content"]),
                              draws, response["created"]))
    assert set(actual) == expected_names and len(actual) == 50
    people = []
    for name in sorted(actual):
        matches = [(p, d, t) for p, d, t in generated
                   if normalized(p) == normalized(actual[name])]
        assert matches, name
        assignments = {json.dumps(d, sort_keys=True, ensure_ascii=False) for _, d, _ in matches}
        assert len(assignments) == 1, f"Ambiguous source assignments: {name}"
        persona, draws, created = max(matches, key=lambda match: match[2])
        age = draws.get("parent_age", draws.get("age"))
        assert persona["name"] == draws["name"] and persona["age"] == age, name
        people.append({
            "name": name, "age": persona["age"], "drawn_age": age,
            "name_matches": True, "age_matches": True, "draws": draws, "persona": persona,
            "matching_generation_response_predates_run": created < start,
        })
    summary = {
        "generation_response_count": len(people), "distinct_names": len(people),
        "exact_drawn_age_matches": len(people), "exact_drawn_name_matches": len(people),
        "exact_actor_visible_biography_matches": len(people),
        "normalization": "Only top-level optional fields absent versus null; no substantive values removed.",
        "matching_generation_responses_predating_run": sum(
            p["matching_generation_response_predates_run"] for p in people
        ),
        "minors": sum(p["age"] < 18 for p in people),
        "age_counts": dict(sorted(Counter(p["age"] for p in people).items())),
        "scope": "Full biographies matched against current-run actor requests and actual cohort names. "
                 "Older API responses are valid generation evidence, not newly billed calls. "
                 "Age/name agreement and biography identity do not establish household eligibility, "
                 "semantic compliance of all sampled traits, or population representativeness.",
    }
    for name, value in [("population-generation-evidence.json", people),
                        ("population-generation-audit.json", summary)]:
        (folder / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    print(study, json.dumps(summary, ensure_ascii=False))
