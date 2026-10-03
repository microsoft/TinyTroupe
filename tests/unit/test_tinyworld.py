import pytest
import logging
logger = logging.getLogger("tinytroupe") # Main logger
test_logger = logging.getLogger(__name__) # Logger for test-specific messages

import sys
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

from tinytroupe.examples import create_lisa_the_data_scientist, create_oscar_the_architect, create_marcos_the_physician
from tinytroupe.environment.tiny_world import TinyWorld # Corrected import path
from tinytroupe.agent import TinyPerson # Added for creating mock targets if needed
from tinytroupe.steering.intervention import Intervention # Added for creating Intervention objects
from tinytroupe.utils import JsonSerializableRegistry # For type checking potentially

from testing_utils import * # Assumes get_relative_to_test_path, EXPORT_BASE_FOLDER etc. are here
import os # For test_save_specification

# Imports for new tests
from unittest.mock import MagicMock, patch

@pytest.mark.core
def test_run(setup, focus_group_world):

    # empty world
    world_1 = TinyWorld("Empty land", [])   
    world_1.run(2)

    # world with agents
    world_2 = focus_group_world
    world_2.broadcast("Discuss ideas for a new AI product you'd love to have.")
    world_2.run(2)

    # check integrity of conversation
    for agent in world_2.agents:
        for msg in agent.episodic_memory.retrieve_all():
            if 'action' in msg['content'] and 'target' in msg['content']['action']:
                assert msg['content']['action']['target'] != agent.name, f"{agent.name} should not have any messages with itself as the target."
            
            # Semantic verification: if it's a TALK action, ensure it relates to AI product discussion
            if 'action' in msg['content'] and msg['content']['action'].get('type') == 'TALK':
                action_content = msg['content']['action'].get('content', '')
                if action_content:  # Only check if there's content
                    assert proposition_holds(action_content + " - The message relates to AI products, technology, or innovation")
    # Stimulus integrity: at least one agent should have received the broadcast
    broadcast_received = False
    for agent in world_2.agents:
        for msg in agent.episodic_memory.retrieve_all():
            for s in msg.get('content', {}).get('stimuli', []):
                if 'content' in s and 'Discuss ideas for a new AI product' in s['content']:
                    broadcast_received = True
                    break
        if broadcast_received:
            break
    assert broadcast_received, "At least one agent should have received the broadcast stimulus"
        

@pytest.mark.core
def test_broadcast(setup, focus_group_world):

    world = focus_group_world
    world.broadcast("""
                Folks, we need to brainstorm ideas for a new baby product. Something moms have been asking for centuries and never got.

                Please start the discussion now.
                """)
    
    for agent in focus_group_world.agents:
        # did the agents receive the message?
        assert "Folks, we need to brainstorm" in agent.episodic_memory.retrieve_first(1)[0]['content']['stimuli'][0]['content'], f"{agent.name} should have received the message."
    
    # Run the world to let agents respond
    world.run(1)
    
    # Semantic verification: check that agent responses relate to baby products or brainstorming
    for agent in focus_group_world.agents:
        recent_actions = agent.episodic_memory.retrieve_first(3)  # Get recent actions
        for msg in recent_actions:
            if 'action' in msg['content'] and msg['content']['action'].get('type') == 'TALK':
                action_content = msg['content']['action'].get('content', '')
                if action_content and len(action_content) > 20:  # Only check substantial responses
                    assert proposition_holds(action_content + " - The message relates to baby products, parenting, or product brainstorming")


@pytest.mark.core
def test_encode_complete_state(setup, focus_group_world):
    world = focus_group_world

    # encode the state
    state = world.encode_complete_state()
    
    assert state is not None, "The state should not be None."
    assert state['name'] == world.name, "The state should have the world name."
    assert state['agents'] is not None, "The state should have the agents."

@pytest.mark.core
def test_decode_complete_state(setup, focus_group_world):
    world = focus_group_world

    name_1 = world.name
    n_agents_1 = len(world.agents)

    # encode the state
    state = world.encode_complete_state()
    
    # screw up the world
    world.name = "New name"
    # world.agents = [] # Let's not remove agents, as decode_complete_state reuses existing agent objects by name

    # decode the state back into a new world instance to avoid issues with global agent list
    # or ensure setup fixture cleans up TinyPerson.all_agents and TinyWorld.all_environments
    new_world_name = f"{name_1}_decoded"
    # Ensure the new world name doesn't clash if environments are registered globally
    if TinyWorld.get_environment_by_name(new_world_name):
        TinyWorld.all_environments.pop(new_world_name)

    new_world = TinyWorld(name=new_world_name) # Create a fresh world

    # If agents are globally registered and reused, ensure they exist for decoding
    # For a clean test, it's better if decode can reconstruct or if agents are passed to constructor
    # Current TinyWorld.decode_complete_state assumes agents can be fetched by name or created.

    decoded_world = new_world.decode_complete_state(state) # state is from the original 'world'

    assert decoded_world is not None, "The world should not be None."
    assert decoded_world.name == name_1, "The world should have the same name as original."
    assert len(decoded_world.agents) == n_agents_1, "The world should have the same number of agents."


# --- New tests for Intervention Serialization ---

def test_world_with_interventions_encode_decode(setup):
    """Test encoding and decoding of a TinyWorld with interventions."""
    # 1. Setup
    # Mock targets for Intervention constructor, as targets are not serialized
    mock_target_person = MagicMock(spec=TinyPerson)
    mock_target_person.name = "MockPerson" # Intervention might use target's name

    # It's important that TinyPerson.all_agents is clear or managed by 'setup' if Intervention's
    # __init__ or other methods try to resolve target names globally.
    # For this test, we assume Intervention.__init__ can take MagicMock.

    world_name = "WorldWithInterventions"
    # Clean up if this world name was used before and registered globally
    if TinyWorld.get_environment_by_name(world_name):
        TinyWorld.all_environments.pop(world_name)

    original_world = TinyWorld(name=world_name)

    intervention1 = Intervention(targets=[mock_target_person], name="Intervention1", text_precondition="Condition1")
    intervention1.first_n = 1
    intervention1.last_n = 1 # Ensure these serializable attrs are set

    intervention2 = Intervention(targets=[mock_target_person], name="Intervention2", text_precondition="Condition2")
    intervention2.first_n = 2
    intervention2.last_n = 2

    original_world._interventions = [intervention1, intervention2]

    # 2. Encode
    encoded_state = original_world.encode_complete_state()

    assert "_interventions" in encoded_state, "Serialized state must contain '_interventions' key."
    assert isinstance(encoded_state["_interventions"], list), "'_interventions' should be a list."
    assert len(encoded_state["_interventions"]) == 2, "Incorrect number of interventions serialized."

    for inter_data in encoded_state["_interventions"]:
        assert isinstance(inter_data, dict), "Each serialized intervention should be a dict."
        assert "name" in inter_data
        assert "text_precondition" in inter_data
        assert "first_n" in inter_data
        assert "last_n" in inter_data
        # Check for one of them specifically
        if inter_data["name"] == "Intervention1":
            assert inter_data["text_precondition"] == "Condition1"
            assert inter_data["first_n"] == 1
            assert inter_data["last_n"] == 1


    # 3. Decode
    new_world_name = "DecodedWorldWithInterventions"
    if TinyWorld.get_environment_by_name(new_world_name):
        TinyWorld.all_environments.pop(new_world_name)

    new_world = TinyWorld(name=new_world_name)
    new_world.decode_complete_state(encoded_state)

    assert isinstance(new_world._interventions, list)
    assert len(new_world._interventions) == 2

    for i, decoded_inter in enumerate(new_world._interventions):
        assert isinstance(decoded_inter, Intervention)
        original_inter = original_world._interventions[i]
        assert decoded_inter.name == original_inter.name
        assert decoded_inter.text_precondition == original_inter.text_precondition
        assert decoded_inter.first_n == original_inter.first_n
        assert decoded_inter.last_n == original_inter.last_n
        # Non-serialized fields should be default or None
        assert decoded_inter.targets == [] # Targets are not restored
        assert decoded_inter.precondition_func is None
        assert decoded_inter.effect_func is None

def test_world_with_no_interventions_encode_decode(setup):
    """Test encoding and decoding of a TinyWorld with no interventions."""
    world_name = "WorldWithoutInterventions"
    if TinyWorld.get_environment_by_name(world_name):
        TinyWorld.all_environments.pop(world_name)
    original_world = TinyWorld(name=world_name)
    original_world._interventions = []

    encoded_state = original_world.encode_complete_state()

    assert "_interventions" in encoded_state
    assert isinstance(encoded_state["_interventions"], list)
    assert len(encoded_state["_interventions"]) == 0

    new_world_name = "DecodedWorldNoInterventions"
    if TinyWorld.get_environment_by_name(new_world_name):
        TinyWorld.all_environments.pop(new_world_name)

    new_world = TinyWorld(name=new_world_name)
    new_world.decode_complete_state(encoded_state)

    assert isinstance(new_world._interventions, list)
    assert len(new_world._interventions) == 0


def test_decode_malformed_intervention_data(setup, caplog):
    """Test graceful handling of malformed intervention data during decode."""
    world_name = "WorldMalformedInterventions"
    if TinyWorld.get_environment_by_name(world_name):
        TinyWorld.all_environments.pop(world_name)

    original_world = TinyWorld(name=world_name) # Not used for encoding, just for a target world

    # Create a state with one good and one malformed intervention
    mock_target_person = MagicMock(spec=TinyPerson)
    mock_target_person.name = "MockPersonTarget"

    good_intervention = Intervention(targets=[mock_target_person], name="GoodOne", text_precondition="GoodCondition")

    # Simulate an encoded state
    # In TinyWorld's encode_complete_state, other attributes are also present.
    # We need a minimal valid structure for TinyWorld state for decode to work.
    encoded_state = {
        'name': 'TestWorldState',
        'current_datetime': '2023-01-01T00:00:00', # Needs to be ISO format
        'agents': [], # Assuming no agents for simplicity of this specific test
        '_interventions': [
            good_intervention.to_json(), # A good one
            {"name": "MalformedIntervention", "text_precondition": "Bad", "unexpected_field": "error"}, # Malformed (Intervention.from_json might handle extra fields, but this is a stand-in for "bad data")
            "not_a_dict_intervention" # Definitely malformed
        ],
        # Add other fields that TinyWorld.decode_complete_state might expect before __dict__.update
        'broadcast_if_no_target': True,
        '_displayed_communications_buffer': [],
        '_target_display_communications_buffer': [],
        '_max_additional_targets_to_display': 3,
        'simulation_id': None
    }

    # Patch Intervention.from_json for the malformed dict case to ensure it raises an error
    # The "not_a_dict_intervention" will be skipped by `isinstance(inter_data, dict)` check.
    # To test the try-except in decode for the dict case, we make from_json raise an error for the specific malformed dict.

    original_from_json = Intervention.from_json
    def mock_from_json(data):
        if isinstance(data, dict) and data.get("name") == "MalformedIntervention":
            raise ValueError("Simulated deserialization error for MalformedIntervention")
        # For "GoodOne", it will call the original from_json via this wrapper if not careful.
        # Better: only patch from_json if we want to control its behavior for specific inputs.
        # The current try-except in TinyWorld.decode_complete_state should catch errors from Intervention.from_json
        return original_from_json(data) # Call original for others

    with patch('tinytroupe.steering.intervention.Intervention.from_json', side_effect=mock_from_json):
      with caplog.at_level(logging.WARNING):
          original_world.decode_complete_state(encoded_state)

    assert len(original_world._interventions) == 1 # Only the good one should be decoded
    assert original_world._interventions[0].name == "GoodOne"

    # Check for logged warnings
    assert any("Failed to deserialize an intervention" in record.message and "MalformedIntervention" in record.message for record in caplog.records), "Warning for malformed dict not logged"
    # The "not_a_dict_intervention" is skipped silently by `isinstance(inter_data, dict)` check, so no log for that.
    # If we want to test that, we'd need to modify the `decode_complete_state` to log for non-dict items too.

# This is standard for pytest, no need for unittest.main()
# Pytest will discover tests automatically.
# if __name__ == '__main__':
#     pytest.main() # Or simply run `pytest` from command line
