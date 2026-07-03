"""
Shared backend services for tools.

Many office tools (email, calendar, chat, file share) are realistically modelled as a
**per-agent client** plus a **shared backend service** -- the way Outlook/Teams clients talk
to a shared mail/calendar server. The per-agent :class:`~tinytroupe.tools.tiny_tool.TinyTool`
is the client (owned by an agent, addressable as ``tinytool:<id>``); the service is a single
object registered in the :class:`~tinytroupe.environment.tiny_world.TinyWorld` that holds the
cross-agent state and routes messages between clients.

Delivery timing
---------------
Communication is **asynchronous**: an item sent during simulation step *N* is perceived by its
recipients during step *N+1*. This is achieved by enqueuing outgoing items and delivering the
queue at the start of each world step via :meth:`TinyService.flush`. All times are
**simulation time** (the world clock), never wall-clock time.
"""

from tinytroupe.utils import JsonSerializableRegistry
from tinytroupe.tools import logger


class TinyService(JsonSerializableRegistry):
    """
    Base class for shared backend services used by tools.

    A service lives inside a :class:`TinyWorld` and is flushed once per simulation step so that
    pending (asynchronous) deliveries reach their recipients on the following step.
    """

    serializable_attributes = ["name"]

    def __init__(self, name: str = None):
        self.name = name if name is not None else self.__class__.__name__

    def flush(self, world) -> None:
        """
        Delivers any pending/due items to their recipient agents as stimuli.

        Called once per :meth:`TinyWorld._step` (after the clock advances, before agents act),
        which yields next-step delivery semantics. Subclasses override this to implement their
        channel-specific delivery. The default implementation does nothing.

        Args:
            world (TinyWorld): The world whose agents should receive deliveries. Used to resolve
                recipient names to agents and to read the current simulation time.
        """
        pass

    def _resolve_agent(self, world, name: str):
        """Resolves a recipient name to an agent in the world, or returns ``None`` if absent."""
        agent = world.get_agent_by_name(name)
        if agent is None:
            logger.warning(
                f"[{self.name}] Could not resolve recipient '{name}' to an agent in world "
                f"'{getattr(world, 'name', '?')}'. The delivery will be dropped."
            )
        return agent
