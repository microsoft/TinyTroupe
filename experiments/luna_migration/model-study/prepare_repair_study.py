"""Prepare configuration-driven prompt repairs with unchanged source evidence and explicit adapters."""

import argparse
import copy
import json
from pathlib import Path

from mine_execution_cases import load_lines
from model_case_study import digest, validate_case
from normalization_assignments import indexed_request, source_items
from sampling_selections import indexed_request as indexed_sampling_request


def prepare(config_path, output):
    """Build only explicitly selected requests; never execute or overwrite an experiment."""
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    sources = {}
    for name in config["corpora"]:
        for case in load_lines(config_path.parent / name):
            if case["case_id"] in sources and sources[case["case_id"]] != case:
                raise ValueError("Conflicting source observations.")
            sources[case["case_id"]] = case
    cases, used, audit = [], {}, []
    for recipe in config["recipes"]:
        instruction = (config_path.parent / recipe["instruction_file"]).read_text(encoding="utf-8")
        for source_id in recipe["cases"]:
            source = sources[source_id]
            validate_case(source)
            used[source_id] = source
            for repetition in range(recipe.get("repetitions", config.get("repetitions", 1))):
                case = copy.deepcopy(source)
                case["case_id"] = f"{source_id}::{recipe['id']}::r{repetition + 1}"
                adapter = recipe.get("adapter", "append_system")
                if adapter == "indexed_normalization":
                    messages, schema = indexed_request(source, instruction)
                    case["request"]["messages"] = messages
                    case["request"]["response_format"] = schema
                    items, _ = source_items(source)
                    decoded = json.loads(messages[1]["content"])["items"]
                    assert list(decoded.values()) == items
                elif adapter == "indexed_sampling":
                    messages, schema = indexed_sampling_request(
                        source, instruction, recipe.get("categorical_encoding", "identifiers"))
                    case["request"]["messages"] = messages
                    case["request"]["response_format"] = schema
                elif adapter == "append_system":
                    focused = instruction
                    marker = recipe.get("focus_user_prefix_before")
                    if marker:
                        prefixes = [m["content"].split(marker, 1)[0] for m in source["request"]["messages"]
                                    if m["role"] == "user" and isinstance(m.get("content"), str)
                                    and marker in m["content"]]
                        if len(prefixes) != 1:
                            raise ValueError("Require one unambiguous original user request prefix.")
                        focused += "\n\n# Current request, verbatim from the original user\n\n" + prefixes[0]
                    case["request"]["messages"].append({"role": "system", "content": focused})
                    assert case["request"]["messages"][:-1] == source["request"]["messages"]
                else:
                    raise ValueError(f"Unknown adapter: {adapter}")
                protected = set(source["request"]) - {"messages", "response_format"}
                assert all(case["request"][k] == source["request"][k] for k in protected)
                case["provenance"]["request_sha256"] = digest(case["request"])
                case["provenance"]["normalization"].append(
                    f"Experimental {adapter}; original_response remains historical, not a treatment result.")
                case["experiment"] = {
                    "stage": config["stage"], "source_case_id": source_id,
                    "variant": recipe["id"], "adapter": adapter, "repetition": repetition + 1,
                    "hypothesis": recipe["hypothesis"], "original_request_sha256": digest(source["request"]),
                    "instruction_sha256": digest(instruction),
                    "categorical_encoding": recipe.get("categorical_encoding"),
                    "source_selection": "Previously reviewed cases are development, regardless of earlier split labels.",
                }
                validate_case(case)
                cases.append(case)
                audit.append({"case_id": case["case_id"], **case["experiment"]})
    if not cases or len({c["case_id"] for c in cases}) != len(cases):
        raise ValueError("Require a nonempty set of unique prepared case IDs.")
    output.mkdir(parents=True)
    for name, rows in [("cases.jsonl", cases), ("sources.jsonl", used.values())]:
        (output / name).write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in rows),
                                   encoding="utf-8")
    (output / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "frozen-config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"Prepared {len(cases)} requests on {len(used)} sources; no API calls.")
    return cases


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.config, args.output)
