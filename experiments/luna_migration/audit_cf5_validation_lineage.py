"""Verify that only the extraction template changed after the complete CF5 rollouts."""

import hashlib
import json
import re
from pathlib import Path

from run_notebook_comparison import library_fingerprint

ROOT = Path(__file__).parent
PACKAGE = Path(__file__).resolve().parents[2] / "tinytroupe"
target = PACKAGE / "extraction" / "prompts" / "interaction_results_extractor.mustache"
rollout = json.loads((ROOT / "cf5-core-result.json").read_text(encoding="utf-8"))
paths = sorted(p for p in PACKAGE.rglob("*") if p.is_file() and p.suffix in {".py", ".mustache"})
raw = target.read_bytes()
marker = b"### Example 3: Keep the justification within the same evidence boundary"
assert raw.count(marker) == 1
prefix = raw.split(marker, 1)[0].rstrip(b"\r\n").replace(b"\r\n", b"\n")
matches = []
for newline in [b"\n", b"\r\n"]:
    for ending_count in range(1, 5):
        replacement = prefix.replace(b"\n", newline) + newline * ending_count
        digest = hashlib.sha256()
        for path in paths:
            digest.update("\0".join(path.relative_to(PACKAGE).parts).encode("utf-8"))
            digest.update(b"\0")
            digest.update(replacement if path == target else path.read_bytes())
            digest.update(b"\0")
        if digest.hexdigest() == rollout["library_sha256"]:
            matches.append(hashlib.sha256(replacement).hexdigest())
assert len(matches) == 1, "The complete-rollout implementation cannot be recovered by only undoing the template addition."
current = library_fingerprint(PACKAGE)
core = {"status": "Pending"}
log = ROOT / "extraction-boundary-core.log"
if log.exists():
    text = log.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"432 passed, 440 deselected, (\d+) warnings in ([\d.]+)s", text)
    if match:
        recorded = (ROOT / "extraction-boundary-core-source.txt").read_text(encoding="utf-8-sig").strip()
        assert current == recorded
        core = {
            "status": "Passed", "passed": 432, "deselected": 440,
            "warnings": int(match[1]), "elapsed_seconds": float(match[2]),
            "library_sha256": recorded,
        }
receipt_path = ROOT / "cf5-reextraction" / "receipt.json"
reextraction = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {"status": "Pending"}
if receipt_path.exists():
    assert reextraction["library_sha256"] == current
report = {
    "full_rollout_library_sha256": rollout["library_sha256"],
    "full_rollouts_core_passed": 429,
    "current_library_sha256": current,
    "only_library_file_changed_since_rollouts": str(target.relative_to(PACKAGE)),
    "prior_template_sha256": matches[0],
    "proof": "Replacing only the extraction template bytes, in memory, exactly reproduces the saved "
             "whole-library fingerprint. No workspace files were temporarily reverted.",
    "current_source_core": core,
    "postprocessing_replay": reextraction,
    "scope": "Full notebooks ran on the prior runtime. Only final extraction instructions changed afterward. "
             "The later core suite and 100-history postprocessing replay validate that change separately; "
             "they are not represented as a new full simulation rollout.",
}
(ROOT / "cf5-validation-lineage.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
