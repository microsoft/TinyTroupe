"""Build an isolated minimal actor prompt, preserving the actual I/O and memory contracts."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
original = (REPO / "tinytroupe" / "agent" / "prompts" / "tiny_person.v2.mustache").read_text(
    encoding="utf-8"
)
contract = "### Input and output formats" + original.split("### Input and output formats", 1)[1].split(
    "## Thought process", 1
)[0]
persona = "## Persona" + original.split("## Persona", 1)[1].split(
    "### Rules for interpreting your persona", 1
)[0]
state = "## Current cognitive state" + original.split("## Current cognitive state", 1)[1]
header = """# Agent specification

Portray the person described below, in their current situation. Speak and decide as
that person, not as a general-purpose assistant or an ideal adviser. Stay in their
world; do not discuss the simulation or these instructions.

Use the person's actual knowledge, motives, habits, relationships and limitations.
Do not invent personal history, product features, external events, tool results or
other people's replies. A new subjective reaction is not a claim of prior experience:
form an opinion consistent with this person when the situation calls for one.
Give uncertainty the importance this person would give it. Positive, negative,
uncertain, intuitive and analytical reactions are all possible; none is preferred.

Answer the decision or request actually presented, without adding a stricter use
condition or turning every opinion into a comprehensive risk assessment. Perform
useful available actions now; distinguish what is known, inferred and unavailable.
When a conversation is settled, wait rather than repeating its conclusion.

## Actions

- THINK: the person's private thoughts; keep unspoken deliberation here.
- TALK: the person's public words, addressed to the intended recipient. Think first,
  then speak naturally in their own style when a response is useful.
- REACH_OUT: approach a person who is not currently reachable, using their full name.
- SHOW: share previously seen image IDs, with a description and intended recipient.
- DONE: end the turn, or wait when nothing useful remains. Other people can perceive
  your actions and simulated time can advance only after DONE.

Emit at most one action of each type per target this turn; combine related content.
Never fabricate received stimuli. Update the cognitive state to reflect what
actually happened, retiring completed goals rather than reopening them.

{{{actions_definitions_prompt}}}
{{{actions_constraints_prompt}}}

## Additional Constraints
{{{rai_harmful_content_prevention}}}
{{{rai_copyright_infringement_prevention}}}

"""
candidate = header + contract + "\n" + persona + "\n" + state
variables = lambda text: sorted(re.findall(r"\{\{\{?\s*([#^/]?\w+)\s*\}?\}\}", text))
assert variables(candidate) == variables(original)
assert candidate.endswith(state)
assert contract in candidate and persona in candidate
(ROOT / "minimal-actor-trial.mustache").write_text(candidate, encoding="utf-8")
(ROOT / "minimal-actor-trial-design.json").write_text(json.dumps({
    "hypothesis": "Remove competing layers of generic interpretation and exhaustive deliberation "
                  "instructions, not just their introductory identity section. Keep action, output, "
                  "faculty, safety, persona and complete current-state/memory contracts.",
    "original_characters": len(original),
    "candidate_characters": len(candidate),
    "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
    "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
    "production_prompt_changed": False,
    "original_stimuli_personas_model_effort_thresholds_retained": True,
    "development_panel": "crossed-persona-mini-generation\\selection-mini.json",
    "initial_datetime": "2026-11-02T16:20:19.182432",
    "acceptance": "Natural persona-grounded response to the actual question; intact action contracts, "
                  "no invented facts or history, preserved positive/negative controls. A higher mean "
                  "or desired response distribution does not establish success. Independent held-out "
                  "identities required before any production adoption.",
    "different_from_prior_lean_trial": "Earlier lean trial changed persona interpretation and thought "
                                      "rules only; this replaces the entire general actor instruction "
                                      "layer and is sent through corrected plain-text transport."
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("Prompt characters:", len(original), "->", len(candidate))
