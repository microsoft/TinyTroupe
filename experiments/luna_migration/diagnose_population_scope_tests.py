"""Explain the failed semantic assertions without changing their generated evidence."""

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from model_case_study import decode_key
from tinytroupe import config_manager
from tinytroupe.clients import client, force_api_cache

selected = []
cache = json.loads((REPO / "openai_api_cache.json").read_text(encoding="utf-8"))
for key, response in cache.items():
    if "This biography describes one American parent of a child currently aged 4 or 5" not in key:
        continue
    request, _ = decode_key(key)
    selected.append({
        "proposition": request["messages"][-1]["content"],
        "original_verdict": response["choices"][0]["message"]["content"],
    })
assert len(selected) == 2
output = ROOT / "population-scope-test-diagnostics"
output.mkdir()
config_manager.update("model", "gpt-6-luna")
config_manager.update("reasoning_model", "gpt-6-luna")
config_manager.update("reasoning_effort", "xhigh")
config_manager.update("timeout", 600)
force_api_cache(True, str(output / "api.cache.json"))


def diagnose(case):
    reply = client().send_message([
        {"role": "system", "content": (
            "Audit the supplied proposition and biography. Do not rewrite or repair either. "
            "Return a JSON object with separate checks for parent_eligibility, food_preference, "
            "absence_of_population_catalogs, and only_this_persons_own_characteristics. "
            "Each check must contain passes (boolean), evidence (a verbatim quote or null), "
            "and explanation. Then give overall_failure_reason. Distinguish references to "
            "actual relatives from hypothetical alternative trait catalogs."
        )},
        {"role": "user", "content": case["proposition"]},
    ], frequency_penalty=0.0, presence_penalty=0.0)
    if reply is None:
        raise RuntimeError("No assertion-diagnostic response returned.")
    case["diagnostic"] = json.loads(reply["content"])
    print(json.dumps(case["diagnostic"], ensure_ascii=False), flush=True)
    return case


with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(diagnose, selected))
(output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
