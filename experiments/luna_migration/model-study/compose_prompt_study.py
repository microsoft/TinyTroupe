"""Compose existing prompt recipes and select explicit variants for a standalone study."""

import argparse
import copy
import json
from pathlib import Path

from prompt_variants import build_variants


def compile_manifest(path):
    """Resolve recipe imports and text files relative to their declaring manifest."""
    spec = json.loads(path.read_text(encoding="utf-8"))
    recipes = {}
    ordered = []
    for imported in spec.get("imports", []):
        source = compile_manifest(path.parent / imported["path"])
        available = {recipe["id"]: recipe for recipe in source["variants"]}
        for name in imported["variants"]:
            if name in recipes:
                raise ValueError(f"Duplicate recipe: {name}")
            recipe = copy.deepcopy(available[name])
            recipes[name] = recipe
            ordered.append(recipe)
    for declared in spec["variants"]:
        recipe = copy.deepcopy(declared)
        if recipe["id"] in recipes:
            raise ValueError(f"Duplicate recipe: {recipe['id']}")
        operations = []
        for name in recipe.pop("operations_from", []):
            operations.extend(copy.deepcopy(recipes[name]["operations"]))
        for operation in recipe["operations"]:
            for key in ("new", "text"):
                file_key = key + "_file"
                if file_key in operation:
                    if key in operation:
                        raise ValueError(f"Specify {key} or {file_key}, not both")
                    operation[key] = (path.parent / operation.pop(file_key)).read_text(encoding="utf-8")
            operations.append(operation)
        recipe["operations"] = operations
        recipes[recipe["id"]] = recipe
        ordered.append(recipe)
    return {**spec, "variants": ordered}


def prepare(corpus, manifest, output):
    """Freeze resolved recipes and a selected corpus without overwriting prior experiments."""
    if output.exists():
        raise FileExistsError(f"Use a new experiment directory: {output}")
    compiled = compile_manifest(manifest)
    output.mkdir(parents=True)
    resolved = output / "resolved-manifest.json"
    resolved.write_text(json.dumps(compiled, ensure_ascii=False, indent=2), encoding="utf-8")
    build_variants(corpus, resolved, output)
    cases = [json.loads(line) for line in (output / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
    wanted = {source + "::" + variant for source, variant in compiled["selection"].items()}
    selected = [case for case in cases if case["case_id"] in wanted]
    if {case["case_id"] for case in selected} != wanted:
        raise ValueError(f"Missing selected cases: {wanted - {c['case_id'] for c in selected}}")
    (output / "selected.jsonl").write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in selected), encoding="utf-8"
    )
    print(f"Selected {len(selected)} requests.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.corpus, args.manifest, args.output)
