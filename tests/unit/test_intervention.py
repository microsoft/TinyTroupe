import pytest

import sys
sys.path.append('../../tinytroupe/')
sys.path.append('../../')
sys.path.append('..')

from testing_utils import *

from tinytroupe.steering import Intervention
from tinytroupe.experimentation import ABRandomizer
from tinytroupe.experimentation import Proposition, check_proposition
from tinytroupe.examples import create_oscar_the_architect, create_oscar_the_architect_2, create_lisa_the_data_scientist, create_lisa_the_data_scientist_2
from tinytroupe.environment import TinyWorld



def test_intervention_1():
    oscar = create_oscar_the_architect()


    oscar.think("I will talk about my travel preferences so that everyone can know and help me plan a trip.")
    oscar.act()

    assert check_proposition(oscar, "Oscar is talking about travel.", last_n=3)
    assert check_proposition(oscar, "Oscar is not talking about movies.", last_n=3)

    intervention = \
        Intervention(oscar)\
        .set_textual_precondition("Oscar is talking about travel.")\
        .set_effect(lambda target: target.think("Ok, enough of travel. Now I'll talk about my favorite movies."))\
    
    world = TinyWorld("Test World", [oscar], interventions=[intervention])

    world.run(2)

    assert check_proposition(oscar, "Oscar was talking about travel, but then started talking about his favorite movies.", last_n = 5)

    # TODO

