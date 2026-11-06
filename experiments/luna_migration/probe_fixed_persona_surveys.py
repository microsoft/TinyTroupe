"""Compare backends on fixed notebook personas without changing their preferences."""

import argparse
import ast
import hashlib
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from tinytroupe import config_manager
from tinytroupe.agent import TinyPerson
from tinytroupe.clients import client, force_api_cache
from tinytroupe.environment import TinyWorld
from tinytroupe.extraction import ResultsExtractor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh"], default="xhigh")
    parser.add_argument("--output", type=Path, required=True)
    variants = parser.add_mutually_exclusive_group()
    variants.add_argument("--interpretation-rules", type=Path)
    variants.add_argument("--template-file", type=Path)
    parser.add_argument("--study", choices=["both", "kids", "gaz"], default="both")
    parser.add_argument("--parent-count", type=int, default=2)
    parser.add_argument("--parent-holdout", action="store_true")
    parser.add_argument("--require-unsupervised", action="store_true")
    parser.add_argument("--source-run-prefix", default="cf2-")
    parser.add_argument("--gaz-random-adults", type=int)
    parser.add_argument("--require-regular-purchases", action="store_true")
    parser.add_argument("--selection-file", type=Path)
    parser.add_argument("--introduction-file", type=Path)
    parser.add_argument("--inner-monologue-file", type=Path)
    parser.add_argument("--initial-datetime", type=datetime.fromisoformat)
    args = parser.parse_args()
    args.output.mkdir()
    template = None
    if args.template_file:
        template = args.output / "variant.mustache"
        template.write_text(args.template_file.read_text(encoding="utf-8"), encoding="utf-8")
    if args.interpretation_rules:
        original = (ROOT / "tinytroupe" / "agent" / "prompts" /
                    "tiny_person.v2.mustache").read_text(encoding="utf-8")
        marker = "### Additional actions instructions and constraints"
        if original.count(marker) != 1:
            raise ValueError("Expected one additional-instructions insertion point.")
        rendered = original.replace(
            marker, args.interpretation_rules.read_text(encoding="utf-8") + "\n" + marker
        )
        template = args.output / "variant.mustache"
        template.write_text(rendered, encoding="utf-8")
    config_manager.update("model", args.model)
    config_manager.update("reasoning_model", args.model)
    config_manager.update("reasoning_effort", args.effort)
    config_manager.update("timeout", 600)
    force_api_cache(True, str(args.output / "api.cache.json"))
    started = time.monotonic()
    results = {}
    for study, filename in (
        ("kids", "AI-enabled Children Story Telling Market Research 2.ipynb"),
        ("gaz", "Bottled Gazpacho Market Research 5 (with behavior correction).ipynb"),
    ):
        if args.study != "both" and study != args.study:
            continue
        TinyPerson.clear_agents()
        TinyWorld.clear_environments()
        evidence = json.loads(
            (ARTIFACTS / (args.source_run_prefix + study) / "population-generation-evidence.json")
            .read_text(encoding="utf-8")
        )
        if args.selection_file:
            selected = json.loads(args.selection_file.read_text(encoding="utf-8"))
        elif study == "kids":
            initial = random.Random(20261102).sample(evidence, 2)
            if args.parent_holdout:
                used = {row["name"] for row in initial}
                evidence = [row for row in evidence if row["name"] not in used]
            selected = random.Random(20261102).sample(evidence, args.parent_count)
        elif args.gaz_random_adults:
            selected = random.Random(20261103).sample(
                [row for row in evidence if row["age"] >= 25],
                args.gaz_random_adults,
            )
        else:
            adventurous = next(
                row for row in evidence
                if "adventurous about food" in row["draws"].get("culinary_tastes", "")
                and "Eagerly tests new products early" in row["draws"].get(
                    "attitude_toward_new_products", ""
                )
            )
            familiar = next(
                row for row in evidence
                if row["age"] >= 18
                and "Prefers mild, simple flavors" in row["draws"].get("culinary_tastes", "")
            )
            selected = [adventurous, familiar]
        notebook = json.loads((ROOT / "examples" / filename).read_text(encoding="utf-8"))
        namespace = {"ResultsExtractor": ResultsExtractor}
        targets = {
            "interviewer_introduction", "interviewer_main_question",
            "inner_monologue", "results_extractor",
        }
        for cell in notebook["cells"]:
            if cell["cell_type"] != "code":
                continue
            for node in ast.parse("".join(cell["source"])).body:
                if isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id in targets
                    for target in node.targets
                ):
                    exec(compile(ast.Module(body=[node], type_ignores=[]),
                                 "<original-notebook>", "exec"), namespace)
        if args.introduction_file:
            namespace["interviewer_introduction"] = args.introduction_file.read_text(encoding="utf-8")
        if args.inner_monologue_file:
            namespace["inner_monologue"] = args.inner_monologue_file.read_text(encoding="utf-8")
        if args.require_unsupervised:
            if study != "kids":
                raise ValueError("The explicit-obligation control is a parent-only diagnostic.")
            namespace["interviewer_main_question"] += (
                "\nFor this hypothetical control only, every device and app option must "
                "be used with no adult present; adult co-use or supervision is not "
                "permitted. Option B remains available. Do not assume any additional "
                "features or safeguards."
            )
        if args.require_regular_purchases:
            if study != "gaz":
                raise ValueError("The regular-purchase control is a gazpacho-only diagnostic.")
            namespace["interviewer_main_question"] += (
                "\nFor this hypothetical control only, rate your likelihood of buying "
                "this product repeatedly as a regular part of your shopping, not "
                "merely trying it once."
            )
        config_manager.update("action_generator_enable_quality_checks", True)
        config_manager.update("action_generator_quality_threshold", 6 if study == "kids" else 5)
        people = []
        for row in selected:
            person = TinyPerson(row["name"])
            person.include_persona_definitions(row["persona"])
            if template:
                person._prompt_template_path = str(template)
                person.reset_prompt()
            if study == "gaz":
                person.action_generator.enable_reasoning_step = False
                person.action_generator.enable_quality_checks = True
                person.action_generator.max_attempts = 5
                person.action_generator.enable_regeneration = True
                person.action_generator.quality_threshold = 5
            people.append(person)
        world = TinyWorld(
            "Fixed-persona market research", people,
            initial_datetime=args.initial_datetime, broadcast_if_no_target=False,
        )
        initial_world_datetime = world.current_datetime.isoformat()
        world.broadcast(namespace["interviewer_introduction"])
        world.broadcast(namespace["interviewer_main_question"])
        world.broadcast_thought(namespace["inner_monologue"])
        world.run(1)
        extracted = namespace["results_extractor"].extract_results_from_agents(people)
        results[study] = {
            "selection": [
                {"name": row["name"], "draws": row["draws"], "persona": row["persona"],
                 **{key: row[key] for key in ("diagnostic_control", "provenance") if key in row}}
                for row in selected
            ],
            "results": extracted,
            "agents": {person.name: person.episodic_memory.retrieve_all() for person in people},
            "stimuli": {key: namespace[key] for key in [
                "interviewer_introduction", "interviewer_main_question", "inner_monologue",
            ]},
            "initial_world_datetime": initial_world_datetime,
        }
        (args.output / (study + ".json")).write_text(
            json.dumps(results[study], ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        print("COMPLETED", study, args.model,
              json.dumps([row["response"] for row in extracted]), flush=True)
    (args.output / "receipt.json").write_text(json.dumps({
        "model": args.model,
        "requested_effort": args.effort,
        "effort_caveat": "The client does not forward this setting to GPT-5-mini; "
                         "the comparison is not effort-controlled.",
        "elapsed_seconds": time.monotonic() - started,
        "usage": client().get_cost_stats(),
        "variant_sha256": hashlib.sha256(template.read_bytes()).hexdigest() if template else None,
        "parent_holdout": args.parent_holdout,
        "require_unsupervised_control": args.require_unsupervised,
        "require_regular_purchases_control": args.require_regular_purchases,
        "source_run_prefix": args.source_run_prefix,
        "gaz_random_adults": args.gaz_random_adults,
        "selection_file": str(args.selection_file) if args.selection_file else None,
        "introduction_file": str(args.introduction_file) if args.introduction_file else None,
        "inner_monologue_file": str(args.inner_monologue_file) if args.inner_monologue_file else None,
        "requested_initial_datetime": args.initial_datetime.isoformat() if args.initial_datetime else None,
        "synthetic_preference_controls": [
            {"name": row["name"], "control": row["diagnostic_control"]}
            for row in selected if "diagnostic_control" in row
        ],
        "scope": "Fixed-persona diagnostics, not representative population estimates. "
                 "Backend changes include quality evaluation and extraction. "
                 "An explicitly selected effort also applies to evaluation and extraction, "
                 "not solely the actor; it does not change repository defaults. "
                 "Persona preferences and original quality thresholds were retained. Original "
                 "rating-question wording was retained except in the explicitly recorded "
                 "require_unsupervised_control or require_regular_purchases_control, "
                 "which are not original-notebook results. Introduction and private "
                 "thought changes are recorded separately by their input files and "
                 "the exact stimuli saved in each study result. Changed conditions "
                 "are diagnostics, not unmodified-notebook results.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
