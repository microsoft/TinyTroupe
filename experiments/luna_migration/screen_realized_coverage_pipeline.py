"""Exercise a predeclared contrast panel through the actual gazpacho pipeline."""

import ast
import copy
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tinytroupe import config_manager
from tinytroupe.clients import client, force_api_cache
from tinytroupe.environment import TinyWorld
from tinytroupe.extraction import ResultsExtractor
from tinytroupe.factory import TinyPersonFactory

OUTPUT = ROOT / "realized-coverage-pipeline"
OUTPUT.mkdir()
protocol = json.loads((ROOT / "realized-behavior-coverage-compact" /
    "plan.json").read_text(encoding="utf-8"))
parameters = protocol["parameters"]
plan = json.loads((ROOT / "realized-behavior-coverage-compact" /
    "sampling-plan.json").read_text(encoding="utf-8"))
config_manager.update("model", "gpt-6-luna")
config_manager.update("reasoning_model", "gpt-6-luna")
config_manager.update("reasoning_effort", "xhigh")
config_manager.update("timeout", 600)
force_api_cache(True, str(OUTPUT / "api.cache.json"))
factory = TinyPersonFactory(
    context=parameters["context"], sampling_space_description=parameters["population_description"],
    total_population_size=6,
)
factory.sampling_dimensions = parameters["sampling_dimensions"]
factory.sampling_plan = plan
factory.randomizer = random.Random(20261102)
draws = factory._flatten_sampling_plan(plan)
chosen, roles = [], []
for family, targets in protocol["targeted_options"].items():
    for target in targets:
        person = next(p for p in draws if p.get(family) == target and p not in chosen)
        chosen.append(person)
        roles.append({"family": family, "value": target})
youngest = min((p for p in draws if p not in chosen), key=lambda p: p["age"])
chosen.append(youngest)
roles.append({"role": "youngest remaining sampled person"})
chosen.append(next(p for p in draws if p not in chosen and p["age"] >= 18))
roles.append({"role": "first remaining sampled adult in fixed shuffled order"})
assert len(chosen) == 6 and len({id(p) for p in chosen}) == 6
(OUTPUT / "protocol.json").write_text(json.dumps({
    "population_sampling_seed": 20261102,
    "selection_rule": "One distinct person for each of the four predefined contrast ends, "
                      "then the youngest remaining draw and the first remaining adult.",
    "roles": roles, "selected_characteristics_before_names": chosen,
    "scope": "A contrast-selected six-person integration screen, not a random population "
             "sample or a calibration estimate. No scores are used for selection.",
    "production_changed": False,
    "planner_caveat": "The public plan came from an experimental compact-schema request; "
                      "this screen uses the actual factory, actor and extractor thereafter.",
}, ensure_ascii=False, indent=2), encoding="utf-8")
names = []
for characteristics in chosen:
    characteristics["name"] = factory._generate_name_for_sample(
        sample_characteristics=characteristics, already_generated_names=names,
    )
    if characteristics["name"] in names:
        raise ValueError(f"Duplicate generated name: {characteristics['name']}")
    names.append(characteristics["name"])
(OUTPUT / "selected-characteristics.json").write_text(
    json.dumps(chosen, ensure_ascii=False, indent=2), encoding="utf-8"
)
factory.remaining_characteristics_sample = copy.deepcopy(chosen)
started = time.monotonic()
people = factory.generate_people(6)
if len(people) != 6:
    raise ValueError(f"Expected six generated people, received {len(people)}.")
expected = {p["name"]: p for p in chosen}
for person in people:
    assert person.name in expected and person.get("age") == expected[person.name]["age"]
(OUTPUT / "personas.json").write_text(
    json.dumps({p.name: p._persona for p in people}, ensure_ascii=False, indent=2), encoding="utf-8"
)
notebook = json.loads((REPO / "examples" /
    "Bottled Gazpacho Market Research 5 (with behavior correction).ipynb").read_text(encoding="utf-8"))
namespace = {"ResultsExtractor": ResultsExtractor}
targets = {"interviewer_introduction", "interviewer_main_question", "inner_monologue",
           "results_extractor"}
for cell in notebook["cells"]:
    if cell["cell_type"] == "code":
        for node in ast.parse("".join(cell["source"])).body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id in targets for target in node.targets
            ):
                exec(compile(ast.Module(body=[node], type_ignores=[]), "<notebook>", "exec"), namespace)
for person in people:
    person.action_generator.enable_reasoning_step = False
    person.action_generator.enable_quality_checks = True
    person.action_generator.max_attempts = 5
    person.action_generator.enable_regeneration = True
    person.action_generator.quality_threshold = 5
world = TinyWorld("Realized contrast coverage diagnostic", people, broadcast_if_no_target=False)
world.broadcast(namespace["interviewer_introduction"])
world.broadcast(namespace["interviewer_main_question"])
world.broadcast_thought(namespace["inner_monologue"])
world.run(1)
(OUTPUT / "agents.json").write_text(json.dumps(
    {p.name: p.episodic_memory.retrieve_all() for p in people},
    ensure_ascii=False, indent=2, default=str,
), encoding="utf-8")
results = namespace["results_extractor"].extract_results_from_agents(people)
(OUTPUT / "results.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
(OUTPUT / "receipt.json").write_text(json.dumps({
    "elapsed_seconds_after_name_generation": time.monotonic() - started,
    "usage": client().get_cost_stats(), "count": len(people),
    "scope": "Contrast-selected integration screen; no population inference.",
}, indent=2), encoding="utf-8")
print("COMPLETED", json.dumps([r.get("response") for r in results]), flush=True)
