import pytest

from tinytroupe.utils.json import merge_dicts


def test_merge_dicts_keeps_nested_duplicates_when_disabled():
    current = {'a': {'l': [1]}}
    additions = {'a': {'l': [1]}}

    assert merge_dicts(current, additions, remove_duplicates=False) == {
        'a': {'l': [1, 1]}
    }


def test_merge_dicts_removes_nested_duplicates_by_default():
    current = {'a': {'l': [1, 2]}}
    additions = {'a': {'l': [2, 3]}}

    assert merge_dicts(current, additions) == {'a': {'l': [1, 2, 3]}}


def test_merge_dicts_nested_flag_matches_top_level():
    current = {'l': [1], 'a': {'l': [1]}}
    additions = {'l': [1], 'a': {'l': [1]}}

    assert merge_dicts(
        current, additions, remove_duplicates=False
    ) == {'l': [1, 1], 'a': {'l': [1, 1]}}
