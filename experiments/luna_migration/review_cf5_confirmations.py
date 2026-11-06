"""Audit completed frozen-source confirmations while retaining honest pending states."""

import json
import re
from pathlib import Path

from audit_notebook_runs import audit
from review_notebook_evidence import summarize
from run_notebook_comparison import library_fingerprint

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
core_log = (ROOT / "text-transport-core.log").read_text(encoding="utf-8", errors="replace")
core_match = re.search(r"429 passed, 440 deselected, 7 warnings in ([\d.]+)s", core_log)
core = {"status": "Pending"}
if core_match:
    recorded_library = (ROOT / "text-transport-core-source.txt").read_text(
        encoding="utf-8-sig"
    ).strip()
    current_library = library_fingerprint(REPO / "tinytroupe")
    if recorded_library != current_library:
        raise ValueError("Current implementation differs from the completed core regression.")
    core = {
        "status": "Passed", "passed": 429, "deselected": 440, "warnings": 7,
        "elapsed_seconds": float(core_match[1]),
        "library_sha256": recorded_library, "library_still_matches": True,
        "command": 'pytest -s --use_cache -m "core and not slow"',
    }
(ROOT / "cf5-core-result.json").write_text(json.dumps(core, indent=2), encoding="utf-8")
print("CORE", core)
manifest = json.loads((ROOT / "cf5-manifest.json").read_text(encoding="utf-8"))
assignments = {
    job["name"].removesuffix(".ipynb"): job["id"]
    for jobs in manifest.values() for job in jobs
}
execution = audit(REPO / "examples", ROOT, assignments, "gpt-6-luna", "xhigh")
(ROOT / "cf5-execution-audit.json").write_text(
    json.dumps(execution, ensure_ascii=False, indent=2), encoding="utf-8"
)
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(encoding="utf-8"))["models"]
metrics = []
for row in execution["runs"]:
    print(row["folder"], row["status"], "execution_audit", row.get("execution_audit_passed"))
    if row["status"] != "completed":
        continue
    if row["execution_audit_passed"] is not True:
        raise ValueError(f"Execution audit failed: {row}")
    result = summarize(ROOT / row["folder"], row["name"] + ".ipynb", prices["gpt-6-luna"])
    metrics.append(result)
    print(json.dumps({key: result[key] for key in [
        "notebook", "population", "public_talk_count", "response_counts", "usage_cost"
    ]}, ensure_ascii=False))
(ROOT / "cf5-current-metrics.json").write_text(
    json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
)
