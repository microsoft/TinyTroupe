import hashlib
from typing import Union
AgentOrWorld = Union["TinyPerson", "TinyWorld"]

################################################################################
# Other
################################################################################
def first_non_none(*args):
    """
    Returns the first non-None argument from the provided arguments.
    
    Args:
        *args: Variable length argument list.
    
    Returns:
        The first non-None argument, or None if all are None.
    """
    for arg in args:
        if arg is not None:
            return arg
    return None

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

# Replace the global counter with a dictionary of counters per scope
_fresh_id_counters = {"default": 0}

def fresh_id(scope="default"):
    """
    Returns a fresh ID for a new object within the specified scope.
    Different scopes have independent ID sequences.
    
    Args:
        scope (str): The scope to generate the ID in. Defaults to "default".
    
    Returns:
        int: A unique ID within the specified scope.
    """
    global _fresh_id_counters
    
    # Initialize the counter for this scope if it doesn't exist
    if scope not in _fresh_id_counters:
        _fresh_id_counters[scope] = 0
    
    _fresh_id_counters[scope] += 1
    return _fresh_id_counters[scope]

def reset_fresh_id(scope=None):
    """
    Resets the fresh ID counter for the specified scope or for all scopes.
    
    Args:
        scope (str, optional): The scope to reset. If None, resets all scopes.
    """
    global _fresh_id_counters
    
    if scope is None:
        # Reset all counters
        _fresh_id_counters = {"default": 0}
    elif scope in _fresh_id_counters:
        # Reset only the specified scope
        _fresh_id_counters[scope] = 0
