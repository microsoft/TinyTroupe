"""Use explicit item identifiers for semantic grouping; reconstruct strings without model copying."""

import json
import re
from collections import Counter


def source_items(case):
    """Recover the literal source occurrences and requested category bound."""
    messages = case["request"]["messages"]
    users = [m for m in messages if m["role"] == "user" and isinstance(m.get("content"), str)
             and "INPUT ELEMENTS:\n" in m["content"]]
    if len(users) != 1:
        raise ValueError("Require one literal normalization source list.")
    text = users[0]["content"]
    match = re.search(r"Produce UP TO (\d+)", text)
    if not match:
        raise ValueError("Missing normalization category bound.")
    items = text.split("INPUT ELEMENTS:\n", 1)[1].removeprefix("  - ").removesuffix("\n").split("\n  - ")
    if not items or any(not item for item in items) or int(match[1]) < 1:
        raise ValueError("Require nonempty items and a positive grouping bound.")
    return items, int(match[1])


def indexed_request(case, instruction):
    """Replace the copying contract with an auditable, strictly keyed assignment contract."""
    items, limit = source_items(case)
    groups = min(limit, len(items))
    ids = [str(i) for i in range(1, len(items) + 1)]
    labels = [str(i) for i in range(1, groups + 1)]
    schema = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "labels": {
                "type": "object", "additionalProperties": False,
                "properties": {k: {"type": "string", "minLength": 1, "maxLength": 40} for k in labels},
                "required": labels,
            },
            "assignments": {
                "type": "object", "additionalProperties": False,
                "properties": {k: {"type": "integer", "minimum": 1, "maximum": groups} for k in ids},
                "required": ids,
            },
        },
        "required": ["labels", "assignments"],
    }
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": json.dumps({
            "maximum_groups": limit, "groups_to_use": groups,
            "items": {k: item for k, item in zip(ids, items)},
        }, ensure_ascii=False)},
    ], {"type": "json_schema", "json_schema": {
        "name": "semantic_partition_by_id", "strict": True, "schema": schema,
    }}


def reconstruct(case, value):
    """Reject invalid partitions explicitly, then restore exact original occurrence strings."""
    items, limit = source_items(case)
    labels, assignments = value["labels"], value["assignments"]
    expected_ids = {str(i) for i in range(1, len(items) + 1)}
    if set(assignments) != expected_ids:
        raise ValueError("Assignment IDs must cover each source occurrence exactly.")
    if not 1 <= len(labels) <= limit or len(set(labels.values())) != len(labels):
        raise ValueError("Require distinct labels within the requested category bound.")
    if any(not isinstance(s, str) or not s.strip() or len(s) > 40 for s in labels.values()):
        raise ValueError("Labels must be nonempty strings of at most 40 characters.")
    if any(type(v) is not int or str(v) not in labels for v in assignments.values()):
        raise ValueError("Every assignment must identify an existing category.")
    output = {label: [] for label in labels.values()}
    for i, item in enumerate(items, 1):
        output[labels[str(assignments[str(i)])]].append(item)
    if any(not members for members in output.values()):
        raise ValueError("Empty categories are not a meaningful partition.")
    if Counter(s for members in output.values() for s in members) != Counter(items):
        raise AssertionError("Reconstruction failed to preserve occurrence multiset.")
    return output
