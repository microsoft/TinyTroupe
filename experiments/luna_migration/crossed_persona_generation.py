"""Replay eight exact factory prompts with Mini, without using human survey votes."""

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ARTIFACTS / "model-study"))

from model_case_study import decode_key
from tinytroupe import config_manager, utils
from tinytroupe.clients import client, force_api_cache


def main():
    selection = json.loads(
        (ARTIFACTS / "fixed-persona-gaz-purchase-baseline" / "gaz.json")
        .read_text(encoding="utf-8")
    )["selection"]
    names = {row["name"] for row in selection}
    original_personas = {row["name"]: row["persona"] for row in selection}
    cache = json.loads(
        (ARTIFACTS / "cf4-gaz" / "api.cache.json").read_text(encoding="utf-8")
    )
    requests = {}
    for key, response in cache.items():
        if "- Name, demographics and other characteristics:" not in key:
            continue
        persona = json.loads(response["choices"][0]["message"]["content"])
        if persona["name"] in names and persona == original_personas[persona["name"]]:
            if persona["name"] in requests:
                raise ValueError("Ambiguous generation provenance: " + persona["name"])
            request, _ = decode_key(key)
            requests[persona["name"]] = request
    if set(requests) != names:
        raise ValueError("Generation requests do not exactly cover the fixed panel.")

    folder = ARTIFACTS / "crossed-persona-mini-generation"
    folder.mkdir()
    config_manager.update("model", "gpt-5-mini")
    config_manager.update("reasoning_model", "gpt-5-mini")
    config_manager.update("reasoning_effort", "xhigh")
    config_manager.update("timeout", 600)
    force_api_cache(True, str(folder / "api.cache.json"))
    started = time.monotonic()
    generated = []
    provenance = []
    for row in selection:
        request = requests[row["name"]]
        response = client().send_message(
            request["messages"],
            dedent_messages=False,
            temperature=request.get("temperature"),
            max_completion_tokens=request.get("max_completion_tokens"),
            response_format=request["response_format"],
        )
        if not response or not response.get("content"):
            raise ValueError("Empty generation response: " + row["name"])
        persona = utils.extract_json(response["content"])
        if persona["name"] != row["name"] or persona["age"] != row["persona"]["age"]:
            raise ValueError("Mini changed a fixed name or age: " + row["name"])
        generated.append({"name": row["name"], "draws": row["draws"], "persona": persona})
        provenance.append({
            "name": row["name"],
            "source_request_sha256": hashlib.sha256(
                json.dumps(request, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest(),
            "source_model": request["model"],
            "generation_model": "gpt-5-mini",
            "messages_unchanged": True,
            "same_draws_name_and_age": True,
        })
        (folder / "selection-mini.partial.json").write_text(
            json.dumps(generated, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("GENERATED", len(generated), row["name"], flush=True)
    (folder / "selection-mini.json").write_text(
        json.dumps(generated, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (folder / "receipt.json").write_text(json.dumps({
        "elapsed_seconds": time.monotonic() - started,
        "cases": provenance,
        "scope": "A bounded crossed-generator diagnostic, not population calibration. "
                 "Eight original factory message lists, demographic/behavior draws, "
                 "names and ages are preserved. Other biography details may differ. "
                 "Backend-specific parameters follow the existing client; requested "
                 "effort is not forwarded to Mini. No human outcome was supplied. "
                 "One generated biography per condition does not establish a causal "
                 "effect size or a representative joint population distribution.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
