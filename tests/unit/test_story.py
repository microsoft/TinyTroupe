import pytest
import logging
logger = logging.getLogger("tinytroupe")

import sys
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

from tinytroupe.steering import TinyStory

from testing_utils import *

def test_story_start(setup, focus_group_world):
    world = focus_group_world

    story = TinyStory(world)

    start = story.start_story()

    print("Story start: ", start)

    assert proposition_holds(f"The following could plausibly be the start of a story involving people named either Lisa, Marcos or Oscar: '{start}'"), f"Proposition is false according to the LLM."

def test_story_start_2(setup, focus_group_world):
    world = focus_group_world

    story = TinyStory(world)

    start = story.start_story(requirements="Start a story which is extremely crazy and out of this world.")

    print("Story start: ", start)

    assert proposition_holds(f"The following could plausibly be the start of a very crazy story involving people named either Lisa, Marcos or Oscar: '{start}'"), f"Proposition is false according to the LLM."

def test_story_continuation(setup, focus_group_world):
    world = focus_group_world

    story_beginning =\
          """
            You were vacationing in the beautiful city of Rio de Janeiro, Brazil. You were walking down the beach when
            the most unexpected thing happened: an Alien spaceship landed right in front of you. The door opened and a
            friendly Alien stepped out. The Alien introduced itself as Zog, and explained that it was on a mission to
            learn more about Earth's cultures. You were intrigued by this encounter and decided to help Zog in its mission.
          """

    world.broadcast(story_beginning)
    
    world.run(2)

    story = TinyStory(world)

    continuation = story.continue_story()

    print("Story continuation: ", continuation)

    assert proposition_holds(f"The following two text blocks could belong to the same story: \n BLOCK 1: '{story_beginning}' and \n BLOCK 2: '{continuation}'"), f"Proposition is false according to the LLM."

