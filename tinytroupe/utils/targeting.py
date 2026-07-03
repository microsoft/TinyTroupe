"""
Targeting utilities for TinyTroupe actions.

TinyTroupe actions are directed at one or more *entities* via the ``target`` (single)
or ``targets`` (list) fields. Both fields denote the **same concept** -- the
destination(s) of the action, i.e. the edges of the simulated social graph -- and
differ only in arity:

  - ``target``:  a single entity URI (enforces exactly one destination).
  - ``targets``: a list of entity URIs (allows zero or more destinations).

Providing both in the same action is ambiguous and raises an error.

Entities are addressed with a uniform URI scheme ``<kind>:<identifier>``:

  - ``tinyperson:<name>``      -- a :class:`TinyPerson` (its name is its id).
  - ``tinytool:<id>``          -- a :class:`TinyTool` (by its id).
  - ``tinygroup:<id>``         -- reserved for a future group of agents.
  - ``tinyroom:<id>`` /
    ``tinyresource:<id>``      -- reserved for future non-agent entities.

For robustness, a bare value without a recognized ``<kind>:`` prefix is interpreted
as a ``tinyperson`` (i.e. ``"Lisa Carter"`` is equivalent to
``"tinyperson:Lisa Carter"``). The empty string denotes an absent/anonymous target.

For *communication* actions the targets are the human recipients; the mediating tool,
if any, is implied by the action type's ``TOOLNAME::`` namespace (see
:mod:`tinytroupe.tools`). For actions that operate *on a tool as an object* (e.g. a
future ``SYSTEM::UNINSTALL_TOOL``), the ``tinytool:`` URI itself is the target -- which
falls out naturally from "target = the entity the action is directed at".
"""

TINYPERSON = "tinyperson"
TINYTOOL = "tinytool"
TINYGROUP = "tinygroup"
TINYROOM = "tinyroom"
TINYRESOURCE = "tinyresource"

# All recognized entity kinds. A prefix not in this set is treated as part of a
# bare tinyperson name (robustness), so values like "Lisa Carter" keep working.
KNOWN_KINDS = frozenset(
    {TINYPERSON, TINYTOOL, TINYGROUP, TINYROOM, TINYRESOURCE}
)


def parse_uri(uri):
    """
    Parses an entity URI into a ``(kind, identifier)`` tuple.

    Args:
        uri (str | None): The URI to parse. May be ``None`` or empty (anonymous),
            a fully-qualified URI (``"tinyperson:Lisa Carter"``), or a bare name
            (``"Lisa Carter"``, interpreted as a ``tinyperson``).

    Returns:
        tuple[str, str]: ``(kind, identifier)``. For an absent/anonymous target,
        returns ``("", "")``. For a bare name, ``kind`` is ``tinyperson``.
    """
    if uri is None:
        return ("", "")
    uri = uri.strip()
    if uri == "":
        return ("", "")
    if ":" in uri:
        prefix, rest = uri.split(":", 1)
        if prefix in KNOWN_KINDS:
            return (prefix, rest.strip())
    # No recognized prefix -> treat the whole value as a bare tinyperson name.
    return (TINYPERSON, uri)


def make_uri(kind, identifier):
    """
    Builds a canonical entity URI from a kind and identifier.

    Args:
        kind (str): One of the recognized entity kinds (see :data:`KNOWN_KINDS`).
        identifier (str): The entity identifier (e.g. a person's name, a tool id).

    Returns:
        str: The canonical URI ``"<kind>:<identifier>"``.
    """
    if kind not in KNOWN_KINDS:
        raise ValueError(
            f"Unknown entity kind '{kind}'. Known kinds: {sorted(KNOWN_KINDS)}."
        )
    return f"{kind}:{identifier}"


def is_kind(uri, kind):
    """Returns True if ``uri`` resolves to the given entity ``kind``."""
    return parse_uri(uri)[0] == kind


def extract_target_uris(action):
    """
    Extracts the list of destination URIs from an action's ``target``/``targets``.

    Both fields mean the same thing and differ only in arity. Exactly one spelling
    may carry destinations; providing both (non-empty) is ambiguous.

    Args:
        action (dict): An action dict that may contain ``target`` and/or ``targets``.

    Returns:
        list[str]: The (possibly empty) list of destination URIs, with empty/absent
        entries removed.

    Raises:
        ValueError: If both ``target`` and ``targets`` carry destinations.
    """
    raw_single = action.get("target", None)
    raw_list = action.get("targets", None)

    has_single = raw_single not in (None, "")
    has_list = bool(raw_list)

    if has_single and has_list:
        raise ValueError(
            "An action must not specify both 'target' and 'targets'. "
            "Use 'target' for a single destination or 'targets' for multiple."
        )

    if has_list:
        return [u for u in raw_list if u not in (None, "")]
    if has_single:
        return [raw_single]
    return []


def recipient_names(action):
    """
    Returns the names of the ``tinyperson`` recipients of an action.

    Convenience for communication tools and social-graph extraction: filters the
    action's destinations down to person identifiers.

    Args:
        action (dict): The action dict.

    Returns:
        list[str]: The recipient person names (identifiers of ``tinyperson`` URIs).
    """
    names = []
    for uri in extract_target_uris(action):
        kind, identifier = parse_uri(uri)
        if kind == TINYPERSON:
            names.append(identifier)
    return names
