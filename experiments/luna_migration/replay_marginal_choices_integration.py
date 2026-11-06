"""Replay the accepted original-input response through the actual integrated factory."""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from run_notebook_comparison import library_fingerprint
from tinytroupe import config_manager, utils
from tinytroupe.clients import force_api_cache
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.factory.sampling import sampling_plan_spec

candidate = ROOT / "demographic-coverage-budget-r4"
protocol = json.loads((candidate / "protocol.json").read_text(encoding="utf-8"))
parameters = protocol["parameters"]
payload, schema = sampling_plan_spec(parameters)
messages = utils.compose_initial_LLM_messages_with_templates(
    "sampling_plan.system.mustache", "sampling_plan.user.mustache",
    base_module_folder="factory",
    rendering_configs={"parameters": json.dumps(payload, ensure_ascii=False)},
)
assert messages == protocol["messages"]
assert schema == protocol["response_format"]
current = library_fingerprint(REPO / "tinytroupe")
assert current == (ROOT / "marginal-choices-core-source.txt").read_text(
    encoding="utf-8"
).strip()
output = ROOT / "marginal-choices-integration"
output.mkdir()
cache_path = output / "api.cache.json"
shutil.copy2(candidate / "api.cache.json", cache_path)
before = json.loads(cache_path.read_text(encoding="utf-8"))
assert len(before) == 1
for key, value in [("model", "gpt-6-luna"), ("reasoning_model", "gpt-6-luna"),
                   ("reasoning_effort", "xhigh"), ("timeout", 600)]:
    config_manager.update(key, value)
force_api_cache(True, str(cache_path))
factory = TinyPersonFactory(context=parameters["context"])
result = factory._compute_sample_plan(**parameters)
assert result["sample_plan"] == json.loads(
    (candidate / "sampling-plan.json").read_text(encoding="utf-8")
)
assert json.loads(cache_path.read_text(encoding="utf-8")) == before
assert library_fingerprint(REPO / "tinytroupe") == current
receipt = {
    "status": "passed",
    "library_sha256": current,
    "actual_factory_method": "TinyPersonFactory._compute_sample_plan",
    "wire_messages_and_schema": "Exact accepted revision-4 messages and schema.",
    "population": sum(row["quantity"] for row in result["sample_plan"]),
    "directives": len(result["sample_plan"]),
    "cache": "Replayed the one saved accepted response; no new cache entry or changed response.",
    "new_returned_response_count": 0,
    "scope": "Production integration replay, not an independent model replication or survey.",
}
(output / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt, indent=2))
