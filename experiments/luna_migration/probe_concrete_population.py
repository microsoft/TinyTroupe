"""Exercise concrete population sampling and original survey questions end to end."""

import argparse
import ast
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from tinytroupe import config_manager
from tinytroupe.agent import TinyPerson
from tinytroupe.clients import client, force_api_cache
from tinytroupe.environment import TinyWorld
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.factory.tiny_factory import TinyFactory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", choices=["kids", "gaz"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--api-timeout", type=int)
    args = parser.parse_args()
    args.output.mkdir()
    config_manager.update("model", "gpt-6-luna")
    config_manager.update("reasoning_model", "gpt-6-luna")
    config_manager.update("reasoning_effort", "xhigh")
    if args.api_timeout is not None:
        if args.api_timeout <= 0:
            raise ValueError("API timeout must be positive.")
        config_manager.update("timeout", args.api_timeout)
    force_api_cache(True, str(args.output / "api.cache.json"))
    if args.study == "kids":
        name = "AI-enabled Children Story Telling Market Research 2"
        prior = ARTIFACTS / "qr-kids"
        config_manager.update("action_generator_enable_quality_checks", True)
        config_manager.update("action_generator_quality_threshold", 6)
    else:
        name = "Bottled Gazpacho Market Research 5 (with behavior correction)"
        prior = ARTIFACTS / "qr-gaz-v2"
    notebook = json.loads((ROOT / "examples" / (name + ".ipynb")).read_text(encoding="utf-8"))
    namespace = {"pd": __import__("pandas")}
    targets = {"interviewer_introduction", "interviewer_main_question", "inner_monologue",
               "results_extractor", "demographic_specification", "additional_demographic_specification"}
    from tinytroupe.extraction import ResultsExtractor
    namespace["ResultsExtractor"] = ResultsExtractor
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id in targets for target in node.targets
            ):
                exec(compile(ast.Module(body=[node], type_ignores=[]), "<notebook>", "exec"), namespace)
    prior_factory = next(iter(json.loads(
        (prior / (name + ".factories.json")).read_text(encoding="utf-8")
    ).values()))
    if args.study == "kids":
        factory = TinyPersonFactory(
            context=prior_factory["context_text"],
            sampling_space_description=namespace["demographic_specification"],
            total_population_size=args.count,
        )
    else:
        factory = TinyPersonFactory.create_factory_from_demography(
            str(ROOT / "examples" / "information" / "populations" / "usa.json"),
            population_size=args.count,
            additional_demographic_specification=namespace["additional_demographic_specification"],
        )
    factory.randomizer = random.Random(20261102)
    factory.sampling_dimensions = prior_factory["sampling_dimensions"]
    factory.sampling_plan = prior_factory["sampling_plan"]
    if args.plan_only:
        factory.sampling_plan = factory._compute_sample_plan(
            N=50, sampling_dimensions=factory.sampling_dimensions,
            enforce_usage_of_all_dimensions=False, context=prior_factory["context_text"],
            population_description=factory.sampling_space_description,
        )["sample_plan"]
        (args.output / "sampling-plan.json").write_text(
            json.dumps(factory.sampling_plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print("PLAN COMPLETED", args.study, flush=True)
        return
    if args.plan:
        factory.sampling_plan = json.loads(args.plan.read_text(encoding="utf-8"))
    samples = factory._flatten_sampling_plan(factory.sampling_plan)
    chosen = random.Random(20261102).sample(samples, args.count)
    names = []
    for sample in chosen:
        sample["name"] = factory._generate_name_for_sample(
            sample_characteristics=sample, already_generated_names=names,
        )
        if sample["name"] in names:
            raise ValueError(f"Duplicate precomputed name: {sample['name']}")
        names.append(sample["name"])
    factory.remaining_characteristics_sample = chosen
    (args.output / "selected-characteristics.json").write_text(
        json.dumps(chosen, ensure_ascii=False, indent=2), encoding="utf-8")
    started = time.monotonic()
    people = factory.generate_people(args.count)
    if len(people) != args.count:
        raise ValueError(f"Expected {args.count} people; got {len(people)}")
    (args.output / "personas.json").write_text(
        json.dumps({p.name: p._persona for p in people}, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.study == "gaz":
        for person in people:
            person.action_generator.enable_reasoning_step = False
            person.action_generator.enable_quality_checks = True
            person.action_generator.max_attempts = 5
            person.action_generator.enable_regeneration = True
            person.action_generator.quality_threshold = 5
    world = TinyWorld("Concrete population diagnostic", people, broadcast_if_no_target=False)
    world.broadcast(namespace["interviewer_introduction"])
    world.broadcast(namespace["interviewer_main_question"])
    world.broadcast_thought(namespace["inner_monologue"])
    world.run(1)
    results = namespace["results_extractor"].extract_results_from_agents(people)
    (args.output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "agents.json").write_text(json.dumps(
        {p.name: p.episodic_memory.retrieve_all() for p in people}, ensure_ascii=False, indent=2, default=str
    ), encoding="utf-8")
    (args.output / "receipt.json").write_text(json.dumps({
        "elapsed_seconds": time.monotonic() - started, "usage": client().get_cost_stats(),
        "study": args.study, "count": args.count,
    }, indent=2), encoding="utf-8")
    print("COMPLETED", args.study, json.dumps([r.get("response") for r in results]), flush=True)


if __name__ == "__main__":
    main()
