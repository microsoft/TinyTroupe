import pytest

import sys
sys.path.append('../../tinytroupe/')
sys.path.append('../../')
sys.path.append('..')

from testing_utils import *

from tinytroupe.experimentation import ABRandomizer
from tinytroupe.experimentation import Proposition, check_proposition
from tinytroupe.examples import create_oscar_the_architect, create_oscar_the_architect_2, create_lisa_the_data_scientist, create_lisa_the_data_scientist_2


def test_randomize():
    randomizer = ABRandomizer()
    # run multiple times to make sure the randomization is properly tested
    for i in range(20):
        a, b = randomizer.randomize(i, "option1", "option2")

        if randomizer.choices[i] == (0, 1):
            assert (a, b) == ("option1", "option2")
        elif randomizer.choices[i] == (1, 0):
            assert (a, b) == ("option2", "option1")
        else:
            raise Exception(f"No randomization found for item {i}")

def test_derandomize():
    randomizer = ABRandomizer()

    # run multiple times to make sure the randomization is properly tested
    for i in range(20):
        a, b = randomizer.randomize(i, "option1", "option2")
        c, d = randomizer.derandomize(i, a, b)

        assert (c, d) == ("option1", "option2")

def test_derandomize_name():
    randomizer = ABRandomizer()

    for i in range(20):
        a, b = randomizer.randomize(i, "cats", "dogs")
        real_name = randomizer.derandomize_name(i, "A")

        if randomizer.choices[i] == (0, 1):
            # "Favorite pet? A: cats, B: dogs"
            # user selects "A"
            # user selected the control group 
            assert real_name == "control"
        elif randomizer.choices[i] == (1, 0):
            # "Favorite pet? A: dogs, B: cats"
            # user selects "A"
            # user selected the treatment group
            assert real_name == "treatment"
        else:
            raise Exception(f"No randomization found for item {i}")


def test_passtrough_name():
    randomizer = ABRandomizer(passtrough_name=["option3"])
    a, b = randomizer.randomize(0, "option1", "option2")
    real_name = randomizer.derandomize_name(0, "option3")

    assert real_name == "option3"

def test_proposition_with_tinyperson(setup):
    oscar = create_oscar_the_architect()
    oscar.listen_and_act("Tell me a bit about your travel preferences.")
    
    true_proposition = Proposition(claim="Oscar mentions his travel preferences.")
    assert true_proposition.check(target=oscar) == True

    false_proposition = Proposition(claim="Oscar writes a novel about how cats are better than dogs.")
    assert false_proposition.check(target=oscar) == False

def test_proposition_with_tinyperson_at_multiple_points(setup):
    oscar = create_oscar_the_architect()
    oscar.listen_and_act("Tell me a bit about your travel preferences.")
    
    proposition = Proposition(target=oscar, 
                              claim="Oscar talks about his travel preferences",
                              last_n=3)
    assert proposition.check() == True

    print(proposition.justification)
    print(proposition.confidence)
    assert len(proposition.justification) > 0
    assert proposition.confidence >= 0.0

    oscar.listen_and_act("Now let's change subjects. What do you work with?")
    assert proposition.check() == False # the _same_ proposition is no longer true, because Oscar changed subjects


def test_proposition_with_tinyworld(setup, focus_group_world):
    world = focus_group_world
    world.broadcast("Discuss the comparative advantages of dogs and cats.")
    world.run(2)

    true_proposition = Proposition(target=world, claim="There's a discussion about dogs and cats.")
    assert true_proposition.check() == True

    false_proposition = Proposition(target=world, claim="There's a discussion about whether porto wine vs french wine.")
    assert false_proposition.check() == False

def test_proposition_with_multiple_targets(setup):
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()

    oscar.listen_and_act("Tell me a bit about your travel preferences.")
    lisa.listen_and_act("Tell me about your data science projects.")

    targets = [oscar, lisa]

    true_proposition = Proposition(target=targets, claim="Oscar mentions his travel preferences and Lisa discusses data science projects.")
    assert true_proposition.check() == True

    false_proposition = Proposition(target=targets, claim="Oscar writes a novel about how cats are better than dogs.")
    assert false_proposition.check() == False

def test_proposition_class_method(setup):
    oscar = create_oscar_the_architect()
    oscar.listen_and_act("Tell me a bit about your travel preferences.")
    
    # notice that now we are using the class method, as a convenience
    assert check_proposition(target=oscar, claim="Oscar mentions his travel preferences.") == True
    assert check_proposition(oscar, "Oscar mentions his travel preferences.") == True

    assert check_proposition(target=oscar, claim="Oscar writes a novel about how cats are better than dogs.") == False
    assert check_proposition(oscar, "Oscar writes a novel about how cats are better than dogs.") == False

