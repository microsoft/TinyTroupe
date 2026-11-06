import pytest
import logging
import tiktoken
logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/') # ensures that the package is imported from the parent directory, not the Python installation
sys.path.insert(0, '../../') # ensures that the package is imported from the parent directory, not the Python installation
sys.path.insert(0, '..') # ensures that the package is imported from the parent directory, not the Python installation


from tinytroupe.examples import create_oscar_the_architect, create_oscar_the_architect_2, create_lisa_the_data_scientist, create_lisa_the_data_scientist_2
from tinytroupe import config_manager

from testing_utils import *

@pytest.mark.core
def test_act(setup):

    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:

        actions = agent.listen_and_act("Tell me a bit about your life.", return_actions=True)

        logger.info(agent.pp_current_interactions())

        assert len(actions) >= 1, f"{agent.name} should have at least one action to perform (even if it is just DONE)."
        assert contains_action_type(actions, "TALK"), f"{agent.name} should have at least one TALK action to perform, since we asked him to do so."
        assert terminates_with_action_type(actions, "DONE"), f"{agent.name} should always terminate with a DONE action."
        
        # Semantic verification: check that the agent actually talks about their life
        for action in actions:
            if action["action"]["type"] == "TALK":
                talk_content = action["action"]["content"]
                assert proposition_holds(f"The following text is someone talking about their personal life, background, or experiences: '{talk_content}'"), \
                    f"Agent should be talking about their life but said: {talk_content}"
                break

@pytest.mark.core
def test_listen(setup):
    # test that the agent listens to a speech stimulus and updates its current messages
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.listen("Hello, how are you?")

        assert len(agent.current_messages) > 0, f"{agent.name} should have at least one message in its current messages."
        assert agent.episodic_memory.retrieve_all()[-1]['role'] == 'user', f"{agent.name} should have the last message as 'user'."
        assert agent.episodic_memory.retrieve_all()[-1]['content']['stimuli'][0]['type'] == 'CONVERSATION', f"{agent.name} should have the last message as a 'CONVERSATION' stimulus."
        assert agent.episodic_memory.retrieve_all()[-1]['content']['stimuli'][0]['content'] == 'Hello, how are you?', f"{agent.name} should have the last message with the correct content."

@pytest.mark.core
@pytest.mark.parametrize("with_image", [False, True])
def test_action_generation_preserves_text_and_serializes_stimuli(setup, monkeypatch, with_image):
    """System instructions are text, whereas structured stimuli require JSON encoding."""
    import copy
    import json

    agent = TinyPerson("Message transport reader")
    generator = agent.action_generator
    generator.enable_quality_checks = False
    messages = [
        {"role": "system", "content": 'Instructions:\nKeep "caf\u00e9" unchanged.'},
        {"role": "user", "content": "Produce the next action."},
        {"role": "user", "content": {"stimuli": [
            {"type": "CONVERSATION", "content": "What do you think?", "source": ""}
        ]}},
    ]
    if with_image:
        messages[2]["content"]["stimuli"][0]["images"] = ["test-image"]
        agent._image_registry["test-image"] = "https://example.com/image.png"
    before = copy.deepcopy(messages)
    captured = []

    def tentative(agent, current_messages, **kwargs):
        captured.extend(copy.deepcopy(current_messages))
        actions = [{"type": "DONE", "content": "", "target": ""}]
        return actions, "assistant", {"actions": actions}

    monkeypatch.setattr(generator, "_generate_tentative_action", tentative)
    generator.generate_next_actions(agent, messages)

    assert captured[:2] == before[:2]
    if with_image:
        parts = captured[2]["content"]
        assert json.loads(parts[0]["text"]) == before[2]["content"]
        assert parts[1]["image_url"]["url"] == "https://example.com/image.png"
    else:
        assert json.loads(captured[2]["content"]) == before[2]["content"]
    assert messages == before


@pytest.mark.core
def test_memory_prompt_marks_a_real_omission(setup):
    """A missing middle block is memory metadata, not an action to silently discard."""
    agent = TinyPerson("Partial memory reader")
    agent.episodic_memory.fixed_prefix_length = 1
    agent.episodic_memory.lookback_length = 1
    for text in ["Opening request.", "Middle answer.", "Latest request."]:
        agent.listen(text)

    prompt = agent._render_recent_episodic_memories_for_prompt()

    assert "Opening request." in prompt and "Latest request." in prompt
    assert "Middle answer." not in prompt
    assert "[MEMORY GAP]" in prompt and "omitted for brevity" in prompt
    assert "[ACTION:" not in prompt


@pytest.mark.core
def test_complete_memory_prompt_has_no_omission_warning(setup):
    """Empty and completely retained histories must not carry a false memory gap."""
    agent = TinyPerson("Complete memory reader")
    assert "[MEMORY GAP]" not in agent._render_recent_episodic_memories_for_prompt()
    agent.listen("An entirely retained message.")
    prompt = agent._render_recent_episodic_memories_for_prompt()
    assert "An entirely retained message." in prompt
    assert "[MEMORY GAP]" not in prompt


@pytest.mark.core
@pytest.mark.parametrize("role", ["user", "assistant"])
def test_memory_prompt_preserves_content_beyond_display_limit(setup, monkeypatch, role):
    """Console shortening must not remove information from model-visible memories."""
    monkeypatch.setitem(config_manager._config, "max_content_display_length", 64)
    agent = TinyPerson("Memory reader")
    text = "The project archive contains drawings and meeting notes. " * 40
    text += "The delivery reference is ORCHID-4729."
    if role == "user":
        event = {
            "role": role,
            "type": "stimulus",
            "content": {"stimuli": [{"type": "THOUGHT", "content": text}]},
        }
    else:
        event = {
            "role": role,
            "type": "action",
            "content": {"action": {"type": "TALK", "content": text, "target": ""}},
        }
    agent.episodic_memory.store(event)

    assert text in agent._render_recent_episodic_memories_for_prompt()


@pytest.mark.core
def test_act_reads_earlier_message_beyond_display_limit(setup, monkeypatch):
    """A real model must retain a long document after a later conversational stimulus."""
    monkeypatch.setitem(config_manager._config, "max_content_display_length", 64)
    agent = create_oscar_the_architect()
    document = "The project archive contains drawings and meeting notes. " * 40
    document += "The delivery reference is ORCHID-4729."
    agent.listen(document)

    actions = agent.listen_and_act(
        "What is the exact delivery reference in the project archive? "
        "Tell me the reference without guessing.",
        return_actions=True,
    )

    assert any(
        action["action"]["type"] == "TALK"
        and "ORCHID-4729" in action["action"]["content"]
        for action in actions
    )


@pytest.mark.core
def test_system_prompt_includes_current_cognitive_state(setup):
    """The prompt's cognitive sections must expose the actual current state."""
    agent = TinyPerson("State reader")
    peer = TinyPerson("Mira Stonebridge")
    state = {
        "datetime": "2025-04-17T09:23:00",
        "location": "Juniper meeting room",
        "context": ["Reviewing the orchid delivery"],
        "attention": "The blue delivery folder",
        "goals": ["Confirm the orchid delivery reference"],
        "emotions": "Curious about the orchid shipment",
        "working_semantic_memory": ["The delivery reference is ORCHID-4729"],
    }
    agent._mental_state.update(state)
    agent.make_agent_accessible(peer, relation_description="The orchid delivery coordinator")

    prompt = agent.generate_agent_system_prompt()

    for value in state.values():
        for text in value if isinstance(value, list) else [value]:
            assert text in prompt
    social_context = prompt.split("#### Social context", 1)[1].split("### Attention", 1)[0]
    assert peer.name in social_context
    assert "The orchid delivery coordinator" in social_context


@pytest.mark.core
def test_recall_last_user_statement_excludes_simulation_control(setup):
    """An agent must recall the user's statement, not the internal turn-control cue."""
    agent = create_lisa_the_data_scientist()
    agent.listen("The delivery reference is ORCHID-4729.")

    actions = agent.listen_and_act("What did I just told you?", return_actions=True)

    talks = [
        item["action"]["content"] for item in actions
        if item["action"]["type"] == "TALK"
    ]
    assert any("ORCHID-4729" in text for text in talks)
    assert all("next sequence of actions" not in text for text in talks)


@pytest.mark.core
@pytest.mark.parametrize("remove_all", [False, True])
def test_system_prompt_tracks_agent_accessibility(setup, remove_all):
    """Removing a contact must remove it from the prompt's reachable contacts."""
    agent = TinyPerson("State reader")
    peer = TinyPerson("Mira Stonebridge")
    agent.make_agent_accessible(peer)
    assert peer.name in agent.generate_agent_system_prompt()

    if remove_all:
        agent.make_all_agents_inaccessible()
    else:
        agent.make_agent_inaccessible(peer)

    assert peer not in agent.accessible_agents
    assert peer.name not in agent.generate_agent_system_prompt()


@pytest.mark.core
def test_act_addresses_contact_from_cognitive_state(setup):
    """A real model must see a contact provided only through accessibility state."""
    agent = create_oscar_the_architect()
    peer = TinyPerson("Mira Stonebridge")
    agent.make_agent_accessible(peer, relation_description="A colleague attending this meeting")

    actions = agent.listen_and_act(
        "Greet the colleague currently accessible to you by name. "
        "Direct your TALK action to that colleague.",
        return_actions=True,
    )

    final_state = actions[-1]["cognitive_state"]
    assert agent._mental_state["attention"] == final_state["attention"]
    assert agent._mental_state["emotions"] == final_state["emotions"]
    assert any(
        action["action"]["type"] == "TALK"
        and action["action"]["target"] == peer.name
        and "Mira" in action["action"]["content"]
        for action in actions
    )


@pytest.mark.core
def test_define(setup):
    # test that the agent defines a value to its configuration and resets its prompt
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        # save the original prompt
        original_prompt = agent.current_messages[0]['content']

        # define a new value
        agent.define('age', 25)

        # check that the configuration has the new value
        assert agent._persona['age'] == 25, f"{agent.name} should have the age set to 25."

        # check that the prompt has changed
        assert agent.current_messages[0]['content'] != original_prompt, f"{agent.name} should have a different prompt after defining a new value."

        # check that the prompt contains the new value
        assert '25' in agent.current_messages[0]['content'], f"{agent.name} should have the age in the prompt."


@pytest.mark.core
@pytest.mark.parametrize(
    "text", ["Delivery notes. " * 100, "\u6f22\u5b57" * 500], ids=["english", "cjk"]
)
def test_contextual_retrieval_query_is_bounded(setup, monkeypatch, text):
    """Embedding cues must not repeat historical cognitive state or exceed the token limit."""
    monkeypatch.setitem(
        config_manager._config, "enable_continuous_contextual_semantic_memory_retrieval", True
    )
    agent = TinyPerson("Memory reader")
    for _ in range(35):
        agent.episodic_memory.store({
            "role": "assistant",
            "type": "action",
            "content": {
                "action": {"type": "THINK", "content": text, "target": ""},
                "cognitive_state": {"context": ["HISTORICAL_STATE_MARKER " * 1000]},
            },
        })
    captured = []

    def capture(target, top_k):
        captured.append(target)
        return []

    monkeypatch.setattr(agent, "retrieve_relevant_memories", capture)
    agent.retrieve_relevant_memories_for_current_context()

    assert len(captured) == 1
    assert "HISTORICAL_STATE_MARKER" not in captured[0]
    assert len(tiktoken.get_encoding("cl100k_base").encode(captured[0])) <= 8191
    assert agent.episodic_memory.retrieve_all()[0]["content"]["action"]["content"] == text
    assert text in agent._render_recent_episodic_memories_for_prompt()


@pytest.mark.core
def test_contextual_retrieval_with_large_history_real_embeddings(setup, monkeypatch):
    """A real embedding request must still retrieve source facts after a long history."""
    monkeypatch.setitem(
        config_manager._config, "enable_continuous_contextual_semantic_memory_retrieval", True
    )
    agent = TinyPerson("Memory reader")
    agent.semantic_memory.store({
        "type": "fact", "content": "The orchid delivery reference is ORCHID-4729."
    })
    for _ in range(35):
        agent.episodic_memory.store({
            "role": "assistant",
            "type": "action",
            "content": {
                "action": {"type": "THINK", "content": "\u6f22\u5b57" * 500, "target": ""},
                "cognitive_state": {"context": ["HISTORICAL_STATE_MARKER " * 1000]},
            },
        })
    agent._mental_state["attention"] = "Find the orchid delivery reference."

    results = agent.retrieve_relevant_memories_for_current_context()

    assert any("ORCHID-4729" in item for item in results)

@pytest.mark.core
def test_define_several(setup):
    # Test that defining several values to a group works as expected
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.define("skills", ["Python", "Machine learning", "GPT-3"])
        
        assert "Python" in agent._persona["skills"], f"{agent.name} should have Python as a skill."
        assert "Machine learning" in agent._persona["skills"], f"{agent.name} should have Machine learning as a skill."
        assert "GPT-3" in agent._persona["skills"], f"{agent.name} should have GPT-3 as a skill."

@pytest.mark.core
def test_socialize(setup):
    # Test that socializing with another agent works as expected
    an_oscar = create_oscar_the_architect()
    a_lisa = create_lisa_the_data_scientist()
    for agent in [an_oscar, a_lisa]:
        other = a_lisa if agent.name == "Oscar" else an_oscar
        agent.make_agent_accessible(other, relation_description="My friend")
        agent.listen(f"Hi {agent.name}, I am {other.name}.")
        actions = agent.act(return_actions=True)
        assert len(actions) >= 1, f"{agent.name} should have at least one action to perform."
        assert contains_action_type(actions, "TALK"), f"{agent.name} should have at least one TALK action to perform, since we started a conversation."
        assert contains_action_content(actions, agent_first_name(other)), f"{agent.name} should mention {other.name}'s first name in the TALK action, since they are friends."

@pytest.mark.core
def test_see(setup):
    # Test that seeing a visual stimulus works as expected
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.see(description="A beautiful sunset over the ocean.")
        actions = agent.act(return_actions=True)
        assert len(actions) >= 1, f"{agent.name} should have at least one action to perform."
        assert contains_action_type(actions, "THINK"), f"{agent.name} should have at least one THINK action to perform, since they saw something interesting."
        # A grounded paraphrase need not repeat the literal stimulus word.
        for action in actions:
            if action["action"]["type"] == "THINK":
                think_content = action["action"]["content"]
                assert proposition_holds(
                    f"Given the visual stimulus 'A beautiful sunset over the ocean.', this is a "
                    f"plausible visually grounded reaction (for example to light, colour, horizon, "
                    f"water or atmosphere), rather than an unrelated thought: '{think_content}'"
                ), \
                    f"Agent should be thinking about the sunset but thought: {think_content}"
                break

@pytest.mark.core
def test_think(setup):
    """A thought to address others must produce speech when a listener is reachable."""
    listener = TinyPerson("Mira Stonebridge")
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.make_agent_accessible(listener, relation_description="A friend here with me")
        agent.think("I will tell everyone right now how awesome life is!")
        actions = agent.act(return_actions=True)
        assert len(actions) >= 1, f"{agent.name} should have at least one action to perform."
        assert contains_action_type(actions, "TALK"), f"{agent.name} should have at least one TALK action to perform, since they are eager to talk."
        assert contains_action_content(actions, "life"), f"{agent.name} should mention life in the TALK action, since they thought about it."
        
        # Semantic verification: check that the agent expresses enthusiasm about life
        for action in actions:
            if action["action"]["type"] == "TALK":
                talk_content = action["action"]["content"]
                assert proposition_holds(f"The following text expresses enthusiasm or positive feelings about life: '{talk_content}'"), \
                    f"Agent should be expressing enthusiasm about life but said: {talk_content}"
                break

@pytest.mark.core
def test_internalize_goal(setup):
    # Test that internalizing a goal works as expected
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.internalize_goal("I want to compose in my head a wonderful poem about how cats are glorious creatures.")
        actions = agent.act(return_actions=True)
        assert len(actions) >= 1, f"{agent.name} should have at least one action to perform."
        assert contains_action_type(actions, "THINK"), f"{agent.name} should have at least one THINK action to perform, since they internalized a goal."
        
        # Verify the goal semantically rather than requiring a particular word form.
        for action in actions:
            if action["action"]["type"] == "THINK":
                think_content = action["action"]["content"]
                assert proposition_holds(f"The following text is someone composing or planning a poem that celebrates cats: '{think_content}'"), \
                    f"Agent should be composing or planning a poem celebrating cats but thought: {think_content}"
                break


@pytest.mark.core
def test_move_to(setup):
    # Test that moving to a new location works as expected
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.move_to("New York", context=["city", "busy", "diverse"])
        assert agent._mental_state["location"] == "New York", f"{agent.name} should have New York as the current location."
        assert "city" in agent._mental_state["context"], f"{agent.name} should have city as part of the current context."
        assert "busy" in agent._mental_state["context"], f"{agent.name} should have busy as part of the current context."
        assert "diverse" in agent._mental_state["context"], f"{agent.name} should have diverse as part of the current context."

@pytest.mark.core
def test_change_context(setup):
    # Test that changing the context works as expected
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.change_context(["home", "relaxed", "comfortable"])
        assert "home" in agent._mental_state["context"], f"{agent.name} should have home as part of the current context."
        assert "relaxed" in agent._mental_state["context"], f"{agent.name} should have relaxed as part of the current context."
        assert "comfortable" in agent._mental_state["context"], f"{agent.name} should have comfortable as part of the current context."

@pytest.mark.core
def test_save_specification(setup):   
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        # save to a file
        agent.save_specification(get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/serialization/{agent.name}.tinyperson.json"), include_memory=True)

        # check that the file exists
        assert os.path.exists(get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/serialization/{agent.name}.tinyperson.json")), f"{agent.name} should have saved the file."

        # load the file to see if the agent is the same. The agent name should be different because it TinyTroupe does not allow two agents with the same name.
        loaded_name = f"{agent.name}_loaded"
        loaded_agent = TinyPerson.load_specification(get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/serialization/{agent.name}.tinyperson.json"), new_agent_name=loaded_name)

        # check that the loaded agent is the same as the original
        assert loaded_agent.name == loaded_name, f"{agent.name} should have the same name as the loaded agent."
        
        assert agents_personas_are_equal(agent, loaded_agent, ignore_name=True), f"{agent.name} should have the same configuration as the loaded agent, except for the name."
        
def test_programmatic_definitions(setup):
    for agent in [create_oscar_the_architect_2(), create_lisa_the_data_scientist_2()]:
        agent.listen_and_act("Tell me a bit about your life.")
    
    
