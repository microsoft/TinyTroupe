"""Reconcile persisted faculties with caller-provided runtime resources.

Tool serialization intentionally excludes owners, exporters and enrichers. Replay
must apply persisted fields to the existing faculty/tool graph, not replace it
with __new__ instances that lack those required runtime fields. This policy is
local to TinyPerson state restoration; the general JSON registry is unchanged.
"""

import copy

from tinytroupe.utils import JsonSerializableRegistry


def restore_faculties(states, existing):
    from tinytroupe.tools import TinyCalendar, TinyTool, TinyWordProcessor

    def identity(value):
        return type(value), getattr(value, "name", None)

    def merge(value, live=None):
        if isinstance(value, JsonSerializableRegistry):
            matched = live is not None and identity(live) == identity(value)
            if matched:
                target = live
            elif isinstance(value, TinyTool):
                # These standard tools have safe no-resource constructors.
                # Custom tool resources cannot be inferred from old records.
                constructor = {
                    TinyCalendar: TinyCalendar,
                    TinyWordProcessor: TinyWordProcessor,
                }.get(type(value))
                if constructor is None:
                    raise ValueError(
                        f"{type(value).__name__} requires a caller-provided runtime tool"
                    )
                target = constructor()
            else:
                target = value
            for name, child in list(value.__dict__.items()):
                previous = getattr(live, name, None) if matched else None
                setattr(target, name, merge(child, previous))
            return target
        if isinstance(value, list):
            candidates = list(live) if isinstance(live, list) else []
            result = []
            for child in value:
                match = None
                if isinstance(child, JsonSerializableRegistry):
                    for index, candidate in enumerate(candidates):
                        if identity(candidate) == identity(child):
                            match = candidates.pop(index)
                            break
                result.append(merge(child, match))
            return result
        if isinstance(value, dict):
            previous = live if isinstance(live, dict) else {}
            return {
                key: merge(child, previous.get(key)) for key, child in value.items()
            }
        return copy.deepcopy(value)

    decoded = [JsonSerializableRegistry.from_json(state) for state in states]
    return merge(decoded, existing)
