from collections import Counter

import pytest

from tinytroupe.extraction import Normalizer
from tinytroupe.utils.llm import LLMChat


@pytest.mark.parametrize(
    ("mapping", "limit"),
    [
        ({"Other": ["a", "b", "c"], "Office": ["d", "e"], "Food": ["f"]}, 2),
        ({"Office": ["a", "b", "c"], "Food": ["d", "e"], "Other": ["f"]}, 2),
        ({"Office": ["a", "b", "c"], "Food": ["d", "e"], "Tech": ["f"]}, 2),
        ({"Other": ["a", "b", "c"], "Office": ["d", "e"], "Food": ["f"]}, 1),
        ({"Other": ["a", "b", "c"], "Office": ["d", "e", "f"]}, 2),
    ],
    ids=[
        "other-retained",
        "other-in-overflow",
        "no-other",
        "single-category",
        "within-limit",
    ],
)
def test_category_limit_preserves_all_original_elements(monkeypatch, mapping, limit):
    monkeypatch.setattr(LLMChat, "call", lambda self, **kwargs: mapping)
    originals = [element for values in mapping.values() for element in values]

    normalizer = Normalizer(elements=originals, n=limit)
    result = normalizer.normalized_mapping()

    assert len(result) <= limit
    assert Counter(
        element for values in result.values() for element in values
    ) == Counter(originals)
    assert "Other" in result
