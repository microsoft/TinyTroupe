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
from tinytroupe.validation import TinyPersonValidator

from testing_utils import *

def test_validate_person(setup):

    ##########################
    # Banker
    ##########################
    bank_spec =\
    """
    A large brazillian bank. It has a lot of branches and a large number of employees. It is facing a lot of competition from fintechs.
    """

    banker_spec =\
    """
    A vice-president of one of the largest brazillian banks. Has a degree in engineering and an MBA in finance.
    """
    
    banker_factory = TinyPersonFactory(bank_spec)
    banker = banker_factory.generate_person(banker_spec)

    banker_expectations =\
    """
    He/she is:
    - Wealthy
    - Very intelligent and ambitious
    - Has a lot of connections
    - Is in his 40s or 50s

    Tastes:
    - Likes to travel to other countries
    - Either read books, collect art or play golf
    - Enjoy only the best, most expensive, wines and food
    - Dislikes taxes and regulation

    Other notable traits:
    - Has some stress issues, and might be a bit of a workaholic
    - Deep knowledge of finance, economics and financial technology
    - Is a bit of a snob
    """
    banker_score, banker_justification = TinyPersonValidator.validate_person(banker, expectations=banker_expectations, include_agent_spec=False, max_content_length=None)
    print("Banker score: ", banker_score)
    print("Banker justification: ", banker_justification)

    assert banker_score > 0.5, f"Validation score is too low: {banker_score:.2f}"
    
    # Semantic verification: ensure the justification is actually about banking and finance
    assert proposition_holds(banker_justification + " - The validation discusses banking, finance, wealth, or business expertise")


    ##########################
    # Monk  
    ########################## 
    monastery_spec = "A remote monastery in the Himalayas, where only spiritual seekers are allowed."

    monk_spec =\
    """
    A poor buddhist monk living alone and isolated in a remote montain.
    """
    monk_spec_factory = TinyPersonFactory(monastery_spec)
    monk = monk_spec_factory.generate_person(monk_spec)
    
    monk_expectations =\
    """
    Some characteristics of this person:
    - Is very poor, and in fact do not seek money
    - Has no formal education, but is very wise
    - Is very calm and patient
    - Is very humble and does not seek attention
    - Honesty is a core value    
    """

    monk_score, monk_justification = TinyPersonValidator.validate_person(monk, expectations=monk_expectations, include_agent_spec=False, max_content_length=None)
    print("Monk score: ", monk_score)
    print("Monk justification: ", monk_justification)
          
    assert monk_score > 0.5, f"Validation score is too low: {monk_score:.2f}"
    
    # Semantic verification: ensure the justification is actually about spiritual or monastic qualities
    assert proposition_holds(monk_justification + " - The validation discusses spirituality, wisdom, humility, or monastic qualities")

    # Now, let's check the score for the monk with the wrong expectations! It has to be low!
    monk.clear_episodic_memory()
    wrong_expectations_score, wrong_expectations_justification = TinyPersonValidator.validate_person(monk, expectations=banker_expectations, include_agent_spec=False, max_content_length=None)

    print("Wrong expectations score: ", wrong_expectations_score)
    print("Wrong expectations justification: ", wrong_expectations_justification)
    assert wrong_expectations_score < 0.5, f"Validation score is too high: {wrong_expectations_score:.2f}"
    
    
    # Semantic verification: the justification should explain why a monk doesn't match banker expectations
    assert proposition_holds(wrong_expectations_justification + " - The validation explains mismatches or contrasts between monastic and banking characteristics")