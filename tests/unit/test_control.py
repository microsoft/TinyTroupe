import pytest
import os

import sys
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')


from tinytroupe.examples import create_oscar_the_architect, create_lisa_the_data_scientist
from tinytroupe.agent import TinyPerson, TinyToolUse
from tinytroupe.environment import TinyWorld
from tinytroupe.control import Simulation
import tinytroupe.control as control
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.enrichment import TinyEnricher
from tinytroupe.extraction import ArtifactExporter
from tinytroupe.tools import TinyWordProcessor

import logging
logger = logging.getLogger("tinytroupe")

import importlib

from testing_utils import *

def test_begin_checkpoint_end_with_agent_only(setup):
    # erase the file if it exists
    remove_file_if_exists("control_test.cache.json")

    control.reset()
    
    assert control._current_simulations["default"] is None, "There should be no simulation running at this point."

    # erase the file if it exists
    remove_file_if_exists("control_test.cache.json")

    control.begin("control_test.cache.json")
    assert control._current_simulations["default"].status == Simulation.STATUS_STARTED, "The simulation should be started at this point."


    exporter = ArtifactExporter(base_output_folder="./synthetic_data_exports_3/")
    enricher = TinyEnricher()
    tooluse_faculty = TinyToolUse(tools=[TinyWordProcessor(exporter=exporter, enricher=enricher)])

    agent_1 = create_oscar_the_architect()
    agent_1.add_mental_faculties([tooluse_faculty])
    agent_1.define("age", 19)
    agent_1.define("nationality", "Brazilian")

    agent_2 = create_lisa_the_data_scientist()
    agent_2.add_mental_faculties([tooluse_faculty])
    agent_2.define("age", 80)
    agent_2.define("nationality", "Argentinian")

    assert control._current_simulations["default"].cached_trace is not None, "There should be a cached trace at this point."
    assert control._current_simulations["default"].execution_trace is not None, "There should be an execution trace at this point."

    control.checkpoint()

    agent_1.listen_and_act("How are you doing?")
    agent_2.listen_and_act("What's up?")

    # check if the file was created
    assert os.path.exists("control_test.cache.json"), "The checkpoint file should have been created."

    control.end()

    assert control._current_simulations["default"].status == Simulation.STATUS_STOPPED, "The simulation should be ended at this point."

def test_begin_checkpoint_end_with_world(setup):
    # erase the file if it exists
    remove_file_if_exists("control_test_world.cache.json")

    control.reset()
    
    assert control._current_simulations["default"] is None, "There should be no simulation running at this point."

    control.begin("control_test_world.cache.json")
    assert control._current_simulations["default"].status == Simulation.STATUS_STARTED, "The simulation should be started at this point."

    world = TinyWorld("Test World", [create_oscar_the_architect(), create_lisa_the_data_scientist()])

    world.make_everyone_accessible()

    assert control._current_simulations["default"].cached_trace is not None, "There should be a cached trace at this point."
    assert control._current_simulations["default"].execution_trace is not None, "There should be an execution trace at this point."

    world.run(2)

    control.checkpoint()

    # check if the file was created
    assert os.path.exists("control_test_world.cache.json"), "The checkpoint file should have been created."

    control.end()

    assert control._current_simulations["default"].status == Simulation.STATUS_STOPPED, "The simulation should be ended at this point."


def test_begin_checkpoint_end_with_factory(setup):
    # erase the file if it exists
    remove_file_if_exists("control_test_personfactory.cache.json")

    control.reset()

    def aux_simulation_to_repeat(iteration, verbose=False):
        control.reset()
    
        assert control._current_simulations["default"] is None, "There should be no simulation running at this point."

        control.begin("control_test_personfactory.cache.json")
        assert control._current_simulations["default"].status == Simulation.STATUS_STARTED, "The simulation should be started at this point."    
        
        factory = TinyPersonFactory("We are interested in experts in the production of the traditional Gazpacho soup.")

        assert control._current_simulations["default"].cached_trace is not None, "There should be a cached trace at this point."
        assert control._current_simulations["default"].execution_trace is not None, "There should be an execution trace at this point."

        agent = factory.generate_person("A Brazilian tourist who learned about Gazpaccho in a trip to Spain.")

        assert control._current_simulations["default"].cached_trace is not None, "There should be a cached trace at this point."
        assert control._current_simulations["default"].execution_trace is not None, "There should be an execution trace at this point."

        control.checkpoint()

        # check if the file was created
        assert os.path.exists("control_test_personfactory.cache.json"), "The checkpoint file should have been created."

        control.end()
        assert control._current_simulations["default"].status == Simulation.STATUS_STOPPED, "The simulation should be ended at this point."

        if verbose:
            logger.debug(f"###################################################################################### Sim Iteration:{iteration}")
            logger.debug(f"###################################################################################### Agent persona configs:{agent._persona}")

        return agent

    assert control.cache_misses() == 0, "There should be no cache misses in this test."
    assert control.cache_hits() == 0, "There should be no cache hits here"

    # FIRST simulation ########################################################
    agent_1 = aux_simulation_to_repeat(1, verbose=True)
    age_1 = agent_1.get("age")
    nationality_1 = agent_1.get("nationality")
    minibio_1 = agent_1.minibio()
    print("minibio_1 =", minibio_1)


    # SECOND simulation ########################################################
    logger.debug(">>>>>>>>>>>>>>>>>>>>>>>>>> Second simulation...")
    agent_2 = aux_simulation_to_repeat(2, verbose=True)
    age_2 = agent_2.get("age")
    nationality_2 = agent_2.get("nationality")
    minibio_2 = agent_2.minibio()
    print("minibio_2 =", minibio_2)

    assert control.cache_misses() == 0, "There should be no cache misses in this test."
    assert control.cache_hits() > 0, "There should be cache hits here."

    assert age_1 == age_2, "The age should be the same in both simulations."
    assert nationality_1 == nationality_2, "The nationality should be the same in both simulations."
    assert minibio_1 == minibio_2, "The minibio should be the same in both simulations."

    #
    # let's also check the contents of the cache file, as raw text, not dict
    #
    with open("control_test_personfactory.cache.json", "r") as f:
        cache_contents = f.read()

    assert "'_aux_model_call'" in cache_contents, "The cache file should contain the '_aux_model_call' call."
    assert "'_setup_agent'" in cache_contents, "The cache file should contain the '_setup_agent' call."
    assert "'define'" not in cache_contents, "The cache file should not contain the 'define' methods, as these are reentrant."
    assert "'define_several'" not in cache_contents, "The cache file should not contain the 'define_several' methods, as these are reentrant."

        
