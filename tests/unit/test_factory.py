import os
import sys

import pytest

sys.path.append("../../tinytroupe/")
sys.path.append("../../")
sys.path.append("..")


from testing_utils import *

import tinytroupe.control as control
from tinytroupe.control import Simulation
from tinytroupe.examples import create_oscar_the_architect
from tinytroupe.factory import TinyPersonFactory


def test_generate_person(setup):
    banker_spec = """
    A vice-president of one of the largest brazillian banks. Has a degree in engineering and an MBA in finance. 
    Is facing a lot of pressure from the board of directors to fight off the competition from the fintechs.    
    """

    banker_factory = TinyPersonFactory(banker_spec)

    banker = banker_factory.generate_person()

    minibio = banker.minibio()

    assert proposition_holds(
        f"The following is an acceptable short description for someone working in banking: '{minibio}'"
    ), f"Proposition is false according to the LLM."
