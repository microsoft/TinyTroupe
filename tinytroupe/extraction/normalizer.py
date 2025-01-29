import pandas as pd
from typing import Union, List

from tinytroupe.extraction import logger

from tinytroupe import openai_utils
import tinytroupe.utils as utils
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

        messages = utils.compose_initial_LLM_messages_with_templates("normalizer.system.mustache", "normalizer.user.mustache",                                                                      
                                                                     base_module_folder="extraction",
                                                                     rendering_configs=rendering_configs)
        
        next_message = openai_utils.client().send_message(messages, temperature=0.1)
        
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
            
            messages = utils.compose_initial_LLM_messages_with_templates("normalizer.applier.system.mustache", "normalizer.applier.user.mustache",                                      
                                                                     base_module_folder="extraction",
                                                                     rendering_configs=rendering_configs)
            
            next_message = openai_utils.client().send_message(messages, temperature=0.1)
            
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
        
