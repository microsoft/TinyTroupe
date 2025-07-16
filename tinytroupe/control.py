"""
Simulation controlling mechanisms.
"""
import json
import os
import tempfile
import threading
import traceback

import tinytroupe
import tinytroupe.utils as utils

import uuid


import logging
logger = logging.getLogger("tinytroupe")

# to protect from race conditions when running in parallel
concurrent_execution_lock = threading.Lock()

class Simulation:

    STATUS_STOPPED = "stopped"
    STATUS_STARTED = "started"

    def __init__(self, id="default", cached_trace:list=None):
        self.id = id

        self.agents = []
        self.name_to_agent = {} # {agent_name: agent, ...}

        self.environments = []

        self.factories = [] # e.g., TinyPersonFactory instances
        self.name_to_factory = {} # {factory_name: factory, ...}

        self.name_to_environment = {} # {environment_name: environment, ...}
        self.status = Simulation.STATUS_STOPPED

        self.cache_path = f"./tinytroupe-{id}.cache.json" # default cache path
        
        # should we always automatically checkpoint at the every transaction?
        self.auto_checkpoint = False

        # whether there are changes not yet saved to the cache file
        self.has_unsaved_cache_changes = False

        # whether the agent is under a transaction or not, used for managing
        # simulation caching later
        self._under_transaction = {None: False}

        # whether the agent is under a parallel transactions segment or not, used for managing
        # simulation caching later
        self._under_parallel_transactions = False

        # Cache chain mechanism.
        # 
        # stores a list of simulation states.
        # Each state is a tuple (prev_node_hash, event_hash, event_output, state), where prev_node_hash is a hash of the previous node in this chain,
        # if any, event_hash is a hash of the event that triggered the transition to this state, if any, event_output is the output of the event,
        # if any, and state is the actual complete state that resulted.
        if cached_trace is None:
            self.cached_trace = []
        else:
            self.cached_trace = cached_trace
        
        self.cache_misses = 0
        self.cache_hits = 0

        # Execution chain mechanism.
        #
        # The actual, current, execution trace. Each state is a tuple (prev_node_hash, event_hash, state), where prev_node_hash is a hash 
        # of the previous node in this chain, if any, event_hash is a hash of the event that triggered the transition to this state, if any, 
        # event_output is the output of the event, if any, and state is the actual complete state that resulted.
        self.execution_trace = []

    def begin(self, cache_path:str=None, auto_checkpoint:bool=False):
        """
        Marks the start of the simulation being controlled.

        Args:
            cache_path (str): The path to the cache file. If not specified, 
                    defaults to the default cache path defined in the class.
            auto_checkpoint (bool, optional): Whether to automatically checkpoint at the end of each transaction. Defaults to False.
        """

        logger.debug(f"Starting simulation, cache_path={cache_path}, auto_checkpoint={auto_checkpoint}.")

        # local import to avoid circular dependencies
        from tinytroupe.agent import TinyPerson
        from tinytroupe.environment import TinyWorld
        from tinytroupe.factory.tiny_factory import TinyFactory
        from tinytroupe.factory.tiny_person_factory import TinyPersonFactory

        if self.status == Simulation.STATUS_STOPPED:
            self.status = Simulation.STATUS_STARTED
        else:
            raise ValueError("Simulation is already started.")
        
        if cache_path is not None:
            self.cache_path = cache_path
        
        # should we automatically checkpoint?
        self.auto_checkpoint = auto_checkpoint

        # clear the agents, environments and other simulated entities, we'll track them from now on
        TinyPerson.clear_agents()
        TinyWorld.clear_environments()
        TinyFactory.clear_factories()
        TinyPersonFactory.clear_factories()

        # All automated fresh ids will start from 0 again for this simulation
        utils.reset_fresh_id()

        # load the cache file, if any
        if self.cache_path is not None:
            self._load_cache_file(self.cache_path)

    def end(self):
        """
        Marks the end of the simulation being controlled.
        """
        logger.debug("Ending simulation.")
        if self.status == Simulation.STATUS_STARTED:
            self.status = Simulation.STATUS_STOPPED
            self.checkpoint()
        else:
            raise ValueError("Simulation is already stopped.")

    def checkpoint(self):
        """
        Saves current simulation trace to a file.
        """
        logger.debug("Checkpointing simulation state...")
        # save the cache file
        if self.has_unsaved_cache_changes:
            self._save_cache_file(self.cache_path)
        else:
            logger.debug("No unsaved cache changes to save to file.")

    def add_agent(self, agent):
        """
        Adds an agent to the simulation.
        """
        if agent.name in self.name_to_agent:
            raise ValueError(f"Agent names must be unique, but '{agent.name}' is already defined.")
        agent.simulation_id = self.id
        self.agents.append(agent)
        self.name_to_agent[agent.name] = agent

    
    def add_environment(self, environment):
        """
        Adds an environment to the simulation.
        """
        if environment.name in self.name_to_environment:
            raise ValueError(f"Environment names must be unique, but '{environment.name}' is already defined.")
        environment.simulation_id = self.id
        self.environments.append(environment)
        self.name_to_environment[environment.name] = environment
    
    def add_factory(self, factory):
        """
        Adds a factory to the simulation.
        """
        if factory.name in self.name_to_factory:
            raise ValueError(f"Factory names must be unique, but '{factory.name}' is already defined.")
        factory.simulation_id = self.id
        self.factories.append(factory)
        self.name_to_factory[factory.name] = factory

    ###################################################################################################
    # Cache and execution chain mechanisms
    ###################################################################################################
    def _execution_trace_position(self) -> int:
        """
        Returns the current position in the execution trace, or -1 if the execution trace is empty.
        """
        return len(self.execution_trace) - 1
    
    def _function_call_hash(self, function_name, *args, **kwargs) -> int:
        """
        Computes the hash of the given function call.
        """

        # if functions are passed as arguments to the function, there's the problem that their
        # string representation always changes due to memory position (e.g., <function my_function at 0x7f8d1a7b7d30>).
        # so we need to remove the changing suffix in those cases, while preserving the function name if it exists.
        
        # positional arguments
        # covnerts to a list of string representations first
        args_str = list(map(str, args))
        for i, arg in enumerate(args):
            if callable(arg):
                args_str[i] = arg.__name__
            
        # keyword arguments
        # converts to a list of string representations first
        kwargs_str = {k: str(v) for k, v in kwargs.items()}
        for k, v in kwargs.items():
            if callable(v):
                kwargs_str[k] = v.__name__
                
        # then, convert to a single string, to obtain a unique hash
        event = str((function_name, args_str, kwargs_str))

        # TODO actually compute a short hash of the event string, e.g., using SHA256 ?
        # event_hash = utils.custom_hash(event)

        return event

    def _skip_execution_with_cache(self):
        """
        Skips the current execution, assuming there's a cached state at the same position.
        """
        assert len(self.cached_trace) > self._execution_trace_position() + 1, "There's no cached state at the current execution position."
        
        self.execution_trace.append(self.cached_trace[self._execution_trace_position() + 1])
    
    def _is_transaction_event_cached(self, event_hash, parallel=False) -> bool:
        """
        Checks whether the given event hash matches the corresponding cached one, if any.
        If there's no corresponding cached state, returns True.
        """
        if not parallel:
            # there's cache that could be used
            if len(self.cached_trace) > self._execution_trace_position() + 1:
                if self._execution_trace_position() >= -1:
                    # here's a graphical depiction of the logic:
                    #
                    # Cache:         c0:(c_prev_node_hash_0, c_event_hash_0, _,  c_state_0) ------------------> c1:(c_prev_node_hash_1, c_event_hash_1,  _,  c_state_1) -> ...
                    # Execution:     e0:(e_prev_node_hash_0, e_event_hash_0, _,  e_state_0) -<being computed>-> e1:(e_prev_node_hash_1, <being computed>, <being computed>, <being computed>)
                    #   position = 0 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                    #
                    #   Must satisfy: 
                    #     - event_hash == c_event_hash_1
                    #     - hash(e0) == c_prev_node_hash_1
                    
                    try:
                        event_hash_match = event_hash == self.cached_trace[self._execution_trace_position() + 1][1]
                    except Exception as e:
                        logger.error(f"Error while checking event hash match: {e}")
                        event_hash_match = False                    
                    
                    prev_node_match = True # TODO implement real check

                    return event_hash_match and prev_node_match
                
                else: 
                    raise ValueError("Execution trace position is invalid, must be >= -1, but is ", self._execution_trace_position())
            
            else: # no cache to use
                return False
        
        else: # parallel
            if len(self.cached_trace) >= self._execution_trace_position():
                if self._execution_trace_position() >= 0:
                    # parallel stores ignore order, so we need to check instead whether the event hash is a key in the parallel store,
                    # regardless of the order of the events generated the data therein.

                    if isinstance(self.cached_trace[self._execution_trace_position()], dict):
                        event_hash_match = event_hash in self.cached_trace[self._execution_trace_position()].keys()
                    else:
                        event_hash_match = False

                    prev_node_match = True # TODO implement real check
                    
                    return event_hash_match and prev_node_match

                else:
                    raise ValueError("Execution trace position is invalid, must be >= 0, but is ", self._execution_trace_position())
    
    def _get_cached_parallel_value(self, event_hash, key):
        parallel_store = self.cached_trace[self._execution_trace_position()]
        value = parallel_store[event_hash][key] 
        return value
    
    def _drop_cached_trace_suffix(self):
        """
        Drops the cached trace suffix starting at the current execution trace position. This effectively
        refreshes the cache to the current execution state and starts building a new cache from there.
        """
        self.cached_trace = self.cached_trace[:self._execution_trace_position()+1]
        
    def _add_to_execution_trace(self, state: dict, event_hash: int, event_output, parallel=False):
        """
        Adds a state to the execution_trace list and computes the appropriate hash.
        The computed hash is compared to the hash of the cached trace at the same position,
        and if they don't match, the execution is aborted. Similarly, the event_hash is compared
        to the hash of the event in the cached trace at the same position, and if they don't match, the execution
        is aborted.
        """
        
        # Compute the hash of the previous execution pair, if any
        previous_hash = None

        if not parallel:
            # Create a tuple of (hash, state) and append it to the execution_trace list
            self.execution_trace.append((previous_hash, event_hash, event_output, state))
        else:
            with concurrent_execution_lock:
                # state is not stored in parallel segments, only outputs
                self.execution_trace[-1][event_hash] = {"prev_node_hash": previous_hash,
                                                        "encoded_output": event_output}
            


    def _add_to_cache_trace(self, state: dict, event_hash: int, event_output, parallel=False):
        """
        Adds a state to the cached_trace list and computes the appropriate hash.
        """
        # Compute the hash of the previous cached pair, if any
        previous_hash = None
        if self.cached_trace:
            previous_hash = utils.custom_hash(self.cached_trace[-1])
        
        if not parallel:
            # Create a tuple of (hash, state) and append it to the cached_trace list
            self.cached_trace.append((previous_hash, event_hash, event_output, state))
        else:
            with concurrent_execution_lock:
                # state is not stored in parallel segments, only outputs
                self.cached_trace[-1][event_hash] = {"prev_node_hash": previous_hash,
                                                    "encoded_output": event_output}


        self.has_unsaved_cache_changes = True
    
    def _load_cache_file(self, cache_path:str):
        """
        Loads the cache file from the given path.
        """
        try:
            self.cached_trace = json.load(open(cache_path, "r"))
        except FileNotFoundError:
            logger.info(f"Cache file not found on path: {cache_path}.")
            self.cached_trace = []
        
    def _save_cache_file(self, cache_path:str):
        """
        Saves the cache file to the given path. Always overwrites.
        """
        logger.debug(f"Now saving cache file to {cache_path}.")
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile('w', delete=False) as temp:
                json.dump(self.cached_trace, temp, indent=4)

            # Replace the original file with the temporary file
            os.replace(temp.name, cache_path)
        except Exception as e:
            traceback_string = ''.join(traceback.format_tb(e.__traceback__))
            logger.error(f"An error occurred while saving the cache file: {e}\nTraceback:\n{traceback_string}")

        self.has_unsaved_cache_changes = False

    

    ###################################################################################################
    # Transactional control
    ###################################################################################################

    #
    # Regular sequential transactions
    #
    def begin_transaction(self, id=None):
        """
        Starts a transaction.
        """
        with concurrent_execution_lock:
            self._under_transaction[id] = True
            self._clear_communications_buffers() # TODO <----------------------------------------------------------------
    
    def end_transaction(self, id=None):
        """
        Ends a transaction.
        """
        with concurrent_execution_lock:
            self._under_transaction[id] = False
    
    def is_under_transaction(self, id=None):
        """
        Checks if the agent is under a transaction.
        """
        with concurrent_execution_lock:
            return self._under_transaction.get(id, False)

    def _clear_communications_buffers(self):
        """
        Cleans the communications buffers of all agents and environments.
        """
        for agent in self.agents:
            agent.clear_communications_buffer()
        
        for environment in self.environments:
            environment.clear_communications_buffer()
    
    #
    # Parallel transactions
    #
    def begin_parallel_transactions(self):
        """
        Starts parallel transactions.
        """
        with concurrent_execution_lock:
            self._under_parallel_transactions = True
            # add a new parallel segment to the execution and cache traces
            self.execution_trace.append({}) 
            self.cached_trace.append({})
    
    def end_parallel_transactions(self):
        """
        Ends parallel transactions.
        """
        self._under_parallel_transactions = False

    def is_under_parallel_transactions(self):
        """
        Checks if the agent is under parallel transactions.
        """
        return self._under_parallel_transactions

    ###################################################################################################
    # Simulation state handling
    ###################################################################################################
    
    def _encode_simulation_state(self) -> dict:
        """
        Encodes the current simulation state, including agents, environments, and other
        relevant information.
        """
        state = {}

        # Encode agents
        state["agents"] = []
        for agent in self.agents:
            state["agents"].append(agent.encode_complete_state())
        
        # Encode environments
        state["environments"] = []
        for environment in self.environments:
            state["environments"].append(environment.encode_complete_state())
        
        # Encode factories
        state["factories"] = []
        for factory in self.factories:
            state["factories"].append(factory.encode_complete_state())
                
        return state
        
    def _decode_simulation_state(self, state: dict):
        """
        Decodes the given simulation state, including agents, environments, and other
        relevant information.

        Args:
            state (dict): The state to decode.
        """
        # local import to avoid circular dependencies
        from tinytroupe.agent import TinyPerson
        from tinytroupe.environment import TinyWorld

        logger.debug(f"Decoding simulation state: {state['factories']}")
        logger.debug(f"Registered factories: {self.name_to_factory}")
        logger.debug(f"Registered agents: {self.name_to_agent}")
        logger.debug(f"Registered environments: {self.name_to_environment}")

        # Decode factories
        for factory_state in state["factories"]:
            factory = self.name_to_factory[factory_state["name"]]
            factory.decode_complete_state(factory_state)

        # Decode environments
        ###self.environments = []
        for environment_state in state["environments"]:
            try:
                environment = self.name_to_environment[environment_state["name"]]
                environment.decode_complete_state(environment_state)
                if TinyWorld.communication_display:
                    environment.pop_and_display_latest_communications()

            except Exception as e:
                raise ValueError(f"Environment {environment_state['name']} is not in the simulation, thus cannot be decoded there.") from e

        # Decode agents (if they were not already decoded by the environment)
        ####self.agents = []
        for agent_state in state["agents"]:
            try:
                agent = self.name_to_agent[agent_state["name"]]
                agent.decode_complete_state(agent_state)
                
                # The agent has not yet been decoded because it is not in any environment. So, decode it.
                if agent.environment is None:
                    if TinyPerson.communication_display:
                        agent.pop_and_display_latest_communications()
            except Exception as e:
                raise ValueError(f"Agent {agent_state['name']} is not in the simulation, thus cannot be decoded there.") from e        


class Transaction:

    def __init__(self, obj_under_transaction, simulation, function, *args, **kwargs):
        # local import to avoid circular dependencies
        from tinytroupe.agent import TinyPerson
        from tinytroupe.environment import TinyWorld
        from tinytroupe.factory.tiny_factory import TinyFactory

        self.obj_under_transaction = obj_under_transaction
        self.simulation = simulation
        self.function_name = function.__name__
        self.function = function
        self.args = args
        self.kwargs = kwargs    

        #
        # If we have an ongoing simulation, set the simulation id of the object under transaction if it is not already set.
        #
        if simulation is not None:
            if hasattr(obj_under_transaction, 'simulation_id') and obj_under_transaction.simulation_id is not None:
                if obj_under_transaction.simulation_id != simulation.id:
                    raise ValueError(f"Object {obj_under_transaction} is already captured by a different simulation (id={obj_under_transaction.simulation_id}), \
                                    and cannot be captured by simulation id={simulation.id}.")
                
                logger.debug(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Object {obj_under_transaction} is already captured by simulation {simulation.id}.")
            else:
                # if is a TinyPerson, add the agent to the simulation
                if isinstance(obj_under_transaction, TinyPerson):
                    simulation.add_agent(obj_under_transaction)
                    logger.debug(f">>>>>>>>>>>>>>>>>>>>>>> Added agent {obj_under_transaction} to simulation {simulation.id}.")

                # if is a TinyWorld, add the environment to the simulation
                elif isinstance(obj_under_transaction, TinyWorld):
                    simulation.add_environment(obj_under_transaction)
                
                # if is a TinyFactory, add the factory to the simulation
                elif isinstance(obj_under_transaction, TinyFactory):
                    simulation.add_factory(obj_under_transaction)
                    logger.debug(f">>>>>>>>>>>>>>>>>>>>>>> Added factory {obj_under_transaction} to simulation {simulation.id}.")

                else:
                    raise ValueError(f"Object {obj_under_transaction} (type = {type(obj_under_transaction)}) is not a TinyPerson or TinyWorld instance, and cannot be captured by the simulation.")
                
        
    def execute(self, begin_parallel=False, parallel_id=None):

        output = None

        # Transaction caching will only operate if there is a simulation and it is started
        if self.simulation is None or self.simulation.status == Simulation.STATUS_STOPPED:
            # Compute the function and return it, no caching, since the simulation is not started
            output = self.function(*self.args, **self.kwargs)
        
        elif self.simulation.status == Simulation.STATUS_STARTED:
            # Compute the event hash
            event_hash = self.simulation._function_call_hash(self.function_name, *self.args, **self.kwargs)

            # Sequential and parallel transactions are handled in different ways
            if begin_parallel:
                self.simulation.begin_parallel_transactions()
            
            # CACHED? Check if the event hash is in the cache
            if self.simulation._is_transaction_event_cached(event_hash, 
                                                            parallel=self.simulation.is_under_parallel_transactions()):
                self.simulation.cache_hits += 1

                # Restore the full state and return the cached output
                logger.info(f"Skipping execution of {self.function_name} with args {self.args} and kwargs {self.kwargs} because it is already cached.")

                # SEQUENTIAL
                if not self.simulation.is_under_parallel_transactions():
                    
                    self.simulation._skip_execution_with_cache()
                    state = self.simulation.cached_trace[self.simulation._execution_trace_position()][3] # state
                    self.simulation._decode_simulation_state(state)
                    
                    # Output encoding/decoding is used to preserve references to TinyPerson and TinyWorld instances
                    # mainly. Scalar values (int, float, str, bool) and composite values (list, dict) are 
                    # encoded/decoded as is.
                    encoded_output = self.simulation.cached_trace[self.simulation._execution_trace_position()][2] # output
                    output = self._decode_function_output(encoded_output)
                
                # PARALLEL
                else: # is under parallel transactions

                    # in parallel segments, state is not restored, only outputs
                    encoded_output = self.simulation._get_cached_parallel_value(event_hash, "encoded_output")
                    output = self._decode_function_output(encoded_output)

            else: # not cached

                if not begin_parallel:
                    # in case of beginning a parallel segment, we don't want to count it as a cache miss,
                    # since the segment itself will not be cached, but rather the events within it.
                    self.simulation.cache_misses += 1
                
                if not self.simulation.is_under_transaction(id=parallel_id) and not begin_parallel:
                    
                    # BEGIN SEQUENTIAL TRANSACTION ###############################################################
                    #
                    # if this is the beginning of a parallel segment, we don't need to begin a transaction, since
                    # we want to allow additional transactions within the parallel segment (i.e., one-level reentrancy).
                    if not begin_parallel:
                        self.simulation.begin_transaction(id=parallel_id)

                    # Compute the function and encode the relevant output and simulation state
                    output = self.function(*self.args, **self.kwargs)
                    self._save_output_with_simulation_state(event_hash, output)

                    # END TRANSACTION #################################################################
                    if not begin_parallel:
                        self.simulation.end_transaction(id=parallel_id)
                    
                else: # already under transaction (thus, now a reentrant transaction) OR beginning a parallel segment

                    # NOTES: 
                    #
                    #   - Reentrant sequential transactions are not cached, since what matters is the final result of
                    #     the top-level transaction.
                    #
                    #   - The event that starts the parallel transactions segment WILL NOT itself be cached, since
                    #     it is not part of the parallel segment, but rather the beginning of it. This event will be
                    #     reconstructed during runtime from the parallel events within the segment.

                    output = self.function(*self.args, **self.kwargs)

            if begin_parallel:
                self.simulation.end_parallel_transactions()

                # execute an ad-hoc Transaction to save the simulation state AFTER the parallel segment is done.
                Transaction(self.obj_under_transaction, self.simulation, lambda: True).execute(begin_parallel=False, parallel_id=parallel_id)

        else:
            raise ValueError(f"Simulation status is invalid at this point: {self.simulation.status}")

        # Checkpoint if needed
        logger.debug(f"Will attempt to checkpoint simulation state after transaction execution.")
        if self.simulation is not None and self.simulation.auto_checkpoint:
            logger.debug("Auto-checkpointing simulation state after transaction execution.")
            self.simulation.checkpoint()

        # after all the transaction is done, return the output - the client will never know about all the complexity we've
        # gone through to get here.
        return output
    
    def _save_output_with_simulation_state(self, event_hash, output):
        encoded_output = self._encode_function_output(output)
        state = self.simulation._encode_simulation_state()

        # immediately drop the cached trace suffix, since we are starting a new execution from this point on.
        # in the case of parallel transactions, this will drop everything _after_ the current parallel segment
        # (which itself occupies one position only, with a dictionary of event hashes and their outputs).
        self.simulation._drop_cached_trace_suffix()

        # Cache the result and update the current execution trace. If this is a parallel transaction, the
        # cache and execution traces will be updated in a different way.
        self.simulation._add_to_cache_trace(state, event_hash, encoded_output, 
                                            parallel=self.simulation.is_under_parallel_transactions())
        self.simulation._add_to_execution_trace(state, event_hash, encoded_output, 
                                                parallel=self.simulation.is_under_parallel_transactions())

  
    def _encode_function_output(self, output) -> dict:
        """
        Encodes the given function output.
        """
        # local import to avoid circular dependencies
        from tinytroupe.agent import TinyPerson
        from tinytroupe.environment import TinyWorld
        from tinytroupe.factory.tiny_factory import TinyFactory

        # if the output is a supported object, encode it
        if output is None:
            return None
        elif isinstance(output, TinyPerson):
            return {"type": "TinyPersonRef", "name": output.name}
        elif isinstance(output, TinyWorld):
            return {"type": "TinyWorldRef", "name": output.name}
        elif isinstance(output, TinyFactory):
            return {"type": "TinyFactoryRef", "name": output.name}
        elif isinstance(output, list):
            encoded_list = []
            for item in output:
                if isinstance(item, TinyPerson):
                    encoded_list.append({"type": "TinyPersonRef", "name": item.name})
                elif isinstance(item, TinyWorld):
                    encoded_list.append({"type": "TinyWorldRef", "name": item.name})
                elif isinstance(item, TinyFactory):
                    encoded_list.append({"type": "TinyFactoryRef", "name": item.name})
                else:
                    encoded_list.append({"type": "JSON", "value": item})
            return {"type": "List", "value": encoded_list}
        elif isinstance(output, (int, float, str, bool, dict, tuple)):
            return {"type": "JSON", "value": output}
        else:
            raise ValueError(f"Unsupported output type: {type(output)}")

    def _decode_function_output(self, encoded_output: dict):
        """
        Decodes the given encoded function output.
        """
        # local import to avoid circular dependencies
        from tinytroupe.agent import TinyPerson
        from tinytroupe.environment import TinyWorld
        from tinytroupe.factory.tiny_factory import TinyFactory

        if encoded_output is None:
            return None
        elif encoded_output["type"] == "TinyPersonRef":
            return TinyPerson.get_agent_by_name(encoded_output["name"])
        elif encoded_output["type"] == "TinyWorldRef":
            return TinyWorld.get_environment_by_name(encoded_output["name"])
        elif encoded_output["type"] == "TinyFactoryRef":
            return TinyFactory.get_factory_by_name(encoded_output["name"])
        elif encoded_output["type"] == "List":
            decoded_list = []
            for item in encoded_output["value"]:
                if item["type"] == "TinyPersonRef":
                    decoded_list.append(TinyPerson.get_agent_by_name(item["name"]))
                elif item["type"] == "TinyWorldRef":
                    decoded_list.append(TinyWorld.get_environment_by_name(item["name"]))
                elif item["type"] == "TinyFactoryRef":
                    decoded_list.append(TinyFactory.get_factory_by_name(item["name"]))
                else:
                    decoded_list.append(item["value"])
            return decoded_list
        elif encoded_output["type"] == "JSON":
            return encoded_output["value"]
        else:
            raise ValueError(f"Unsupported output type: {encoded_output['type']}")

def transactional(parallel=False):
    """
    A helper decorator that makes a function simulation-transactional.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            obj_under_transaction = args[0]
            simulation = current_simulation()
            obj_sim_id = obj_under_transaction.simulation_id if hasattr(obj_under_transaction, 'simulation_id') else None

            logger.debug(f"-----------------------------------------> Transaction: {func.__name__} with args {args[1:]} and kwargs {kwargs} under simulation {obj_sim_id}, parallel={parallel}.")
            
            parallel_id = str(threading.current_thread())
            
            transaction = Transaction(obj_under_transaction, simulation, func, *args, **kwargs)
            result = transaction.execute(begin_parallel=parallel, parallel_id=parallel_id)
            
            return result
        
        return wrapper
    
    return decorator

class SkipTransaction(Exception):
    pass

class CacheOutOfSync(Exception):
    """
    Raised when a cached and the corresponding freshly executed elements are out of sync.
    """
    pass

class ExecutionCached(Exception):
    """
    Raised when a proposed execution is already cached.
    """
    pass


###################################################################################################
# Convenience functions
###################################################################################################

def reset():
    """	
    Resets the entire simulation control state.
    """
    global _current_simulations, _current_simulation_id
    _current_simulations = {"default": None}

    # TODO Currently, only one simulation can be started at a time. In future versions, this should be
    #      changed to allow multiple simulations to be started at the same time, e.g., for fast
    #      analyses through parallelization.
    _current_simulation_id = None

def _simulation(id="default"):
    global _current_simulations
    if _current_simulations[id] is None:
        _current_simulations[id] = Simulation()
    
    return _current_simulations[id]

def begin(cache_path=None, id="default", auto_checkpoint=False):
    """
    Marks the start of the simulation being controlled.
    """
    global _current_simulation_id
    if _current_simulation_id is None:
        _simulation(id).begin(cache_path, auto_checkpoint)
        _current_simulation_id = id
    else:
        raise ValueError(f"Simulation is already started under id {_current_simulation_id}. Currently only one simulation can be started at a time.")   
    
def end(id="default"):
    """
    Marks the end of the simulation being controlled.
    """
    global _current_simulation_id
    _simulation(id).end()
    _current_simulation_id = None

def checkpoint(id="default"):
    """
    Saves current simulation state.
    """
    _simulation(id).checkpoint()

def current_simulation():
    """
    Returns the current simulation.
    """
    global _current_simulation_id
    if _current_simulation_id is not None:
        return _simulation(_current_simulation_id)
    else:
        return None

def cache_hits(id="default"):
    """
    Returns the number of cache hits.
    """
    return _simulation(id).cache_hits

def cache_misses(id="default"):
    """
    Returns the number of cache misses.
    """
    return _simulation(id).cache_misses
    
reset() # initialize the control state