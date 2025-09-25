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


# Case Study 2: Marcelo and the Mediterranean Vegan Restaurant in Montreal

SITUATION_2 = """
Marcelo, an entrepreneur, wants to open a Mediterranean vegan restaurant in Montreal. The concept is unique: Mediterranean cuisine made entirely vegan, focusing on fruits, vegetables, legumes, nuts, and olive oil, with no animal products.
Marcelo's challenge is to validate if there is enough demand for this niche, how the concept is perceived, and which neighborhood would be ideal for the restaurant.
"""

RESTAURANT_CONCEPT = """
The restaurant will offer a conceptual menu with typical Mediterranean vegan dishes and a modern, welcoming ambiance with natural elements.
Personas will experience a virtual ordering and tasting session, discussing the menu, ambiance, and overall concept.
"""

TASK_2 = """
Collect feedback from the personas:

    Niche Validation: Would they enjoy and pay for Mediterranean vegan food? Is the niche appealing enough to sustain a business?

    Concept Perception: Do they find the fusion of Mediterranean and vegan innovative and delicious, or too restrictive?

    Menu Interest: Which dishes generate the most curiosity or desire?

    Price and Value: Are they willing to pay suggested prices for this cuisine?

    Location Preference: Which Montreal neighborhoods would attract them to this restaurant?

    Overall Sentiment: What is the predominant sentiment (enthusiasm, skepticism, indifference)?
"""

# Example personas for the restaurant scenario
PERSONA_1 = {
    "type": "TinyPerson",
    "persona": {
        "name": "Health-Conscious Young Professional",
        "age": 29,
        "gender": "Unspecified",
        "nationality": "Canadian",
        "residence": "Mile End, Montreal",
        "education": "Master's in Environmental Studies",
        "long_term_goals": [
            "Maintain a healthy lifestyle.",
            "Support sustainable businesses.",
            "Explore new food experiences.",
        ],
        "occupation": {
            "title": "Marketing Specialist",
            "organization": "Eco-friendly Startup",
            "description": "Works in sustainability marketing, values ethical consumption.",
        },
        "style": "Eco-chic, minimalist, and modern.",
        "personality": {
            "traits": [
                "Adventurous eater.",
                "Environmentally conscious.",
                "Social and outgoing.",
                "Enjoys discovering new trends.",
            ],
            "big_five": {
                "openness": "High. Loves new food concepts.",
                "conscientiousness": "High. Plans meals and activities.",
                "extraversion": "Medium. Enjoys group outings.",
                "agreeableness": "High. Supportive of friends' ideas.",
                "neuroticism": "Low. Handles change well.",
            },
        },
        "preferences": {
            "interests": [
                "Vegan cuisine",
                "Yoga",
                "Farmers' markets",
                "Sustainable living",
            ],
            "likes": ["Plant-based restaurants", "Seasonal menus", "Community events"],
            "dislikes": ["Processed foods", "Wasteful packaging", "Uninspired menus"],
        },
        "skills": [
            "Organizes group dinners.",
            "Researches new restaurants.",
            "Advocates for sustainability.",
        ],
        "beliefs": [
            "Food choices impact the planet.",
            "Healthy eating is essential.",
            "Supporting local is important.",
        ],
        "behaviors": {
            "general": [
                "Tries new vegan spots monthly.",
                "Shares food experiences online.",
                "Attends wellness workshops.",
            ],
            "routines": {
                "morning": ["Smoothie and yoga.", "Reads food blogs."],
                "workday": ["Lunch at healthy cafes.", "Walks or bikes to work."],
                "evening": ["Cooks plant-based meals.", "Socializes at local events."],
                "weekend": [
                    "Visits new restaurants.",
                    "Explores Montreal neighborhoods.",
                ],
            },
        },
        "health": "Excellent, prioritizes wellness.",
        "relationships": [
            {
                "name": "Yoga Group",
                "description": "Friends from yoga and wellness community.",
            },
            {
                "name": "Colleagues",
                "description": "Work together on sustainability projects.",
            },
        ],
        "other_facts": [
            "Prefers restaurants with eco-friendly practices.",
            "Often recommends new places to friends.",
        ],
    },
}

PERSONA_2 = {
    "type": "TinyPerson",
    "persona": {
        "name": "Vegan University Student",
        "age": 22,
        "gender": "Unspecified",
        "nationality": "Canadian",
        "residence": "Plateau Mont-Royal, Montreal",
        "education": "Undergraduate in Nutrition",
        "long_term_goals": [
            "Graduate and become a dietitian.",
            "Promote plant-based diets.",
            "Enjoy Montreal's food scene.",
        ],
        "occupation": {
            "title": "Student",
            "organization": "McGill University",
            "description": "Active in vegan student groups, passionate about food and health.",
        },
        "style": "Casual, colorful, and expressive.",
        "personality": {
            "traits": [
                "Budget-conscious.",
                "Curious about new foods.",
                "Active in student life.",
                "Values inclusivity.",
            ],
            "big_five": {
                "openness": "High. Loves trying new vegan dishes.",
                "conscientiousness": "Medium. Balances studies and fun.",
                "extraversion": "High. Enjoys group activities.",
                "agreeableness": "High. Friendly and supportive.",
                "neuroticism": "Medium. Sometimes stressed by exams.",
            },
        },
        "preferences": {
            "interests": [
                "Vegan cooking",
                "Student activism",
                "Music festivals",
                "Affordable dining",
            ],
            "likes": ["Creative vegan menus", "Student discounts", "Community spaces"],
            "dislikes": [
                "Expensive restaurants",
                "Limited vegan options",
                "Unwelcoming atmospheres",
            ],
        },
        "skills": [
            "Organizes vegan potlucks.",
            "Finds best deals for students.",
            "Promotes events on social media.",
        ],
        "beliefs": [
            "Plant-based is the future.",
            "Food should be accessible.",
            "Community matters.",
        ],
        "behaviors": {
            "general": [
                "Explores new vegan spots.",
                "Attends student events.",
                "Shares food reviews online.",
            ],
            "routines": {
                "morning": ["Quick breakfast before class.", "Listens to podcasts."],
                "workday": ["Studies in cafes.", "Lunch with friends."],
                "evening": ["Cooks or eats out.", "Attends club meetings."],
                "weekend": ["Visits markets.", "Discovers new restaurants."],
            },
        },
        "health": "Good, manages stress with activities.",
        "relationships": [
            {
                "name": "Roommates",
                "description": "Shares apartment with other students.",
            },
            {
                "name": "Vegan Club",
                "description": "Active member of university vegan group.",
            },
        ],
        "other_facts": [
            "Always looking for new vegan places.",
            "Enjoys organizing group outings.",
        ],
    },
}


agent_specs = {"PERSON_1": PERSONA_1, "PERSON_2": PERSONA_2}

TinyPerson.load_specification(load_example_agent_specification("PERSON_1", agent_specs))
TinyPerson.load_specification(load_example_agent_specification("PERSON_2", agent_specs))

focus_group = TinyWorld("Focus group", [TinyPerson("PERSON_1"), TinyPerson("PERSON_2")])
focus_group.broadcast(SITUATION_2)
focus_group.broadcast(RESTAURANT_CONCEPT)
focus_group.broadcast(TASK_2)
focus_group.run(6)

extractor = ResultsExtractor()

extractor.extract_results_from_world(
    focus_group,
    extraction_objective="Detailed reports of insights, acceptance rates, suggestions for the service.",
    fields=["ad_copy"],
    fields_hints={
        "ad_copy": "A concise summary of the agent's overall impression and feedback on the Mediterranean vegan restaurant concept, suitable for marketing material."
    },
    verbose=True,
)
extractor.save_as_json("restaurant_extraction.json")
