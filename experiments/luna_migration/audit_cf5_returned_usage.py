"""Price owned saved responses without excluding calls at ambiguous timestamp-window edges."""

import json
from pathlib import Path

from review_notebook_evidence import cost_for_run

ROOT = Path(__file__).parent
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(encoding="utf-8"))["models"]["gpt-6-luna"]
slices = ROOT / "cf5-returned-usage-slices"
slices.mkdir(exist_ok=True)
report = {
    "basis": "Saved standard list rates applied to owned unique returned responses. "
             "Full-run ownership is the exact cache difference from its copied CF4 source; "
             "the replay cache began empty and belongs solely to the 100-history replay. "
             "No invoice claim; failed/unreturned requests and core-suite usage are not included.",
    "runs": {},
    "extraction_prompt_trials": {},
}
for study in ["inv", "kids", "gaz", "reextraction"]:
    current = json.loads((ROOT / f"cf5-{study}" / "api.cache.json").read_text(encoding="utf-8"))
    if study != "reextraction":
        prior = json.loads((ROOT / f"cf4-{study}" / "api.cache.json").read_text(encoding="utf-8"))
        assert all(key in current and current[key] == value for key, value in prior.items())
        owned = {key: value for key, value in current.items() if key not in prior}
    else:
        owned = current
        assert len(owned) == 100
    assert len({response["id"] for response in owned.values()}) == len(owned)
    folder = slices / study
    folder.mkdir(exist_ok=True)
    (folder / "api.cache.json").write_text(json.dumps(owned, ensure_ascii=False), encoding="utf-8")
    latest = max(response["created"] for response in owned.values())
    cost = cost_for_run(folder, {
        "started_at": "1970-01-01T00:00:00+00:00", "elapsed_seconds": latest + 1,
    }, prices)
    assert cost["unique_saved_api_responses_in_run_window"] == len(owned)
    cost["ownership"] = (
        "Exact new responses relative to the copied CF4 cache."
        if study != "reextraction" else "All 100 responses in the new isolated replay cache."
    )
    report["runs"][study] = cost
    print(study, "returned responses", len(owned), "USD", cost["usd"])
for name in [
    "extraction-done-boundary-trial",
    "extraction-boundary-reasons-trial",
    "extraction-public-clauses-trial",
]:
    folder = ROOT / name
    saved = json.loads((folder / "api.cache.json").read_text(encoding="utf-8"))
    latest = max(response["created"] for response in saved.values())
    report["extraction_prompt_trials"][name] = cost_for_run(folder, {
        "started_at": "1970-01-01T00:00:00+00:00", "elapsed_seconds": latest + 1,
    }, prices)
receipt_path = ROOT / "cf5-reextraction" / "receipt.json"
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
receipt.setdefault("prior_in_process_estimate", receipt["returned_usage_estimate"])
receipt["returned_usage_estimate"] = report["runs"]["reextraction"]
receipt["pricing_note"] = "The earlier in-process snapshot priced 94 saved responses. "
receipt["pricing_note"] += "After process completion the isolated cache contains 100; the corrected estimate includes all 100 without rerunning or resampling any response."
receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
(ROOT / "cf5-returned-usage-audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
