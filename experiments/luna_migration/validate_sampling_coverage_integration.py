"""Verify the exact compact-schema integration and its post-change validation lineage."""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "tinytroupe"
sys.path.insert(0, str(REPO))
from tinytroupe import utils
from tinytroupe.factory.sampling import restore_sampling_plan, sampling_plan_spec

baseline = ROOT / "sampling-coverage-integration-baseline"
replacements = {
    PACKAGE / "factory" / "sampling.py": baseline / "sampling.py",
    PACKAGE / "factory" / "prompts" / "sampling_plan.system.mustache":
        baseline / "sampling_plan.system.mustache",
}


def fingerprint(previous=False):
    digest = hashlib.sha256()
    paths = sorted(p for p in PACKAGE.rglob("*")
                   if p.is_file() and p.suffix in {".py", ".mustache"})
    for path in paths:
        digest.update("\0".join(path.relative_to(PACKAGE).parts).encode("utf-8"))
        digest.update(b"\0")
        digest.update((replacements[path] if previous and path in replacements else path).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


prior = fingerprint(previous=True)
assert prior == "000fcfb488ab982f259f778def4269a13e6972f0113eb5046d7c0f45a6b6fbd8"
current = fingerprint()
assert current != prior
experiment = ROOT / "realized-behavior-coverage-compact"
protocol = json.loads((experiment / "plan.json").read_text(encoding="utf-8"))
parameters = protocol["parameters"]
payload, schema = sampling_plan_spec(parameters)
assert schema == protocol["response_format"]
messages = utils.compose_initial_LLM_messages_with_templates(
    "sampling_plan.system.mustache", "sampling_plan.user.mustache", base_module_folder="factory",
    rendering_configs={"parameters": json.dumps(payload, ensure_ascii=False)},
)
assert messages == protocol["messages"]
native = json.loads((experiment / "native-response.json").read_text(encoding="utf-8"))
restored = restore_sampling_plan(parameters, native)["sample_plan"]
assert restored == json.loads((experiment / "sampling-plan.json").read_text(encoding="utf-8"))
validation = {}
for name in ["sampling-coverage-targeted", "sampling-coverage-core"]:
    path = ROOT / f"{name}.log"
    if not path.exists():
        validation[name] = {"status": "not run"}
        continue
    log = path.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(
        r"^=+ (\d+) passed(?:, (\d+) deselected)?(?:, (\d+) warnings?)? "
        r"in ([\d.]+)s(?: \([^)]+\))? =+$",
        log, re.M,
    )
    if not matches:
        validation[name] = {"status": "not passed or still running"}
        continue
    count, deselected, warnings, seconds = matches[-1]
    validation[name] = {
        "status": "passed", "passed": int(count), "deselected": int(deselected or 0),
        "warnings": int(warnings or 0), "elapsed_seconds": float(seconds),
    }
core_hash = ROOT / "sampling-coverage-core-source.txt"
if validation.get("sampling-coverage-core", {}).get("status") == "passed":
    assert core_hash.read_text(encoding="utf-8-sig").strip() == current
summary = {
    "status": validation.get("sampling-coverage-core", {}).get("status", "not run"),
    "previous_library_sha256": prior, "current_library_sha256": current,
    "only_library_files_changed_since_434": [
        str(path.relative_to(PACKAGE)) for path in replacements
    ],
    "proof": "Restoring only the two exact snapshotted pre-change files in memory "
             "reconstructs the previously validated 434-case library.",
    "experimental_messages_and_schema_match_integrated_factory": True,
    "saved_79_dimension_50_person_native_response_reconstructs_exactly": True,
    "public_sampling_plan_shape_unchanged": True,
    "tests": validation,
    "scientific_scope": "A selection-validity and contrast-coverage repair, not a "
                        "demonstrated survey-calibration repair. The prior six-person "
                        "screen predates integration and retains its separate lineage.",
}
(ROOT / "sampling-coverage-integration-validation.json").write_text(
    json.dumps(summary, indent=2), encoding="utf-8"
)
print(json.dumps(summary, indent=2))
