import pytest

import sys
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

from testing_utils import *

from tinytroupe.steering import Intervention
from tinytroupe.experimentation import ABRandomizer
from tinytroupe.experimentation import Proposition, check_proposition
from tinytroupe.examples import create_oscar_the_architect, create_oscar_the_architect_2, create_lisa_the_data_scientist, create_lisa_the_data_scientist_2
from tinytroupe.environment import TinyWorld


def test_intervention_1(setup):
    oscar = create_oscar_the_architect()


    oscar.think("I will talk about my travel preferences so that everyone can know and help me plan a trip.")
    oscar.act()

    assert check_proposition(oscar, "Oscar is talking about travel.", last_n=10)
    assert check_proposition(oscar, "Oscar is not talking about movies.", last_n=10)

    intervention = \
        Intervention(oscar)\
        .set_textual_precondition("Oscar is talking about travel.")\
        .set_effect(lambda target: target.think("Ok, enough of travel. Now I'll IMMEDIATLY talk about my favorite movies, RIGHT NOW, I'm suddenly in a hurry."))\
    
    world = TinyWorld("Test World", [oscar], interventions=[intervention])

    world.run(2)

    assert check_proposition(oscar, "Oscar was talking about travel, but then started talking about his favorite movies.", last_n = 30)


def test_intervention_batch_creation(setup):
    """Test that create_for_each creates an intervention for each target"""
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()
    
    # Create batch for multiple agents
    batch = Intervention.create_for_each([oscar, lisa])
    
    # Verify batch has correct number of interventions
    assert len(batch.interventions) == 2
    assert batch.interventions[0].targets == oscar
    assert batch.interventions[1].targets == lisa

def test_intervention_batch_settings(setup):
    """Test that batch methods apply settings to all interventions"""
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()
    
    precondition_text = "The agent is talking about work."
    effect_func = lambda target: target.think("I should talk about hobbies instead.")
    
    batch = Intervention.create_for_each([oscar, lisa])\
        .set_textual_precondition(precondition_text)\
        .set_effect(effect_func)
    
    # Verify settings were applied to all interventions
    for intervention in batch.interventions:
        assert intervention.text_precondition == precondition_text
        assert intervention.effect_func == effect_func

def test_intervention_batch_iteration(setup):
    """Test that the batch can be used with iteration and list()"""
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()
    
    batch = Intervention.create_for_each([oscar, lisa])
    
    # Test direct iteration
    count = 0
    for intervention in batch:
        count += 1
    assert count == 2
    
    # Test list conversion
    interventions_list = list(batch)
    assert len(interventions_list) == 2
    assert isinstance(interventions_list[0], Intervention)
    assert isinstance(interventions_list[1], Intervention)
    
    # Test as_list method
    as_list_result = batch.as_list()
    assert as_list_result == interventions_list

def test_intervention_batch_in_world(setup):
    """Test that a batch can be used directly with TinyWorld"""
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()
    
    # Set up initial state
    oscar.think("I will talk about work projects. I'll provide details on my current tasks.")
    oscar.act()
    lisa.think("I will discuss data analysis methods. I'll provide details on my current tasks.")
    lisa.act()
    
    # Create intervention batch
    batch = Intervention.create_for_each([oscar, lisa])\
        .set_textual_precondition("The agent is talking about work-related topics.")\
        .set_effect(lambda target: target.think("I will switch to TALK about my hobbies IMMEDIATELY before issuing DONE. I'll start NOW, without any delay, not waiting another turn, talking about them like this: 'Let me tell you about my hobbies (...)'."))
    
    # Create world with the batch directly (should work with iteration)
    world = TinyWorld("Test World", [oscar, lisa], interventions=batch)
    
    world.run(2)
    
    # Verify effect on both agents
    assert check_proposition(oscar, "Oscar was talking about work, but then switched to talking about hobbies.", last_n=30)
    assert check_proposition(lisa, "Lisa was talking about work, but then switched to talking about hobbies.", last_n=30)

