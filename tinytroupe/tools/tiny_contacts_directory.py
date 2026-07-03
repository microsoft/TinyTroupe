"""
Contacts directory: the bridge between routing identity and realistic channel addresses.

TinyTroupe uses two addressing layers:

  - **Routing / social-graph layer**: canonical URIs such as ``tinyperson:Lisa Carter``. This is
    the simulation's ground-truth identity, on which policies and graph extraction operate.
  - **Artifact layer**: realistic, channel-specific addresses such as ``lisa.carter@simcorp.tt``
    (email) or ``@lisa.carter`` (chat), so simulated artifacts mimic real ones.

:class:`TinyContactsDirectory` resolves between these layers in both directions, and also between
a person and their per-channel tool instance (``tinytool:<id>``). It answers in-world questions
like "what is Lisa's email address?" and lets tools render realistic message headers.
"""

from tinytroupe.tools.services import TinyService
from tinytroupe.tools.tiny_tool import _slugify


# Default address formats per channel.
EMAIL = "email"
CHAT = "chat"


class TinyContactsDirectory(TinyService):
    """
    A shared directory mapping people to realistic channel addresses and to their tool instances.

    Addresses are auto-derived from a person's name and the world ``domain`` (e.g.
    ``lisa.carter@simcorp.tt``) unless explicitly overridden.
    """

    serializable_attributes = ["name", "domain", "_person_to_addresses",
                               "_person_to_tools"]

    def __init__(self, domain: str = "simcorp.tt", name: str = None):
        super().__init__(name)
        self.domain = domain
        # person_name -> {channel: address}
        self._person_to_addresses = {}
        # person_name -> {channel: tinytool_uri}
        self._person_to_tools = {}

    # ------------------------------------------------------------------ #
    # Address derivation
    # ------------------------------------------------------------------ #
    def default_address(self, person_name: str, channel: str) -> str:
        """Derives the default channel address for a person (e.g. ``lisa.carter@simcorp.tt``)."""
        slug = _slugify(person_name).replace("-", ".")
        if channel == EMAIL:
            return f"{slug}@{self.domain}"
        if channel == CHAT:
            return f"@{slug}"
        return slug

    # ------------------------------------------------------------------ #
    # Registration
    # ------------------------------------------------------------------ #
    def register(self, person_name: str, channel: str, address: str = None, tool_uri: str = None):
        """
        Registers a person's channel address and (optionally) their tool URI for that channel.

        Args:
            person_name (str): The person's name (the identifier of their ``tinyperson:`` URI).
            channel (str): The channel (e.g. ``"email"``, ``"chat"``).
            address (str, optional): The channel address. Auto-derived if omitted.
            tool_uri (str, optional): The ``tinytool:`` URI of the person's client for the channel.
        """
        if address is None:
            address = self.default_address(person_name, channel)
        self._person_to_addresses.setdefault(person_name, {})[channel] = address
        if tool_uri is not None:
            self._person_to_tools.setdefault(person_name, {})[channel] = tool_uri
        return self

    # ------------------------------------------------------------------ #
    # Resolution
    # ------------------------------------------------------------------ #
    def address_of(self, person_name: str, channel: str) -> str:
        """Returns the channel address of a person, auto-deriving it if not explicitly registered."""
        return self._person_to_addresses.get(person_name, {}).get(
            channel, self.default_address(person_name, channel)
        )

    def person_of_address(self, channel: str, address: str):
        """Returns the person name owning a channel address, or ``None`` if unknown."""
        for person, channels in self._person_to_addresses.items():
            if channels.get(channel) == address:
                return person
        # Fall back to matching an auto-derived address for any known person.
        for person in self._person_to_addresses:
            if self.default_address(person, channel) == address:
                return person
        return None

    def tool_uri_of(self, person_name: str, channel: str):
        """Returns the ``tinytool:`` URI of a person's client for a channel, or ``None``."""
        return self._person_to_tools.get(person_name, {}).get(channel)

    def known_people(self):
        """Returns the set of canonical person names known to the directory (those registered)."""
        return set(self._person_to_addresses.keys()) | set(self._person_to_tools.keys())

    def _match_person(self, name):
        """
        Reconciles a (possibly informal) person name to a canonical registered person.

        Tries, in order: exact match, case-insensitive match, and first-name/prefix match (so
        "Oscar Silva" reconciles to a registered "Oscar", and vice versa). Returns the canonical
        name if found, else ``None``.
        """
        if name is None:
            return None
        known = self.known_people()
        if name in known:
            return name
        lowered = {p.lower(): p for p in known}
        if name.lower() in lowered:
            return lowered[name.lower()]
        # First-name / prefix reconciliation in either direction.
        req_first = name.strip().split()[0].lower() if name.strip() else ""
        for person in known:
            person_first = person.split()[0].lower() if person else ""
            if person_first and req_first and (
                person.lower().startswith(name.lower())
                or name.lower().startswith(person.lower())
                or person_first == req_first
            ):
                return person
        return None

    def resolve_recipient(self, value: str, channel: str):
        """
        Resolves a recipient reference to a canonical person name.

        Accepts a ``tinyperson:`` URI, a bare name (possibly informal), or a channel address, and
        returns the canonical person name. When the reference cannot be reconciled to a known
        person, the parsed identifier is returned unchanged.

        Args:
            value (str): The recipient reference.
            channel (str): The channel used to interpret addresses.

        Returns:
            str: The resolved person name.
        """
        from tinytroupe.utils import targeting

        if value is None:
            return None
        value = value.strip()

        kind, identifier = targeting.parse_uri(value)
        if kind == targeting.TINYPERSON:
            # Could be an address misinterpreted as a bare name; check the directory first.
            person = self.person_of_address(channel, identifier)
            if person is not None:
                return person
            # Otherwise reconcile the (possibly informal) name to a known person.
            matched = self._match_person(identifier)
            return matched if matched is not None else identifier
        # An address or other reference.
        person = self.person_of_address(channel, value)
        return person if person is not None else value
