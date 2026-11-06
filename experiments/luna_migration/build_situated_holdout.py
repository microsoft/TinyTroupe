"""Select an outcome-blind adult holdout, excluding every development-panel identity."""

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent
source = ROOT / "cf4-gaz" / "population-generation-evidence.json"
population = json.loads(source.read_text(encoding="utf-8"))
development = json.loads(
    (ROOT / "crossed-persona-mini-generation" / "selection-mini.json").read_text(encoding="utf-8")
)
excluded = {row["name"] for row in development}
eligible = [row for row in population if row["age"] >= 18 and row["name"] not in excluded]
assert len({row["name"] for row in eligible}) == len(eligible)
selected = random.Random(20261104).sample(eligible, 8)
assert not ({row["name"] for row in selected} & excluded)
(ROOT / "situated-decision-holdout.json").write_text(
    json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8"
)
(ROOT / "situated-decision-holdout-design.json").write_text(json.dumps({
    "source": str(source.relative_to(ROOT)),
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "seed": 20261104,
    "eligibility": "Age 18+; not in the eight-person development panel.",
    "eligible_count": len(eligible),
    "selection_size": 8,
    "selected_names": [row["name"] for row in selected],
    "excluded_development_names": sorted(excluded),
    "selection_used_no_outcomes": True,
    "original_persona_payloads_unchanged": True,
    "conditions": ["plain-transport production prompt", "plain-transport situated decision rules"],
    "fixed_initial_datetime": "2026-11-02T16:20:19.182432",
    "limitations": "Small fixed-biography diagnostic, not population calibration. Adult selection "
                   "does not establish the original PickFu eligibility criteria."
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("Selected independent identities:", [row["name"] for row in selected])
