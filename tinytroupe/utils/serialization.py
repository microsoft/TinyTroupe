"""
Deterministic serialization utilities for cache key generation.

This module provides robust, deterministic serialization for creating consistent
cache keys across different executions. It handles complex nested structures,
custom objects, and excludes unpickleable internals (e.g. threading primitives)
so the primary path succeeds without fallbacks.
"""
import pickle
import hashlib
import inspect
import json
import threading
from typing import Any, Callable, Dict, Optional, Tuple
from collections import OrderedDict

import logging
logger = logging.getLogger("tinytroupe")


# Registry for custom serializers for specific types
_custom_serializers: Dict[type, Callable[[Any], Any]] = {}

_THREAD_PRIMITIVE_TYPES = (
    type(threading.Lock()),
    type(threading.RLock()),
    threading.Condition,
    threading.Event,
    threading.Semaphore,
    threading.Thread,
)


def register_serializer(obj_type: type, serializer: Callable[[Any], Any]) -> None:
    """
    Register a custom serializer for a specific type.

    This allows objects of custom types to be serialized in a deterministic way
    for cache key generation.

    Args:
        obj_type: The type to register a serializer for
        serializer: A function that takes an object of obj_type and returns
                   a serializable representation (dict, list, str, etc.)

    Example:
        >>> class MyClass:
        ...     def __init__(self, value):
        ...         self.value = value
        >>>
        >>> def serialize_my_class(obj):
        ...     return {"_type": "MyClass", "value": obj.value}
        >>>
        >>> register_serializer(MyClass, serialize_my_class)
    """
    _custom_serializers[obj_type] = serializer
    logger.debug(f"Registered custom serializer for type {obj_type.__name__}")


def unregister_serializer(obj_type: type) -> None:
    """
    Remove a custom serializer for a specific type.

    Args:
        obj_type: The type to unregister
    """
    if obj_type in _custom_serializers:
        del _custom_serializers[obj_type]
        logger.debug(f"Unregistered custom serializer for type {obj_type.__name__}")


def make_canonical(data: Any) -> Any:
    """
    Create a canonical (deterministic) representation of data.

    This function recursively processes data structures to ensure they can be
    pickled in a deterministic way. It handles:
    - Dictionaries: Sorted by key
    - Sets: Converted to sorted tuples
    - Lists/Tuples: Recursively canonicalized
    - Custom objects: Uses registered serializers or attempts standard pickle

    Args:
        data: The data to canonicalize

    Returns:
        A canonical representation of the data

    Examples:
        >>> make_canonical({"b": 2, "a": 1})
        (('a', 1), ('b', 2))

        >>> make_canonical([{3, 1, 2}, {"y": 0, "x": 1}])
        ((1, 2, 3), (('x', 1), ('y', 0)))
    """
    # Check for custom serializer first
    obj_type = type(data)
    if obj_type in _custom_serializers:
        try:
            serialized = _custom_serializers[obj_type](data)
            # Recursively canonicalize the serialized form
            return make_canonical(serialized)
        except Exception as e:
            logger.warning(f"Custom serializer for {obj_type.__name__} failed: {e}")
            # Fall through to default handling

    # Handle built-in types
    if isinstance(data, dict):
        # Sort dictionary by keys and canonicalize values
        return tuple(sorted((k, make_canonical(v)) for k, v in data.items()))

    elif isinstance(data, (list, tuple)):
        # Recursively canonicalize elements
        return tuple(make_canonical(elem) for elem in data)

    elif isinstance(data, set):
        # Convert set to sorted tuple
        # Elements must be hashable, so we canonicalize then sort
        try:
            return tuple(sorted(make_canonical(elem) for elem in data))
        except TypeError:
            # If elements aren't sortable, convert to string first
            return tuple(sorted(str(make_canonical(elem)) for elem in data))

    elif isinstance(data, frozenset):
        # Similar to set
        try:
            return tuple(sorted(make_canonical(elem) for elem in data))
        except TypeError:
            return tuple(sorted(str(make_canonical(elem)) for elem in data))

    elif isinstance(data, OrderedDict):
        # Preserve order but canonicalize values
        return tuple((k, make_canonical(v)) for k, v in data.items())

    # For basic types (int, str, float, bool, None), return as is
    elif isinstance(data, (int, str, float, bool, type(None), bytes)):
        return data

    # Threading primitives are unpickleable; use stable placeholder (excluded from cache key content)
    elif isinstance(data, _THREAD_PRIMITIVE_TYPES):
        return ("__thread_primitive__", type(data).__name__)

    elif inspect.isfunction(data) or inspect.ismethod(data) or inspect.isbuiltin(data):
        code = getattr(data, "__code__", None)
        code_marker = None
        if code is not None:
            code_marker = (
                code.co_filename,
                code.co_firstlineno,
                code.co_name,
                code.co_code,
                tuple(repr(const) for const in code.co_consts),
                code.co_names,
            )
        return (
            "__callable__",
            getattr(data, "__module__", None),
            getattr(data, "__qualname__", getattr(data, "__name__", type(data).__name__)),
            code_marker,
        )

    # For custom objects, canonicalize __dict__ but exclude unpickleable attributes
    elif hasattr(data, "__dict__"):
        filtered = {}
        for k, v in data.__dict__.items():
            if isinstance(v, _THREAD_PRIMITIVE_TYPES):
                continue
            try:
                filtered[k] = make_canonical(v)
            except (TypeError, RecursionError):
                filtered[k] = ("__unpickleable__", type(v).__name__, k)
        return ("__custom_object__", type(data).__name__, tuple(sorted((k, filtered[k]) for k in filtered)))

    else:
        return data


def compute_hash(data: Any, algorithm: str = "sha256") -> str:
    """
    Compute a deterministic hash of the given data.

    Uses canonical representation and pickle serialization to ensure
    the same data always produces the same hash.

    Args:
        data: The data to hash
        algorithm: Hash algorithm to use (default: "sha256")
                  Supported: "sha256", "sha512", "md5", "sha1"

    Returns:
        Hexadecimal hash string

    Raises:
        ValueError: If algorithm is not supported
        SerializationError: If data cannot be serialized

    Examples:
        >>> compute_hash({"a": 1, "b": 2})
        '...'  # Some hex string

        >>> compute_hash([1, 2, 3]) == compute_hash([1, 2, 3])
        True
    """
    # Validate algorithm
    hash_algorithms = {
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
        "md5": hashlib.md5,
        "sha1": hashlib.sha1
    }

    if algorithm not in hash_algorithms:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}. "
                        f"Supported: {list(hash_algorithms.keys())}")

    try:
        # Create canonical representation
        canonical_data = make_canonical(data)

        # Pickle with highest protocol for consistency
        pickled_data = pickle.dumps(canonical_data, protocol=pickle.HIGHEST_PROTOCOL)

        # Compute hash
        hash_func = hash_algorithms[algorithm]()
        hash_func.update(pickled_data)

        return hash_func.hexdigest()

    except Exception as e:
        logger.error(f"Failed to serialize data for hashing: {e}")
        raise SerializationError(f"Cannot serialize data: {e}") from e


def compute_function_call_hash(
    function_name: str,
    *args,
    algorithm: str = "sha256",
    **kwargs
) -> str:
    """
    Compute a deterministic hash for a function call.

    This is the primary function for generating cache keys for function calls.
    It ensures that the same function called with the same arguments always
    produces the same hash, regardless of argument order (for kwargs).

    Args:
        function_name: Name of the function
        *args: Positional arguments
        algorithm: Hash algorithm (default: "sha256")
        **kwargs: Keyword arguments

    Returns:
        Hexadecimal hash string

    Examples:
        >>> compute_function_call_hash("my_func", 1, 2, x=3, y=4)
        '...'  # Some hex string

        >>> h1 = compute_function_call_hash("f", x=1, y=2)
        >>> h2 = compute_function_call_hash("f", y=2, x=1)
        >>> h1 == h2  # Keyword argument order doesn't matter
        True
    """
    # Canonicalize and hash; no fallback - primary path must succeed
    canonical_args = make_canonical(args)
    canonical_kwargs = tuple(sorted((k, make_canonical(v)) for k, v in kwargs.items()))
    representation = (function_name, canonical_args, canonical_kwargs)
    return compute_hash(representation, algorithm=algorithm)


def compute_fallback_hash(
    function_name: str,
    args: tuple,
    kwargs: dict,
    algorithm: str = "sha256"
) -> str:
    """
    Compute a fallback hash when standard serialization fails.

    This uses string representation as a last resort. It's less reliable
    but ensures the system can continue functioning even with unpickleable objects.

    Args:
        function_name: Name of the function
        args: Positional arguments tuple
        kwargs: Keyword arguments dict
        algorithm: Hash algorithm (default: "sha256")

    Returns:
        Hexadecimal hash string

    Warning:
        This fallback may produce different hashes for semantically identical
        objects if their string representations differ.
    """
    try:
        # Create a string representation
        # Use repr instead of str for more detailed representation
        args_repr = repr(args)
        kwargs_repr = repr(sorted(kwargs.items()))
        fallback_str = f"{function_name}|{args_repr}|{kwargs_repr}"

        # Hash the string
        hash_func = getattr(hashlib, algorithm)()
        # Use 'surrogatepass' error handler to handle any problematic characters
        hash_func.update(fallback_str.encode('utf-8', 'surrogatepass'))

        hash_value = hash_func.hexdigest()

        logger.debug(f"Computed fallback hash for {function_name}: {hash_value[:16]}...")
        return hash_value

    except Exception as e:
        # Absolute last resort: hash the function name only
        logger.error(f"Fallback hash failed for {function_name}: {e}. Using function name only.")
        hash_func = getattr(hashlib, algorithm)()
        hash_func.update(function_name.encode('utf-8'))
        return hash_func.hexdigest()


def serialize_to_json(data: Any, use_canonical: bool = True) -> str:
    """
    Serialize data to JSON string.

    Args:
        data: Data to serialize
        use_canonical: Whether to use canonical representation first (default: True)

    Returns:
        JSON string

    Note:
        If use_canonical=True, data is canonicalized first, which may change
        the structure (e.g., sets become tuples, dicts become tuple of tuples).
    """
    if use_canonical:
        data = make_canonical(data)

    # Custom JSON encoder for non-standard types
    def default_encoder(obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8', 'replace')
        elif hasattr(obj, '__dict__'):
            return {'__type__': type(obj).__name__, '__dict__': obj.__dict__}
        else:
            return str(obj)

    return json.dumps(data, default=default_encoder, sort_keys=True, indent=None)


def is_pickleable(obj: Any) -> bool:
    """
    Check if an object can be pickled.

    Args:
        obj: Object to check

    Returns:
        True if object can be pickled, False otherwise
    """
    try:
        pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        return True
    except Exception:
        return False


def ensure_serializable(data: Any) -> Any:
    """
    Ensure data is serializable by converting problematic types.

    This is a best-effort function that attempts to make data serializable
    by converting common problematic types.

    Args:
        data: Data to make serializable

    Returns:
        Serializable version of data
    """
    if isinstance(data, dict):
        return {k: ensure_serializable(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [ensure_serializable(elem) for elem in data]
    elif type(data).__name__ == "deque":
        return [ensure_serializable(elem) for elem in data]
    elif isinstance(data, set):
        return tuple(ensure_serializable(elem) for elem in sorted(data, key=str))
    elif isinstance(data, (int, str, float, bool, type(None))):
        return data
    elif type(data).__name__ in ("Lock", "RLock"):
        return "<Lock>"
    elif hasattr(data, '__dict__'):
        # Attempt to serialize object's __dict__
        return {
            '__type__': type(data).__name__,
            '__dict__': ensure_serializable(data.__dict__)
        }
    else:
        # Last resort: convert to string
        return str(data)


class SerializationError(Exception):
    """Raised when data cannot be serialized for hashing."""
    pass


# Backward compatibility aliases
canonical_representation = make_canonical
deterministic_hash = compute_hash
function_call_hash = compute_function_call_hash
