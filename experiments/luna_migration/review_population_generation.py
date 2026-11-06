"""Audit concrete population assignments without inferring survey preferences."""

import argparse
import html
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "model-study"))
from model_case_study import decode_key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--record", type=Path)
    args = parser.parse_args()
    cache = json.loads((args.folder / "api.cache.json").read_text(encoding="utf-8"))
    window = None
    expected_names = None
    if args.record:
        record = json.loads(args.record.read_text(encoding="utf-8"))
        if record.get("status") != "completed":
            raise ValueError("A completed run is required for a windowed generation audit.")
        start = datetime.fromisoformat(record["started_at"]).timestamp()
        window = (start - 1, start + record["elapsed_seconds"] + 1)
        traits_path = args.record.with_name(
            args.record.name.removesuffix(".run.json") + ".traits.json"
        )
        expected_names = set(json.loads(traits_path.read_text(encoding="utf-8")))
    people = []
    selected = defaultdict(Counter)
    for key, response in cache.items():
        if window and not window[0] <= response["created"] <= window[1]:
            continue
        marker = "- Name, demographics and other characteristics:"
        if marker not in key:
            continue
        request, _ = decode_key(key)
        prompt = request["messages"][-1]["content"]
        if marker not in prompt:
            continue
        draws, _ = json.JSONDecoder().raw_decode(
            html.unescape(prompt.split(marker, 1)[1]).lstrip()
        )
        persona = json.loads(response["choices"][0]["message"]["content"])
        expected_age = draws.get("parent_age", draws.get("age"))
        for field, value in draws.items():
            selected[field][json.dumps(value, ensure_ascii=False, sort_keys=True)] += 1
        people.append({
            "name": persona["name"],
            "drawn_age": expected_age,
            "age": persona["age"],
            "age_matches": persona["age"] == expected_age,
            "name_matches": persona["name"] == draws["name"],
            "draws": draws,
            "persona": persona,
        })
    if not people:
        raise ValueError("No generation responses found.")
    if expected_names is not None and (
        len(people) != len(expected_names)
        or {person["name"] for person in people} != expected_names
    ):
        raise ValueError("New generation responses do not exactly cover the actual population; "
                         "a separate cached-response/retry audit is required.")
    ages = [person["age"] for person in people]
    summary = {
        "generation_response_count": len(people),
        "distinct_names": len({person["name"] for person in people}),
        "exact_drawn_age_matches": sum(person["age_matches"] for person in people),
        "exact_drawn_name_matches": sum(person["name_matches"] for person in people),
        "age_min": min(ages),
        "age_max": max(ages),
        "age_counts": dict(sorted(Counter(ages).items())),
        "minors": sum(age < 18 for age in ages),
        "ages_100_or_more": sum(age >= 100 for age in ages),
        "realized_draw_counts": dict(selected),
        "scope": "Generation evidence only. Exact age/name agreement does not establish "
                 "semantic compliance, household eligibility, empirical representativeness "
                 "or faithful later behavior.",
        "execution_window_applied": window is not None,
    }
    for filename, value in (
        ("population-generation-audit.json", summary),
        ("population-generation-evidence.json", people),
    ):
        (args.folder / filename).write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(json.dumps({key: value for key, value in summary.items()
                      if key != "realized_draw_counts"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
