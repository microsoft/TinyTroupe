import os
import json
import chevron
import pandas as pd
from typing import Union, List

from tinytroupe.extraction import logger
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld

from tinytroupe import openai_utils
import tinytroupe.utils as utils


class ResultsExtractor:

    def __init__(self, 
                 extraction_prompt_template_path:str = os.path.join(os.path.dirname(__file__), './prompts/interaction_results_extractor.mustache'),
                 extraction_objective:str = "The main points present in the agents' interactions history.",
                 situation:str = "",
                 fields:List[str] = None,
                 fields_hints:dict = None,
                 verbose:bool = False):
        """
        Initializes the ResultsExtractor with default parameters.

        Args:
            extraction_prompt_template_path (str): The path to the extraction prompt template.
            extraction_objective (str): The default extraction objective.
            situation (str): The default situation to consider.
            fields (List[str], optional): The default fields to extract. Defaults to None.
            fields_hints (dict, optional): The default hints for the fields to extract. Defaults to None.
            verbose (bool, optional): Whether to print debug messages by default. Defaults to False.
        """
        self._extraction_prompt_template_path = extraction_prompt_template_path

        # Default parameters
        self.default_extraction_objective = extraction_objective
        self.default_situation = situation
        self.default_fields = fields
        self.default_fields_hints = fields_hints
        self.default_verbose = verbose

        # Cache for the last extraction results
        self.agent_extraction = {}
        self.world_extraction = {}

    def extract_results_from_agents(self,
                                    agents:List[TinyPerson],
                                    extraction_objective:str=None,
                                    situation:str =None,
                                    fields:list=None,
                                    fields_hints:dict=None,
                                    verbose:bool=None):
        """
        Extracts results from a list of TinyPerson instances.

        Args:
            agents (List[TinyPerson]): The list of TinyPerson instances to extract results from.
            extraction_objective (str): The extraction objective.
            situation (str): The situation to consider.
            fields (list, optional): The fields to extract. If None, the extractor will decide what names to use. 
                Defaults to None.
            fields_hints (dict, optional): Hints for the fields to extract. Maps field names to strings with the hints. Defaults to None.
            verbose (bool, optional): Whether to print debug messages. Defaults to False.

        
        """
        results = []
        for agent in agents:
            result = self.extract_results_from_agent(agent, extraction_objective, situation, fields, fields_hints, verbose)
            results.append(result)
        
        return results
        
    def extract_results_from_agent(self, 
                        tinyperson:TinyPerson, 
                        extraction_objective:str="The main points present in the agent's interactions history.", 
                        situation:str = "", 
                        fields:list=None,
                        fields_hints:dict=None,
                        verbose:bool=None):
        """
        Extracts results from a TinyPerson instance.

        Args:
            tinyperson (TinyPerson): The TinyPerson instance to extract results from.
            extraction_objective (str): The extraction objective.
            situation (str): The situation to consider.
            fields (list, optional): The fields to extract. If None, the extractor will decide what names to use. 
                Defaults to None.
            fields_hints (dict, optional): Hints for the fields to extract. Maps field names to strings with the hints. Defaults to None.
            verbose (bool, optional): Whether to print debug messages. Defaults to False.
        """

        extraction_objective, situation, fields, fields_hints, verbose = self._get_default_values_if_necessary(
            extraction_objective, situation, fields, fields_hints, verbose
        )

        messages = []

        rendering_configs = {}
        if fields is not None:
            rendering_configs["fields"] = ", ".join(fields)
        
        if fields_hints is not None:
            rendering_configs["fields_hints"] = list(fields_hints.items())
        
        messages.append({"role": "system", 
                         "content": chevron.render(
                             open(self._extraction_prompt_template_path, 'r', encoding='utf-8', errors='replace').read(), 
                             rendering_configs)})


        interaction_history = tinyperson.pretty_current_interactions(max_content_length=None)

        extraction_request_prompt = \
f"""
## Extraction objective

{extraction_objective}

## Situation
You are considering a single agent, named {tinyperson.name}. Your objective thus refers to this agent specifically.
{situation}

## Agent Interactions History

You will consider an agent's history of interactions, which include stimuli it received as well as actions it 
performed.

{interaction_history}
"""
        messages.append({"role": "user", "content": extraction_request_prompt})

        next_message = openai_utils.client().send_message(messages, temperature=0.0, frequency_penalty=0.0, presence_penalty=0.0)
        
        debug_msg = f"Extraction raw result message: {next_message}"
        logger.debug(debug_msg)
        if verbose:
            print(debug_msg)

        if next_message is not None:
            result = utils.extract_json(next_message["content"])
        else:
            result = None
        
        # cache the result
        self.agent_extraction[tinyperson.name] = result

        return result
    

    def extract_results_from_world(self, 
                                   tinyworld:TinyWorld, 
                                   extraction_objective:str="The main points that can be derived from the agents conversations and actions.", 
                                   situation:str="", 
                                   fields:list=None,
                                   fields_hints:dict=None,
                                   verbose:bool=None):
        """
        Extracts results from a TinyWorld instance.

        Args:
            tinyworld (TinyWorld): The TinyWorld instance to extract results from.
            extraction_objective (str): The extraction objective.
            situation (str): The situation to consider.
            fields (list, optional): The fields to extract. If None, the extractor will decide what names to use. 
                Defaults to None.
            verbose (bool, optional): Whether to print debug messages. Defaults to False.
        """

        extraction_objective, situation, fields, fields_hints, verbose = self._get_default_values_if_necessary(
            extraction_objective, situation, fields, fields_hints, verbose
        )

        messages = []

        rendering_configs = {}
        if fields is not None:
            rendering_configs["fields"] = ", ".join(fields)
        
        if fields_hints is not None:
            rendering_configs["fields_hints"] = list(fields_hints.items())
        
        messages.append({"role": "system", 
                         "content": chevron.render(
                             open(self._extraction_prompt_template_path, 'r', encoding='utf-8', errors='replace').read(), 
                             rendering_configs)})

        # TODO: either summarize first or break up into multiple tasks
        interaction_history = tinyworld.pretty_current_interactions(max_content_length=None)

        extraction_request_prompt = \
f"""
## Extraction objective

{extraction_objective}

## Situation
You are considering various agents.
{situation}

## Agents Interactions History

You will consider the history of interactions from various agents that exist in an environment called {tinyworld.name}. 
Each interaction history includes stimuli the corresponding agent received as well as actions it performed.

{interaction_history}
"""
        messages.append({"role": "user", "content": extraction_request_prompt})

        next_message = openai_utils.client().send_message(messages, temperature=0.0)
        
        debug_msg = f"Extraction raw result message: {next_message}"
        logger.debug(debug_msg)
        if verbose:
            print(debug_msg)

        if next_message is not None:
            result = utils.extract_json(next_message["content"])
        else:
            result = None
        
        # cache the result
        self.world_extraction[tinyworld.name] = result

        return result
    
    def save_as_json(self, filename:str, verbose:bool=False):
        """
        Saves the last extraction results as JSON.

        Args:
            filename (str): The filename to save the JSON to.
            verbose (bool, optional): Whether to print debug messages. Defaults to False.
        """
        with open(filename, 'w', encoding="utf-8", errors="replace") as f:
            json.dump({"agent_extractions": self.agent_extraction, 
                       "world_extraction": self.world_extraction}, f, indent=4)
        
        if verbose:
            print(f"Saved extraction results to {filename}")
    
    def _get_default_values_if_necessary(self,
                            extraction_objective:str,
                            situation:str,
                            fields:List[str],
                            fields_hints:dict,
                            verbose:bool):
        
        if extraction_objective is None:
            extraction_objective = self.default_extraction_objective

        if situation is None:
            situation = self.default_situation

        if fields is None:
            fields = self.default_fields

        if fields_hints is None:
            fields_hints = self.default_fields_hints

        if verbose is None:
            verbose = self.default_verbose

        return extraction_objective, situation, fields, fields_hints, verbose

