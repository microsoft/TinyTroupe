"""Verify the generator-only change after the validated 432-case implementation."""

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

from run_notebook_comparison import library_fingerprint
from review_notebook_evidence import cost_for_run

ROOT = Path(__file__).parent
PACKAGE = Path(__file__).resolve().parents[2] / "tinytroupe"
sys.path.insert(0, str(ROOT / "model-study"))
from model_case_study import decode_key

earlier = json.loads((ROOT / "cf5-validation-lineage.json").read_text(encoding="utf-8"))
target = PACKAGE / "factory" / "prompts" / "generate_person.mustache"
addition = next(ast.literal_eval(node.value) for node in ast.parse(
    (ROOT / "probe_population_scope.py").read_text(encoding="utf-8")
).body if isinstance(node, ast.Assign) and any(
    isinstance(t, ast.Name) and t.id == "ADDITION" for t in node.targets
))
raw = target.read_bytes()
normalized = raw.replace(b"\r\n", b"\n")
block = b"\n\n" + addition.strip().encode("utf-8")
assert normalized.count(block) == 1
prior_lf = normalized.replace(block, b"")
paths = sorted(p for p in PACKAGE.rglob("*")
               if p.is_file() and p.suffix in {".py", ".mustache"})
matches = []
for prior in [prior_lf, prior_lf.replace(b"\n", b"\r\n")]:
    digest = hashlib.sha256()
    for path in paths:
        digest.update("\0".join(path.relative_to(PACKAGE).parts).encode("utf-8"))
        digest.update(b"\0")
        digest.update(prior if path == target else path.read_bytes())
        digest.update(b"\0")
    if digest.hexdigest() == earlier["current_library_sha256"]:
        matches.append(hashlib.sha256(prior).hexdigest())
assert len(matches) == 1, "The new library cannot be reconstructed by undoing only this generator paragraph."
current = library_fingerprint(PACKAGE)
core = {"status": "Pending"}
log = ROOT / "population-scope-core.log"
if log.exists():
    match = re.search(
        r"434 passed, 440 deselected, (\d+) warnings in ([\d.]+)s",
        log.read_text(encoding="utf-8", errors="replace"),
    )
    if match:
        recorded = (ROOT / "population-scope-core-source.txt").read_text(encoding="utf-8-sig").strip()
        assert current == recorded
        core = {
            "status": "Passed", "passed": 434, "deselected": 440,
            "warnings": int(match[1]), "elapsed_seconds": float(match[2]),
            "library_sha256": recorded,
        }
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(encoding="utf-8"))["models"]["gpt-6-luna"]
usage = {}
for name, count in [
    ("population-scope-trial", 3),
    ("population-scope-actor-replays", 6),
    ("population-scope-test-diagnostics", 2),
]:
    folder = ROOT / name
    cache = json.loads((folder / "api.cache.json").read_text(encoding="utf-8"))
    assert len(cache) == count
    assert len({value["id"] for value in cache.values()}) == count
    for key in cache:
        request, _ = decode_key(key)
        assert request["model"] == "gpt-6-luna" and request["reasoning_effort"] == "xhigh"
    usage[name] = cost_for_run(folder, {
        "started_at": "1970-01-01T00:00:00+00:00",
        "elapsed_seconds": max(value["created"] for value in cache.values()) + 1,
    }, prices)
report = {
    "status": core["status"],
    "previous_validated_library_sha256": earlier["current_library_sha256"],
    "current_library_sha256": current,
    "only_library_file_changed_since_432": str(target.relative_to(PACKAGE)),
    "prior_generator_template_sha256": matches[0],
    "generator_template_sha256": hashlib.sha256(raw).hexdigest(),
    "proof": "Undoing only the new generator paragraph, in memory, exactly reproduces the "
             "432-case library fingerprint. Actor/runtime and final extraction implementation are unchanged.",
    "current_source_core": core,
    "generator_cases": {
        "returned": 3, "catalogs_removed": 3, "names_and_ages_preserved": 3,
        "manual_review": "Food-adventurous early adopter, traditional-food early adopter and "
                         "novelty-resistant mild-food adult retain the corresponding individual preferences. "
                         "No exhaustive audit of every sampled dimension is claimed.",
        "scope": "A paragraph-equivalent preintegration candidate, with different surrounding blank-line "
                 "spacing. The later real-factory core cases exercise the exact production template.",
        "request_format_caveat": "The three raw generator replays omitted the production factory's "
                                 "response_format=json_object setting. They are exploratory content "
                                 "checks, not exact-production request replays. The two real-factory "
                                 "core cases independently exercise production JSON mode.",
    },
    "regression_development": {
        "initial_targeted_run": "2 passed, 2 failed, 56 deselected.",
        "cause": "The two new assertions unintentionally prohibited descriptions of actual relatives. "
                 "Separate diagnostics verified eligibility, food preference and catalog absence in both "
                 "unchanged biographies; only that unintended restriction failed.",
        "correction": "The assertion now explicitly permits actual relatives while retaining all intended "
                      "eligibility, food-preference and no-population-catalog requirements.",
        "final_targeted_run": "2 passed, 58 deselected, 3 warnings in 43.18 seconds.",
        "earlier_existing_guards": "The existing parent-eligibility and infant-age cases passed on the new "
                                   "production prompt in the initial four-case run.",
    },
    "actor_replays": {
        "returned": 6,
        "manual_public_scores": {
            "Diego Andr\u00e9s Quintana": {"original": 3, "catalog_only_removed": 3, "regenerated_biography": 3},
            "Marco Antonio Salazar": {"original": 2, "catalog_only_removed": 2, "regenerated_biography": 2},
            "Gabriel Leon Sandoval": {"original": 2, "catalog_only_removed": 2, "regenerated_biography": 2},
        },
        "finding": "Removing catalogs and separately regenerating scoped biographies did not change "
                   "these purchase ratings. The fidelity repair is not a demonstrated calibration solution.",
        "scope": "Frozen first-turn replays, not full simulation rollouts; raw candidates were not "
                 "quality-corrected. All public replies were read directly, without inferring from THINK/DONE.",
    },
    "correction_audit": {
        "owned_actor_calls": 53, "individuals": 50,
        "regenerated_names": ["Hazel Marie Kessler", "Wyatt Thomas Miller", "Clara Whitaker"],
        "finding": "Only infants were regenerated in CF5. No adult purchase rating was selected by "
                   "a correction loop; disabling it would not explain those observed adult ratings.",
    },
    "returned_usage_estimates": usage,
    "overall_quality_status": "Unresolved; no new complete 50-person study or empirical validation is claimed.",
}
(ROOT / "population-scope-validation.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("Generator-only source lineage verified; current core:", core["status"])
for name, cost in usage.items():
    print(name, "USD", cost["usd"])
