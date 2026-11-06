"""Audit isolated reaction-prompt trials without treating higher ratings as truth."""

import ast
import hashlib
import json
import statistics
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from review_notebook_evidence import check_responses, cost_for_run, public_actions


ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(encoding="utf-8"))
prices = prices["models"]["gpt-6-luna"]
original = (REPO / "tinytroupe" / "agent" / "prompts" / "tiny_person.v2.mustache").read_text(
    encoding="utf-8"
)
panel = json.loads(
    (ROOT / "crossed-persona-mini-generation" / "selection-mini.json").read_text(encoding="utf-8")
)
expected = {row["name"]: row["persona"] for row in panel}
holdout = json.loads((ROOT / "situated-decision-holdout.json").read_text(encoding="utf-8"))
holdout_expected = {row["name"]: row["persona"] for row in holdout}
control_source = json.loads(
    (ROOT / "subjective-choice-controls.json").read_text(encoding="utf-8")
)
control_expected = {row["name"]: row["persona"] for row in control_source}
notebook = json.loads(
    (REPO / "examples" / "Bottled Gazpacho Market Research 5 (with behavior correction).ipynb")
    .read_text(encoding="utf-8")
)
original_stimuli = {}
for cell in notebook["cells"]:
    if cell["cell_type"] == "code":
        for node in ast.parse("".join(cell["source"])).body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in {
                        "interviewer_introduction", "interviewer_main_question", "inner_monologue"
                    }:
                        original_stimuli[target.id] = ast.literal_eval(node.value)
folders = [
    "fixed-persona-gaz-new-reactions",
    "fixed-persona-gaz-persona-deliberation",
    "fixed-persona-gaz-reaction-repair",
    "fixed-persona-gaz-control-baseline",
    "fixed-persona-gaz-control-repair",
    "fixed-persona-gaz-neutral-identity",
    "fixed-persona-gaz-lean-interpretation",
    "fixed-persona-gaz-natural-thought",
    "fixed-persona-gaz-neutral-introduction",
    "fixed-persona-gaz-natural-framing",
    "fixed-persona-gaz-summer",
    "fixed-persona-gaz-autumn",
    "fixed-persona-gaz-text-transport",
    "fixed-persona-gaz-text-controls",
    "fixed-persona-gaz-situated-decisions",
    "fixed-persona-gaz-holdout-text",
    "fixed-persona-gaz-holdout-situated",
    "fixed-persona-gaz-situated-controls",
    "fixed-persona-gaz-minimal-actor",
    "fixed-persona-gaz-minimal-controls",
    "fixed-persona-gaz-low-effort",
]
summary = {
    "status": "Prompt variants not accepted. Actor transport and memory correctness repairs "
              "passed core regressions; full confirmations remain separate and empirical calibration unresolved.",
    "production_prompt_sha256": hashlib.sha256(
        (REPO / "tinytroupe" / "agent" / "prompts" / "tiny_person.v2.mustache").read_bytes()
    ).hexdigest(),
    "experiments": {},
    "limitations": [
        "Single small panel, not a population calibration or a precise causal estimate.",
        "Higher ratings alone do not establish better simulated behavior.",
        "Synthetic preference controls are not empirical observations or unchanged participants.",
        "Original rated question, quality thresholds, and model retained. Effort is xhigh except "
        "the explicitly labeled low-effort diagnostic, which changes actor, evaluation and extraction effort.",
        "Introduction, private thought, and season changes are recorded experimental conditions.",
        "Only saved returned usage is priced; failed unreturned requests remain unpriced.",
    ],
}
total = Decimal(0)
for name in folders:
    folder = ROOT / name
    receipt_path = folder / "receipt.json"
    if not receipt_path.exists():
        summary["experiments"][name] = {"status": "Awaiting receipt; not audited."}
        continue
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    data = json.loads((folder / "gaz.json").read_text(encoding="utf-8"))
    controls = bool(receipt.get("synthetic_preference_controls"))
    actual = {row["name"]: row["persona"] for row in data["selection"]}
    expected_personas = (
        control_expected if controls else holdout_expected if "-holdout-" in name else expected
    )
    if actual != expected_personas:
        raise ValueError(f"{name}: persona payload changed unexpectedly.")
    expected_effort = "low" if name == "fixed-persona-gaz-low-effort" else "xhigh"
    if receipt["model"] != "gpt-6-luna" or receipt["requested_effort"] != expected_effort:
        raise ValueError(f"{name}: unexpected model or requested effort.")
    if receipt["require_unsupervised_control"] or receipt["require_regular_purchases_control"]:
        raise ValueError(f"{name}: original survey was changed.")
    if "stimuli" in data:
        expected_stimuli = dict(original_stimuli)
        for key, argument in [
            ("interviewer_introduction", "introduction_file"),
            ("inner_monologue", "inner_monologue_file"),
        ]:
            if receipt.get(argument):
                expected_stimuli[key] = Path(receipt[argument]).read_text(encoding="utf-8")
        if data["stimuli"] != expected_stimuli:
            raise ValueError(f"{name}: saved stimuli do not match the recorded condition.")
    if receipt.get("requested_initial_datetime"):
        if data["initial_world_datetime"] != receipt["requested_initial_datetime"]:
            raise ValueError(f"{name}: simulation datetime does not match the condition.")
    if receipt.get("variant_sha256"):
        if hashlib.sha256((folder / "variant.mustache").read_bytes()).hexdigest() != receipt["variant_sha256"]:
            raise ValueError(f"{name}: variant hash does not match receipt.")
        variant = (folder / "variant.mustache").read_text(encoding="utf-8")
        for marker in ["### Input and output formats", "## Current cognitive state"]:
            suffix = variant.split(marker, 1)[1]
            baseline = original.split(marker, 1)[1]
            if marker == "### Input and output formats":
                suffix = suffix.split("\n## ", 1)[0].rstrip()
                baseline = baseline.split("\n## ", 1)[0].rstrip()
            if suffix != baseline:
                raise ValueError(f"{name}: contract changed after {marker}.")
    talks = public_actions(data["agents"])
    checks = check_responses(data["results"], talks)
    if any(check["matches"] is False for check in checks):
        raise ValueError(f"{name}: public/extracted mismatch.")
    review = [
        {"name": row["name"], "extracted": row["response"],
         "public": talks[row["name"]], "justification": row["justification"]}
        for row in data["results"]
    ]
    (folder / "public-review.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in review) + "\n",
        encoding="utf-8"
    )
    ratings = [int(row["response"]) for row in data["results"]]
    cost = cost_for_run(
        folder,
        {"started_at": "1970-01-01T00:00:00+00:00",
         "elapsed_seconds": datetime.now(timezone.utc).timestamp()},
        prices,
    )
    total += Decimal(cost["usd"])
    result = {
        "status": "Completed; qualitative acceptance not implied.",
        "synthetic_controls": controls,
        "unchanged_persona_payloads": True,
        "counts": dict(Counter(ratings)),
        "mean": statistics.mean(ratings),
        "sample_sd": statistics.stdev(ratings),
        "responses": data["results"],
        "public_extraction_checks": checks,
        "manual_public_review_required": [
            row["name"] for row in checks if row["matches"] is None
        ],
        "returned_usage_estimate": cost,
        "variant_sha256": receipt["variant_sha256"],
        "introduction_file": receipt.get("introduction_file"),
        "inner_monologue_file": receipt.get("inner_monologue_file"),
        "requested_initial_datetime": receipt.get("requested_initial_datetime"),
    }
    if controls:
        mapped = {row["name"]: int(row["response"]) for row in data["results"]}
        result["positive_control_passes"] = mapped[control_source[0]["name"]] >= 4
        result["negative_control_passes"] = mapped[control_source[1]["name"]] <= 2
    summary["experiments"][name] = result
summary["new_trials_returned_usage_usd"] = str(total)
(ROOT / "reaction-experiment-summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps({
    name: {"status": value["status"], "mean": value.get("mean"),
           "manual_review": value.get("manual_public_review_required")}
    for name, value in summary["experiments"].items()
}, ensure_ascii=False, indent=2))
print("New trials returned-usage estimate USD:", total)
