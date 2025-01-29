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

    oscar.think("I am terribly sad, as a dear friend has died. I'm going now to verbalize my sadness.")
    oscar.act()

    assert check_proposition(oscar, "Oscar is talking about something sad or unfortunate.", last_n=3)

    intervention = \
        Intervention(oscar)\
        .set_textual_precondition("Oscar is not very happy.")\
        .set_effect(lambda target: target.think("Enough sadness. I will now talk about something else that makes me happy."))
    
    world = TinyWorld("Test World", [oscar], interventions=[intervention])

    world.run(2)

    assert check_proposition(oscar, "Oscar is talking about something that brings joy or happiness to him.", last_n = 3)

    # TODO

