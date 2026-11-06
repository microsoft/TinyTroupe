"""Verify exact final prompt-source lineage and its completed core regression."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "tinytroupe"
actor = PACKAGE / "agent" / "prompts" / "tiny_person.v2.mustache"
factory = PACKAGE / "factory" / "tiny_person_factory.py"
actor_lines = [
    "  - A request's wording or answer format cannot grant the person knowledge or abilities they lack. A required number, explanation, or internal instruction to reason deeply does not make an infant understand a survey scale or a toddler evaluate a household purchase.",
    "  - Respond only within the person's actual comprehension and agency. They may express a concrete like or dislike without understanding the requested judgment; do not attach an arbitrary rating to make their answer fit. Do not speak as an invented caregiver.",
    "  - Apply this to the particular task, not an age cutoff: a child who understands a simple preference question or a counting task can answer it. A capable adult can give a clear rating without perfect information.",
]
factory_lines = [
    "           - each categorical option must identify one coherent characteristic that can be selected for an individual.",
    '             Keep opposing ends as separate options, not a single option such as "strongly rejects novelty OR adopts everything impulsively".',
    "             A list can contain both ends; one selected option must not leave the person's position between incompatible alternatives unresolved.",
    "             Related reasons for the same characteristic can share an option, but opposite behaviors require distinct options.",
]
digests = {key: hashlib.sha256() for key in ["current", "previous"]}
for path in sorted(p for p in PACKAGE.rglob("*")
                   if p.is_file() and p.suffix in {".py", ".mustache"}):
    content = path.read_bytes()
    previous = content
    if path in {actor, factory}:
        newline = "\r\n" if b"\r\n" in content else "\n"
        lines = actor_lines if path == actor else factory_lines
        block = (newline.join(lines) + newline).encode("utf-8")
        assert content.count(block) == 1, path
        previous = content.replace(block, b"", 1)
    for label, digest in digests.items():
        digest.update("\0".join(path.relative_to(PACKAGE).parts).encode())
        digest.update(b"\0")
        digest.update(previous if label == "previous" else content)
        digest.update(b"\0")
assert digests["previous"].hexdigest() == (
    "8c6a0a640111c4c219a1dfa06e8bcee99621fd03c1d45a0bf3871c50f28b8333"
)
current = digests["current"].hexdigest()
assert (ROOT / "comprehension-options-core-source.txt").read_text(
    encoding="utf-8-sig"
).strip() == current
log = (ROOT / "comprehension-options-core.log").read_text(encoding="utf-8", errors="replace")
matches = re.findall(
    r"^=+ (\d+) passed(?:, (\d+) deselected)?(?:, (\d+) warnings?)? "
    r"in ([\d.]+)s(?: \([^)]+\))? =+$", log, re.M
)
status = "passed" if matches else "not passed or still running"
result = {
    "status": status, "current_library_sha256": current,
    "previous_library_sha256": digests["previous"].hexdigest(),
    "only_library_delta": {
        str(actor.relative_to(PACKAGE)): actor_lines,
        str(factory.relative_to(PACKAGE)): factory_lines,
    },
    "proof": "Removing only the three actor lines and four dimension-method docstring "
             "lines in memory exactly recovers the validated full-CF6/444-core source.",
    "core": None,
    "screen_audit": "cf6-comprehension-screen/receipt.json",
    "full_notebook_review": "cf6-gaz-manual-quality-review.json",
    "scope": "Task-comprehension and individually selectable-option repairs, not an "
             "empirical calibration cure. Full CF6 predates these seven added lines.",
}
if matches:
    count, deselected, warnings, seconds = matches[-1]
    result["core"] = {
        "passed": int(count), "deselected": int(deselected or 0),
        "warnings": int(warnings or 0), "elapsed_seconds": float(seconds),
    }
(ROOT / "comprehension-options-validation.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8"
)
print(json.dumps(result, indent=2))
