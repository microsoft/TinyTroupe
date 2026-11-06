"""Build auditable diversity-seeking prompts from saved candidate drafts; never call an API."""

import argparse
import copy
import json
from pathlib import Path

from model_case_study import digest, validate_case
from prompt_variants import transform_content


def build(corpus, config_path, history_paths, output, label):
    """Append explicit prior-draft context without changing fixed persona requirements."""
    if output.exists():
        raise FileExistsError(f"Use a new output directory: {output}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    indexed = {case["case_id"]: case for case in map(json.loads, corpus.read_text(encoding="utf-8").splitlines())}
    histories = []
    for path in history_paths:
        for run in map(json.loads, path.read_text(encoding="utf-8").splitlines()):
            if run["status"] != "completed":
                raise ValueError(f"Review failed attempt before using this history: {path}")
            histories.append((path, run))
    instruction = (config_path.parent / config["instruction_file"]).read_text(encoding="utf-8")
    cases, audit = [], []
    for case_id in config["case_ids"]:
        case = copy.deepcopy(indexed[case_id])
        validate_case(case)
        source_id = case["experiment"]["source_case_id"]
        drafts, provenance = [], []
        for path, run in histories:
            if run["case_id"].split("::")[0] != source_id:
                continue
            value = json.loads(run["response"]["choices"][0]["message"]["content"])
            missing = [key for key in config["context_fields"] if key not in value]
            if missing:
                raise ValueError(f"Prior draft lacks context fields {missing}: {run['case_id']}")
            drafts.append({key: value[key] for key in config["context_fields"]})
            provenance.append({
                "file": path.name, "case_id": run["case_id"], "replicate": run["replicate"],
                "response_id": run["response"]["id"], "response_sha256": digest(run["response"]),
            })
        if not drafts:
            raise ValueError(f"No candidate history for {case_id}")
        message = case["request"]["messages"][config["message"]]
        message["content"], count = transform_content(message["content"], {
            "kind": "append", "text": "\n\n" + instruction + "\n" + json.dumps(drafts, ensure_ascii=False, indent=2),
        })
        if count != 1:
            raise ValueError("Prior drafts must be appended to one text message, not each envelope field.")
        case["case_id"] = source_id + "::" + label
        case["experiment"].update({
            "variant": label, "parent_case_id": case_id, "hypothesis": config["purpose"],
            "prior_candidate_provenance": provenance, "diversity_seeking_not_population_sample": True,
        })
        case["provenance"]["request_sha256"] = digest(case["request"])
        validate_case(case)
        cases.append(case)
        audit.append({"case_id": case["case_id"], "drafts": len(drafts), "sources": provenance})
    output.mkdir(parents=True)
    (output / "selected.jsonl").write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases), encoding="utf-8"
    )
    (output / "context-audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--history", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    build(args.corpus, args.config, args.history, args.output, args.label)
