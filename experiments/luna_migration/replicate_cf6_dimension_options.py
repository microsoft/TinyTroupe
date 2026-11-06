"""Recompute the original full-population vocabulary with coherent-option instructions."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from run_notebook_comparison import library_fingerprint
from review_notebook_evidence import cost_for_run
from tinytroupe import config_manager
from tinytroupe.clients import force_api_cache
from tinytroupe.factory import TinyPersonFactory

OUTPUT = ROOT / "cf6-coherent-dimensions"
OUTPUT.mkdir(exist_ok=True)
assert not (OUTPUT / "protocol.json").exists(), "Do not overwrite a recorded experiment."
original = json.loads((ROOT / "cf6-dimension-request.json").read_text(encoding="utf-8"))
parameter_text = original["request"]["messages"][-1]["content"].split(
    "## Named parameters", 1
)[1].lstrip()
parameters, parameter_end = json.JSONDecoder().raw_decode(parameter_text)
assert set(parameters) == {"sampling_space_description"}
fingerprint = library_fingerprint(REPO / "tinytroupe")
(OUTPUT / "protocol.json").write_text(json.dumps({
    "library_sha256": fingerprint, "parameters": parameters,
    "original_request_suffix": parameter_text[parameter_end:],
    "hypothesis": "Separately selectable opposing ends remove the observed disjunctive "
                  "novelty-resistance option before planning.",
    "constants": "Original full population source and additional instructions; actual "
                 "production dimension method; Luna/xhigh and JSON mode.",
    "acceptance": "Explicit separately selectable resistance and impulsive adoption; "
                  "no category combining them as alternatives. Also review original "
                  "food-adventure coverage. No downstream ratings are used.",
    "scope": "A full-input vocabulary replication, not a new complete notebook or "
             "an empirical rating-calibration result.",
}, ensure_ascii=False, indent=2), encoding="utf-8")
for key, value in [("model", "gpt-6-luna"), ("reasoning_model", "gpt-6-luna"),
                   ("reasoning_effort", "xhigh"), ("timeout", 600)]:
    config_manager.update(key, value)
force_api_cache(True, str(OUTPUT / "api.cache.json"))
dimensions = TinyPersonFactory()._compute_sampling_dimensions(**parameters)
(OUTPUT / "dimensions.json").write_text(
    json.dumps(dimensions, ensure_ascii=False, indent=2), encoding="utf-8"
)
assert library_fingerprint(REPO / "tinytroupe") == fingerprint
cache = json.loads((OUTPUT / "api.cache.json").read_text(encoding="utf-8"))
assert len(cache) == 1
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(
    encoding="utf-8"
))["models"]["gpt-6-luna"]
usage = cost_for_run(OUTPUT, {"started_at": "1970-01-01T00:00:00+00:00",
    "elapsed_seconds": max(r["created"] for r in cache.values()) + 1}, prices)
(OUTPUT / "receipt.json").write_text(json.dumps({
    "returned_responses": 1, "returned_usage_estimate": usage,
    "source_unchanged": True, "semantic_review": "Pending.",
}, indent=2), encoding="utf-8")
print(json.dumps([d for d in dimensions["dimensions"]
                  if d["name"] in ["culinary_tastes", "attitude_toward_new_products"]],
                 ensure_ascii=False), flush=True)
