"""Typed closed-vocabulary sampling plans with exact public-value reconstruction."""

import copy
import math


def sampling_plan_spec(parameters):
    """Build identifier-based input and a strict schema without changing option meanings."""
    n = parameters["N"]
    if type(n) is not int or n < 1:
        raise ValueError("N must be a positive integer.")
    for key in ("min_sampling_directives", "max_sampling_directives",
                "max_quantity_per_sample_directive"):
        value = parameters[key]
        if value is not None and (type(value) is not int or value < 1):
            raise ValueError(f"{key} must be a positive integer or None.")
    cap = parameters["max_quantity_per_sample_directive"]
    lower = max(min(n, parameters["min_sampling_directives"] or 1),
                math.ceil(n / cap) if cap else 1)
    upper = min(n, parameters["max_sampling_directives"] or n)
    if lower > upper:
        raise ValueError("Sampling directive and quantity limits cannot cover N people.")

    dimensions = parameters["sampling_dimensions"]["dimensions"]
    if not isinstance(dimensions, list) or not dimensions:
        raise ValueError("Sampling dimensions must be a nonempty list.")
    names = [dimension["name"] for dimension in dimensions]
    if any(not isinstance(name, str) or not name for name in names) or len(set(names)) != len(names):
        raise ValueError("Sampling dimensions require unique nonempty names.")
    properties, indexed = {}, {}
    for i, dimension in enumerate(dimensions, 1):
        key = str(i)
        if ("range" in dimension) == ("values" in dimension):
            raise ValueError("Each dimension requires either a range or categorical values.")
        if "range" in dimension:
            bounds = dimension["range"]
            if (not isinstance(bounds, list) or len(bounds) != 2
                    or any(type(v) not in (int, float) or not math.isfinite(v) for v in bounds)
                    or bounds[0] > bounds[1]):
                raise ValueError("Numeric dimensions require ordered finite bounds.")
            scalar = {"type": "number", "minimum": bounds[0], "maximum": bounds[1]}
            variants = [scalar, {"type": "array", "items": scalar, "minItems": 2, "maxItems": 2}]
            indexed[key] = copy.deepcopy(dimension)
        else:
            values = dimension["values"]
            if not isinstance(values, (list, dict)) or not values:
                raise ValueError("Categorical values must be a nonempty list or weighted dictionary.")
            if any(not isinstance(value, str) or not value for value in values):
                raise ValueError("Categorical options must be nonempty strings.")
            options = {str(j): value for j, value in enumerate(values, 1)}
            variants = [{"type": "array",
                         "items": {"type": "integer", "enum": list(range(1, len(options) + 1))},
                         "minItems": 1, "maxItems": len(options)}]
            indexed[key] = {"name": dimension["name"], "options": options}
            if isinstance(values, dict):
                indexed[key]["supplied_option_weights"] = {
                    str(j): weight for j, weight in enumerate(values.values(), 1)
                }
        if not parameters["enforce_usage_of_all_dimensions"]:
            variants.append({"type": "null"})
        properties[key] = {"anyOf": variants}
    quantity = {"type": "integer", "minimum": 1}
    if cap is not None:
        quantity["maximum"] = cap
    fields = {
        "id": {"type": "integer", "minimum": 1},
        "subpopulation_description": {"type": "string", "minLength": 1},
        "sampled_values": {"type": "object", "additionalProperties": False,
                           "properties": properties, "required": list(properties)},
        "quantity": quantity,
    }
    directives = {"type": "array", "minItems": lower, "maxItems": upper,
                  "items": {"type": "object", "additionalProperties": False,
                            "properties": fields, "required": list(fields)}}
    schema = {"type": "object", "additionalProperties": False,
              "properties": {"sample_plan": directives}, "required": ["sample_plan"]}
    payload = copy.deepcopy(parameters)
    payload["sampling_dimensions"]["dimensions"] = indexed
    payload["min_sampling_directives"] = lower
    payload["max_sampling_directives"] = upper
    return payload, {"type": "json_schema", "json_schema": {
        "name": "sampling_plan_by_identifiers", "strict": True, "schema": schema}}


def restore_sampling_plan(parameters, value):
    """Reject malformed selections and restore exact names/options, without semantic repair."""
    payload, _ = sampling_plan_spec(parameters)
    if not isinstance(value, dict) or set(value) != {"sample_plan"}:
        raise ValueError("Expected a sample_plan object.")
    plan = value["sample_plan"]
    if (not isinstance(plan, list)
            or not payload["min_sampling_directives"] <= len(plan) <= payload["max_sampling_directives"]):
        raise ValueError("Sampling directive count is outside the supplied limits.")
    dimensions = parameters["sampling_dimensions"]["dimensions"]
    expected = {str(i) for i in range(1, len(dimensions) + 1)}
    restored_plan = []
    for index, directive in enumerate(plan, 1):
        if not isinstance(directive, dict) or set(directive) != {
                "id", "subpopulation_description", "sampled_values", "quantity"}:
            raise ValueError("Invalid sampling directive fields.")
        if type(directive["id"]) is not int or directive["id"] != index:
            raise ValueError("Sampling directive IDs must be consecutive integers starting at 1.")
        quantity = directive["quantity"]
        cap = parameters["max_quantity_per_sample_directive"]
        if type(quantity) is not int or quantity < 1 or (cap is not None and quantity > cap):
            raise ValueError("Invalid sampling directive quantity.")
        description = directive["subpopulation_description"]
        if not isinstance(description, str) or not description.strip():
            raise ValueError("Sampling directives require a nonempty description.")
        selected = directive["sampled_values"]
        if not isinstance(selected, dict) or set(selected) != expected:
            raise ValueError("Selections must include exactly every dimension slot.")
        restored = {}
        for i, dimension in enumerate(dimensions, 1):
            selection = selected[str(i)]
            if selection is None:
                if parameters["enforce_usage_of_all_dimensions"]:
                    raise ValueError("A required dimension cannot be unconstrained.")
                continue
            if "range" in dimension:
                values = selection if isinstance(selection, list) else [selection]
                low, high = dimension["range"]
                if (len(values) not in (1, 2)
                        or any(type(v) not in (int, float) or not math.isfinite(v)
                               or not low <= v <= high for v in values)
                        or (isinstance(selection, list) and (len(values) != 2 or values[0] > values[1]))):
                    raise ValueError("Numeric selection must be a scalar or ordered in-bounds pair.")
                restored[dimension["name"]] = copy.deepcopy(selection)
            else:
                options = list(dimension["values"])
                if (not isinstance(selection, list) or not selection
                        or any(type(option) is not int or not 1 <= option <= len(options)
                               for option in selection)
                        or len(set(selection)) != len(selection)):
                    raise ValueError("Categorical selection requires unique in-range option identifiers.")
                strings = [s for j, s in enumerate(options, 1) if j in selection]
                restored[dimension["name"]] = strings[0] if len(strings) == 1 else strings
        if not restored:
            raise ValueError("A directive cannot omit every dimension.")
        restored_plan.append({**directive, "sampled_values": restored})
    if sum(d["quantity"] for d in restored_plan) != parameters["N"]:
        raise ValueError("Sampling quantities must sum to exactly N.")
    return {"sample_plan": restored_plan}
