"""Recover a completed screen receipt while disclosing an unrelated mid-run source edit."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from model_case_study import decode_key
from review_notebook_evidence import cost_for_run

OUTPUT = ROOT / "cf6-comprehension-screen"
protocol = json.loads((OUTPUT / "protocol.json").read_text(encoding="utf-8"))
package = REPO / "tinytroupe"
factory = package / "factory" / "tiny_person_factory.py"
added = (
    '           - each categorical option must identify one coherent characteristic that can be selected for an individual.\n'
    '             Keep opposing ends as separate options, not a single option such as "strongly rejects novelty OR adopts everything impulsively".\n'
    "             A list can contain both ends; one selected option must not leave the person's position between incompatible alternatives unresolved.\n"
    "             Related reasons for the same characteristic can share an option, but opposite behaviors require distinct options.\n"
)
digests = {name: hashlib.sha256() for name in ["current", "screen_source"]}
for path in sorted(p for p in package.rglob("*")
                   if p.is_file() and p.suffix in {".py", ".mustache"}):
    content = path.read_bytes()
    previous = content
    if path == factory:
        # Preserve the file's line endings when reconstructing its previous bytes.
        block = added.replace("\n", "\r\n").encode() if b"\r\n" in content else added.encode()
        assert content.count(block) == 1
        previous = content.replace(block, b"", 1)
    for label, digest in digests.items():
        digest.update("\0".join(path.relative_to(package).parts).encode())
        digest.update(b"\0")
        digest.update(previous if label == "screen_source" else content)
        digest.update(b"\0")
assert digests["screen_source"].hexdigest() == protocol["library_sha256"]
cache = json.loads((OUTPUT / "api.cache.json").read_text(encoding="utf-8"))
actor_text = (package / "agent" / "prompts" / "tiny_person.v2.mustache").read_text(
    encoding="utf-8"
)
new_rule = next(line.strip()[2:] for line in actor_text.splitlines()
                if "A request's wording or answer format cannot grant" in line)
actor_requests = []
for key in cache:
    request, schema = decode_key(key)
    if schema == "tinytroupe.agent.CognitiveActionsModel":
        assert new_rule in request["messages"][0]["content"]
        actor_requests.append(request)
assert actor_requests
results = json.loads((OUTPUT / "results.json").read_text(encoding="utf-8"))
by_age = {row["age"]: row for row in results}
assert all(by_age[age]["response"] == "N/A" for age in [0, 2, 3])
assert by_age[66]["response"] == "2" and by_age[69]["response"] == "3"
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(
    encoding="utf-8"
))["models"]["gpt-6-luna"]
usage = cost_for_run(OUTPUT, {"started_at": "1970-01-01T00:00:00+00:00",
    "elapsed_seconds": max(r["created"] for r in cache.values()) + 1}, prices)
receipt = {
    "returned_responses": len(cache), "returned_usage_estimate": usage,
    "original_command_exit": 1,
    "failure": "Final whole-library fingerprint assertion, after all six pipeline results saved.",
    "recovery": "No model calls repeated. In-memory removal of only the four-line "
                "dimension-generation docstring addition recovers the exact screen-start hash.",
    "screen_start_library_sha256": protocol["library_sha256"],
    "current_library_sha256": digests["current"].hexdigest(),
    "only_intervening_library_change": str(factory.relative_to(package)),
    "actor_instructions_unchanged_during_screen": True,
    "new_comprehension_rule_present_in_every_saved_actor_request": True,
    "scope": "Frozen biographies; dimension generation is never called in this screen. "
             "The docstring edit does not affect its actor/correction/extractor execution.",
    "review": {
        "age_0_2_3": "No purchase digit invented; actual original extractor returns N/A.",
        "age_4": "Still gives a public 2. Not claimed repaired or used as an adult purchase "
                 "judgment; no universal preschool age cutoff is imposed.",
        "adults": "Original public ratings 2 and 3 remain available.",
        "calibration": "Not tested; no distribution or high-score improvement claim.",
    },
}
(OUTPUT / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt, indent=2))
