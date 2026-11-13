"""Regression test: ``compute_score`` must delegate to ``Proposition.score``.

It previously called ``Proposition.compute``, which does not exist, so every
call raised ``AttributeError`` before any model request was made.
"""

from tinytroupe.experimentation.proposition import Proposition, compute_score


def test_compute_score_delegates_to_proposition_score(monkeypatch):
    calls = {}

    def fake_score(
        self,
        target=None,
        additional_context="No additional context available.",
        claim_variables={},
        return_full_response=False,
    ):
        calls["target"] = target
        calls["additional_context"] = additional_context
        calls["return_full_response"] = return_full_response
        return 7

    monkeypatch.setattr(Proposition, "score", fake_score)

    result = compute_score(
        None,
        "The claim holds.",
        additional_context="some context",
        first_n=2,
        last_n=3,
    )

    assert result == 7
    assert calls["target"] is None
    assert calls["additional_context"] == "some context"
    assert calls["return_full_response"] is False


def test_compute_score_forwards_return_full_response(monkeypatch):
    def fake_score(self, target=None, additional_context="", claim_variables={}, return_full_response=False):
        return {"value": 9, "full_response": return_full_response}

    monkeypatch.setattr(Proposition, "score", fake_score)

    result = compute_score(None, "The claim holds.", return_full_response=True)

    assert result == {"value": 9, "full_response": True}
