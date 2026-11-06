"""Audit explicitly listed experiment batches and aggregate usage without counting shard copies."""

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from mine_execution_cases import load_lines
from model_case_study import digest, validate_case
from review_phase_study import cost_with_bounds


def summarize(config_path, output):
    """Verify all canonical attempts and report usage-bearing failures as well as successes."""
    config = json.loads(config_path.read_text(encoding="utf-8"))
    root = config_path.parent
    prices = json.loads((root / config["prices"]).read_text(encoding="utf-8"))
    batches, response_ids, source_ids = [], set(), set()
    total_lower, total_upper = Decimal(0), Decimal(0)
    all_statuses, all_phases, all_sources = Counter(), Counter(), {}
    unknown = 0
    for spec in config["batches"]:
        cases = {}
        for case in load_lines(root / spec["cases"]):
            validate_case(case)
            if case["case_id"] in cases:
                raise ValueError("Duplicate prepared case in batch.")
            cases[case["case_id"]] = case
        seen, statuses, phases, attempts = set(), Counter(), Counter(), []
        lower, upper = Decimal(0), Decimal(0)
        for run in load_lines(root / spec["results"]):
            cid = run["case_id"]
            if cid in seen:
                raise ValueError("Repeated canonical attempt in batch.")
            seen.add(cid)
            case = cases[cid]
            if run["request"] != case["request"] or digest(run["request"]) != run["request_sha256"]:
                raise ValueError("Paid request differs from the prepared request.")
            if run["request"].get("reasoning_effort") != config["reasoning_effort"]:
                raise ValueError("Unexpected reasoning effort.")
            if run["request"].get("model") != config["model"]:
                raise ValueError("Unexpected model.")
            sid = case["experiment"]["source_case_id"]
            source_ids.add(sid)
            all_sources[sid] = case["phase"]
            statuses[run["status"]] += 1
            phases[case["phase"]] += 1
            row = {"case_id": cid, "source_case_id": sid, "phase": case["phase"],
                   "status": run["status"], "elapsed_seconds": run["elapsed_seconds"],
                   "request_sha256": run["request_sha256"]}
            response = run.get("response")
            if response:
                rid = response["id"]
                if rid in response_ids:
                    raise ValueError("The same API response appears in multiple canonical attempts.")
                response_ids.add(rid)
                cost = cost_with_bounds(response, prices)
                row.update(response_id=rid, cost=cost)
                lower += Decimal(cost["total_usd"] if cost["total_usd"] is not None else cost["minimum_usd"])
                upper += Decimal(cost["total_usd"] if cost["total_usd"] is not None else cost["maximum_usd"])
            else:
                unknown += 1
                row["error"] = run["error"]
            attempts.append(row)
        if seen != set(cases):
            raise ValueError("Missing or unexpected canonical attempts.")
        batches.append({"name": spec["name"], "attempt_count": len(attempts),
                        "statuses": dict(statuses), "phases": dict(phases),
                        "usage_list_price_bounds_usd": [str(lower), str(upper)],
                        "attempts": attempts})
        total_lower += lower
        total_upper += upper
        all_statuses.update(statuses)
        all_phases.update(phases)
    result = {
        "model": config["model"], "reasoning_effort": config["reasoning_effort"],
        "canonical_attempts": sum(all_statuses.values()), "unique_sources": len(source_ids),
        "unique_sources_by_phase": dict(Counter(all_sources.values())),
        "attempts_by_phase": dict(all_phases), "statuses": dict(all_statuses),
        "usage_list_price_bounds_usd": [str(total_lower), str(total_upper)],
        "attempts_without_usage_unknown_charge": unknown,
        "cost_scope": "All listed attempts with usage, including incomplete outputs; no shard duplicates. "
                      "Unreported usage is not assumed free. List-price estimate, not an invoice.",
        "batches": batches,
    }
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "batches"}, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summarize(args.config, args.output)
