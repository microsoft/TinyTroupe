from tinytroupe.environment.tiny_world import TinyWorld
from tinytroupe.environment import logger

import copy
from datetime import datetime, timedelta

from tinytroupe.agent import *
from tinytroupe.control import transactional
 
from rich.console import Console

from typing import Any, TypeVar, Union
AgentOrWorld = Union["TinyPerson", "TinyWorld"]


class TinySocialNetwork(TinyWorld):

    def __init__(self, name, broadcast_if_no_target=True):
        """
        Create a new TinySocialNetwork environment.

        Args:
            name (str): The name of the environment.
            broadcast_if_no_target (bool): If True, broadcast actions through an agent's available relations
              if the target of an action is not found.
        """
        
        super().__init__(name, broadcast_if_no_target=broadcast_if_no_target)

        self.relations = {}
    
    @transactional()
    def add_relation(self, agent_1, agent_2, name="default"):
        """
        Adds a relation between two agents.
        
        Args:
            agent_1 (TinyPerson): The first agent.
            agent_2 (TinyPerson): The second agent.
            name (str): The name of the relation.
        """

        logger.debug(f"Adding relation {name} between {agent_1.name} and {agent_2.name}.")

        # agents must already be in the environment, if not they are first added
        if agent_1 not in self.agents:
            self.agents.append(agent_1)
        if agent_2 not in self.agents:
            self.agents.append(agent_2)

        if name in self.relations:
            self.relations[name].append((agent_1, agent_2))
        else:
            self.relations[name] = [(agent_1, agent_2)]

        return self # for chaining
    
    @transactional()
    def _update_agents_contexts(self):
        """
        Updates the agents' observations based on the current state of the world.
        """

        # clear all accessibility first
        for agent in self.agents:
            agent.make_all_agents_inaccessible()

        # now update accessibility based on relations
        for relation_name, relation in self.relations.items():
            logger.debug(f"Updating agents' observations for relation {relation_name}.")
            for agent_1, agent_2 in relation:
                agent_1.make_agent_accessible(agent_2)
                agent_2.make_agent_accessible(agent_1)

    @transactional()
    def _step(self):
        self._update_agents_contexts()

        #call super
        super()._step()
    
    @transactional()
    def _handle_reach_out(self, source_agent: TinyPerson, content: str, target: str):
        """
        Handles the REACH_OUT action. This social network implementation only allows
        REACH_OUT to succeed if the target agent is in the same relation as the source agent.

        Args:
            source_agent (TinyPerson): The agent that issued the REACH_OUT action.
            content (str): The content of the message.
            target (str): The target of the message.
        """
            
        # check if the target is in the same relation as the source
        if self.is_in_relation_with(source_agent, self.get_agent_by_name(target)):
            super()._handle_reach_out(source_agent, content, target)
            
        # if we get here, the target is not in the same relation as the source
        source_agent.socialize(f"{target} is not in the same relation as you, so you cannot reach out to them.", source=self)


    # TODO implement _handle_talk using broadcast_if_no_target too

    #######################################################################
    # Utilities and conveniences
    #######################################################################

    def is_in_relation_with(self, agent_1:TinyPerson, agent_2:TinyPerson, relation_name=None) -> bool:
        """
        Checks if two agents are in a relation. If the relation name is given, check that
        the agents are in that relation. If no relation name is given, check that the agents
        are in any relation. Relations are undirected, so the order of the agents does not matter.

        Args:
            agent_1 (TinyPerson): The first agent.
            agent_2 (TinyPerson): The second agent.
            relation_name (str): The name of the relation to check, or None to check any relation.

        Returns:
            bool: True if the two agents are in the given relation, False otherwise.
        """
        if relation_name is None:
            for relation_name, relation in self.relations.items():
                if (agent_1, agent_2) in relation or (agent_2, agent_1) in relation:
                    return True
            return False
        
        else:
            if relation_name in self.relations:
                return (agent_1, agent_2) in self.relations[relation_name] or (agent_2, agent_1) in self.relations[relation_name]
            else:
                return False