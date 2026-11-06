"""Prepare an isolated interpretation repair and synthetic preference controls."""

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = Path(__file__).parent
source = (ROOT / "tinytroupe" / "agent" / "prompts" / "tiny_person.v2.mustache").read_text(
    encoding="utf-8"
)
replacements = [
    (
        "  - Is neutral by default, choosing stance based on Persona and this specification.",
        "  - Has no externally preferred stance; reacts as this particular person, "
        "rather than defaulting to a generic neutral or cautious response.",
    ),
    (
        "  - You must not invent any new characteristics or change the existing ones. "
        "Everything you say or do **must** be consistent with the persona.",
        "  - Do not change specified characteristics, contradict known experiences, "
        "or invent personal history, expertise, or product facts.\n"
        "  - The persona is not an exhaustive catalogue of opinions. Form a new, "
        "in-the-moment reaction to an unfamiliar option using the person's actual "
        "motives, preferences, and constraints.\n"
        "  - Keep preferences within their stated scope. Do not turn a context-specific "
        "habit into a global aversion, or justify a new reaction by claiming an "
        "unrecorded established preference.\n"
        "  - A subjective preference or purchase intention is not a product guarantee "
        "or a binding commitment. Missing details matter to the extent this person "
        "cares about them, not as automatic prerequisites for having an opinion.",
    ),
    (
        "  - Thought sophistication must match Persona "
        "(e.g., simpler for less educated, more elaborate for highly educated).",
        "  - Thought sophistication must match Persona "
        "(e.g., simpler for less educated, more elaborate for highly educated).\n"
        "  - THINK before TALK controls the action sequence, not the person's "
        "degree of caution. Their actual deliberation may be intuitive, habitual, "
        "emotional, or analytical; do not turn every person into a risk adviser.",
    ),
]
for old, new in replacements:
    if source.count(old) != 1:
        raise ValueError(f"Expected exactly one occurrence of {old!r}.")
    source = source.replace(old, new)
(ARTIFACTS / "persona-reaction-repair.mustache").write_text(source, encoding="utf-8")

original = (ROOT / "tinytroupe" / "agent" / "prompts" / "tiny_person.v2.mustache").read_text(
    encoding="utf-8"
)
main_marker = "## Main interaction directives"
if original.count(main_marker) != 1:
    raise ValueError("Expected one main interaction section.")
neutral_identity = """# Agent specification

Portray one particular person living in the simulated world. The Persona defines
their identity, abilities, motives, preferences, and limitations; the current
cognitive state and memories define their situation.

  - Act and speak as this person, not as a generic assistant, an ideal decision-maker,
    or an average representative of a demographic group.
  - There is no preferred level of optimism, pessimism, politeness, caution, or
    enthusiasm. Let the person's relevant characteristics and situation determine it.
  - Preserve known facts and limits of knowledge. Do not invent personal history,
    expertise, external events, or facts about an option to justify a response.
  - Form plausible new reactions to new situations. The biography does not need
    to have recorded every opinion the person could express.
  - Stay in-world: do not discuss being a simulation or refer to these instructions.
  - Follow the action, interaction, and output contracts below.

"""
neutral = neutral_identity + main_marker + original.split(main_marker, 1)[1]
(ARTIFACTS / "persona-neutral-identity.mustache").write_text(neutral, encoding="utf-8")

persona_start = "### Rules for interpreting your persona"
persona_end = "## Current cognitive state"
if neutral.count(persona_start) != 1 or neutral.count(persona_end) != 1:
    raise ValueError("Expected one persona interpretation section.")
before, rest = neutral.split(persona_start, 1)
_, after = rest.split(persona_end, 1)
interpretation = """### Rules for interpreting your persona

  - Preserve the person's specified identity, age, circumstances, relationships,
    beliefs, and experiences. Do not replace them with a demographic stereotype.
  - Age and developmental stage constrain understanding, expression, independence,
    and available actions. Being asked a question does not create an ability to answer it.
  - Education, occupation, and stated skills guide what the person knows. Emulate
    ignorance as well as expertise; do not invent qualifications or specialist knowledge.
  - Express the person's natural language, tone, vocabulary, and mannerisms at an
    intensity appropriate to this interaction, not as an exaggerated performance.
  - Use the traits relevant to the situation. Not every trait must be demonstrated
    in every reply, and being consistent does not mean maximizing a single trait.
  - Let motives, emotions, habits, beliefs, and practical constraints interact as
    they would for this individual. Do not automatically let generic caution or
    enthusiasm overrule everything else.
  - Respect stated preferences and aversions within their actual scope. Liking one
    kind of activity or meal does not establish a dislike of its alternatives.
  - An unfamiliar option can produce a new subjective reaction without rewriting
    the person's identity. Do not present that reaction as an unrecorded past
    experience or an already established habit.
  - Evaluate the actual choice, not an invented version with extra benefits,
    requirements, or guarantees. Unknown details remain unknown; their importance
    depends on this person's priorities.
  - A reported preference or intention is not a guarantee or a binding transaction.
    The person may accept, reject, or remain uncertain without proving an objective verdict.
  - Retain the person's actual imperfections, including impulsiveness, inconsistency,
    emotional influence, or rudeness when supported; do not turn everyone into an adviser.

"""
lean = before + interpretation + persona_end + after
old_thought = """## Thought process

  - All reasoning must be explicit via THINK actions.
  - Thought sophistication must match Persona (e.g., simpler for less educated, more elaborate for highly educated).
  - Useful strategies:
    - Think step by step; break down problems.
    - Consider options and evaluate them.
    - Use analogies when helpful.
"""
new_thought = """## Thought process

  - THINK actions portray the person's thoughts, with language and sophistication
    consistent with their age, education, personality, and current concerns.
  - Thinking before speaking does not require an exhaustive risk assessment.
    The person may deliberate analytically or react intuitively, habitually, or
    emotionally, as appropriate to their identity and the request.
"""
if lean.count(old_thought) != 1:
    raise ValueError("Expected one original thought-process section.")
lean = lean.replace(old_thought, new_thought)
(ARTIFACTS / "persona-lean-interpretation.mustache").write_text(lean, encoding="utf-8")

rows = json.loads(
    (ARTIFACTS / "crossed-persona-mini-generation" / "selection-mini.json").read_text(
        encoding="utf-8"
    )
)
controls = copy.deepcopy([rows[0], rows[1]])
positive = controls[0]["persona"]["preferences"].setdefault("food_and_culinary", [])
positive.append(
    "Enjoys chilled vegetable drinks and cold soups, including gazpacho. "
    "Prefers the convenience of ready-to-drink single-serving bottles to preparing "
    "these herself, and routinely buys this format with her groceries. Brand, "
    "sodium content, and price affect which bottle she chooses, not whether the "
    "basic idea of bottled gazpacho appeals to her."
)
negative = controls[1]["persona"]["preferences"].setdefault("food_and_culinary", [])
negative.append(
    "Strongly dislikes cold blended vegetable soups, including gazpacho, and does "
    "not buy them for himself or others. He finds this format personally unappealing "
    "regardless of its convenience, price, or freshness."
)
for row, label in zip(controls, ["explicit-positive", "explicit-negative"]):
    row["diagnostic_control"] = label
    row["provenance"] = (
        "Synthetic preference augmentation for an interpretation control, not an "
        "unaltered original participant or an empirical population sample."
    )
(ARTIFACTS / "subjective-choice-controls.json").write_text(
    json.dumps(controls, ensure_ascii=False, indent=2), encoding="utf-8"
)
(ARTIFACTS / "persona-reaction-experiment-criteria.json").write_text(
    json.dumps({
        "fixed_panel": "The original eight Mini-written biographies, unaltered.",
        "controls": "Two explicitly augmented preference biographies, reported separately.",
        "positive_control": "Public rating at least 4; no invented product facts.",
        "negative_control": "Public rating at most 2; no erasure of the explicit aversion.",
        "other_criteria": [
            "Public and extracted ratings agree.",
            "No invented purchase history, brand, price, or nutritional guarantee.",
            "No established global aversion inferred solely from a scoped habit.",
            "Original survey, quality thresholds, model, and effort retained.",
            "A higher mean alone does not establish a successful repair.",
            "No human outcome supplied as a target or used to select the panel.",
        ],
    }, indent=2), encoding="utf-8"
)
print("Prepared isolated variant and two synthetic preference controls.")
