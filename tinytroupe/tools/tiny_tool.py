import re

from tinytroupe.tools import logger
from tinytroupe.utils import JsonSerializableRegistry
from tinytroupe.utils import repeat_on_error


# Separator between a tool's namespace and its action verb, e.g. "TINYEMAILCLIENT::SEND_EMAIL".
# Using "::" (rather than ":") avoids any clash with the target URI scheme (e.g. "tinytool:...").
ACTION_NAMESPACE_SEPARATOR = "::"


def _slugify(text: str) -> str:
    """Turns an arbitrary label into a lowercase, dash-separated slug suitable for ids."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "anonymous"


def namespaced_action_type(tool_namespace: str, verb: str) -> str:
    """Builds a namespaced action type, e.g. ``("TINYEMAILCLIENT", "SEND_EMAIL")`` -> ``"TINYEMAILCLIENT::SEND_EMAIL"``."""
    return f"{tool_namespace}{ACTION_NAMESPACE_SEPARATOR}{verb}"


def parse_action_namespace(action_type: str):
    """
    Splits a (possibly namespaced) action type into ``(namespace, verb)``.

    Args:
        action_type (str): e.g. ``"TINYEMAILCLIENT::SEND_EMAIL"`` or a bare ``"TALK"``.

    Returns:
        tuple[str | None, str]: ``(namespace, verb)``. For an un-namespaced action,
        ``namespace`` is ``None`` and ``verb`` is the action type unchanged.
    """
    if action_type is None:
        return (None, None)
    if ACTION_NAMESPACE_SEPARATOR in action_type:
        namespace, verb = action_type.split(ACTION_NAMESPACE_SEPARATOR, 1)
        return (namespace, verb)
    return (None, action_type)


class TinyTool(JsonSerializableRegistry):
    """
    Base class for tools that agents can use to accomplish specialized tasks, simulating
    office productivity and other software (word processors, calendars, email clients, etc.).

    Identity and ownership
    ----------------------
    Each tool has:
      - ``id``:    its canonical, immutable identifier. This is what ``tinytool:<id>`` URIs
                   reference, and what is recorded in stored events / service records. It does
                   **not** change when ownership changes.
      - ``name``:  a cosmetic/presentation label only (e.g. "Lisa's Calendar").
      - ``owner``: the :class:`TinyPerson` that owns this instance, or ``None`` for a *shared*
                   tool (e.g. an information kiosk or ATM) usable by anyone.

    The tool's *kind* is defined by its class -- there is no separate ``kind`` attribute.

    Per-agent instances vs. shared services
    ---------------------------------------
    By default each agent holds its own tool instance (its own "app"). Tools that need
    cross-agent state (email, calendar, chat, file share) delegate that state to a shared
    *service* object registered in the :class:`TinyWorld` (the "mail server", "calendar
    service", etc.), while the per-agent tool acts as the *client*. Tools that need no shared
    state (e.g. the word processor) simply omit a service.

    Actions and targets
    --------------------
    A tool exposes one or more *namespaced* actions (``TOOLNAMESPACE::VERB``). The mediating
    tool for an action is determined by this namespace plus the acting agent's ownership, so an
    agent always acts through *its own* instance. Action recipients are carried in the action's
    ``target``/``targets`` fields as entity URIs (see :mod:`tinytroupe.utils.targeting`); for
    communication tools these are the human recipients.
    """

    # The action namespace for this tool kind. Subclasses that expose actions should override
    # this with an uppercase token (e.g. "TINYWORDPROCESSOR"). Used to route namespaced actions.
    action_namespace = None

    # Define what attributes should be serialized
    serializable_attributes = ["id", "name", "description", "real_world_side_effects"]

    def __init__(self, id=None, name=None, description=None, owner=None,
                 real_world_side_effects=False, exporter=None, enricher=None):
        """
        Initialize a new tool.

        Args:
            id (str, optional): The canonical, immutable identifier of this tool instance.
                If ``None``, an id is derived from the owner (if any) and the tool class.
            name (str, optional): A cosmetic display label. Defaults to the tool class name.
            description (str, optional): A brief human-readable description of the tool.
            owner (TinyPerson, optional): The agent that owns the tool. If ``None``, the tool
                is *shared* and can be used by anyone.
            real_world_side_effects (bool): Whether the tool has real-world side effects. That
                is to say, if it has the potential to change the state of the world outside of
                the simulation. If it does, it should be used with caution.
            exporter (ArtifactExporter, optional): An exporter that can be used to export the
                results of the tool's actions. If None, the tool will not export results.
            enricher (Enricher, optional): An enricher that can be used to enrich the results of
                the tool's actions. If None, the tool will not enrich results.
        """
        self.name = name if name is not None else self.__class__.__name__
        self.description = description
        self.owner = owner
        self.real_world_side_effects = real_world_side_effects
        self.exporter = exporter
        self.enricher = enricher

        # The id is canonical and immutable; derive a sensible default when not given.
        self.id = id if id is not None else self._default_id(owner)

    def _default_id(self, owner) -> str:
        """Derives a default id of the form ``{owner-slug}.{class-kind}`` or ``shared.{class-kind}``."""
        owner_slug = _slugify(owner.name) if owner is not None else "shared"
        return f"{owner_slug}.{self._class_kind()}"

    @classmethod
    def _class_kind(cls) -> str:
        """Short, lowercase kind token derived from the class name (e.g. ``TinyCalendar`` -> ``calendar``)."""
        name = cls.__name__
        if name.startswith("Tiny"):
            name = name[len("Tiny"):]
        return name.lower()

    def uri(self) -> str:
        """Returns the canonical ``tinytool:<id>`` URI for this tool instance."""
        from tinytroupe.utils import targeting
        return targeting.make_uri(targeting.TINYTOOL, self.id)

    def _process_action(self, agent, action: dict) -> bool:
        raise NotImplementedError("Subclasses must implement this method.")
    
    def _protect_real_world(self):
        if self.real_world_side_effects:
            logger.warning(f" !!!!!!!!!! Tool {self.name} (id={self.id}) has REAL-WORLD SIDE EFFECTS. This is NOT just a simulation. Use with caution. !!!!!!!!!!")
        
    def _enforce_ownership(self, agent):
        if self.owner is not None and agent.name != self.owner.name:
            raise ValueError(f"Agent {agent.name} does not own tool {self.name} (id={self.id}), which is owned by {self.owner.name}.")
    
    def set_owner(self, owner):
        """Sets the owner of this tool. Note: the tool's ``id`` is immutable and does not change."""
        self.owner = owner

    def handles_action(self, action: dict) -> bool:
        """
        Returns True if this tool is responsible for the given action, based on the action
        type's namespace matching this tool's :attr:`action_namespace`.
        """
        if self.action_namespace is None:
            return False
        namespace, _verb = parse_action_namespace(action.get("type"))
        return namespace == self.action_namespace

    def actions_definitions_prompt(self) -> str:
        raise NotImplementedError("Subclasses must implement this method.")
    
    def actions_constraints_prompt(self) -> str:
        raise NotImplementedError("Subclasses must implement this method.")

    def process_action(self, agent, action: dict) -> bool:
        """
        Processes an action by delegating to the subclass implementation.

        If ``_process_action`` raises an exception, the tool-level retry
        mechanism re-invokes it (up to 3 times) after invalidating the
        last API cache entry.  This keeps retries granular — only the
        tool execution is repeated, avoiding side-effects that a full
        turn-level retry would cause.
        """
        self._protect_real_world()
        self._enforce_ownership(agent)

        @repeat_on_error(retries=3, exceptions=[Exception])
        def _try_process():
            return self._process_action(agent, action)

        return _try_process()
