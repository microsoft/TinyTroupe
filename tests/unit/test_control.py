import pytest
import os

import sys
sys.path.append('../../tinytroupe/')
sys.path.append('../../')
sys.path.append('..')


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


# Test-specific TinyPerson subclass with simple transactional methods
class CacheTestPerson(TinyPerson):
    def __init__(self, name="CacheTestAgent", **kwargs):
        super().__init__(name=name, **kwargs)
        self._value = 0
        self.call_count = 0

    @control.transactional
    def simple_method(self, arg1, kwarg1="default"):
        self.call_count += 1
        # self._value += arg1 if isinstance(arg1, int) else len(str(arg1)) # Remove state change for this test method
        # Ensure the return value is pickleable and comparable
        return {"processed_arg1": arg1, "processed_kwarg1": kwarg1} # Removed current_value from output

    @control.transactional
    def method_with_dict_arg(self, data_dict: dict):
        self.call_count += 1
        # Return a sorted tuple of items to ensure consistent output for comparison
        return tuple(sorted(data_dict.items()))

    @control.transactional
    def method_with_list_arg(self, data_list: list):
        self.call_count += 1
        return len(data_list) # Simple return

    @control.transactional
    def method_with_custom_obj_arg(self, custom_obj: 'SimpleCustomObject'):
        self.call_count += 1
        return custom_obj.x + custom_obj.y

class SimpleCustomObject:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"SimpleCustomObject(x={self.x}, y={self.y})"

    def __repr__(self):
        return f"SimpleCustomObject(x={self.x}, y={self.y})"

    def __eq__(self, other):
        if not isinstance(other, SimpleCustomObject):
            return NotImplemented
        return self.x == other.x and self.y == other.y

def test_cache_key_generation_and_hits(setup, caplog):
    control.reset()
    cache_file = "test_cache_key_gen.cache.json"
    remove_file_if_exists(cache_file)

    control.begin(cache_path=cache_file, id="cache_test_sim") # Use a specific sim ID
    sim_instance = control.current_simulation()
    assert sim_instance is not None

    # Instantiate a Simulation directly to test its _function_call_hash method
    # This avoids complexities of the transactional decorator and TinyPerson state changes.
    sim_for_hash_test = Simulation(id="hash_test_sim")

    # Test 1: Simple primitives
    key1 = sim_for_hash_test._function_call_hash("method_name", 1, "hello", kwarg1="val1")
    key2 = sim_for_hash_test._function_call_hash("method_name", 1, "hello", kwarg1="val1")
    key3 = sim_for_hash_test._function_call_hash("method_name", 2, "hello", kwarg1="val1") # Different arg
    key4 = sim_for_hash_test._function_call_hash("method_name", 1, "world", kwarg1="val1") # Different arg
    key5 = sim_for_hash_test._function_call_hash("method_name", 1, "hello", kwarg1="val2") # Different kwarg
    key6 = sim_for_hash_test._function_call_hash("method_name_diff", 1, "hello", kwarg1="val1") # Different method name

    assert key1 == key2
    assert key1 != key3
    assert key1 != key4
    assert key1 != key5
    assert key1 != key6

    # Test 2: Dictionaries - key order in kwargs, and dicts as args
    # For kwargs, sorted_kwargs in _function_call_hash should handle order.
    key_dict_kw1 = sim_for_hash_test._function_call_hash("method_dict_kw", kwarg_dict={"a": 1, "b": 2})
    key_dict_kw2 = sim_for_hash_test._function_call_hash("method_dict_kw", kwarg_dict={"b": 2, "a": 1})
    assert key_dict_kw1 == key_dict_kw2

    # For dicts as positional args, pickle itself is generally consistent for same-content dicts.
    dict_arg1 = {"x": 10, "y": 20}
    dict_arg2 = {"y": 20, "x": 10}
    key_dict_arg1 = sim_for_hash_test._function_call_hash("method_dict_arg", dict_arg1)
    key_dict_arg2 = sim_for_hash_test._function_call_hash("method_dict_arg", dict_arg2)
    assert key_dict_arg1 == key_dict_arg2

    key_dict_arg3 = sim_for_hash_test._function_call_hash("method_dict_arg", {"x": 10, "y": 30}) # Different content
    assert key_dict_arg1 != key_dict_arg3

    # Test 3: Lists and Tuples - order matters
    key_list1 = sim_for_hash_test._function_call_hash("method_list", [1, 2, 3])
    key_list2 = sim_for_hash_test._function_call_hash("method_list", [1, 2, 3])
    key_list3 = sim_for_hash_test._function_call_hash("method_list", [3, 2, 1]) # Different order
    assert key_list1 == key_list2
    assert key_list1 != key_list3

    key_tuple1 = sim_for_hash_test._function_call_hash("method_tuple", (1, 2, 3))
    key_tuple2 = sim_for_hash_test._function_call_hash("method_tuple", (1, 2, 3))
    key_tuple3 = sim_for_hash_test._function_call_hash("method_tuple", (3, 2, 1))
    assert key_tuple1 == key_tuple2
    assert key_tuple1 != key_tuple3

    # Test 4: Custom objects
    custom_obj1 = SimpleCustomObject(x=1, y="a")
    custom_obj2 = SimpleCustomObject(x=1, y="a") # Identical content
    custom_obj3 = SimpleCustomObject(x=2, y="b") # Different content

    key_custom1 = sim_for_hash_test._function_call_hash("method_custom", custom_obj1)
    key_custom2 = sim_for_hash_test._function_call_hash("method_custom", custom_obj2)
    key_custom3 = sim_for_hash_test._function_call_hash("method_custom", custom_obj3)
    assert key_custom1 == key_custom2
    assert key_custom1 != key_custom3

    # Test 5: Nested structures
    nested1 = {"list": [1, SimpleCustomObject(10,20)], "val": "test"}
    nested2 = {"list": [1, SimpleCustomObject(10,20)], "val": "test"}
    nested3 = {"list": [1, SimpleCustomObject(10,30)], "val": "test"} # Inner obj different

    key_nested1 = sim_for_hash_test._function_call_hash("method_nested", nested_data=nested1)
    key_nested2 = sim_for_hash_test._function_call_hash("method_nested", nested_data=nested2)
    key_nested3 = sim_for_hash_test._function_call_hash("method_nested", nested_data=nested3)
    assert key_nested1 == key_nested2
    assert key_nested1 != key_nested3

    # Test 6: Fallback test for unpickleable objects
    unpickleable_lambda = lambda x: x
    original_pickle_dumps = control.pickle.dumps

    # Mock pickle.dumps to raise an error for this specific test section
    def mock_pickle_raiser_for_lambda_test(obj_to_pickle, protocol):
        # Check if the object to pickle contains our specific lambda
        # This is a bit heuristic; depends on the structure passed to pickle.dumps
        if isinstance(obj_to_pickle, tuple) and len(obj_to_pickle) > 1: # (name, args, sorted_kwargs)
            args_tuple = obj_to_pickle[1]
            if args_tuple and callable(args_tuple[0]) and args_tuple[0].__name__ == "<lambda>":
                raise TypeError("Mocked Unpickleable Lambda")
        return original_pickle_dumps(obj_to_pickle, protocol=protocol)

    control.pickle.dumps = mock_pickle_raiser_for_lambda_test
    caplog.clear()
    # Set level to DEBUG to ensure both ERROR and WARNING are captured for checking
    with caplog.at_level(logging.DEBUG):
        key_unpickleable1 = sim_for_hash_test._function_call_hash("method_lambda", unpickleable_lambda, kwarg1="test_fallback")

        error_log_found = any(
            "Error pickling/hashing event" in rec.message and rec.levelname == 'ERROR' for rec in caplog.records
        )
        error_records = [rec for rec in caplog.records if rec.levelname == 'ERROR']
        warning_records = [rec for rec in caplog.records if rec.levelname == 'WARNING']

        assert len(error_records) >= 1, "Expected at least one error log for pickling failure."
        assert "Error pickling/hashing event" in error_records[0].message

        assert len(warning_records) == 1, f"Expected 1 warning log, got {len(warning_records)}. Full log: {caplog.text}"
        assert "FALLBACK_CACHE_KEY_USED" in warning_records[0].message
        assert "method_lambda" in key_unpickleable1 # Check it's a hash of string rep (contains method name at least)

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        key_unpickleable2 = sim_for_hash_test._function_call_hash("method_lambda", lambda y: y*2, kwarg1="test_fallback")
        
        error_records_2 = [rec for rec in caplog.records if rec.levelname == 'ERROR']
        warning_records_2 = [rec for rec in caplog.records if rec.levelname == 'WARNING']

        assert len(error_records_2) >= 1, "Expected at least one error log for pickling failure (call 2)."
        assert "Error pickling/hashing event" in error_records_2[0].message

        assert len(warning_records_2) == 1, f"Expected 1 warning log (call 2), got {len(warning_records_2)}. Full log: {caplog.text}"
        assert "FALLBACK_CACHE_KEY_USED" in warning_records_2[0].message
        assert key_unpickleable1 != key_unpickleable2

    control.pickle.dumps = original_pickle_dumps # Restore

    # No need for control.begin/end or cache file for direct hash testing.
    # control.end()
    # remove_file_if_exists(cache_file) # No cache file used
