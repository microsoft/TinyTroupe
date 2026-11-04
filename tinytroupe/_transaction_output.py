"""Detached transaction outputs with references to canonical simulation objects.

The legacy None/JSON/List/reference envelopes remain readable. New Dict and
Tuple envelopes make nested containers unambiguous without inspecting user data
for reserved keys. Ordinary containers are copied; simulated entities retain
identity through their existing global registries.
"""

import copy


def _registries():
    # Lazy imports avoid the control -> agent -> control import cycle.
    from tinytroupe.agent import TinyPerson
    from tinytroupe.environment import TinyWorld
    from tinytroupe.factory.tiny_factory import TinyFactory

    return (
        ("TinyPersonRef", TinyPerson, TinyPerson.all_agents),
        ("TinyWorldRef", TinyWorld, TinyWorld.all_environments),
        ("TinyFactoryRef", TinyFactory, TinyFactory.all_factories),
    )


def encode_output(output):
    """Encode recursively, rejecting cycles before a trace can be published."""
    registries = _registries()
    active = set()

    def encode(value):
        if value is None:
            return None
        for tag, cls, registry in registries:
            if isinstance(value, cls):
                if registry.get(value.name) is not value:
                    raise ValueError(f"Unregistered {tag} output: {value.name}")
                return {"type": tag, "name": value.name}
        if isinstance(value, (str, int, float, bool)):
            return {"type": "JSON", "value": value}
        if not isinstance(value, (list, tuple, dict)):
            raise ValueError(f"Unsupported output type: {type(value)}")
        identity = id(value)
        if identity in active:
            raise ValueError("Cyclic transaction output cannot be cached")
        active.add(identity)
        try:
            if isinstance(value, dict):
                pairs = []
                for key, item in value.items():
                    if key is not None and not isinstance(key, (str, int, float, bool)):
                        raise ValueError(
                            f"Unsupported output dictionary key: {type(key)}"
                        )
                    pairs.append([key, encode(item)])
                return {"type": "Dict", "value": pairs}
            tag = "Tuple" if isinstance(value, tuple) else "List"
            return {"type": tag, "value": [encode(item) for item in value]}
        finally:
            active.remove(identity)

    return encode(output)


def decode_output(encoded):
    """Restore canonical references and a fresh ordinary value on each replay."""
    registries = {tag: registry for tag, _, registry in _registries()}
    active = set()

    def decode(value):
        if value is None:
            return None
        if not isinstance(value, dict) or "type" not in value:
            raise ValueError("Invalid cached output envelope")
        identity = id(value)
        if identity in active:
            raise ValueError("Cyclic cached output envelope")
        active.add(identity)
        try:
            tag = value["type"]
            if not isinstance(tag, str):
                raise ValueError("Invalid cached output type")
            if tag in registries:
                name = value.get("name")
                if not isinstance(name, str) or name not in registries[tag]:
                    raise ValueError(f"Unknown {tag} output reference: {name}")
                return registries[tag][name]
            if tag == "JSON":
                if "value" not in value:
                    raise ValueError("Missing cached JSON output value")
                # Old caches stored whole ordinary dicts/tuples in this envelope.
                # They are data, even if their own keys resemble an envelope.
                return copy.deepcopy(value["value"])
            items = value.get("value")
            if tag not in ("List", "Tuple", "Dict") or not isinstance(items, list):
                raise ValueError(f"Unsupported cached output type: {tag}")
            if tag == "Dict":
                result = {}
                for pair in items:
                    if not isinstance(pair, list) or len(pair) != 2:
                        raise ValueError("Invalid cached dictionary entry")
                    key, child = pair
                    if key is not None and not isinstance(key, (str, int, float, bool)):
                        raise ValueError("Invalid cached dictionary key")
                    if key in result:
                        raise ValueError("Duplicate cached dictionary key")
                    result[key] = decode(child)
                return result
            result = [decode(child) for child in items]
            return tuple(result) if tag == "Tuple" else result
        finally:
            active.remove(identity)

    return decode(encoded)
