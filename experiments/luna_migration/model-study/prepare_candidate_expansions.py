"""Select one candidate per saved plan and build auditable expansion requests; no API calls."""

import argparse
import copy
import json
import random
from pathlib import Path

from audit_prompt_revision import load_lines
from model_case_study import digest, validate_case
from prompt_variants import transform_content


def build(base_corpus, plan_corpus, results, config_path, output, label):
    """Make reproducible uniform draws without inspecting or ranking candidate content."""
    if output.exists():
        raise FileExistsError(f"Use a new output directory: {output}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    count, seed = config["candidate_count"], config["selection_seed"]
    if type(count) is not int or count < 2 or type(seed) is not int:
        raise ValueError("Require candidate_count >= 2 and an integer selection_seed.")
    instruction = (config_path.parent / config["expansion_instruction"]).read_text(encoding="utf-8")
    bases, plans = {}, {}
    for row in load_lines(base_corpus):
        validate_case(row)
        source = row["experiment"]["source_case_id"]
        if source in bases:
            raise ValueError(f"Multiple expansion bases for {source}")
        bases[source] = row
    for row in load_lines(plan_corpus):
        validate_case(row)
        if row["case_id"] in plans:
            raise ValueError(f"Duplicate plan case: {row['case_id']}")
        plans[row["case_id"]] = row
    runs = load_lines(results)
    if not runs:
        raise ValueError("No plan responses.")
    cases, selections, seen, response_ids = [], [], set(), set()
    for run in sorted(runs, key=lambda x: (x["case_id"], x["condition_id"], x["replicate"])):
        identity = (run["case_id"], run["condition_id"], run["replicate"])
        if identity in seen:
            raise ValueError(f"Duplicate plan observation: {identity}")
        seen.add(identity)
        plan = plans[run["case_id"]]
        if run["request"] != plan["request"] or digest(run["request"]) != run["request_sha256"]:
            raise ValueError(f"Plan request mismatch: {identity}")
        if run["status"] != "completed":
            raise ValueError(f"Uncompleted plan: {identity}")
        response = run["response"]
        if response["id"] in response_ids:
            raise ValueError(f"Repeated response ID: {response['id']}")
        response_ids.add(response["id"])
        choice = response["choices"][0]
        if choice["finish_reason"] != "stop" or choice["message"].get("refusal"):
            raise ValueError(f"Incomplete or refused plan: {identity}")
        candidates = json.loads(choice["message"]["content"])["candidates"]
        if not isinstance(candidates, list) or len(candidates) != count:
            raise ValueError(f"Expected {count} candidates: {identity}")
        for candidate in candidates:
            if not isinstance(candidate, dict) or any(
                not candidate.get(key) for key in config["required_candidate_fields"]
            ):
                raise ValueError(f"Incomplete candidate: {identity}")
        draw_seed = int(digest({"seed": seed, "identity": identity}), 16)
        index = random.Random(draw_seed).randrange(count)
        source = plan["experiment"]["source_case_id"]
        case = copy.deepcopy(bases[source])
        case["case_id"] = f"{source}::{label}-{run['condition_id']}-{run['replicate']}"
        selection = {
            "case_id": case["case_id"], "plan_case_id": run["case_id"],
            "condition_id": run["condition_id"], "replicate": run["replicate"],
            "response_id": response["id"], "response_sha256": digest(response),
            "seed": seed, "draw_seed": str(draw_seed),
            "candidate_count": count, "selected_index_zero_based": index,
            "candidate_sha256": digest(candidates[index]),
            "selected_candidate": candidates[index],
        }
        case["experiment"].update({
            "variant": label, "parent_case_id": bases[source]["case_id"],
            "hypothesis": "Explicit proposal generation followed by external uniform candidate selection.",
            "selection": selection,
            "coverage_seeking_not_population_sample": True,
        })
        message = case["request"]["messages"][1]
        message["content"], matches = transform_content(message["content"], {
            "kind": "append",
            "text": "\n\n" + instruction + "\n" + json.dumps(candidates[index], ensure_ascii=False, indent=2),
        })
        if matches != 1:
            raise ValueError("Expected one text message for candidate expansion.")
        case["provenance"]["request_sha256"] = digest(case["request"])
        validate_case(case)
        cases.append(case)
        selections.append(selection)
    output.mkdir(parents=True)
    (output / "selected.jsonl").write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases), encoding="utf-8"
    )
    (output / "selection-audit.json").write_text(
        json.dumps(selections, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Built {len(cases)} expansions; selections frozen with seed {seed}. No API calls.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-corpus", type=Path, required=True)
    parser.add_argument("--plan-corpus", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    build(args.base_corpus, args.plan_corpus, args.results, args.config, args.output, args.label)
