import pytest
import logging
logger = logging.getLogger("tinytroupe")

import sys
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

from tinytroupe.examples import create_lisa_the_data_scientist, create_oscar_the_architect, create_marcos_the_physician
from tinytroupe.environment import TinyWorld
from testing_utils import *

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
            
            # TODO stimulus integrity check?
        

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


def test_encode_complete_state(setup, focus_group_world):
    world = focus_group_world

    # encode the state
    state = world.encode_complete_state()
    
    assert state is not None, "The state should not be None."
    assert state['name'] == world.name, "The state should have the world name."
    assert state['agents'] is not None, "The state should have the agents."

def test_decode_complete_state(setup, focus_group_world):
    world = focus_group_world

    name_1 = world.name
    n_agents_1 = len(world.agents)

    # encode the state
    state = world.encode_complete_state()
    
    # screw up the world
    world.name = "New name"
    world.agents = []

    # decode the state back into the world
    world_2 = world.decode_complete_state(state)

    assert world_2 is not None, "The world should not be None."
    assert world_2.name == name_1, "The world should have the same name."
    assert len(world_2.agents) == n_agents_1, "The world should have the same number of agents."


