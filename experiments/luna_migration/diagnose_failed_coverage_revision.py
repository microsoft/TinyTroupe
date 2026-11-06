"""Preserve an invalid returned plan without repairing or replacing it."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from model_case_study import decode_key
from review_notebook_evidence import cost_for_run
from tinytroupe.factory.sampling import restore_sampling_plan, sampling_plan_spec

folder = ROOT / "realized-behavior-coverage-r2"
protocol = json.loads((folder / "plan.json").read_text(encoding="utf-8"))
baseline = json.loads((ROOT / "realized-behavior-coverage" /
    "production_baseline_replication.json").read_text(encoding="utf-8"))
cache = json.loads((folder / "api.cache.json").read_text(encoding="utf-8"))
assert len(cache) == 1
key, response = next(iter(cache.items()))
request, model_schema = decode_key(key)
assert model_schema is None
_, schema = sampling_plan_spec(baseline["parameters"])
assert request["response_format"] == schema
assert request["model"] == "gpt-6-luna" and request["reasoning_effort"] == "xhigh"
assert request["messages"][1:] == baseline["messages"][1:]
marker = "Population eligibility is mandatory in every directive"
assert request["messages"][0]["content"] == baseline["messages"][0]["content"].replace(
    marker, protocol["candidate_paragraph"] + "\n" + marker
)
assert response["choices"][0]["finish_reason"] == "stop"
native = json.loads(response["choices"][0]["message"]["content"])
(folder / "native-response.json").write_text(
    json.dumps(native, ensure_ascii=False, indent=2), encoding="utf-8"
)
empty = []
dimensions = baseline["parameters"]["sampling_dimensions"]["dimensions"]
for directive in native["sample_plan"]:
    for index, dimension in enumerate(dimensions, 1):
        selected = directive["sampled_values"][str(index)]
        if isinstance(selected, dict) and not any(selected.values()):
            empty.append({"directive": directive["id"], "dimension": dimension["name"]})
assert empty
try:
    restore_sampling_plan(baseline["parameters"], native)
except ValueError as error:
    assert str(error) == "Categorical selections cannot be empty."
    rejection = str(error)
else:
    raise AssertionError("The invalid returned plan was unexpectedly accepted.")
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(
    encoding="utf-8"
))["models"]["gpt-6-luna"]
usage = cost_for_run(folder, {"started_at": "1970-01-01T00:00:00+00:00",
    "elapsed_seconds": response["created"] + 1}, prices)
summary = {
    "status": "Rejected by the unchanged production validator; no repair or redraw.",
    "condition": "concrete_contrast_coverage_v2",
    "response_id": response["id"], "finish_reason": "stop",
    "request_fidelity": "Strict production schema, original input and recorded paragraph verified.",
    "rejection": rejection, "empty_categorical_selections": empty,
    "observed_transport_timeout_before_returned_retry": 1,
    "returned_responses": 1, "returned_usage_estimate": usage,
    "unreturned_attempt_cost": "Unknown; not included in returned-usage estimate.",
    "production_changed": False,
}
(folder / "failure.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
