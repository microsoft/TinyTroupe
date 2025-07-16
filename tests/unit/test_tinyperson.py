import pytest
import logging
logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/') # ensures that the package is imported from the parent directory, not the Python installation
sys.path.insert(0, '../../') # ensures that the package is imported from the parent directory, not the Python installation
sys.path.insert(0, '..') # ensures that the package is imported from the parent directory, not the Python installation


from tinytroupe.examples import create_oscar_the_architect, create_oscar_the_architect_2, create_lisa_the_data_scientist, create_lisa_the_data_scientist_2

from testing_utils import *

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

def test_listen(setup):
    # test that the agent listens to a speech stimulus and updates its current messages
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.listen("Hello, how are you?")

        assert len(agent.current_messages) > 0, f"{agent.name} should have at least one message in its current messages."
        assert agent.episodic_memory.retrieve_all()[-1]['role'] == 'user', f"{agent.name} should have the last message as 'user'."
        assert agent.episodic_memory.retrieve_all()[-1]['content']['stimuli'][0]['type'] == 'CONVERSATION', f"{agent.name} should have the last message as a 'CONVERSATION' stimulus."
        assert agent.episodic_memory.retrieve_all()[-1]['content']['stimuli'][0]['content'] == 'Hello, how are you?', f"{agent.name} should have the last message with the correct content."

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

def test_define_several(setup):
    # Test that defining several values to a group works as expected
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.define("skills", ["Python", "Machine learning", "GPT-3"])
        
        assert "Python" in agent._persona["skills"], f"{agent.name} should have Python as a skill."
        assert "Machine learning" in agent._persona["skills"], f"{agent.name} should have Machine learning as a skill."
        assert "GPT-3" in agent._persona["skills"], f"{agent.name} should have GPT-3 as a skill."

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

def test_see(setup):
    # Test that seeing a visual stimulus works as expected
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.see("A beautiful sunset over the ocean.")
        actions = agent.act(return_actions=True)
        assert len(actions) >= 1, f"{agent.name} should have at least one action to perform."
        assert contains_action_type(actions, "THINK"), f"{agent.name} should have at least one THINK action to perform, since they saw something interesting."
        assert contains_action_content(actions, "sunset"), f"{agent.name} should mention the sunset in the THINK action, since they saw it."
        
        # Semantic verification: check that the agent's thoughts relate to what they saw
        for action in actions:
            if action["action"]["type"] == "THINK":
                think_content = action["action"]["content"]
                assert proposition_holds(f"The following text is someone thinking about or reacting to seeing a beautiful sunset over the ocean: '{think_content}'"), \
                    f"Agent should be thinking about the sunset but thought: {think_content}"
                break

def test_think(setup):
    # Test that thinking about something works as expected
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
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

def test_internalize_goal(setup):
    # Test that internalizing a goal works as expected
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.internalize_goal("I want to compose in my head a wonderful poem about how cats are glorious creatures.")
        actions = agent.act(return_actions=True)
        assert len(actions) >= 1, f"{agent.name} should have at least one action to perform."
        assert contains_action_type(actions, "THINK"), f"{agent.name} should have at least one THINK action to perform, since they internalized a goal."
        assert contains_action_content(actions, "cats"), f"{agent.name} should mention cats in the THINK action, since they internalized a goal about them."
        
        # Semantic verification: check that the agent's thoughts relate to cats or poetry
        for action in actions:
            if action["action"]["type"] == "THINK":
                think_content = action["action"]["content"]
                assert proposition_holds(f"The following text is someone thinking about cats, poetry, or composing a poem about cats: '{think_content}'"), \
                    f"Agent should be thinking about cats or poetry but thought: {think_content}"
                break


def test_move_to(setup):
    # Test that moving to a new location works as expected
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.move_to("New York", context=["city", "busy", "diverse"])
        assert agent._mental_state["location"] == "New York", f"{agent.name} should have New York as the current location."
        assert "city" in agent._mental_state["context"], f"{agent.name} should have city as part of the current context."
        assert "busy" in agent._mental_state["context"], f"{agent.name} should have busy as part of the current context."
        assert "diverse" in agent._mental_state["context"], f"{agent.name} should have diverse as part of the current context."

def test_change_context(setup):
    # Test that changing the context works as expected
    for agent in [create_oscar_the_architect(), create_lisa_the_data_scientist()]:
        agent.change_context(["home", "relaxed", "comfortable"])
        assert "home" in agent._mental_state["context"], f"{agent.name} should have home as part of the current context."
        assert "relaxed" in agent._mental_state["context"], f"{agent.name} should have relaxed as part of the current context."
        assert "comfortable" in agent._mental_state["context"], f"{agent.name} should have comfortable as part of the current context."

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
    
    
