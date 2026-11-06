"""Replicate full-size planning through the integrated production factory method."""

import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from tinytroupe import config_manager
from tinytroupe.clients import force_api_cache
from tinytroupe.factory import TinyPersonFactory
from review_notebook_evidence import cost_for_run

OUTPUT = ROOT / "integrated-coverage-plan"
OUTPUT.mkdir()
protocol = json.loads((ROOT / "realized-behavior-coverage-compact" /
    "plan.json").read_text(encoding="utf-8"))
parameters = protocol["parameters"]
lineage = json.loads((ROOT / "sampling-coverage-integration-validation.json").read_text(encoding="utf-8"))
(OUTPUT / "protocol.json").write_text(json.dumps({
    "library_sha256": lineage["current_library_sha256"],
    "parameters": parameters, "targeted_options": protocol["targeted_options"],
    "acceptance": protocol["acceptance"],
    "scope": "One fresh production-method plan, not a population survey or 100 model replications.",
}, ensure_ascii=False, indent=2), encoding="utf-8")
for key, value in [("model", "gpt-6-luna"), ("reasoning_model", "gpt-6-luna"),
                   ("reasoning_effort", "xhigh"), ("timeout", 600)]:
    config_manager.update(key, value)
force_api_cache(True, str(OUTPUT / "api.cache.json"))
factory = TinyPersonFactory(context=parameters["context"])
plan = factory._compute_sample_plan(**parameters)["sample_plan"]
(OUTPUT / "sampling-plan.json").write_text(
    json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
)
guaranteed = {
    name: {target: sum(d["quantity"] for d in plan if d["sampled_values"].get(name) == target)
           for target in targets}
    for name, targets in protocol["targeted_options"].items()
}
coverage = {name: {target: [] for target in targets}
            for name, targets in protocol["targeted_options"].items()}
for seed in range(100):
    factory.randomizer = random.Random(seed)
    samples = factory._flatten_sampling_plan(plan, sampling_dimensions=parameters["sampling_dimensions"])
    for name, targets in coverage.items():
        counts = Counter(p.get(name) for p in samples)
        for target in targets:
            targets[target].append(counts[target])
age_counts = Counter()
for directive in plan:
    group = directive["sampled_values"].get("age_distribution")
    if isinstance(group, str):
        age_counts[group] += directive["quantity"]
audit = {
    "library_sha256": lineage["current_library_sha256"],
    "directives": len(plan), "population": sum(d["quantity"] for d in plan),
    "guaranteed_predefined_contrasts": guaranteed,
    "all_four_predefined_contrasts_guaranteed": all(
        count > 0 for choices in guaranteed.values() for count in choices.values()
    ),
    "coverage_over_100_seeds": {
        name: {target: {"minimum": min(counts), "maximum": max(counts),
                        "seeds_without_value": counts.count(0)}
               for target, counts in targets.items()}
        for name, targets in coverage.items()
    },
    "age_distribution_singleton_allocations": age_counts,
    "semantic_review": "Pending; counts and guaranteed endpoints do not establish joint fidelity.",
}
(OUTPUT / "audit.json").write_text(
    json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
)
cache = json.loads((OUTPUT / "api.cache.json").read_text(encoding="utf-8"))
assert len(cache) == 1
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(
    encoding="utf-8"
))["models"]["gpt-6-luna"]
usage = cost_for_run(OUTPUT, {"started_at": "1970-01-01T00:00:00+00:00",
    "elapsed_seconds": max(response["created"] for response in cache.values()) + 1}, prices)
(OUTPUT / "receipt.json").write_text(json.dumps({
    "returned_responses": 1, "returned_usage_estimate": usage,
}, indent=2), encoding="utf-8")
print(json.dumps(audit, ensure_ascii=False, indent=2), flush=True)
