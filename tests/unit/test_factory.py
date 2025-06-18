import pytest
import os

import sys
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

from tinytroupe.examples import create_oscar_the_architect
from tinytroupe.control import Simulation
import tinytroupe.control as control
from tinytroupe.factory import TinyPersonFactory

from testing_utils import *

def test_generate_person(setup):
    bank_spec =\
    """
    A large brazillian bank. It has a lot of branches and a large number of employees. It is facing a lot of competition from fintechs.
    """

    banker_spec =\
    """
    A vice-president of one of the largest brazillian banks. Has a degree in engineering and an MBA in finance.
    """
    
    banker_factory = TinyPersonFactory(context=bank_spec)
    banker = banker_factory.generate_person(banker_spec)
    minibio = banker.minibio()

    assert proposition_holds(f"The following is an acceptable short description for someone working in banking: '{minibio}'"), f"Proposition is false according to the LLM."


def test_generate_people(setup):
    general_context = "We are performing some market research, and in that examining the whole of the American population."
    sampling_space_description = "A uniform random representative sample of people from the American population."

    factory = TinyPersonFactory(sampling_space_description=sampling_space_description, total_population_size=50, context=general_context)
    people = factory.generate_people(10, agent_particularities="A random person from the American population.", verbose=True)

    assert len(people) == 10
    for person in people:
        assert person.get("nationality") == "American"
        assert person.get("age") > 0
        assert person.name is not None


def test_generate_people_2(setup):
    general_context = "We are performing some market research, and in that examining the whole of the American population."
    sampling_space_description = "A uniform random representative sample of people from the American population."

    factory = TinyPersonFactory(sampling_space_description=sampling_space_description, total_population_size=20, context=general_context)
    people = factory.generate_people(20, agent_particularities="A random person from the American population.", verbose=True)

    assert len(people) == 20
    for person in people:
        assert person.get("nationality") == "American"
        assert person.get("age") > 0
        assert person.name is not None

