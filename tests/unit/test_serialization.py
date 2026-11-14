"""
Tests for deterministic serialization utilities.

This module tests the serialization functions used for cache key generation,
ensuring they produce consistent, deterministic hashes.
"""
import pytest
import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from testing_utils import *

from tinytroupe.utils.serialization import (
    make_canonical,
    compute_hash,
    compute_function_call_hash,
    compute_fallback_hash,
    register_serializer,
    unregister_serializer,
    is_pickleable,
    ensure_serializable,
    SerializationError
)


class TestMakeCanonical:
    """Test canonical representation creation."""

    def test_dict_ordering(self, setup):
        """Test that dictionaries are canonicalized with sorted keys."""
        dict1 = {"b": 2, "a": 1}
        dict2 = {"a": 1, "b": 2}

        canon1 = make_canonical(dict1)
        canon2 = make_canonical(dict2)

        assert canon1 == canon2
        assert canon1 == (('a', 1), ('b', 2))

    def test_nested_dict_ordering(self, setup):
        """Test nested dictionary canonicalization."""
        dict1 = {"outer": {"b": 2, "a": 1}, "key": "value"}
        dict2 = {"key": "value", "outer": {"a": 1, "b": 2}}

        canon1 = make_canonical(dict1)
        canon2 = make_canonical(dict2)

        assert canon1 == canon2

    def test_list_ordering(self, setup):
        """Test that lists preserve order."""
        list1 = [3, 1, 2]
        list2 = [1, 2, 3]

        canon1 = make_canonical(list1)
        canon2 = make_canonical(list2)

        # Lists should preserve order, so these should be different
        assert canon1 != canon2
        assert canon1 == (3, 1, 2)
        assert canon2 == (1, 2, 3)

    def test_set_determinism(self, setup):
        """Test that sets are converted to sorted tuples."""
        set1 = {3, 1, 2}
        set2 = {2, 1, 3}

        canon1 = make_canonical(set1)
        canon2 = make_canonical(set2)

        # Sets should produce same canonical form
        assert canon1 == canon2
        assert canon1 == (1, 2, 3)

    def test_mixed_structures(self, setup):
        """Test canonicalization of mixed data structures."""
        data = {
            "list": [1, 2, 3],
            "dict": {"x": 10, "y": 20},
            "set": {5, 4, 6},
            "scalar": 42
        }

        canon = make_canonical(data)

        # Should be deterministic
        assert canon == make_canonical(data)
        assert isinstance(canon, tuple)

    def test_basic_types(self, setup):
        """Test that basic types are returned as-is."""
        assert make_canonical(42) == 42
        assert make_canonical("hello") == "hello"
        assert make_canonical(3.14) == 3.14
        assert make_canonical(True) == True
        assert make_canonical(None) == None

    def test_custom_object_with_dict(self, setup):
        """Test canonicalization of custom objects."""
        class MyClass:
            def __init__(self, value):
                self.value = value
                self.name = "test"

        obj = MyClass(42)
        canon = make_canonical(obj)

        # Should attempt to canonicalize __dict__
        assert isinstance(canon, tuple)
        assert canon[0] == '__custom_object__'
        assert canon[1] == 'MyClass'


class TestComputeHash:
    """Test hash computation."""

    def test_hash_determinism(self, setup):
        """Test that same data produces same hash."""
        data = {"a": 1, "b": [2, 3], "c": {4, 5}}

        hash1 = compute_hash(data)
        hash2 = compute_hash(data)

        assert hash1 == hash2

    def test_hash_different_data(self, setup):
        """Test that different data produces different hashes."""
        data1 = {"a": 1}
        data2 = {"a": 2}

        hash1 = compute_hash(data1)
        hash2 = compute_hash(data2)

        assert hash1 != hash2

    def test_hash_dict_order_independence(self, setup):
        """Test that dict order doesn't affect hash."""
        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "a": 1, "b": 2}

        hash1 = compute_hash(data1)
        hash2 = compute_hash(data2)

        assert hash1 == hash2

    def test_hash_algorithms(self, setup):
        """Test different hash algorithms."""
        data = {"test": "data"}

        sha256_hash = compute_hash(data, algorithm="sha256")
        sha512_hash = compute_hash(data, algorithm="sha512")
        md5_hash = compute_hash(data, algorithm="md5")

        # Different algorithms should produce different hashes
        assert sha256_hash != sha512_hash
        assert sha256_hash != md5_hash

        # Same algorithm should be consistent
        assert sha256_hash == compute_hash(data, algorithm="sha256")

    def test_invalid_algorithm(self, setup):
        """Test that invalid algorithm raises error."""
        with pytest.raises(ValueError):
            compute_hash({"a": 1}, algorithm="invalid")


class TestComputeFunctionCallHash:
    """Test function call hash computation."""

    def test_function_hash_determinism(self, setup):
        """Test that same function call produces same hash."""
        hash1 = compute_function_call_hash("my_func", 1, 2, x=3, y=4)
        hash2 = compute_function_call_hash("my_func", 1, 2, x=3, y=4)

        assert hash1 == hash2

    def test_function_hash_kwargs_order(self, setup):
        """Test that kwargs order doesn't affect hash."""
        hash1 = compute_function_call_hash("func", x=1, y=2, z=3)
        hash2 = compute_function_call_hash("func", z=3, x=1, y=2)

        assert hash1 == hash2

    def test_function_hash_different_names(self, setup):
        """Test that different function names produce different hashes."""
        hash1 = compute_function_call_hash("func1", 1, 2)
        hash2 = compute_function_call_hash("func2", 1, 2)

        assert hash1 != hash2

    def test_function_hash_different_args(self, setup):
        """Test that different args produce different hashes."""
        hash1 = compute_function_call_hash("func", 1, 2)
        hash2 = compute_function_call_hash("func", 1, 3)

        assert hash1 != hash2

    def test_function_hash_complex_args(self, setup):
        """Test with complex argument structures."""
        args = ([1, 2, 3], {"a": 1, "b": 2})
        kwargs = {"config": {"x": 10, "y": 20}, "data": [4, 5, 6]}

        hash1 = compute_function_call_hash("process", *args, **kwargs)
        hash2 = compute_function_call_hash("process", *args, **kwargs)

        assert hash1 == hash2


class TestComputeFallbackHash:
    """Test fallback hash computation."""

    def test_fallback_hash_determinism(self, setup):
        """Test that fallback hash is deterministic."""
        args = (1, 2, 3)
        kwargs = {"x": 4, "y": 5}

        hash1 = compute_fallback_hash("func", args, kwargs)
        hash2 = compute_fallback_hash("func", args, kwargs)

        assert hash1 == hash2

    def test_fallback_hash_different_data(self, setup):
        """Test that different data produces different fallback hashes."""
        hash1 = compute_fallback_hash("func", (1,), {})
        hash2 = compute_fallback_hash("func", (2,), {})

        assert hash1 != hash2


class TestCustomSerializers:
    """Test custom serializer registration."""

    def test_register_serializer(self, setup):
        """Test registering a custom serializer."""
        class CustomClass:
            def __init__(self, value):
                self.value = value

        def custom_serializer(obj):
            return {"type": "CustomClass", "value": obj.value}

        register_serializer(CustomClass, custom_serializer)

        obj = CustomClass(42)
        canon = make_canonical(obj)

        # Should use custom serializer
        assert canon == (('type', 'CustomClass'), ('value', 42))

        # Cleanup
        unregister_serializer(CustomClass)

    def test_unregister_serializer(self, setup):
        """Test unregistering a custom serializer."""
        class CustomClass:
            def __init__(self, value):
                self.value = value

        def custom_serializer(obj):
            return {"custom": True}

        register_serializer(CustomClass, custom_serializer)
        unregister_serializer(CustomClass)

        obj = CustomClass(42)
        canon = make_canonical(obj)

        # Should not use custom serializer after unregistering
        assert canon[0] == '__custom_object__'

    def test_custom_serializer_in_hash(self, setup):
        """Test that custom serializers work with hash computation."""
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        def point_serializer(obj):
            return {"x": obj.x, "y": obj.y}

        register_serializer(Point, point_serializer)

        p1 = Point(1, 2)
        p2 = Point(1, 2)
        p3 = Point(2, 1)

        hash1 = compute_hash(p1)
        hash2 = compute_hash(p2)
        hash3 = compute_hash(p3)

        assert hash1 == hash2
        assert hash1 != hash3

        # Cleanup
        unregister_serializer(Point)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_is_pickleable(self, setup):
        """Test is_pickleable function."""
        assert is_pickleable(42)
        assert is_pickleable("string")
        assert is_pickleable([1, 2, 3])
        assert is_pickleable({"a": 1})

        # Lambda functions are not pickleable
        assert not is_pickleable(lambda x: x)

    def test_ensure_serializable(self, setup):
        """Test ensure_serializable function."""
        # Simple types
        assert ensure_serializable(42) == 42
        assert ensure_serializable("test") == "test"

        # Dict
        result = ensure_serializable({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

        # Set (converted to tuple)
        result = ensure_serializable({1, 2, 3})
        assert isinstance(result, tuple)
        assert set(result) == {1, 2, 3}

    def test_ensure_serializable_custom_object(self, setup):
        """Test ensure_serializable with custom objects."""
        class MyClass:
            def __init__(self):
                self.value = 42
                self.name = "test"

        obj = MyClass()
        result = ensure_serializable(obj)

        assert isinstance(result, dict)
        assert result['__type__'] == 'MyClass'
        assert '__dict__' in result


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_structures(self, setup):
        """Test with empty structures."""
        assert make_canonical({}) == ()
        assert make_canonical([]) == ()
        assert make_canonical(set()) == ()

    def test_unicode_strings(self, setup):
        """Test with unicode strings."""
        data = {"emoji": "😀", "chinese": "你好"}
        canon1 = make_canonical(data)
        canon2 = make_canonical(data)

        assert canon1 == canon2

        hash1 = compute_hash(data)
        hash2 = compute_hash(data)

        assert hash1 == hash2

    def test_large_nested_structure(self, setup):
        """Test with large nested structure."""
        data = {
            f"key_{i}": {
                f"nested_{j}": [k for k in range(10)]
                for j in range(10)
            }
            for i in range(10)
        }

        canon = make_canonical(data)
        hash_value = compute_hash(data)

        # Should complete without error
        assert canon is not None
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 hex length

    def test_circular_reference_handling(self, setup):
        """Test handling of circular references."""
        # Circular references can't be pickled
        # This should gracefully fail
        data = {}
        data["self"] = data

        # This will fail to pickle
        with pytest.raises(SerializationError):
            compute_hash(data)


class TestBackwardCompatibility:
    """Test backward compatibility with original implementation."""

    def test_simple_function_call(self, setup):
        """Test that simple function calls produce consistent hashes."""
        hash_val = compute_function_call_hash("test_func", 1, 2, x=3)

        # Should be a 64-character hex string (SHA256)
        assert len(hash_val) == 64
        assert all(c in '0123456789abcdef' for c in hash_val)

    def test_dict_argument_consistency(self, setup):
        """Test consistency with dict arguments."""
        dict_arg = {"a": 1, "b": 2, "c": 3}

        hash1 = compute_function_call_hash("func", dict_arg)
        hash2 = compute_function_call_hash("func", {"c": 3, "a": 1, "b": 2})

        # Dict order shouldn't matter
        assert hash1 == hash2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
