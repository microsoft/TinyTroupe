from tinytroupe.environment import logger, default

import copy
from datetime import datetime, timedelta
import textwrap
import random
import concurrent.futures

from tinytroupe.agent import *
from tinytroupe.utils import name_or_empty, pretty_datetime
import tinytroupe.control as control
from tinytroupe.control import transactional
from tinytroupe import utils
 
from rich.console import Console

from typing import Any, TypeVar, Union
AgentOrWorld = Union["TinyPerson", "TinyWorld"]

class TinyWorld:
    """
    Base class for environments.
    """

    # A dict of all environments created so far.
    all_environments = {} # name -> environment

    # Whether to display environments communications or not, for all environments. 
    communication_display = True

    def __init__(self, name: str="A TinyWorld", agents=[], 
                 initial_datetime=datetime.now(),
                 interventions=[],
                 broadcast_if_no_target=True,
                 max_additional_targets_to_display=3):
        """
        Initializes an environment.

        Args:
            name (str): The name of the environment.
            agents (list): A list of agents to add to the environment.
            initial_datetime (datetime): The initial datetime of the environment, or None (i.e., explicit time is optional). 
                Defaults to the current datetime in the real world.
            interventions (list): A list of interventions to apply in the environment at each simulation step.
            broadcast_if_no_target (bool): If True, broadcast actions if the target of an action is not found.
            max_additional_targets_to_display (int): The maximum number of additional targets to display in a communication. If None, 
                all additional targets are displayed.
        """

        self.name = name
        self.current_datetime = initial_datetime
        self.broadcast_if_no_target = broadcast_if_no_target
        self.simulation_id = None # will be reset later if the agent is used within a specific simulation scope
        
        self.agents = []
        self.name_to_agent = {} # {agent_name: agent, agent_name_2: agent_2, ...}

        self._interventions = interventions

        # the buffer of communications that have been displayed so far, used for
        # saving these communications to another output form later (e.g., caching)
        self._displayed_communications_buffer = []

        # a temporary buffer for communications target to make rendering easier
        self._target_display_communications_buffer = []
        self._max_additional_targets_to_display = max_additional_targets_to_display

        self.console = Console()

        # add the environment to the list of all environments
        TinyWorld.add_environment(self)
        
        self.add_agents(agents)
        
    #######################################################################
    # Simulation control methods
    #######################################################################
    @transactional()
    def _step(self, 
              timedelta_per_step=None, 
              randomize_agents_order=True,
              parallelize=True): # TODO have a configuration for parallelism?
        """
        Performs a single step in the environment. This default implementation
        simply calls makes all agents in the environment act and properly
        handle the resulting actions. Subclasses might override this method to implement 
        different policies.
        """
        
        # Increase current datetime if timedelta is given. This must happen before
        # any other simulation updates, to make sure that the agents are acting
        # in the correct time, particularly if only one step is being run.
        self._advance_datetime(timedelta_per_step)

        # Apply interventions. 
        # 
        # Why not in parallel? Owing to the very general nature of their potential effects,
        # interventions are never parallelized, since that could introduce unforeseen race conditions.
        for intervention in self._interventions:
            should_apply_intervention = intervention.check_precondition()
            if should_apply_intervention:
                if TinyWorld.communication_display:
                    self._display_intervention_communication(intervention)
                intervention.apply_effect()
                
                logger.debug(f"[{self.name}] Intervention '{intervention.name}' was applied.")

        # Agents can act in parallel or sequentially
        if parallelize:
            agents_actions = self._step_in_parallel(timedelta_per_step=timedelta_per_step)
        else:
            agents_actions = self._step_sequentially(timedelta_per_step=timedelta_per_step, 
                                                 randomize_agents_order=randomize_agents_order)
        
        return agents_actions
        
    def _step_sequentially(self, timedelta_per_step=None, randomize_agents_order=True):
        """
        The sequential version of the _step method to request agents to act. 
        """
        
        # agents can act in a random order
        reordered_agents = copy.copy(self.agents)
        if randomize_agents_order:
            random.shuffle(reordered_agents)

        # agents can act
        agents_actions = {}
        for agent in reordered_agents:
            logger.debug(f"[{self.name}] Agent {name_or_empty(agent)} is acting.")
            actions = agent.act(return_actions=True)
            agents_actions[agent.name] = actions

            self._handle_actions(agent, agent.pop_latest_actions())
        
        return agents_actions

    def _step_in_parallel(self, timedelta_per_step=None):
        """
        A parallelized version of the _step method to request agents to act.
        """

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(agent.act, return_actions=True): agent for agent in self.agents}
            agents_actions = {}
            for future in concurrent.futures.as_completed(futures):
                agent = futures[future]
                try:
                    actions = future.result()
                    agents_actions[agent.name] = actions
                    self._handle_actions(agent, agent.pop_latest_actions())
                except Exception as exc:
                    logger.error(f"[{self.name}] Agent {name_or_empty(agent)} generated an exception: {exc}")

        return agents_actions

        

    def _advance_datetime(self, timedelta):
        """
        Advances the current datetime of the environment by the specified timedelta.

        Args:
            timedelta (timedelta): The timedelta to advance the current datetime by.
        """
        if timedelta is not None:
            self.current_datetime += timedelta
        else:
            logger.info(f"[{self.name}] No timedelta provided, so the datetime was not advanced.")

    @transactional()
    def run(self, steps: int, timedelta_per_step=None, return_actions=False, randomize_agents_order=True, parallelize=default["parallel_agent_actions"]):
        """
        Runs the environment for a given number of steps.

        Args:
            steps (int): The number of steps to run the environment for.
            timedelta_per_step (timedelta, optional): The time interval between steps. Defaults to None.
            return_actions (bool, optional): If True, returns the actions taken by the agents. Defaults to False.
            randomize_agents_order (bool, optional): If True, randomizes the order in which agents act. Defaults to True.
            parallelize (bool, optional): If True, agents act in parallel. Defaults to True.
        
        Returns:
            list: A list of actions taken by the agents over time, if return_actions is True. The list has this format:
                  [{agent_name: [action_1, action_2, ...]}, {agent_name_2: [action_1, action_2, ...]}, ...]
        """
        agents_actions_over_time = []
        for i in range(steps):
            logger.info(f"[{self.name}] Running world simulation step {i+1} of {steps}.")

            if TinyWorld.communication_display:
                self._display_step_communication(cur_step=i+1, total_steps=steps, timedelta_per_step=timedelta_per_step)

            agents_actions = self._step(timedelta_per_step=timedelta_per_step, randomize_agents_order=randomize_agents_order, parallelize=parallelize)
            agents_actions_over_time.append(agents_actions)
        
        if return_actions:
            return agents_actions_over_time
    
    @transactional()
    def skip(self, steps: int, timedelta_per_step=None):
        """
        Skips a given number of steps in the environment. That is to say, time shall pass, but no actions will be taken
        by the agents or any other entity in the environment.

        Args:
            steps (int): The number of steps to skip.
            timedelta_per_step (timedelta, optional): The time interval between steps. Defaults to None.
        """
        self._advance_datetime(steps * timedelta_per_step)

    def run_minutes(self, minutes: int, randomize_agents_order=True, parallelize=True):
        """
        Runs the environment for a given number of minutes.

        Args:
            minutes (int): The number of minutes to run the environment for.
        """
        self.run(steps=minutes, timedelta_per_step=timedelta(minutes=1), randomize_agents_order=randomize_agents_order, parallelize=parallelize)
    
    def skip_minutes(self, minutes: int):
        """
        Skips a given number of minutes in the environment.

        Args:
            minutes (int): The number of minutes to skip.
        """
        self.skip(steps=minutes, timedelta_per_step=timedelta(minutes=1))
    
    def run_hours(self, hours: int, randomize_agents_order=True, parallelize=True):
        """
        Runs the environment for a given number of hours.

        Args:
            hours (int): The number of hours to run the environment for.
        """
        self.run(steps=hours, timedelta_per_step=timedelta(hours=1), randomize_agents_order=randomize_agents_order, parallelize=parallelize)
    
    def skip_hours(self, hours: int):
        """
        Skips a given number of hours in the environment.

        Args:
            hours (int): The number of hours to skip.
        """
        self.skip(steps=hours, timedelta_per_step=timedelta(hours=1))
    
    def run_days(self, days: int, randomize_agents_order=True, parallelize=True):
        """
        Runs the environment for a given number of days.

        Args:
            days (int): The number of days to run the environment for.
        """
        self.run(steps=days, timedelta_per_step=timedelta(days=1), randomize_agents_order=randomize_agents_order, parallelize=parallelize)
    
    def skip_days(self, days: int):
        """
        Skips a given number of days in the environment.

        Args:
            days (int): The number of days to skip.
        """
        self.skip(steps=days, timedelta_per_step=timedelta(days=1))
    
    def run_weeks(self, weeks: int, randomize_agents_order=True, parallelize=True):
        """
        Runs the environment for a given number of weeks.

        Args:
            weeks (int): The number of weeks to run the environment for.
            randomize_agents_order (bool, optional): If True, randomizes the order in which agents act. Defaults to True.
        """
        self.run(steps=weeks, timedelta_per_step=timedelta(weeks=1), randomize_agents_order=randomize_agents_order, parallelize=parallelize)
    
    def skip_weeks(self, weeks: int):
        """
        Skips a given number of weeks in the environment.

        Args:
            weeks (int): The number of weeks to skip.
        """
        self.skip(steps=weeks, timedelta_per_step=timedelta(weeks=1))
    
    def run_months(self, months: int, randomize_agents_order=True, parallelize=True):
        """
        Runs the environment for a given number of months.

        Args:
            months (int): The number of months to run the environment for.
            randomize_agents_order (bool, optional): If True, randomizes the order in which agents act. Defaults to True.
        """
        self.run(steps=months, timedelta_per_step=timedelta(weeks=4), randomize_agents_order=randomize_agents_order, parallelize=parallelize)
    
    def skip_months(self, months: int):
        """
        Skips a given number of months in the environment.

        Args:
            months (int): The number of months to skip.
        """
        self.skip(steps=months, timedelta_per_step=timedelta(weeks=4))
    
    def run_years(self, years: int, randomize_agents_order=True, parallelize=True):
        """
        Runs the environment for a given number of years.

        Args:
            years (int): The number of years to run the environment for.
            randomize_agents_order (bool, optional): If True, randomizes the order in which agents act. Defaults to True.
        """
        self.run(steps=years, timedelta_per_step=timedelta(days=365), randomize_agents_order=randomize_agents_order, parallelize=parallelize)
    
    def skip_years(self, years: int):
        """
        Skips a given number of years in the environment.

        Args:
            years (int): The number of years to skip.
        """
        self.skip(steps=years, timedelta_per_step=timedelta(days=365))

    #######################################################################
    # Agent management methods
    #######################################################################
    def add_agents(self, agents: list):
        """
        Adds a list of agents to the environment.

        Args:
            agents (list): A list of agents to add to the environment.
        """
        for agent in agents:
            self.add_agent(agent)
        
        return self # for chaining

    def add_agent(self, agent: TinyPerson):
        """
        Adds an agent to the environment. The agent must have a unique name within the environment.

        Args:
            agent (TinyPerson): The agent to add to the environment.
        
        Raises:
            ValueError: If the agent name is not unique within the environment.
        """

        # check if the agent is not already in the environment
        if agent not in self.agents:
            logger.debug(f"Adding agent {agent.name} to the environment.")
            
            # Agent names must be unique in the environment. 
            # Check if the agent name is already there.
            if agent.name not in self.name_to_agent:
                agent.environment = self
                self.agents.append(agent)
                self.name_to_agent[agent.name] = agent
            else:
                raise ValueError(f"Agent names must be unique, but '{agent.name}' is already in the environment.")
        else:
            logger.warn(f"Agent {agent.name} is already in the environment.")
        
        return self # for chaining

    def remove_agent(self, agent: TinyPerson):
        """
        Removes an agent from the environment.

        Args:
            agent (TinyPerson): The agent to remove from the environment.
        """
        logger.debug(f"Removing agent {agent.name} from the environment.")
        self.agents.remove(agent)
        del self.name_to_agent[agent.name]

        return self # for chaining
    
    def remove_all_agents(self):
        """
        Removes all agents from the environment.
        """
        logger.debug(f"Removing all agents from the environment.")
        self.agents = []
        self.name_to_agent = {}

        return self # for chaining

    def get_agent_by_name(self, name: str) -> TinyPerson:
        """
        Returns the agent with the specified name. If no agent with that name exists in the environment, 
        returns None.

        Args:
            name (str): The name of the agent to return.

        Returns:
            TinyPerson: The agent with the specified name.
        """
        if name in self.name_to_agent:
            return self.name_to_agent[name]
        else:
            return None
    
    #######################################################################
    # Intervention management methods
    #######################################################################

    def add_intervention(self, intervention):
        """
        Adds an intervention to the environment.

        Args:
            intervention: The intervention to add to the environment.
        """
        self._interventions.append(intervention)

    #######################################################################
    # Action handlers
    #
    # Specific actions issued by agents are handled by the environment,
    # because they have effects beyond the agent itself.
    #######################################################################
    @transactional()
    def _handle_actions(self, source: TinyPerson, actions: list):
        """ 
        Handles the actions issued by the agents.

        Args:
            source (TinyPerson): The agent that issued the actions.
            actions (list): A list of actions issued by the agents. Each action is actually a
              JSON specification.
            
        """
        for action in actions:
            action_type = action["type"] # this is the only required field
            content = action["content"] if "content" in action else None
            target = action["target"] if "target" in action else None

            logger.debug(f"[{self.name}] Handling action {action_type} from agent {name_or_empty(source)}. Content: {content}, target: {target}.")

            # only some actions require the enviroment to intervene
            if action_type == "REACH_OUT":
                self._handle_reach_out(source, content, target)
            elif action_type == "TALK":
                self._handle_talk(source, content, target)

    @transactional()
    def _handle_reach_out(self, source_agent: TinyPerson, content: str, target: str):
        """
        Handles the REACH_OUT action. This default implementation always allows REACH_OUT to succeed.
        Subclasses might override this method to implement different policies.

        Args:
            source_agent (TinyPerson): The agent that issued the REACH_OUT action.
            content (str): The content of the message.
            target (str): The target of the message.
        """

        # This default implementation always allows REACH_OUT to suceed.
        target_agent = self.get_agent_by_name(target)

        if target_agent is not None:
            source_agent.make_agent_accessible(target_agent)
            target_agent.make_agent_accessible(source_agent)

            source_agent.socialize(f"{name_or_empty(target_agent)} was successfully reached out, and is now available for interaction.", source=self)
            target_agent.socialize(f"{name_or_empty(source_agent)} reached out to you, and is now available for interaction.", source=self)
        
        else:
            logger.debug(f"[{self.name}] REACH_OUT action failed: target agent '{target}' not found.")

    @transactional()
    def _handle_talk(self, source_agent: TinyPerson, content: str, target: str):
        """
        Handles the TALK action by delivering the specified content to the specified target.

        Args:
            source_agent (TinyPerson): The agent that issued the TALK action.
            content (str): The content of the message.
            target (str, optional): The target of the message.
        """
        target_agent = self.get_agent_by_name(target)

        logger.debug(f"[{self.name}] Delivering message from {name_or_empty(source_agent)} to {name_or_empty(target_agent)}.")

        if target_agent is not None:
            target_agent.listen(content, source=source_agent)
        elif self.broadcast_if_no_target:
            self.broadcast(content, source=source_agent)

    #######################################################################
    # Interaction methods
    #######################################################################
    @transactional()
    def broadcast(self, speech: str, source: AgentOrWorld=None):
        """
        Delivers a speech to all agents in the environment.

        Args:
            speech (str): The content of the message.
            source (AgentOrWorld, optional): The agent or environment that issued the message. Defaults to None.
        """
        logger.debug(f"[{self.name}] Broadcasting message: '{speech}'.")

        for agent in self.agents:
            # do not deliver the message to the source
            if agent != source:
                agent.listen(speech, source=source)
    
    @transactional()
    def broadcast_thought(self, thought: str, source: AgentOrWorld=None):
        """
        Broadcasts a thought to all agents in the environment.

        Args:
            thought (str): The content of the thought.
        """
        logger.debug(f"[{self.name}] Broadcasting thought: '{thought}'.")

        for agent in self.agents:
            agent.think(thought)
    
    @transactional()
    def broadcast_internal_goal(self, internal_goal: str):
        """
        Broadcasts an internal goal to all agents in the environment.

        Args:
            internal_goal (str): The content of the internal goal.
        """
        logger.debug(f"[{self.name}] Broadcasting internal goal: '{internal_goal}'.")

        for agent in self.agents:
            agent.internalize_goal(internal_goal)
    
    @transactional()
    def broadcast_context_change(self, context:list):
        """
        Broadcasts a context change to all agents in the environment.

        Args:
            context (list): The content of the context change.
        """
        logger.debug(f"[{self.name}] Broadcasting context change: '{context}'.")

        for agent in self.agents:
            agent.change_context(context)

    def make_everyone_accessible(self):
        """
        Makes all agents in the environment accessible to each other.
        """
        for agent_1 in self.agents:
            for agent_2 in self.agents:
                if agent_1 != agent_2:
                    agent_1.make_agent_accessible(agent_2)
            

    ###########################################################
    # Formatting conveniences
    ###########################################################

    # TODO better names for these "display" methods
    def _display_step_communication(self, cur_step, total_steps, timedelta_per_step=None):
        """
        Displays the current communication and stores it in a buffer for later use.
        """
        rendering = self._pretty_step(cur_step=cur_step, total_steps=total_steps, timedelta_per_step=timedelta_per_step) 

        self._push_and_display_latest_communication({"kind": 'step', "rendering": rendering, "content": None, "source":  None, "target": None})
    
    def _display_intervention_communication(self, intervention):
        """
        Displays the current intervention communication and stores it in a buffer for later use.
        """
        rendering = self._pretty_intervention(intervention)
        self._push_and_display_latest_communication({"kind": 'intervention', "rendering": rendering, "content": None, "source":  None, "target": None})
    
    def _push_and_display_latest_communication(self, communication):
        """
        Pushes the latest communications to the agent's buffer.
        """
        #
        # check if the communication is just repeating the last one for a different target
        #
        if len(self._displayed_communications_buffer) > 0:
            # get values from last communication
            last_communication = self._displayed_communications_buffer[-1]
            last_kind = last_communication["kind"]
            last_target = last_communication["target"]
            last_source = last_communication["source"]
            if last_kind == 'action':  
                last_content = last_communication["content"]["action"]["content"]
                last_type = last_communication["content"]["action"]["type"]
            elif last_kind == 'stimulus':
                last_content = last_communication["content"]["stimulus"]["content"]
                last_type = last_communication["content"]["stimulus"]["type"]
            elif last_kind == 'stimuli':
                last_stimulus = last_communication["content"]["stimuli"][0]
                last_content = last_stimulus["content"]
                last_type = last_stimulus["type"]
            else:
                last_content = None
                last_type = None
        
            # get values from current communication
            current_kind = communication["kind"]
            current_target = communication["target"]
            current_source = communication["source"]
            if current_kind == 'action':
                current_content = communication["content"]["action"]["content"]
                current_type = communication["content"]["action"]["type"]
            elif current_kind == 'stimulus':
                current_content = communication["content"]["stimulus"]["content"]
                current_type = communication["content"]["stimulus"]["type"]
            elif current_kind == 'stimuli':
                current_stimulus = communication["content"]["stimuli"][0]
                current_content = current_stimulus["content"]
                current_type = current_stimulus["type"]
            else:
                current_content = None
                current_type = None

            # if we are repeating the last communication, let's simplify the rendering
            if (last_source == current_source) and (last_type == current_type) and (last_kind == current_kind) and \
               (last_content is not None) and (last_content == current_content) and \
               (current_target is not None):
               
                self._target_display_communications_buffer.append(current_target)

                rich_style = utils.RichTextStyle.get_style_for(last_kind, last_type)
                
                # print the additional target a limited number of times if a max is set, or
                # always if no max is set.
                if (self._max_additional_targets_to_display is None) or\
                   len(self._target_display_communications_buffer) < self._max_additional_targets_to_display:
                    communication["rendering"] = " " * len(last_source) + f"[{rich_style}]       + --> [underline]{current_target}[/][/]"

                elif len(self._target_display_communications_buffer) == self._max_additional_targets_to_display:
                    communication["rendering"] = " " * len(last_source) + f"[{rich_style}]       + --> ...others...[/]"
                
                else: # don't display anything anymore
                    communication["rendering"] = None
            
            else:
                # no repetition, so just display the communication and reset the targets buffer
                self._target_display_communications_buffer = [] # resets
        
        else:
            # no repetition, so just display the communication and reset the targets buffer
            self._target_display_communications_buffer = [] # resets



        self._displayed_communications_buffer.append(communication)
        self._display(communication)

    def pop_and_display_latest_communications(self):
        """
        Pops the latest communications and displays them.
        """
        communications = self._displayed_communications_buffer
        self._displayed_communications_buffer = []

        for communication in communications:
            self._display(communication)

        return communications    

    def _display(self, communication:dict):
        # unpack the rendering to find more info
        content = communication["rendering"]
        kind = communication["kind"]
        
        if content is not None:
            # render as appropriate
            if kind == 'step':
                self.console.rule(content)
            else:
                self.console.print(content)
    
    def clear_communications_buffer(self):
        """
        Cleans the communications buffer.
        """
        self._displayed_communications_buffer = []

    def __repr__(self):
        return f"TinyWorld(name='{self.name}')"

    def _pretty_step(self, cur_step, total_steps, timedelta_per_step=None):
        rendering = f"{self.name} step {cur_step} of {total_steps}"
        if timedelta_per_step is not None:
            rendering += f" ({pretty_datetime(self.current_datetime)})"

        return rendering

    def _pretty_intervention(self, intervention):
        indent = "          > "
        justification = textwrap.fill(
            intervention.precondition_justification(),
            width=TinyPerson.PP_TEXT_WIDTH,
            initial_indent=indent,
            subsequent_indent=indent,
        )
        
        rich_style = utils.RichTextStyle.get_style_for("intervention")
        rendering = f"[{rich_style}] :zap: [bold] <<{intervention.name}>> Triggered, effects are being applied...[/] \n" + \
                    f"[italic]{justification}[/][/]"
        # TODO add details about why the intervention was applied

        return rendering

    def pp_current_interactions(self, simplified=True, skip_system=True):
        """
        Pretty prints the current messages from agents in this environment.
        """
        print(self.pretty_current_interactions(simplified=simplified, skip_system=skip_system))

    def pretty_current_interactions(self, simplified=True, skip_system=True, max_content_length=default["max_content_display_length"], first_n=None, last_n=None, include_omission_info:bool=True):
      """
      Returns a pretty, readable, string with the current messages of agents in this environment.
      """
      agent_contents = []

      for agent in self.agents:
          agent_content = f"#### Interactions from the point of view of {agent.name} agent:\n"
          agent_content += f"**BEGIN AGENT {agent.name} HISTORY.**\n "
          agent_content += agent.pretty_current_interactions(simplified=simplified, skip_system=skip_system, max_content_length=max_content_length, first_n=first_n, last_n=last_n, include_omission_info=include_omission_info) + "\n"
          agent_content += f"**FINISHED AGENT {agent.name} HISTORY.**\n\n"
          agent_contents.append(agent_content)      
          
      return "\n".join(agent_contents)
    
    #######################################################################
    # IO
    #######################################################################

    def encode_complete_state(self) -> dict:
        """
        Encodes the complete state of the environment in a dictionary.

        Returns:
            dict: A dictionary encoding the complete state of the environment.
        """
        to_copy = copy.copy(self.__dict__)

        # remove the logger and other fields
        del to_copy['console']
        del to_copy['agents']
        del to_copy['name_to_agent']
        del to_copy['current_datetime']
        del to_copy['_interventions'] # TODO: encode interventions

        state = copy.deepcopy(to_copy)

        # agents are encoded separately
        state["agents"] = [agent.encode_complete_state() for agent in self.agents]

        # datetime also has to be encoded separately
        state["current_datetime"] = self.current_datetime.isoformat()

        return state
    
    def decode_complete_state(self, state:dict):
        """
        Decodes the complete state of the environment from a dictionary.

        Args:
            state (dict): A dictionary encoding the complete state of the environment.

        Returns:
            Self: The environment decoded from the dictionary.
        """
        state = copy.deepcopy(state)

        #################################
        # restore agents in-place
        #################################
        self.remove_all_agents()
        for agent_state in state["agents"]:
            try:
                try:
                    agent = TinyPerson.get_agent_by_name(agent_state["name"])
                except Exception as e:
                    raise ValueError(f"Could not find agent {agent_state['name']} for environment {self.name}.") from e
                
                agent.decode_complete_state(agent_state)
                self.add_agent(agent)
                
            except Exception as e:
                raise ValueError(f"Could not decode agent {agent_state['name']} for environment {self.name}.") from e
        
        # remove the agent states to update the rest of the environment
        del state["agents"]

        # restore datetime
        state["current_datetime"] = datetime.fromisoformat(state["current_datetime"])

        # restore other fields
        self.__dict__.update(state)

        return self

    @staticmethod
    def add_environment(environment):
        """
        Adds an environment to the list of all environments. Environment names must be unique,
        so if an environment with the same name already exists, an error is raised.
        """
        if environment.name in TinyWorld.all_environments:
            raise ValueError(f"Environment names must be unique, but '{environment.name}' is already defined.")
        else:
            TinyWorld.all_environments[environment.name] = environment
        

    @staticmethod
    def set_simulation_for_free_environments(simulation):
        """
        Sets the simulation if it is None. This allows free environments to be captured by specific simulation scopes
        if desired.
        """
        for environment in TinyWorld.all_environments.values():
            if environment.simulation_id is None:
                simulation.add_environment(environment)
    
    @staticmethod
    def get_environment_by_name(name: str):
        """
        Returns the environment with the specified name. If no environment with that name exists, 
        returns None.

        Args:
            name (str): The name of the environment to return.

        Returns:
            TinyWorld: The environment with the specified name.
        """
        if name in TinyWorld.all_environments:
            return TinyWorld.all_environments[name]
        else:
            return None
    
    @staticmethod
    def clear_environments():
        """
        Clears the list of all environments.
        """
        TinyWorld.all_environments = {}
