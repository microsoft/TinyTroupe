"""Extract public evidence and returned-usage costs from isolated notebook runs."""

import argparse
import ast
import json
import re
import statistics
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def load(path):
    """Read an existing UTF-8 JSON artifact without hiding missing evidence."""
    return json.loads(path.read_text(encoding="utf-8"))


def cost_for_run(folder, record, prices):
    """Price saved unique API responses within this notebook's execution window."""
    start = datetime.fromisoformat(record["started_at"]).timestamp()
    end = start + record["elapsed_seconds"]
    total = Decimal(0)
    tokens = Counter()
    calls = 0
    missing_usage = 0
    for response in load(folder / "api.cache.json").values():
        created = response.get("created")
        if created is None or not start - 1 <= created <= end + 1:
            continue
        usage = response.get("usage")
        if not usage:
            missing_usage += 1
            continue
        calls += 1
        prompt = usage["prompt_tokens"]
        output = usage["completion_tokens"]
        details = usage.get("prompt_tokens_details") or {}
        cached = details.get("cached_tokens", 0) or 0
        writes = details.get("cache_write_tokens", 0) or 0
        if cached + writes > prompt:
            raise ValueError("Cache billing components exceed prompt tokens.")
        long = prompt > prices["long_context_threshold"]
        input_factor = Decimal(prices["long_input_multiplier"]) if long else Decimal(1)
        output_factor = Decimal(prices["long_output_multiplier"]) if long else Decimal(1)
        total += (
            (
                Decimal(prompt - cached - writes) * Decimal(prices["input"])
                + Decimal(cached) * Decimal(prices["cached_input"])
                + Decimal(writes) * Decimal(prices["cache_write"])
            ) * input_factor
            + Decimal(output) * Decimal(prices["output"]) * output_factor
        ) / Decimal(1_000_000)
        tokens.update(prompt=prompt, completion=output, cached=cached, writes=writes)
    return {
        "unique_saved_api_responses_in_run_window": calls,
        "responses_missing_usage": missing_usage,
        "tokens": dict(tokens),
        "usd": str(total),
        "basis": "Saved standard API list rates and returned usage; not an invoice. "
                 "Responses grouped by server creation time and notebook run window. "
                 "Failed requests without saved responses are not priced.",
    }


def public_actions(memories):
    """Read actual public TALK actions, never infer speech from private thought."""
    result = {}
    for name, events in memories.items():
        talks = []
        for event in events:
            if event.get("role") != "assistant":
                continue
            content = event.get("content")
            if not isinstance(content, dict):
                raise ValueError(f"Unexpected assistant memory representation for {name}.")
            action = content.get("action", {})
            if action.get("type") == "TALK":
                talks.append({
                    "timestamp": event.get("simulation_timestamp"),
                    "target": action.get("target", ""),
                    "text": action.get("content", ""),
                })
        result[name] = talks
    return result


def normalization_audit(folder, record):
    """Audit bounded IDs and full global-plan coverage from actual API payloads."""
    start = datetime.fromisoformat(record["started_at"]).timestamp()
    end = start + record["elapsed_seconds"]
    responses = sorted(load(folder / "api.cache.json").items(), key=lambda item: item[1]["created"])
    partitions = []
    current = None
    for key, response in responses:
        if not start - 1 <= response["created"] <= end + 1 or "'json_schema':" not in key:
            continue
        request = ast.literal_eval(key)[1]
        schema = request["response_format"]["json_schema"]["name"]
        if not schema.startswith("normalizer"):
            continue
        user = request["messages"][-1]["content"]
        payload = json.loads(user.split("Input (JSON):", 1)[1])
        output = json.loads(response["choices"][0]["message"]["content"])
        if schema in {"normalizer_plan", "normalizer"}:
            labels = output.get("labels") or [group["label"] for group in output["groups"]]
            current = {
                "labels": labels,
                "planned_sources": set(payload["items"].values()),
                "assigned_sources": set(),
                "assignment_calls": 0,
                "largest_batch": 0,
                "samples": {label: [] for label in labels},
                "sources_per_group": Counter(),
            }
            partitions.append(current)
            if schema == "normalizer_plan":
                current["groups"] = {
                    str(i): group for i, group in enumerate(output["groups"], 1)
                }
                continue
        if current is None:
            raise ValueError("Assignment call lacks its global plan.")
        if schema == "normalizer_assign" and payload["groups"] != current["groups"]:
            raise ValueError("Assignment changed its global theme definitions.")
        assignments, items = output["assignments"], payload["items"]
        if set(assignments) != set(items) or len(items) > 240:
            raise ValueError("Source IDs incomplete or assignment batch exceeded 240 items.")
        current["assignment_calls"] += 1
        current["largest_batch"] = max(current["largest_batch"], len(items))
        for item_id, group_id in assignments.items():
            if type(group_id) is not int or not 1 <= group_id <= len(current["labels"]):
                raise ValueError("Invalid group identifier.")
            label, source = current["labels"][group_id - 1], items[item_id]
            if source not in current["planned_sources"] or source in current["assigned_sources"]:
                raise ValueError("Unexpected or duplicate source assignment.")
            current["assigned_sources"].add(source)
            current["sources_per_group"][label] += 1
            if len(current["samples"][label]) < 3:
                current["samples"][label].append(source)
    result = []
    for partition in partitions:
        if partition["planned_sources"] != partition["assigned_sources"]:
            raise ValueError("Global theme plan did not receive complete source coverage.")
        result.append({
            "labels": partition["labels"],
            "source_count": len(partition["planned_sources"]),
            "assignment_calls": partition["assignment_calls"],
            "largest_batch": partition["largest_batch"],
            "sources_per_group": dict(partition["sources_per_group"]),
            "samples": partition["samples"],
        })
    return {
        "partitions": result,
        "total_distinct_sources_across_partitions": sum(p["source_count"] for p in result),
        "all_source_ids_covered": True,
        "all_assignment_batches_at_most_240": True,
        "global_theme_definitions_unchanged": True,
    }


def table_rows(tables):
    """Recover the notebook's complete named-response table."""
    table = tables.get("df")
    if table is None:
        return []
    return [dict(zip(table["columns"], row)) for row in table["data"]]


def check_responses(rows, talks):
    """Compare explicit public scores/rankings against extraction without guessing."""
    checks = []
    for row in rows:
        name, response = row.get("name"), row.get("response")
        speech = "\n".join(action["text"] for action in talks.get(name, []))
        if not speech.strip():
            explicit = "N/A"
        elif isinstance(response, str) and re.fullmatch(r"[A-E](?:-[A-E]){4}", response):
            ranking = re.search(
                r"Ranking\s*:\s*([A-E](?:\s*[,>\-]\s*[A-E]){4})",
                speech, flags=re.IGNORECASE,
            )
            explicit = "-".join(re.findall(r"[A-E]", ranking.group(1).upper())) if ranking else None
        elif str(response) in {"1", "2", "3", "4", "5"}:
            candidates = re.findall(
                r"(?:propensity(?:\s+(?:score|to buy))?(?:\s+(?:is|would be))?"
                r"|rating(?:\s+is)?|score(?:\s+is)?)\s*[:=]?\s*([1-5])\b",
                speech, flags=re.IGNORECASE,
            )
            leading = re.match(r"\s*(?:\*\*)?([1-5])\b", speech)
            explicit = candidates[0] if candidates else leading.group(1) if leading else None
        else:
            explicit = None
        checks.append({
            "name": name, "extracted": response, "parsed_public": explicit,
            "matches": str(response) == explicit if explicit is not None else None,
        })
    return checks


def summarize(folder, name, prices):
    """Write all public outputs alongside reproducible quantitative checks."""
    stem = folder / Path(name).stem
    record = load(stem.with_suffix(".run.json"))
    if record.get("status") != "completed":
        raise ValueError(f"Notebook not complete: {name}: {record.get('status')}")
    talks = public_actions(load(stem.with_suffix(".agents.json")))
    traits = load(stem.with_suffix(".traits.json"))
    tables = load(stem.with_suffix(".tables.json"))
    rows = table_rows(tables)
    ages = [t.get("age") for t in traits.values() if isinstance(t.get("age"), (int, float))]
    result = {
        "notebook": name,
        "folder": str(folder),
        "elapsed_seconds": record["elapsed_seconds"],
        "model": record["model"],
        "effort": record["effort"],
        "population": len(talks),
        "public_talk_count": sum(map(len, talks.values())),
        "agents_without_public_talk": [n for n, values in talks.items() if not values],
        "ages": dict(Counter(ages)),
        "minors": sum(age < 18 for age in ages),
        "response_counts": dict(Counter(str(row.get("response")) for row in rows)),
        "response_checks": check_responses(rows, talks),
        "usage_cost": cost_for_run(folder, record, prices),
    }
    normalization = normalization_audit(folder, record)
    if normalization["partitions"]:
        result["normalization_audit"] = normalization
    personality_labels = Counter()
    occupations = Counter()
    for profile in traits.values():
        occupation = profile.get("occupation")
        occupations[str(occupation.get("title")) if isinstance(occupation, dict) else str(occupation)] += 1
        personality = profile.get("personality")
        if isinstance(personality, dict):
            for trait in personality.get("traits", []):
                if isinstance(trait, str):
                    personality_labels[trait.split(":")[0].strip().lower()] += 1
    result["occupation_titles"] = dict(occupations)
    result["common_personality_labels"] = personality_labels.most_common(15)
    numeric = [float(row["response"]) for row in rows if str(row.get("response")) in set("12345")]
    if numeric:
        result["score_mean"] = statistics.mean(numeric)
        result["score_sample_sd"] = statistics.stdev(numeric) if len(numeric) > 1 else None
    rankings = [row["response"].split("-") for row in rows
                if isinstance(row.get("response"), str)
                and re.fullmatch(r"[A-E](?:-[A-E]){4}", row["response"])]
    if rankings:
        result["first_choices"] = dict(Counter(r[0] for r in rankings))
        borda = Counter()
        for ranking in rankings:
            for i, option in enumerate(ranking):
                borda[option] += 4 - i
        result["borda"] = dict(borda)
    evidence = []
    row_by_name = {row["name"]: row for row in rows}
    for agent_name, actions in talks.items():
        evidence.append(f"\n=== {agent_name} ===")
        profile = traits.get(agent_name, {})
        occupation = profile.get("occupation")
        evidence.append(json.dumps({
            "age": profile.get("age"),
            "occupation": occupation.get("title") if isinstance(occupation, dict) else occupation,
        }, ensure_ascii=False))
        for action in actions:
            evidence.append(f"\nTALK {action['timestamp']} -> {action['target']}\n{action['text']}")
        if agent_name in row_by_name:
            evidence.append("\nEXTRACTED\n" + json.dumps(row_by_name[agent_name], ensure_ascii=False))
    stem.with_suffix(".public-evidence.txt").write_text("\n".join(evidence), encoding="utf-8")
    stem.with_suffix(".review-metrics.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result


def main():
    """Extract evidence for every manifest entry or one named notebook."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prices = load(args.prices)["models"]
    results = []
    for lane in load(args.manifest).values():
        for job in lane:
            folder = args.artifact_root / job["id"]
            record = load((folder / Path(job["name"]).stem).with_suffix(".run.json"))
            result = summarize(folder, job["name"], prices[record["model"]])
            results.append(result)
            print(json.dumps({k: result[k] for k in (
                "notebook", "population", "public_talk_count", "response_counts", "usage_cost"
            )}, ensure_ascii=False))
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
