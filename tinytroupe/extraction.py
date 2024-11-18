"""
Simulations produce a lot of data, and it is often useful to extract these data in a structured way. For instance, you might wish to:
  - Extract the main points from an agent's interactions history, so that you can consult them later in a concise form.
  - Generate synthetic data from a simulation, so that you can use it for training machine learning models or testing software.
  - Simply turn some of the data into a more machine-readable format, such as JSON or CSV, so that you can analyze it more easily.

This module provides various utilities to help you extract data from TinyTroupe elements, such as agents and worlds. It also provides a 
mechanism to reduce the extracted data to a more concise form, and to export artifacts from TinyTroupe elements. Incidentaly, it showcases 
one of the many ways in which agent simulations differ from AI assistants, as the latter are not designed to be introspected in this way.
"""

import os
import json
import chevron
import logging
import pandas as pd
import pypandoc
import markdown 
from typing import Union, List
import logging
logger = logging.getLogger("tinytroupe")

from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.utils import JsonSerializableRegistry


from tinytroupe.clients import client
import tinytroupe.utils as utils

class ResultsExtractor:

    def __init__(self):
        self._extraction_prompt_template_path = os.path.join(os.path.dirname(__file__), 'prompts/interaction_results_extractor.mustache')

        # we'll cache the last extraction results for each type of extraction, so that we can use them to
        # generate reports or other additional outputs.
        self.agent_extraction = {}
        self.world_extraction = {}

    def extract_results_from_agent(self, 
                        tinyperson:TinyPerson, 
                        extraction_objective:str="The main points present in the agent's interactions history.", 
                        situation:str = "", 
                        fields:list=None,
                        fields_hints:dict=None,
                        verbose:bool=False):
        """
        Extracts results from a TinyPerson instance.

        Args:
            tinyperson (TinyPerson): The TinyPerson instance to extract results from.
            extraction_objective (str): The extraction objective.
            situation (str): The situation to consider.
            fields (list, optional): The fields to extract. If None, the extractor will decide what names to use. 
                Defaults to None.
            verbose (bool, optional): Whether to print debug messages. Defaults to False.
        """

        messages = []

        rendering_configs = {}
        if fields is not None:
            rendering_configs["fields"] = ", ".join(fields)
        
        if fields_hints is not None:
            rendering_configs["fields_hints"] = list(fields_hints.items())
        
        messages.append({"role": "system", 
                         "content": chevron.render(
                             open(self._extraction_prompt_template_path).read(), 
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

        next_message = client().send_message(messages, temperature=0.0)
        
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
                                   verbose:bool=False):
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

        messages = []

        rendering_configs = {}
        if fields is not None:
            rendering_configs["fields"] = ", ".join(fields)
        
        if fields_hints is not None:
            rendering_configs["fields_hints"] = list(fields_hints.items())
        
        messages.append({"role": "system", 
                         "content": chevron.render(
                             open(self._extraction_prompt_template_path).read(), 
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

        next_message = client().send_message(messages, temperature=0.0)
        
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
        with open(filename, 'w') as f:
            json.dump({"agent_extractions": self.agent_extraction, 
                       "world_extraction": self.world_extraction}, f, indent=4)
        
        if verbose:
            print(f"Saved extraction results to {filename}")



class ResultsReducer:

    def __init__(self):
        self.results = {}

        self.rules = {}
    
    def add_reduction_rule(self, trigger: str, func: callable):
        if trigger in self.rules:
            raise Exception(f"Rule for {trigger} already exists.")
        
        self.rules[trigger] = func
    
    def reduce_agent(self, agent: TinyPerson) -> list:
        reduction = []
        for message in agent.episodic_memory.retrieve_all():
            if message['role'] == 'system':
                continue # doing nothing for `system` role yet at least

            elif message['role'] == 'user':
                # User role is related to stimuli only
                stimulus_type = message['content']['stimuli'][0]['type']
                stimulus_content = message['content']['stimuli'][0]['content']
                stimulus_source = message['content']['stimuli'][0]['source']
                stimulus_timestamp = message['simulation_timestamp']

                if stimulus_type in self.rules:
                    extracted = self.rules[stimulus_type](focus_agent=agent, source_agent=TinyPerson.get_agent_by_name(stimulus_source), target_agent=agent, kind='stimulus', event=stimulus_type, content=stimulus_content, timestamp=stimulus_timestamp)
                    if extracted is not None:
                        reduction.append(extracted)

            elif message['role'] == 'assistant':
                # Assistant role is related to actions only
                if 'action' in message['content']: 
                    action_type = message['content']['action']['type']
                    action_content = message['content']['action']['content']
                    action_target = message['content']['action']['target']
                    action_timestamp = message['simulation_timestamp']
                    
                    if action_type in self.rules:
                        extracted = self.rules[action_type](focus_agent=agent, source_agent=agent, target_agent=TinyPerson.get_agent_by_name(action_target), kind='action', event=action_type, content=action_content, timestamp=action_timestamp)
                        if extracted is not None:
                            reduction.append(extracted)
            
        return reduction

    def reduce_agent_to_dataframe(self, agent: TinyPerson, column_names: list=None) -> pd.DataFrame:
        reduction = self.reduce_agent(agent)
        return pd.DataFrame(reduction, columns=column_names)


class ArtifactExporter(JsonSerializableRegistry):
    """
    An artifact exporter is responsible for exporting artifacts from TinyTroupe elements, for example 
    in order to create synthetic data files from simulations. 
    """

    def __init__(self, base_output_folder:str) -> None:
        self.base_output_folder = base_output_folder

    def export(self, artifact_name:str, artifact_data:Union[dict, str], content_type:str, content_format:str=None, target_format:str="txt", verbose:bool=False):
        """
        Exports the specified artifact data to a file.

        Args:
            artifact_name (str): The name of the artifact.
            artifact_data (Union[dict, str]): The data to export. If a dict is given, it will be saved as JSON. 
                If a string is given, it will be saved as is.
            content_type (str): The type of the content within the artifact.
            content_format (str, optional): The format of the content within the artifact (e.g., md, csv, etc). Defaults to None.
            target_format (str): The format to export the artifact to (e.g., json, txt, docx, etc).
            verbose (bool, optional): Whether to print debug messages. Defaults to False.
        """
        
        # dedent inputs, just in case
        if isinstance(artifact_data, str):
            artifact_data = utils.dedent(artifact_data)
        elif isinstance(artifact_data, dict):
            artifact_data['content'] = utils.dedent(artifact_data['content'])
        else:
            raise ValueError("The artifact data must be either a string or a dictionary.")
        
        # clean the artifact name of invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\t', '\r', ';']
        for char in invalid_chars:
            # check if the character is in the artifact name
            if char in artifact_name:
                # replace the character with an underscore
                artifact_name = artifact_name.replace(char, "-")
                logger.warning(f"Replaced invalid character {char} with hyphen in artifact name '{artifact_name}'.")
        
        artifact_file_path = self._compose_filepath(artifact_data, artifact_name, content_type, target_format, verbose)


        if target_format == "json":
            self._export_as_json(artifact_file_path, artifact_data, content_type, verbose)
        elif target_format == "txt" or target_format == "text" or target_format == "md" or target_format == "markdown":
            self._export_as_txt(artifact_file_path, artifact_data, content_type, verbose)
        elif target_format == "docx":
            self._export_as_docx(artifact_file_path, artifact_data, content_format, verbose)
        else:
            raise ValueError(f"Unsupported target format: {target_format}.")


    def _export_as_txt(self, artifact_file_path:str, artifact_data:Union[dict, str], content_type:str, verbose:bool=False):
        """
        Exports the specified artifact data to a text file.
        """

        with open(artifact_file_path, 'w', encoding="utf-8") as f:
            if isinstance(artifact_data, dict):
                content = artifact_data['content']
            else:
                content = artifact_data
        
            f.write(content)
    
    def _export_as_json(self, artifact_file_path:str, artifact_data:Union[dict, str], content_type:str, verbose:bool=False):
        """
        Exports the specified artifact data to a JSON file.
        """

        with open(artifact_file_path, 'w', encoding="utf-8") as f:
            if isinstance(artifact_data, dict):
                json.dump(artifact_data, f, indent=4)                
            else:
                raise ValueError("The artifact data must be a dictionary to export to JSON.")
    
    def _export_as_docx(self, artifact_file_path:str, artifact_data:Union[dict, str], content_original_format:str, verbose:bool=False):
        """
        Exports the specified artifact data to a DOCX file.
        """

        # original format must be 'text' or 'markdown'
        if content_original_format not in ['text', 'txt', 'markdown', 'md']:
            raise ValueError(f"The original format cannot be {content_original_format} to export to DOCX.")
        else:
            # normalize content value
            content_original_format = 'markdown' if content_original_format == 'md' else content_original_format

        # first, get the content to export. If `artifact_date` is a dict, the contant should be under the key `content`.
        # If it is a string, the content is the string itself.
        # using pypandoc
        if isinstance(artifact_data, dict):
            content = artifact_data['content']
        else:
            content = artifact_data
        
        # first, convert to HTML. This is necessary because pypandoc does not support a GOOD direct conversion from markdown to DOCX.
        html_content = markdown.markdown(content)

        ## write this intermediary HTML to file
        #html_file_path = artifact_file_path.replace(".docx", ".html")
        #with open(html_file_path, 'w', encoding="utf-8") as f:
        #    f.write(html_content)

        # then, convert to DOCX
        pypandoc.convert_text(html_content, 'docx', format='html', outputfile=artifact_file_path)   
    
    ###########################################################
    # IO
    ###########################################################
                  
    def _compose_filepath(self, artifact_data:Union[dict, str], artifact_name:str, content_type:str, target_format:str=None, verbose:bool=False):
        """
        Composes the file path for the artifact to export.

        Args:
            artifact_data (Union[dict, str]): The data to export.
            artifact_name (str): The name of the artifact.
            content_type (str): The type of the content within the artifact.
            content_format (str, optional): The format of the content within the artifact (e.g., md, csv, etc). Defaults to None.
            verbose (bool, optional): Whether to print debug messages. Defaults to False.
        """        

        # Extension definition: 
        #
        # - If the content format is specified, we use it as the part of the extension.
        # - If artificat_data is a dict, we add .json to the extension. Note that if content format was specified, we'd get <content_format>.json.
        # - If artifact_data is a string and no content format is specified, we add .txt to the extension.
        extension = None
        if target_format is not None:
            extension = f"{target_format}"
        elif isinstance(artifact_data, str) and target_format is None:
            extension = "txt"
        
        # content type definition
        if content_type is None:
            subfolder = ""
        else:
            subfolder = content_type

        # save to the specified file name or path, considering the base output folder.
        artifact_file_path = os.path.join(self.base_output_folder, subfolder, f"{artifact_name}.{extension}")    

        # create intermediate directories if necessary
        os.makedirs(os.path.dirname(artifact_file_path), exist_ok=True)

        return artifact_file_path
        
            
class Normalizer:
    """
    A mechanism to normalize passages, concepts and other textual elements.
    """

    def __init__(self, elements:List[str], n:int, verbose:bool=False):
        """
        Normalizes the specified elements.

        Args:
            elements (list): The elements to normalize.
            n (int): The number of normalized elements to output.
            verbose (bool, optional): Whether to print debug messages. Defaults to False.
        """
        # ensure elements are unique
        self.elements = list(set(elements))
        
        self.n = n  
        self.verbose = verbose 
        
        # a JSON-based structure, where each output element is a key to a list of input elements that were merged into it
        self.normalized_elements = None
        # a dict that maps each input element to its normalized output. This will be used as cache later.
        self.normalizing_map = {}      

        rendering_configs = {"n": n,
                             "elements": self.elements}

        messages = utils.compose_initial_LLM_messages_with_templates("normalizer.system.mustache", "normalizer.user.mustache", rendering_configs)
        next_message = client().send_message(messages, temperature=0.1)
        
        debug_msg = f"Normalization result message: {next_message}"
        logger.debug(debug_msg)
        if self.verbose:
            print(debug_msg)

        result = utils.extract_json(next_message["content"])
        logger.debug(result)
        if self.verbose:
            print(result)

        self.normalized_elements = result

    
    def normalize(self, element_or_elements:Union[str, List[str]]) -> Union[str, List[str]]:
        """
        Normalizes the specified element or elements.

        This method uses a caching mechanism to improve performance. If an element has been normalized before, 
        its normalized form is stored in a cache (self.normalizing_map). When the same element needs to be 
        normalized again, the method will first check the cache and use the stored normalized form if available, 
        instead of normalizing the element again.

        The order of elements in the output will be the same as in the input. This is ensured by processing 
        the elements in the order they appear in the input and appending the normalized elements to the output 
        list in the same order.

        Args:
            element_or_elements (Union[str, List[str]]): The element or elements to normalize.

        Returns:
            str: The normalized element if the input was a string.
            list: The normalized elements if the input was a list, preserving the order of elements in the input.
        """
        if isinstance(element_or_elements, str):
            denormalized_elements = [element_or_elements]
        elif isinstance(element_or_elements, list):
            denormalized_elements = element_or_elements
        else:
            raise ValueError("The element_or_elements must be either a string or a list.")
        
        normalized_elements = []
        elements_to_normalize = []
        for element in denormalized_elements:
            if element not in self.normalizing_map:
                elements_to_normalize.append(element)
        
        if elements_to_normalize:
            rendering_configs = {"categories": self.normalized_elements,
                                    "elements": elements_to_normalize}
            
            messages = utils.compose_initial_LLM_messages_with_templates("normalizer.applier.system.mustache", "normalizer.applier.user.mustache", rendering_configs)
            next_message = client().send_message(messages, temperature=0.1)
            
            debug_msg = f"Normalization result message: {next_message}"
            logger.debug(debug_msg)
            if self.verbose:
                print(debug_msg)
    
            normalized_elements_from_llm = utils.extract_json(next_message["content"])
            assert isinstance(normalized_elements_from_llm, list), "The normalized element must be a list."
            assert len(normalized_elements_from_llm) == len(elements_to_normalize), "The number of normalized elements must be equal to the number of elements to normalize."
    
            for i, element in enumerate(elements_to_normalize):
                normalized_element = normalized_elements_from_llm[i]
                self.normalizing_map[element] = normalized_element
        
        for element in denormalized_elements:
            normalized_elements.append(self.normalizing_map[element])
        
        return normalized_elements
        

################################################################################	
# Convenience mechanisms
################################################################################

# default extractor
default_extractor = ResultsExtractor()