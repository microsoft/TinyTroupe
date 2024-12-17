import hashlib
from typing import Union
AgentOrWorld = Union["TinyPerson", "TinyWorld"]

################################################################################
# Other
################################################################################
def name_or_empty(named_entity: AgentOrWorld):
    """
    Returns the name of the specified agent or environment, or an empty string if the agent is None.
    """
    if named_entity is None:
        return ""
    else:
        return named_entity.name

def custom_hash(obj):
    """
    Returns a hash for the specified object. The object is first converted
    to a string, to make it hashable. This method is deterministic,
    contrary to the built-in hash() function.
    """

    return hashlib.sha256(str(obj).encode()).hexdigest()

_fresh_id_counter = 0
def fresh_id():
    """
    Returns a fresh ID for a new object. This is useful for generating unique IDs for objects.
    """
    global _fresh_id_counter
    _fresh_id_counter += 1
    return _fresh_id_counter

def reset_fresh_id():
    """
    Resets the fresh ID counter. This is useful for testing purposes.
    """
    global _fresh_id_counter
    _fresh_id_counter = 0
