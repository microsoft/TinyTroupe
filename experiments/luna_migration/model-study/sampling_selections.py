"""Represent closed-vocabulary sampling choices as typed identifiers, then restore exact options."""

import copy
import json

from review_phase_study import checks, named_parameters


def indexed_request(case, instruction, categorical_encoding="identifiers"):
    """Keep all parameter meanings while exposing a strict, nullable selection per dimension."""
    if categorical_encoding not in ("identifiers", "membership"):
        raise ValueError("Unknown categorical encoding.")
    params = named_parameters(case)
    if not params or not params.get("sampling_dimensions", {}).get("dimensions"):
        raise ValueError("Require literal named sampling parameters and dimensions.")
    properties, dimensions = {}, {}
    enforce = params.get("enforce_usage_of_all_dimensions", False)
    for i, dimension in enumerate(params["sampling_dimensions"]["dimensions"], 1):
        key = str(i)
        if "range" in dimension:
            low, high = dimension["range"]
            scalar = {"type": "number", "minimum": low, "maximum": high}
            pair = {"type": "array", "items": scalar, "minItems": 2, "maxItems": 2}
            variants = [scalar, pair]
            dimensions[key] = copy.deepcopy(dimension)
        else:
            options = list(dimension["values"])
            if not options or not all(isinstance(s, str) for s in options):
                raise ValueError("Require nonempty string categorical options.")
            scalar = {"type": "integer", "minimum": 1, "maximum": len(options)}
            variants = [scalar, {"type": "array", "items": scalar, "minItems": 2}]
            if categorical_encoding == "membership":
                keys = [str(j) for j in range(1, len(options) + 1)]
                variants = [{"type": "object", "additionalProperties": False,
                             "properties": {k: {"type": "boolean"} for k in keys},
                             "required": keys}]
            dimensions[key] = {"name": dimension["name"],
                               "options": {str(j): s for j, s in enumerate(options, 1)}}
            if isinstance(dimension["values"], dict):
                dimensions[key]["supplied_option_weights"] = {
                    str(j): weight for j, weight in enumerate(dimension["values"].values(), 1)
                }
        if not enforce:
            variants.append({"type": "null"})
        properties[key] = {"anyOf": variants}
    quantity = {"type": "integer", "minimum": 1}
    if params.get("max_quantity_per_sample_directive") is not None:
        quantity["maximum"] = params["max_quantity_per_sample_directive"]
    directives = {
        "type": "array", "minItems": params.get("min_sampling_directives") or 1,
        "items": {"type": "object", "additionalProperties": False, "required": [
            "id", "subpopulation_description", "sampled_values", "quantity"],
            "properties": {
                "id": {"type": "integer", "minimum": 1},
                "subpopulation_description": {"type": "string"},
                "quantity": quantity,
                "sampled_values": {"type": "object", "additionalProperties": False,
                                   "properties": properties, "required": list(properties)},
            }},
    }
    if params.get("max_sampling_directives") is not None:
        directives["maxItems"] = params["max_sampling_directives"]
    schema = {"type": "object", "additionalProperties": False,
              "properties": {"sample_plan": directives}, "required": ["sample_plan"]}
    payload = copy.deepcopy(params)
    payload["sampling_dimensions"]["dimensions"] = dimensions
    return [{"role": "system", "content": instruction},
            {"role": "user", "content": "Input parameter values (JSON):\n" + json.dumps(payload, ensure_ascii=False)}], {
        "type": "json_schema", "json_schema": {
            "name": "sampling_plan_by_identifiers", "strict": True, "schema": schema,
        }}


def reconstruct(case, value):
    """Restore names/options exactly; reject invalid arithmetic and eligibility without silent repair."""
    params = named_parameters(case)
    dimensions = params["sampling_dimensions"]["dimensions"]
    expected = {str(i) for i in range(1, len(dimensions) + 1)}
    plan = copy.deepcopy(value)
    for directive in plan["sample_plan"]:
        selected = directive["sampled_values"]
        if set(selected) != expected:
            raise ValueError("Indexed sampled_values must include every dimension slot.")
        restored = {}
        for i, dimension in enumerate(dimensions, 1):
            selection = selected[str(i)]
            if selection is None:
                if params.get("enforce_usage_of_all_dimensions"):
                    raise ValueError("Required dimension was left unselected.")
                continue
            if "range" in dimension:
                restored[dimension["name"]] = selection
            else:
                options = list(dimension["values"])
                if isinstance(selection, dict):
                    if set(selection) != {str(j) for j in range(1, len(options) + 1)}:
                        raise ValueError("Membership selection must contain every option slot.")
                    if any(type(flag) is not bool for flag in selection.values()):
                        raise ValueError("Membership selections require boolean values.")
                    ids = [j for j in range(1, len(options) + 1) if selection[str(j)]]
                else:
                    ids = selection if isinstance(selection, list) else [selection]
                if not ids or any(type(j) is not int or not 1 <= j <= len(options) for j in ids):
                    raise ValueError("Option identifier outside its supplied dimension.")
                if len(ids) != len(set(ids)):
                    raise ValueError("Duplicate selected option identifiers.")
                strings = [options[j - 1] for j in ids]
                restored[dimension["name"]] = strings if len(strings) > 1 else strings[0]
        if not restored:
            raise ValueError("A directive cannot omit every dimension.")
        directive["sampled_values"] = restored
    measured = checks(case, json.dumps(plan, ensure_ascii=False))
    failures = [k for k in ["exact_total", "positive_integer_quantities", "sequential_directive_ids"]
                if measured[k] is not True]
    failures += [k for k, valid in measured.items() if k.endswith("_satisfied") and valid is not True]
    if measured["unknown_dimensions"] or measured["invalid_or_rewritten_sampled_values"]:
        failures.append("sampled value eligibility")
    if any(measured.get("missing_dimensions_by_directive", [])):
        failures.append("required dimensions")
    if failures:
        raise ValueError("Invalid reconstructed sampling plan: " + ", ".join(failures))
    return plan
