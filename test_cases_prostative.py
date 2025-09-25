import sys

sys.path.insert(0, "..")

from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.extraction import ResultsExtractor


def load_example_agent_specification(name: str, agent_specs: dict):
    """
    Load an example agent specification from a provided dictionary.

    Args:
        name (str): The name of the agent.
        agent_specs (dict): Dictionary containing agent specifications.

    Returns:
        dict: The agent specification.
    """
    return agent_specs.get(name)


# Case Study: Men (45-75) Searching Online When Experiencing Urinary Discomfort

SITUATION_2 = """
Four men, ages 45, 52, 63 and 75, experience intermittent urinary discomfort (urgency, nocturia, weak stream) at different severities. They often turn to internet searches when symptoms start — looking for causes, self-care, when to see a doctor, and possible treatments. The goal is to simulate their search behavior, likely queries, concerns about privacy and stigma, and what kinds of information or actions they prefer (symptom checkers, forum reassurance, medical advice, telehealth, or seeing a urologist).
"""

TASK_2 = """
Simulate the online search behavior and responses for each persona:

    - Typical search queries they would use for their symptoms.
    - How urgently they seek medical help vs self-care.
    - Trusted sources they prefer (forums, health sites, government, telehealth).
    - Privacy concerns or language they avoid.
    - The next actions they are likely to take after searching (self-medicate, book appointment, wait).
    - Suggested messaging or content that would motivate appropriate care-seeking.
"""

# Personas: four men across the 45-75 age range with concise, search-focused profiles
PERSONA_1 = {
    "type": "TinyPerson",
    "persona": {
        "name": "Man A - 45, early symptoms",
        "age": 45,
        "gender": "Male",
        "nationality": "Unspecified",
        "residence": "Suburban",
        "education": "College",
        "occupation": "Office manager",
        "long_term_goals": ["Stay healthy for family", "Avoid time off work"],
        "style": "Practical, straightforward",
        "personality": {"traits": ["Privacy-minded", "cost-conscious"]},
        "preferences": {"interests": ["quick answers", "practical self-care"]},
        "behaviors": {
            "general": ["Searches first for quick fixes", "reads Q&A forums"],
            "routines": {"evening": ["Looks up symptoms after work"]},
        },
        "health": "Generally good, occasional issues",
        "other_facts": ["Likely to try OTC remedies before seeing doctor"]
    }
}

PERSONA_2 = {
    "type": "TinyPerson",
    "persona": {
        "name": "Man B - 52, concerned",
        "age": 52,
        "gender": "Male",
        "residence": "Urban",
        "education": "University",
        "occupation": "Sales",
        "long_term_goals": ["Maintain activity level", "avoid invasive procedures"],
        "style": "Researcher",
        "personality": {"traits": ["reads medical articles", "asks follow-up questions"]},
        "preferences": {"interests": ["evidence-based info", "telehealth options"]},
        "behaviors": {"general": ["uses reputable health sites first", "compares sources"]},
        "health": "Mild hypertension",
        "other_facts": ["Concerned about prostate issues due to family history"]
    }
}

PERSONA_3 = {
    "type": "TinyPerson",
    "persona": {
        "name": "Man C - 63, experienced",
        "age": 63,
        "gender": "Male",
        "residence": "Small town",
        "education": "High school",
        "occupation": "Retired technician",
        "long_term_goals": ["Manage symptoms", "stay independent"],
        "style": "Cautious",
        "personality": {"traits": ["follows forums", "values peer stories"]},
        "preferences": {"interests": ["practical management tips", "local care options"]},
        "behaviors": {"general": ["searches forums and social groups", "asks about medications"]},
        "health": "Has chronic conditions (diabetes)",
        "other_facts": ["May delay care due to transport/cost"]
    }
}

PERSONA_4 = {
    "type": "TinyPerson",
    "persona": {
        "name": "Man D - 75, severe symptoms",
        "age": 75,
        "gender": "Male",
        "residence": "Assisted living",
        "education": "Secondary",
        "occupation": "Retired",
        "long_term_goals": ["Comfort, reduce nocturia"],
        "style": "Reserved",
        "personality": {"traits": ["trusts doctors but hesitant about surgery"]},
        "preferences": {"interests": ["clear guidance", "appointment help"]},
        "behaviors": {"general": ["searches for nearby specialists", "asks caregiver to help"]},
        "health": "Multiple comorbidities",
        "other_facts": ["More likely to call clinic or accept referral once convinced"]
    }
}


agent_specs = {
    "PERSON_1": PERSONA_1,
    "PERSON_2": PERSONA_2,
    "PERSON_3": PERSONA_3,
    "PERSON_4": PERSONA_4,
}

TinyPerson.load_specification(load_example_agent_specification("PERSON_1", agent_specs))
TinyPerson.load_specification(load_example_agent_specification("PERSON_2", agent_specs))
TinyPerson.load_specification(load_example_agent_specification("PERSON_3", agent_specs))
TinyPerson.load_specification(load_example_agent_specification("PERSON_4", agent_specs))

focus_group = TinyWorld(
    "Men urinary search group",
    [
        TinyPerson("PERSON_1"),
        TinyPerson("PERSON_2"),
        TinyPerson("PERSON_3"),
        TinyPerson("PERSON_4"),
    ],
)
focus_group.broadcast(SITUATION_2)
focus_group.broadcast(TASK_2)
focus_group.run(6)

extractor = ResultsExtractor()

extractor.extract_results_from_world(
    focus_group,
    extraction_objective=(
        "Summarize likely search queries, trust channels, privacy concerns, and recommended next actions "
        "to guide appropriate care-seeking for men aged 45-75 experiencing urinary symptoms."
    ),
    fields=["search_queries", "help_seeking_likelihood", "trusted_sources", "recommended_messages"],
    fields_hints={
        "search_queries": "List 5-8 realistic search query examples this persona would type, in descending likelihood.",
        "help_seeking_likelihood": "For each persona, give a brief likelihood (low/medium/high) they will seek professional care and why.",
        "trusted_sources": "Where they look first (forums, WebMD-like sites, government health pages, telehealth).",
        "recommended_messages": "Short messaging suggestions (1-2 lines) that would encourage appropriate care-seeking for this persona.",
    },
    verbose=True,
)
extractor.save_as_json("prostative_search_extraction.json")
