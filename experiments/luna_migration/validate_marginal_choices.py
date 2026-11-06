"""Verify the sole planner delta against the preceding 449-case source."""

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "tinytroupe"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--capture", action="store_true")
args = parser.parse_args()
protocol = json.loads((ROOT / "demographic-coverage-budget-r4" / "protocol.json").read_text(
    encoding="utf-8"
))
template = PACKAGE / "factory" / "prompts" / "sampling_plan.system.mustache"
digests = {key: hashlib.sha256() for key in ["current", "previous"]}
for path in sorted(p for p in PACKAGE.rglob("*")
                   if p.is_file() and p.suffix in {".py", ".mustache"}):
    content = path.read_bytes()
    previous = content
    if path == template:
        newline = "\r\n" if b"\r\n" in content else "\n"
        block = (protocol["candidate_paragraph"] + "\n").replace("\n", newline).encode()
        assert content.count(block) == 1, "Integrated prompt must match tested candidate exactly."
        previous = content.replace(block, b"", 1)
    for label, digest in digests.items():
        digest.update("\0".join(path.relative_to(PACKAGE).parts).encode())
        digest.update(b"\0")
        digest.update(previous if label == "previous" else content)
        digest.update(b"\0")
old_hash = digests["previous"].hexdigest()
assert old_hash == "ca9b09398b9dab603bc54a6fa729d7b27ce386dc80eeb3cff6e5117d51fa16f9"
assert protocol["library_sha256"] == old_hash
current = digests["current"].hexdigest()
capture = ROOT / "marginal-choices-core-source.txt"
if args.capture:
    if capture.exists():
        assert capture.read_text(encoding="utf-8").strip() == current
    else:
        capture.write_text(current + "\n", encoding="utf-8")
else:
    assert capture.read_text(encoding="utf-8").strip() == current
result = {
    "status": "not passed or still running",
    "current_library_sha256": current,
    "previous_library_sha256": old_hash,
    "only_library_delta": str(template.relative_to(PACKAGE)),
    "proof": "Removing the exact tested revision-4 paragraph in memory reconstructs "
             "the preceding source that passed 449 core cases. No actor, extractor, "
             "questionnaire, model, effort or threshold changed.",
    "candidate_screen": "demographic-coverage-budget-r4/numerical-screen.json",
    "candidate_request_audit": "demographic-coverage-budget-r4/structural-audit.json",
    "core": None,
    "scope": "Marginal-preserving sampling repair, not a gazpacho calibration result. "
             "Both the full CF6 survey and six-person comprehension screen predate this change.",
}
log_path = ROOT / "marginal-choices-core.log"
if not args.capture and log_path.exists():
    matches = re.findall(
        r"^=+ (\d+) passed(?:, (\d+) deselected)?(?:, (\d+) warnings?)? "
        r"in ([\d.]+)s(?: \([^)]+\))? =+$",
        log_path.read_text(encoding="utf-8", errors="replace"), re.M,
    )
    if matches:
        count, deselected, warnings, seconds = matches[-1]
        result["status"] = "passed"
        result["core"] = {
            "passed": int(count), "deselected": int(deselected or 0),
            "warnings": int(warnings or 0), "elapsed_seconds": float(seconds),
        }
(ROOT / "marginal-choices-validation.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8"
)
print(json.dumps(result, indent=2))
