"""
Scenario tests for the pricing change customer response simulation.

These tests verify that four customer personas — spanning different income levels,
usage intensities, and switching costs — produce structurally valid and behaviorally
distinct responses to a SaaS price increase.

Per TinyTroupe contribution guidelines, all LLM calls use real API calls (no mocking).
Use --use_cache to run from cached responses and avoid API costs on repeated runs.
"""
import json
import logging
import os

import pytest

logger = logging.getLogger("tinytroupe")

import sys

sys.path.insert(0, "../../tinytroupe/")
sys.path.insert(0, "../../")
sys.path.insert(0, "..")

import tinytroupe
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.extraction import ResultsExtractor
import tinytroupe.control as control

from testing_utils import *

# Path to the persona JSON files shared with the notebook example
_AGENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "examples", "agents")


def _agent_path(filename):
    return os.path.join(_AGENTS_DIR, filename)


# ── Shared scenario content ────────────────────────────────────────────────────
# These constants are identical to those in the notebook so the test exercises
# exactly the same scenario.

PRODUCT_CONTEXT = (
    "You are a paying customer of FlowDesk, a productivity SaaS tool you have been using "
    "for the past year. FlowDesk helps you manage tasks, track time, and collaborate on "
    "projects. You currently pay $12/month and have integrated it into your daily workflow."
)

PRICING_ANNOUNCEMENT = (
    "You just received this email from FlowDesk:\n\n"
    "Subject: Important update to your FlowDesk subscription\n\n"
    "Hi there,\n\n"
    "We are writing to let you know that starting next billing cycle, your FlowDesk "
    "monthly subscription will increase from $12/month to $18/month. This change reflects "
    "our ongoing investment in new collaboration features, a redesigned mobile app, and "
    "faster customer support.\n\n"
    "Your account, data, and current plan features remain unchanged. If you have "
    "questions, our support team is here to help.\n\n"
    "Thank you for being a FlowDesk customer.\n"
    "— The FlowDesk Team\n\n"
    "How do you feel about this? What will you do?"
)

REFLECTION_PRIMER = (
    "I will think carefully and honestly about this situation. I will consider: "
    "how much I actually use and value FlowDesk, how $6/month more fits into my budget, "
    "whether I trust this company and its communication, whether I would look for "
    "alternatives, and what specific improvements I would need to see to feel the "
    "price increase is justified. I will not give a polite or generic answer "
    "— I will respond as I genuinely would in real life."
)

# Fields extracted in both tests — kept intentionally concise for cost efficiency
_EXTRACTION_FIELDS = ["name", "switching_risk", "overall_reaction"]
_EXTRACTION_HINTS = {
    "switching_risk": "One of: Very High, High, Medium, Low, Very Low.",
    "overall_reaction": "One of: Strongly Positive, Positive, Neutral, Negative, Strongly Negative.",
}

# Full field list used by the structural completeness test
REQUIRED_FIELDS = [
    "name",
    "switching_risk",
    "likelihood_to_continue",
    "likelihood_to_churn",
    "likelihood_to_recommend",
    "requested_improvements",
    "overall_reaction",
]


# ── Tests ──────────────────────────────────────────────────────────────────────

@pytest.mark.slow
def test_pricing_simulation_produces_structured_results(setup):
    """
    Full end-to-end simulation: four personas receive the pricing announcement and
    ResultsExtractor returns a dict with all required fields for each agent.

    Personas are loaded from the same JSON files used by the notebook, ensuring
    the test exercises the exact same persona definitions the user sees.
    """
    control.reset()

    maya  = TinyPerson.load_specification(_agent_path("MayaChen.agent.json"))
    raj   = TinyPerson.load_specification(_agent_path("RajPatel.agent.json"))
    sarah = TinyPerson.load_specification(_agent_path("SarahKim.agent.json"))
    ethan = TinyPerson.load_specification(_agent_path("EthanBrooks.agent.json"))

    world = TinyWorld(
        "FlowDesk Customer Panel",
        [maya, raj, sarah, ethan],
        broadcast_if_no_target=False,
    )

    world.broadcast(PRODUCT_CONTEXT)
    world.broadcast(PRICING_ANNOUNCEMENT)
    world.broadcast_thought(REFLECTION_PRIMER)
    world.run(1)

    extractor = ResultsExtractor(
        extraction_objective=(
            "Determine how the customer persona responded to a 50% price increase "
            "($12/month to $18/month) for a productivity SaaS called FlowDesk."
        ),
        situation=(
            "The agent received an email announcing a price increase from $12 to $18/month "
            "and was asked to respond honestly and in character."
        ),
        fields=REQUIRED_FIELDS,
        fields_hints={
            "switching_risk": "One of: Very High, High, Medium, Low, Very Low.",
            "likelihood_to_continue": "Integer 1-5. 1 = will definitely cancel, 5 = will definitely stay. Or N/A.",
            "likelihood_to_churn": "Integer 1-5. 1 = will definitely stay, 5 = will definitely cancel. Or N/A.",
            "likelihood_to_recommend": "Integer 1-5. 1 = would never recommend, 5 = would strongly recommend. Or N/A.",
            "requested_improvements": "Comma-separated list of requested changes. Write 'None mentioned' if none.",
            "overall_reaction": "One of: Strongly Positive, Positive, Neutral, Negative, Strongly Negative.",
        },
        verbose=False,
    )

    results = extractor.extract_results_from_agents(world.agents)
    valid_results = [r for r in results if isinstance(r, dict)]

    # All four agents should produce a result
    assert len(valid_results) == 4, (
        f"Expected 4 extracted results, got {len(valid_results)}. "
        f"Raw results: {results}"
    )

    # Each result must contain all required fields
    for result in valid_results:
        for field in REQUIRED_FIELDS:
            assert field in result, (
                f"Field '{field}' missing from result for {result.get('name', '?')}. "
                f"Got keys: {list(result.keys())}"
            )


@pytest.mark.slow
def test_pricing_simulation_churn_variance(setup):
    """
    Verify that the simulation produces meaningful variance in churn signals across personas.

    Maya (budget freelancer) and Ethan (grad student) are expected to show higher churn
    intent than Sarah (enterprise PM), who has low price sensitivity and high switching cost.
    This tests that personas with different financial constraints produce differentiated
    behavioral outputs — the core value proposition of persona-based simulation.

    Assertions use proposition_holds() on short extracted result strings (not raw interaction
    histories), consistent with how other scenario tests in this suite validate outcomes.
    """
    control.reset()

    maya  = TinyPerson.load_specification(_agent_path("MayaChen.agent.json"))
    sarah = TinyPerson.load_specification(_agent_path("SarahKim.agent.json"))
    ethan = TinyPerson.load_specification(_agent_path("EthanBrooks.agent.json"))

    world = TinyWorld(
        "FlowDesk Churn Contrast",
        [maya, sarah, ethan],
        broadcast_if_no_target=False,
    )

    world.broadcast(PRODUCT_CONTEXT)
    world.broadcast(PRICING_ANNOUNCEMENT)
    world.broadcast_thought(REFLECTION_PRIMER)
    world.run(1)

    # Extract a concise result for each agent — used as the proposition context
    extractor = ResultsExtractor(
        extraction_objective=(
            "Determine whether the customer persona intends to stay with or leave FlowDesk "
            "after a 50% price increase, and how strongly they reacted."
        ),
        situation=(
            "The agent received a price increase announcement from $12 to $18/month "
            "and was asked to respond in character."
        ),
        fields=_EXTRACTION_FIELDS,
        fields_hints=_EXTRACTION_HINTS,
        verbose=False,
    )

    results = extractor.extract_results_from_agents(world.agents)
    by_name = {r["name"]: r for r in results if isinstance(r, dict) and "name" in r}

    maya_result  = json.dumps(by_name.get("Maya Chen", {}))
    sarah_result = json.dumps(by_name.get("Sarah Kim", {}))
    ethan_result = json.dumps(by_name.get("Ethan Brooks", {}))

    # Maya — budget freelancer — should show high switching risk or negative reaction
    assert proposition_holds(
        f"The following data describes Maya Chen's reaction to a 50% SaaS price increase: "
        f"{maya_result}. "
        f"The data indicates concern, frustration, high switching risk, or a negative reaction."
    ), f"Maya (budget freelancer) should show high churn intent. Got: {maya_result}"

    # Ethan — grad student — should show very high switching risk or strongly negative reaction
    assert proposition_holds(
        f"The following data describes Ethan Brooks's reaction to a 50% SaaS price increase: "
        f"{ethan_result}. "
        f"The data indicates that $18/month is too expensive or that the persona would "
        f"switch to a free or cheaper alternative."
    ), f"Ethan (grad student) should show very high churn intent. Got: {ethan_result}"

    # Sarah — enterprise PM — should show low switching risk despite possible disapproval
    assert proposition_holds(
        f"The following data describes Sarah Kim's reaction to a 50% SaaS price increase: "
        f"{sarah_result}. "
        f"The data indicates low or medium switching risk — the persona is unlikely to cancel "
        f"immediately, even if she disapproves of how the increase was communicated."
    ), f"Sarah (enterprise PM) should show low switching risk. Got: {sarah_result}"
