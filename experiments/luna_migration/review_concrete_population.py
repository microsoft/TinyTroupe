"""Audit diagnostic draws, generated biographies, public answers and saved costs."""

import argparse
import html
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

from review_notebook_evidence import cost_for_run, public_actions

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "model-study"))
from model_case_study import decode_key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    folder = args.folder
    load = lambda name: json.loads((folder / name).read_text(encoding="utf-8"))
    personas, results, actions = load("personas.json"), load("results.json"), public_actions(load("agents.json"))
    assignments = {}
    for key, response in load("api.cache.json").items():
        request, _ = decode_key(key)
        prompt = request["messages"][-1]["content"]
        marker = "- Name, demographics and other characteristics:"
        if marker not in prompt:
            continue
        particulars, _ = json.JSONDecoder().raw_decode(html.unescape(prompt.split(marker, 1)[1]).lstrip())
        specification = json.loads(response["choices"][0]["message"]["content"])
        assignments[specification["name"]] = particulars
    findings, evidence = [], []
    if len(personas) != len(results):
        raise ValueError("Persona and extraction counts differ.")
    for (name, persona), result in zip(personas.items(), results):
        draws, talks = assignments[name], actions[name]
        expected_age = draws.get("parent_age", draws.get("age"))
        row = {
            "name": name, "drawn_age": expected_age, "actual_age": persona["age"],
            "age_matches": persona["age"] == expected_age,
            "drawn_child_age": draws.get("child_age_years"),
            "selected_name_preserved": draws["name"] == name,
            "extracted_name": result["name"],
            "extracted_name_matches": result["name"] == name,
            "public_answers": len(talks), "response": result["response"],
        }
        public = "\n\n".join(talk["text"] for talk in talks)
        ranking = re.search(r"Ranking:\s*([A-E](?:\s*[,>-]\s*[A-E]){4})", public, re.I)
        if ranking:
            row["public_ranking_matches"] = "-".join(re.findall("[A-E]", ranking[1].upper())) == result["response"]
        findings.append(row)
        evidence.extend([
            f"\n=== {name} ===", json.dumps(row, ensure_ascii=False),
            "DRAWS " + json.dumps(draws, ensure_ascii=False),
            "OCCUPATION " + json.dumps(persona.get("occupation"), ensure_ascii=False),
            "RELATIONSHIPS " + json.dumps(persona.get("relationships"), ensure_ascii=False),
            "PERSONALITY " + json.dumps(persona.get("personality"), ensure_ascii=False),
            "PUBLIC\n" + public, "EXTRACTED " + json.dumps(result, ensure_ascii=False),
        ])
    prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(encoding="utf-8"))
    report = {
        "count": len(results), "response_counts": dict(Counter(r["response"] for r in results)),
        "first_choice_counts": dict(Counter(r["response"].split("-")[0] for r in results)),
        "age_matches": sum(row["age_matches"] for row in findings),
        "ages": sorted(row["actual_age"] for row in findings),
        "name_deviations": sum(not row["selected_name_preserved"] for row in findings),
        "findings": findings,
        "cost": cost_for_run(folder, {"started_at": "1970-01-01T00:00:00+00:00",
                                    "elapsed_seconds": time.time()}, prices["models"]["gpt-6-luna"]),
        "scope": "Reduced diagnostic, not a complete notebook or empirical validation. "
                 "Early r1 and parent r2 used artificial participant names; later diagnostics use the actual factory name-generation method.",
    }
    (folder / "audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (folder / "public-evidence.txt").write_text("\n".join(evidence), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "findings"}, indent=2))


if __name__ == "__main__":
    main()
