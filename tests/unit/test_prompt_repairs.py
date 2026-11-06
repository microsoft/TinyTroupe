"""Contract regressions and real-model checks for the integrated prompt repairs."""

import copy
from collections import Counter

import pytest

from testing_utils import proposition_holds, setup
from tinytroupe.extraction import Normalizer
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.factory.sampling import restore_sampling_plan, sampling_plan_spec
from tinytroupe.steering import TinyStory
from tinytroupe import utils


pytestmark = pytest.mark.core


def sampling_parameters():
    """Provide numeric bounds and weighted options whose punctuation must survive."""
    return {
        "N": 2, "min_sampling_directives": 1, "max_sampling_directives": 2,
        "max_quantity_per_sample_directive": 2,
        "enforce_usage_of_all_dimensions": False, "context": "Illustrative coverage, not prevalence.",
        "population_description": "Adults in a reading group; include fiction & nonfiction tastes.",
        "sampling_dimensions": {"sampling_space_description": "Adults in a reading group.",
                                "dimensions": [
                                    {"name": "age", "range": [18, 90]},
                                    {"name": "interest", "values": {'Reads "fiction", often.': 0.6,
                                                                   "Prefers factual accounts.": 0.4}},
                                ]},
    }


def selected_plan():
    """Select one literal categorical option without asking the model to copy it."""
    return {"sample_plan": [{
        "id": 1, "subpopulation_description": "Adult fiction readers.", "quantity": 2,
        "sampled_values": {"1": [18, 90], "2": [1]},
    }]}


def test_sampling_identifier_round_trip():
    parameters = sampling_parameters()
    before = copy.deepcopy(parameters)
    payload, response_format = sampling_plan_spec(parameters)
    assert payload["sampling_dimensions"]["dimensions"]["2"]["supplied_option_weights"] == {"1": 0.6, "2": 0.4}
    assert payload["population_description"] == parameters["population_description"]
    assert response_format["json_schema"]["strict"]
    selection = response_format["json_schema"]["schema"]["properties"]["sample_plan"]["items"][
        "properties"]["sampled_values"]["properties"]["2"]["anyOf"][0]
    assert selection == {"type": "array", "items": {"type": "integer", "enum": [1, 2]},
                         "minItems": 1, "maxItems": 2}
    result = restore_sampling_plan(parameters, selected_plan())
    assert result["sample_plan"][0]["sampled_values"] == {
        "age": [18, 90], "interest": 'Reads "fiction", often.',
    }
    assert parameters == before


@pytest.mark.parametrize("selection", [
    {"1": False, "2": False}, {"1": 1, "2": False}, {"1": True},
    {"1": True, "2": False, "3": False}, [1, 1],
    [], [0], [3], [True], ["1"], 1, [[1]],
])
def test_sampling_rejects_invalid_identifiers(selection):
    value = selected_plan()
    value["sample_plan"][0]["sampled_values"]["2"] = selection
    with pytest.raises(ValueError):
        restore_sampling_plan(sampling_parameters(), value)


def test_sampling_identifier_order_does_not_change_public_option_order():
    """Keep the original vocabulary order, without mutating the model's selection."""
    value = selected_plan()
    value["sample_plan"][0]["sampled_values"]["2"] = [2, 1]
    before = copy.deepcopy(value)
    restored = restore_sampling_plan(sampling_parameters(), value)["sample_plan"]
    assert restored[0]["sampled_values"]["interest"] == [
        'Reads "fiction", often.', "Prefers factual accounts.",
    ]
    assert value == before


@pytest.mark.parametrize("selection", [[90, 18], [18], [18, 40, 90], True, float("nan"), 91])
def test_sampling_rejects_invalid_numeric_ranges(selection):
    value = selected_plan()
    value["sample_plan"][0]["sampled_values"]["1"] = selection
    with pytest.raises(ValueError):
        restore_sampling_plan(sampling_parameters(), value)


@pytest.mark.parametrize("field,value", [("id", True), ("id", 2), ("quantity", 1), ("quantity", True)])
def test_sampling_rejects_invalid_counts(field, value):
    plan = selected_plan()
    plan["sample_plan"][0][field] = value
    with pytest.raises(ValueError):
        restore_sampling_plan(sampling_parameters(), plan)


def test_sampling_optional_and_required_dimensions():
    value = selected_plan()
    value["sample_plan"][0]["sampled_values"]["2"] = None
    parameters = sampling_parameters()
    assert restore_sampling_plan(parameters, value)["sample_plan"][0]["sampled_values"] == {"age": [18, 90]}
    parameters["enforce_usage_of_all_dimensions"] = True
    with pytest.raises(ValueError, match="required dimension"):
        restore_sampling_plan(parameters, value)


def test_sampling_small_population_and_infeasible_limits():
    parameters = sampling_parameters()
    parameters["min_sampling_directives"] = 10
    payload, _ = sampling_plan_spec(parameters)
    assert payload["min_sampling_directives"] == 2
    parameters.update(N=20, max_sampling_directives=2, max_quantity_per_sample_directive=5)
    with pytest.raises(ValueError, match="cannot cover"):
        sampling_plan_spec(parameters)


def test_flattened_sampling_preserves_population_description():
    """Eligibility stated in a stratum must reach each generated person."""
    plan = restore_sampling_plan(sampling_parameters(), selected_plan())["sample_plan"]
    plan[0]["subpopulation_description"] = "Parents of a child aged 4 or 5 who enjoy reading."
    before = copy.deepcopy(plan)
    samples = TinyPersonFactory()._flatten_sampling_plan(plan)
    assert len(samples) == 2
    assert all(sample["subpopulation_description"] == plan[0]["subpopulation_description"]
               for sample in samples)
    assert all(type(sample["age"]) is int and 18 <= sample["age"] <= 90 for sample in samples)
    samples[0]["subpopulation_description"] = "Changed locally."
    assert samples[1]["subpopulation_description"] == plan[0]["subpopulation_description"]
    assert plan == before


def test_sampling_initialization_preserves_original_population(monkeypatch, setup):
    """A generated dimension summary cannot replace the experimenter's requirements."""
    population = "Adult readers; retain the supplied demographic proportions and fiction & nonfiction tastes."
    factory = TinyPersonFactory(sampling_space_description=population, total_population_size=2)
    parameters = sampling_parameters()
    captured = []
    monkeypatch.setattr(factory, "_compute_sampling_dimensions",
                        lambda **kwargs: copy.deepcopy(parameters["sampling_dimensions"]))

    def plan(**kwargs):
        captured.append(kwargs)
        return restore_sampling_plan(parameters, selected_plan())

    monkeypatch.setattr(factory, "_compute_sample_plan", plan)
    monkeypatch.setattr(factory, "_generate_name_for_sample",
                        lambda sample_characteristics, already_generated_names:
                        f"Reader {len(already_generated_names) + 1}")
    result = factory._initialize_sampling_plan_transaction(2, population, "A reading group.")
    assert captured[0]["population_description"] == population
    assert len(result["remaining_characteristics_sample"]) == 2


def test_flattened_sampling_draws_concrete_values(setup):
    """Ranges and alternatives must not be delegated back to the model's mode."""
    import random
    factory = TinyPersonFactory()
    factory.randomizer = random.Random(42)
    plan = [{"quantity": 100, "sampled_values": {
        "age": [18, 75], "interest": ["fiction", "nonfiction"], "budget": [1.5, 2.5],
    }}]
    before = copy.deepcopy(plan)
    samples = factory._flatten_sampling_plan(plan)
    assert len({sample["age"] for sample in samples}) > 30
    assert {sample["interest"] for sample in samples} == {"fiction", "nonfiction"}
    assert all(1.5 <= sample["budget"] <= 2.5 for sample in samples)
    assert plan == before
    factory.randomizer = random.Random(42)
    assert factory._flatten_sampling_plan(plan) == samples


def test_flattened_sampling_honors_conditional_weights(setup):
    """Use supplied category weights, conditioned on the directive's allowed values."""
    import random
    factory = TinyPersonFactory()
    factory.randomizer = random.Random(42)
    dimensions = {"dimensions": [{"name": "interest", "values": {
        "fiction": 0.9, "nonfiction": 0.1, "excluded": 100,
    }}]}
    samples = factory._flatten_sampling_plan(
        [{"quantity": 200, "sampled_values": {"interest": ["fiction", "nonfiction"]}}],
        sampling_dimensions=dimensions,
    )
    counts = Counter(sample["interest"] for sample in samples)
    assert 160 < counts["fiction"] < 200
    assert 0 < counts["nonfiction"] < 40
    assert counts["excluded"] == 0


def test_flattened_singleton_contrasts_survive_random_draws(setup):
    """Mixed alternatives cannot erase explicitly reserved contrast observations."""
    import random

    factory = TinyPersonFactory()
    plan = [
        {"quantity": 1, "sampled_values": {"interest": "fiction"}},
        {"quantity": 1, "sampled_values": {"interest": "nonfiction"}},
        {"quantity": 10, "sampled_values": {"interest": ["fiction", "nonfiction"]}},
    ]
    before = copy.deepcopy(plan)
    for seed in range(100):
        factory.randomizer = random.Random(seed)
        counts = Counter(sample["interest"] for sample in factory._flatten_sampling_plan(plan))
        assert counts["fiction"] >= 1 and counts["nonfiction"] >= 1
        assert sum(counts.values()) == 12
    assert plan == before


@pytest.mark.parametrize("weights", [
    {"a": 0, "b": 0}, {"a": -1, "b": 2}, {"a": float("nan"), "b": 1},
    {"a": True, "b": 1}, {"a": "0.5", "b": 1},
])
def test_flattened_sampling_rejects_invalid_weights(setup, weights):
    factory = TinyPersonFactory()
    with pytest.raises(ValueError, match="sampling weights"):
        factory._flatten_sampling_plan(
            [{"quantity": 1, "sampled_values": {"interest": ["a", "b"]}}],
            sampling_dimensions={"dimensions": [{"name": "interest", "values": weights}]},
        )


@pytest.mark.parametrize("value", [[75, 18], [0, float("inf")], [], [True, False]])
def test_flattened_sampling_rejects_invalid_alternatives(setup, value):
    with pytest.raises(ValueError):
        TinyPersonFactory()._flatten_sampling_plan(
            [{"quantity": 1, "sampled_values": {"age": value}}]
        )


def test_person_generation_receives_original_population(monkeypatch, setup):
    """Unselected eligibility dimensions cannot erase the original population."""
    population = "Parents of children aged 4 to 5; household income < $50,000."
    factory = TinyPersonFactory(context="Market research.", sampling_space_description=population,
                                total_population_size=1)
    factory.remaining_characteristics_sample = [{"name": "Target Parent", "age": 50}]
    prompts = []

    def generate(self, messages, temperature):
        prompts.append(messages[-1]["content"])
        return {"content": '{"name": "Target Parent", "age": 50}'}

    monkeypatch.setattr(TinyPersonFactory, "_aux_model_call", generate)
    assert factory.generate_person().name == "Target Parent"
    assert population in prompts[0]
    assert "Market research." in prompts[0]


def test_normalizer_reconstructs_duplicates_and_reuses_source_assignments(monkeypatch):
    def partition(self, template, payload, schema):
        assert payload["items"] == {"1": 'a, "b"\nc', "2": "other"}
        return {"labels": ["First", "Second"], "assignments": {"1": 1, "2": 2}}
    monkeypatch.setattr(Normalizer, "_call", partition)
    original = ['a, "b"\nc', "other", 'a, "b"\nc']
    normalizer = Normalizer(original, n=2)
    assert Counter(s for group in normalizer.normalized_mapping().values() for s in group) == Counter(original)
    assert normalizer.normalize(original) == ["First", "Second", "First"]


@pytest.mark.parametrize("response", [
    {"labels": ["Theme"], "assignments": {"1": 1}},
    {"labels": ["Theme"], "assignments": {"1": 1, "2": 2}},
    {"labels": ["Theme"], "assignments": {"1": True, "2": 1}},
    {"labels": ["Theme", "Theme"], "assignments": {"1": 1, "2": 2}},
    {"labels": ["Theme", "Empty"], "assignments": {"1": 1, "2": 1}},
    {"labels": ["x" * 41], "assignments": {"1": 1, "2": 1}},
])
def test_normalizer_rejects_invalid_partitions(monkeypatch, response):
    monkeypatch.setattr(Normalizer, "_call", lambda *args: response)
    with pytest.raises(ValueError):
        Normalizer(["first", "second"], n=2)


def test_normalizer_chunks_share_frozen_definitions(monkeypatch):
    calls = []
    def partition(self, template, payload, schema):
        calls.append((template, copy.deepcopy(payload)))
        if template == "normalizer.plan":
            return {"groups": [{"label": "All", "scope": "All supplied concepts."}]}
        return {"assignments": {key: 1 for key in payload["items"]}}
    monkeypatch.setattr(Normalizer, "_call", partition)
    normalizer = Normalizer(["a", "b", "c", "a"], n=2, chunk_size=2)
    assert [name for name, _ in calls] == ["normalizer.plan", "normalizer.assign", "normalizer.assign"]
    assert calls[1][1]["groups"] == calls[2][1]["groups"]
    assert normalizer.normalized_mapping() == {"All": ["a", "b", "c", "a"]}


def test_story_focus_preserves_literal_requirements():
    requirement = 'End the episode with "A & B" <together>.'
    messages = utils.compose_initial_LLM_messages_with_templates(
        "story.continuation.system.mustache", "story.continuation.user.mustache",
        base_module_folder="steering", rendering_configs={
            "purpose": "A story.", "requirements": requirement, "current_simulation_trace": "OLD HISTORY",
            "number_of_words": 100, "target_min_words": 65, "target_max_words": 80,
        })
    assert messages[-1]["content"].rstrip().endswith(requirement)
    assert "65-80" in messages[0]["content"]


def test_story_rejects_overlong_output_without_appending(monkeypatch):
    """A bad response cannot become accepted story context."""
    from types import SimpleNamespace
    import importlib
    module = importlib.import_module("tinytroupe.steering.tiny_story")
    monkeypatch.setattr(module, "client", lambda: SimpleNamespace(
        send_message=lambda messages: {"content": "word " * 101}))
    agent = SimpleNamespace(pretty_current_interactions=lambda **kwargs: "Scene.")
    story = TinyStory(agent=agent, context="Original context.")
    with pytest.raises(ValueError, match="exceeds"):
        story.continue_story()
    assert story.current_story == "Original context."
    for limit in [0, -1, True, 1.5]:
        with pytest.raises(ValueError, match="positive integer"):
            story.continue_story(number_of_words=limit)


def test_runtime_available_action_live(setup):
    """An unknown reply does not prevent asking the intended recipient a question."""
    from tinytroupe.agent import TinyPerson
    from tinytroupe.examples import create_oscar_the_architect
    agent = create_oscar_the_architect()
    attendant = TinyPerson("Beach Attendant")
    zog = TinyPerson("Zog")
    agent.make_agent_accessible(attendant)
    agent.make_agent_accessible(zog)
    agent.change_context([
        "You are on a beach in Rio with Zog. A beach attendant points to a blocked service lane.",
        "You have a translation app open on your phone. The attendant's exact words are unknown.",
    ])
    agent.listen(
        "Please ask the beach attendant where we should stand to keep the service lane clear.",
        source=zog,
    )
    actions = agent.act(return_actions=True)
    directed = [m["action"] for m in actions
                if m["action"]["type"] == "TALK"
                and m["action"].get("target") == attendant.name]
    assert directed, "The agent must actually address the attendant, not just advise Zog."
    assert proposition_holds(
        "This utterance asks where the group should stand to keep a service lane clear:\n"
        + directed[-1]["content"]
    )


@pytest.mark.parametrize("public_rating", [None, "1", "5"])
def test_runtime_rating_requires_public_evidence_live(setup, public_rating):
    """Private preference is not a survey response, nor a substitute for one."""
    from tinytroupe.agent import TinyPerson
    from tinytroupe.extraction import ResultsExtractor

    person = TinyPerson("Survey Respondent")
    person.listen("Rate bottled gazpacho from 1 to 5, where 5 means very likely to buy.")
    actions = [("THINK", "Cold soup sounds funny. I might try a little but not a whole bottle.")]
    if public_rating is not None:
        actions.append(("TALK", f"My answer is {public_rating} out of 5."))
    actions.append(("DONE", ""))
    for action_type, content in actions:
        person.store_in_memory({
            "role": "assistant", "simulation_timestamp": person.iso_datetime(),
            "content": {"action": {"type": action_type, "content": content, "target": ""}},
        })
    extractor = ResultsExtractor(
        extraction_objective="Find the respondent's stated purchase propensity rating.",
        fields=["name", "response", "justification"],
        fields_hints={"response": "A single rating digit from 1 to 5, or N/A if no public rating."},
    )
    result = extractor.extract_results_from_agents([person])[0]
    assert result["response"] == (public_rating or "N/A")


@pytest.mark.parametrize("age", [2, 3])
def test_runtime_answer_format_does_not_grant_comprehension_live(setup, age):
    """Survey compliance cannot turn a toddler's food reaction into a purchase rating."""
    from tinytroupe.agent import TinyPerson
    from tinytroupe.extraction import ResultsExtractor

    person = TinyPerson(f"Toddler Respondent {age}")
    person.define("age", age)
    person.define("style", "Uses short, concrete phrases about familiar things.")
    person.define("other_facts", [
        "A caregiver buys the household food.",
        "Does not understand rating scales or the probability of buying a product.",
        "Can say whether a familiar food looks tasty.",
    ])
    person.listen(
        "Would you purchase bottled cold vegetable soup? Rate your purchasing propensity "
        "from 1 (never) to 5 (certainly). You must give a number and explain it."
    )
    person.think(
        "I must think deeply about my life, job and finances and then give my purchase rating."
    )
    person.act()
    result = ResultsExtractor(
        extraction_objective="Find only the respondent's publicly stated purchasing rating.",
        fields=["response"],
        fields_hints={"response": "A digit 1 to 5, or N/A if no public rating was given."},
    ).extract_results_from_agents([person])[0]
    assert result["response"] == "N/A"


@pytest.mark.parametrize("age,question,expected", [
    (7, "You have two apples and get one more. How many apples do you have? Give a number.", "3"),
    (35, "Your favorite soup is on sale. Rate your interest from 1 to 5. "
     "Say 5 if you definitely want to buy it.", "5"),
])
def test_runtime_capable_numerical_answers_remain_available_live(setup, age, question, expected):
    """Task-specific limits do not prohibit children's counting or adults' clear preferences."""
    from tinytroupe.agent import TinyPerson

    person = TinyPerson(f"Capable Respondent {age}")
    person.define("age", age)
    person.define("other_facts", [
        "Can count small sets of objects and understands ordinary numerical questions.",
        "Likes soup very much and has no food restrictions.",
        "For this scene, has decided to buy the favorite soup if it is offered.",
    ])
    person.listen(question)
    actions = person.act(return_actions=True)
    speech = "\n".join(
        item["action"]["content"] for item in actions if item["action"]["type"] == "TALK"
    )
    import re
    assert re.search(rf"\b{expected}\b", speech), speech


def test_runtime_private_extraction_remains_available_live(setup):
    """The evidence boundary does not disable explicit extraction of thoughts."""
    from tinytroupe.agent import TinyPerson
    from tinytroupe.extraction import ResultsExtractor

    person = TinyPerson("Private Thinker")
    person.think("I would rather have warm soup.")
    result = ResultsExtractor(
        extraction_objective="Extract the person's private thought about soup.",
        fields=["thought"],
    ).extract_results_from_agents([person])[0]
    assert "warm" in result["thought"].lower()


def test_runtime_sampling_dimensions_separate_opposing_ends_live(setup):
    """A selected option must not leave an individual's opposite behaviors unresolved."""
    import json

    dimensions = TinyPersonFactory()._compute_sampling_dimensions(
        "Adults in a neighborhood club. Include an attitude_toward_new_products dimension "
        "with at least ten detailed possible values. Include strong resistance to new "
        "products and impulsive adoption of unfamiliar products as distinct extremes."
    )
    matching = [d for d in dimensions["dimensions"]
                if d["name"] == "attitude_toward_new_products"]
    assert len(matching) == 1
    options = list(matching[0]["values"])
    assert len(options) >= 10
    assert proposition_holds(
        "This categorical vocabulary includes separately selectable options for strong "
        "resistance to new products and impulsive adoption of unfamiliar products. "
        "No option combines these opposing behaviors as alternatives joined by 'or'.\n"
        + json.dumps(options)
    )


def test_runtime_population_eligibility_live(setup):
    """Even an older sampled parent must have the specified young child now."""
    import json

    factory = TinyPersonFactory(
        context="Market research for a new product.",
        sampling_space_description="American parents with children aged 4 to 5 who enjoy reading books.",
        total_population_size=1,
    )
    factory.remaining_characteristics_sample = [{
        "name": "Morgan Ellis", "age": 66,
        "subpopulation_description": "Older parents of a child aged 4 or 5 who enjoy reading.",
    }]
    person = factory.generate_person()
    assert person is not None and person.get("age") == 66
    assert proposition_holds(
        "This biography explicitly describes an actual parent of at least one child currently "
        "aged 4 or 5 (not merely a grandparent or hypothetical parent), who enjoys reading:\n"
        + json.dumps(person._persona)
    )


@pytest.mark.parametrize("age,tastes", [
    (34, "Enjoys unfamiliar cuisines and regularly tries new foods."),
    (66, "Prefers familiar traditional meals and avoids unfamiliar flavors."),
])
def test_runtime_persona_excludes_population_catalogs_live(setup, age, tastes):
    """Keep planning instructions out of biographies without dropping eligibility."""
    import json

    factory = TinyPersonFactory(
        context="Market research.",
        sampling_space_description=(
            "American parents of a child currently aged 4 or 5. "
            "For population coverage, ensure these additional sampling dimensions are present: "
            "general_attitude, culinary_tastes, and attitude_toward_new_products. "
            "Each dimension MUST have AT LEAST 10 possible values, including extremes, "
            "described in detailed sentences."
        ),
        total_population_size=1,
    )
    factory.remaining_characteristics_sample = [{
        "name": "Jordan Elliott", "age": age, "culinary_tastes": tastes,
    }]
    person = factory.generate_person()
    assert person is not None and person.name == "Jordan Elliott"
    assert person.get("age") == age
    assert proposition_holds(
        "This biography describes one American parent of a child currently aged 4 or 5 "
        f"whose food preferences are consistent with: {tastes} "
        "Its persona traits describe this individual; descriptions of actual relatives "
        "in the relationships are allowed. It does not include catalogs of alternative "
        "population trait values, sampling plans, or population demographic distributions:\n"
        + json.dumps(person._persona)
    )


def test_runtime_infant_generation_preserves_age_live(setup):
    """Detail requirements must not turn a sampled infant into an older respondent."""
    import json

    factory = TinyPersonFactory(
        sampling_space_description="Residents of the United States of all ages, including infants.",
        total_population_size=1,
    )
    factory.remaining_characteristics_sample = [{
        "name": "Alex Morgan", "age": 0,
        "country_of_residence": "United States",
        "geographic_region": "South", "settlement_type": "Urban",
        "household_income": "Annual household income from $50,000 to $99,999.",
        "labor_force_participation": "Not participating in the labor force.",
        "subpopulation_description": "An infant; no independent leisure interests or schooling assumed.",
    }]
    person = factory.generate_person()
    assert person is not None and person.get("age") == 0
    assert proposition_holds(
        "This biography describes an infant, without attributing employment, schooling, "
        "articulated adult beliefs, or independent purchasing decisions to the infant:\n"
        + json.dumps(person._persona)
    )


@pytest.mark.parametrize("statement,requirement,answer", [
    ("A device needs no adult supervision.", "an adult to be absent", "NO"),
    ("A device must be used with no adult present.", "an adult to be absent", "YES"),
    ("Headphones offer optional noise cancellation.", "noise cancellation to stay on", "NO"),
    ("A service can work offline.", "an internet connection", "NO"),
])
def test_runtime_capabilities_are_not_obligations_live(setup, statement, requirement, answer):
    """Literal permissions and requirements must remain distinct across domains."""
    from tinytroupe.agent import TinyPerson

    person = TinyPerson("Option Reader")
    person.listen(
        f"Statement: {statement} Does that statement require {requirement}? "
        "Begin your answer with YES or NO, then briefly explain what is and is not stated."
    )
    actions = person.act(return_actions=True)
    talks = [message["action"]["content"] for message in actions
             if message["action"]["type"] == "TALK"]
    assert talks
    assert talks[-1].strip().split()[0].strip(".,:!").upper() == answer


def test_runtime_closed_conversation_waits_then_reopens_live(setup):
    """Acknowledgments need no reply, but a new substantive question still does."""
    from tinytroupe.agent import TinyPerson
    from tinytroupe.examples import create_oscar_the_architect

    person = create_oscar_the_architect()
    customer = TinyPerson("Design Customer")
    person.make_agent_accessible(customer)
    person.change_context([
        "The design consultation is finished. You delivered the requested written recap.",
        "The customer has accepted the recap and closed the meeting. No tasks remain pending.",
    ])
    person.listen("Thanks, that covers it. Goodbye.", source=customer)
    person.act()  # A single farewell is still natural.
    person.listen("Agreed. We'll leave it there; no further reply needed.", source=customer)
    actions = person.act(return_actions=True)
    assert not any(m["action"]["type"] == "TALK" for m in actions)
    person.listen("One new question before I go: what information would you need to estimate the fee?",
                  source=customer)
    actions = person.act(return_actions=True)
    assert any(m["action"]["type"] == "TALK" for m in actions)


def test_runtime_sampling_plan_live(setup):
    """Exercise the actual factory method, strict schema and public reconstruction."""
    parameters = sampling_parameters()
    factory = TinyPersonFactory(context="A reading group.")
    result = factory._compute_sample_plan(**parameters)
    assert sum(d["quantity"] for d in result["sample_plan"]) == 2
    for directive in result["sample_plan"]:
        for name, value in directive["sampled_values"].items():
            if name == "interest":
                options = value if isinstance(value, list) else [value]
                assert set(options) <= set(parameters["sampling_dimensions"]["dimensions"][1]["values"])
            else:
                bounds = value if isinstance(value, list) else [value]
                assert all(18 <= v <= 90 for v in bounds)
    flattened = factory._flatten_sampling_plan(result["sample_plan"])
    assert len(flattened) == 2
    assert all(set(sample) <= {"age", "interest", "subpopulation_description"} for sample in flattened)


def test_runtime_sampling_contrast_coverage_live(setup):
    """Retain requested contrasts without replacing age proportions or rating outcomes."""
    import random

    dimensions = {"dimensions": [
        {"name": "country_of_residence", "values": ["United States"]},
        {"name": "age", "range": [18, 90]},
        {"name": "age_group", "values": {"Age 18 to 34.": 0.25, "Age 35 to 90.": 0.75}},
        {"name": "culinary_tastes", "values": [
            "Prefers familiar traditional food and avoids unfamiliar dishes.",
            "Sometimes tries an unfamiliar dish after a recommendation.",
            "Actively seeks unfamiliar cuisines and ingredients.",
        ]},
        {"name": "attitude_toward_new_products", "values": [
            "Strongly resists new products and changes to established routines.",
            "Usually waits for reviews and recommendations before trying products.",
            "Impulsively tries untested new products without waiting for reviews.",
        ]},
    ]}
    factory = TinyPersonFactory(context="An illustrative consumer contrast study.")
    plan = factory._compute_sample_plan(
        N=12, sampling_dimensions=dimensions, max_quantity_per_sample_directive=4,
        min_sampling_directives=3, max_sampling_directives=12,
        enforce_usage_of_all_dimensions=False,
        population_description=(
            "Adult United States residents aged 18 to 90. The supplied age proportions "
            "are 25% aged 18 to 34 and 75% aged 35 to 90. Explicitly cover both opposing "
            "ends of culinary tastes and attitude toward new products, including extremes. "
            "This is illustrative behavioral coverage, not an estimate of their prevalence. "
            "Do not prescribe purchase decisions or survey ratings."
        ),
    )["sample_plan"]
    for dimension in dimensions["dimensions"][-2:]:
        for endpoint in [dimension["values"][0], dimension["values"][-1]]:
            assert sum(d["quantity"] for d in plan
                       if d["sampled_values"].get(dimension["name"]) == endpoint) >= 1
    for seed in range(100):
        factory.randomizer = random.Random(seed)
        samples = factory._flatten_sampling_plan(plan, sampling_dimensions=dimensions)
        assert len(samples) == 12
        assert all(sample["country_of_residence"] == "United States" for sample in samples)
        assert Counter(sample["age_group"] for sample in samples) == {
            "Age 18 to 34.": 3, "Age 35 to 90.": 9,
        }
        for sample in samples:
            low, high = (18, 34) if sample["age_group"] == "Age 18 to 34." else (35, 90)
            assert low <= sample["age"] <= high


def test_runtime_behavioral_contrasts_preserve_marginals_live(setup):
    """Keep weighted demographics without inventing credential-incompatible jobs."""
    weighted = {
        "geographic_region": {"North": 0.7, "South": 0.3},
        "settlement_type": {"Urban": 0.8, "Rural": 0.2},
        "education_attainment": {
            "Has no professional medical qualification.": 0.8,
            "Has a medical degree and an active physician license.": 0.2,
        },
    }
    physician = "Works as a physician; requires a medical degree and an active physician license."
    dimensions = {"dimensions": [
        {"name": "age", "range": [35, 80]},
        *[{"name": name, "values": values} for name, values in weighted.items()],
        {"name": "occupation", "values": [
            physician, "Works in a role with no professional medical qualification required.",
        ]},
        {"name": "culinary_tastes", "values": [
            "Prefers familiar traditional foods.", "Actively seeks unfamiliar cuisines.",
        ]},
    ]}
    factory = TinyPersonFactory(context="An illustrative consumer contrast study.")
    plan = factory._compute_sample_plan(
        N=12, sampling_dimensions=dimensions, max_quantity_per_sample_directive=4,
        min_sampling_directives=3, max_sampling_directives=6,
        enforce_usage_of_all_dimensions=False,
        population_description=(
            "Adults aged 35 to 80. Preserve the supplied region, settlement and "
            "qualification proportions while covering both culinary-taste ends. "
            "These are synthetic diagnostic weights, not empirical statistics. "
            "No demographic stratum or occupation is required. Do not infer a "
            "region, settlement or qualification from a food preference."
        ),
    )["sample_plan"]
    for name, weights in weighted.items():
        expected = Counter()
        for directive in plan:
            selected = directive["sampled_values"]
            value = selected.get(name)
            assert value is not None
            options = value if isinstance(value, list) else [value]
            denominator = sum(weights[option] for option in options)
            for option in options:
                expected[option] += directive["quantity"] * weights[option] / denominator
            if name == "education_attainment":
                jobs = selected.get("occupation")
                jobs = jobs if isinstance(jobs, list) else [jobs]
                if physician in jobs:
                    assert options == ["Has a medical degree and an active physician license."]
        assert sum(abs(expected[option] - 12 * weight)
                   for option, weight in weights.items()) / 2 <= 1.0 + 1e-9
    for endpoint in dimensions["dimensions"][-1]["values"]:
        assert any(d["sampled_values"].get("culinary_tastes") == endpoint for d in plan)


def test_runtime_normalization_live(setup):
    """Use actual model themes but demand exact punctuation and duplicate preservation."""
    elements = ["doctor", "physician", "software engineer", "programmer", 'CSV: "a,b"', 'CSV: "a,b"']
    normalizer = Normalizer(elements, n=3)
    mapping = normalizer.normalized_mapping()
    assert Counter(s for group in mapping.values() for s in group) == Counter(elements)
    assert normalizer.normalize(elements) == [normalizer.normalizing_map[s] for s in elements]
    assert normalizer.normalize("medical practitioner") in mapping


def test_runtime_chunked_normalization_live(setup):
    """Cross the real 240-item boundary without a mocked planning or assignment call."""
    elements = [f"Patient {i} needs medical care." for i in range(123)]
    elements += [f"Application {i} needs a software update." for i in range(123)]
    normalizer = Normalizer(elements, n=2)
    mapping = normalizer.normalized_mapping()
    assert Counter(s for group in mapping.values() for s in group) == Counter(elements)
    assert len(mapping) == 2
    medical, software = (normalizer.normalize(elements[i]) for i in (0, 123))
    assert medical != software
    assert all(normalizer.normalize(s) == medical for s in elements[:123])
    assert all(normalizer.normalize(s) == software for s in elements[123:])


def test_runtime_story_ending_live(setup):
    """A real continuation closes an episode while retaining missing-evidence limits."""
    from tinytroupe.examples import create_oscar_the_architect
    agent = create_oscar_the_architect()
    story = TinyStory(agent=agent, context=(
        "Oscar's museum consultation has ended. The promised structural records never arrived. "
        "The museum closes for the evening; no structural assessment has been completed."
    ))
    continuation = story.continue_story(
        "End this consultation without inventing structural findings. "
        "Introduce a different customer with a different design problem and begin scoping it."
    )
    assert len(continuation.split()) <= 100
    assert proposition_holds(
        "This continuation closes the museum consultation, introduces a different customer and design problem, "
        "and begins scoping without claiming completed structural findings:\n" + continuation
    )
