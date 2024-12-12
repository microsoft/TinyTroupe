from tinytroupe.agent.mental_faculty import TinyMentalFaculty
from tinytroupe.agent.grounding import BaseSemanticGroundingConnector
import tinytroupe.utils as utils

from llama_index.core import Document
from typing import Any
import copy

#######################################################################################################################
# Memory mechanisms 
#######################################################################################################################

class TinyMemory(TinyMentalFaculty):
    """
    Base class for different types of memory.
    """

    def _preprocess_value_for_storage(self, value: Any) -> Any:
        """
        Preprocesses a value before storing it in memory.
        """
        # by default, we don't preprocess the value
        return value

    def _store(self, value: Any) -> None:
        """
        Stores a value in memory.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    def store(self, value: dict) -> None:
        """
        Stores a value in memory.
        """
        self._store(self._preprocess_value_for_storage(value))
    
    def store_all(self, values: list) -> None:
        """
        Stores a list of values in memory.
        """
        for value in values:
            self.store(value)

    def retrieve(self, first_n: int, last_n: int, include_omission_info:bool=True) -> list:
        """
        Retrieves the first n and/or last n values from memory. If n is None, all values are retrieved.

        Args:
            first_n (int): The number of first values to retrieve.
            last_n (int): The number of last values to retrieve.
            include_omission_info (bool): Whether to include an information message when some values are omitted.

        Returns:
            list: The retrieved values.
        
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_recent(self) -> list:
        """
        Retrieves the n most recent values from memory.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_all(self) -> list:
        """
        Retrieves all values from memory.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_relevant(self, relevance_target:str, top_k=20) -> list:
        """
        Retrieves all values from memory that are relevant to a given target.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class EpisodicMemory(TinyMemory):
    """
    Provides episodic memory capabilities to an agent. Cognitively, episodic memory is the ability to remember specific events,
    or episodes, in the past. This class provides a simple implementation of episodic memory, where the agent can store and retrieve
    messages from memory.
    
    Subclasses of this class can be used to provide different memory implementations.
    """

    MEMORY_BLOCK_OMISSION_INFO = {'role': 'assistant', 'content': "Info: there were other messages here, but they were omitted for brevity.", 'simulation_timestamp': None}

    def __init__(
        self, fixed_prefix_length: int = 100, lookback_length: int = 100
    ) -> None:
        """
        Initializes the memory.

        Args:
            fixed_prefix_length (int): The fixed prefix length. Defaults to 20.
            lookback_length (int): The lookback length. Defaults to 20.
        """
        self.fixed_prefix_length = fixed_prefix_length
        self.lookback_length = lookback_length

        self.memory = []

    def _store(self, value: Any) -> None:
        """
        Stores a value in memory.
        """
        self.memory.append(value)

    def count(self) -> int:
        """
        Returns the number of values in memory.
        """
        return len(self.memory)

    def retrieve(self, first_n: int, last_n: int, include_omission_info:bool=True) -> list:
        """
        Retrieves the first n and/or last n values from memory. If n is None, all values are retrieved.

        Args:
            first_n (int): The number of first values to retrieve.
            last_n (int): The number of last values to retrieve.
            include_omission_info (bool): Whether to include an information message when some values are omitted.

        Returns:
            list: The retrieved values.
        
        """

        omisssion_info = [EpisodicMemory.MEMORY_BLOCK_OMISSION_INFO] if include_omission_info else []

        # use the other methods in the class to implement
        if first_n is not None and last_n is not None:
            return self.retrieve_first(first_n) + omisssion_info + self.retrieve_last(last_n)
        elif first_n is not None:
            return self.retrieve_first(first_n)
        elif last_n is not None:
            return self.retrieve_last(last_n)
        else:
            return self.retrieve_all()

    def retrieve_recent(self, include_omission_info:bool=True) -> list:
        """
        Retrieves the n most recent values from memory.
        """
        omisssion_info = [EpisodicMemory.MEMORY_BLOCK_OMISSION_INFO] if include_omission_info else []

        # compute fixed prefix
        fixed_prefix = self.memory[: self.fixed_prefix_length] + omisssion_info

        # how many lookback values remain?
        remaining_lookback = min(
            len(self.memory) - len(fixed_prefix), self.lookback_length
        )

        # compute the remaining lookback values and return the concatenation
        if remaining_lookback <= 0:
            return fixed_prefix
        else:
            return fixed_prefix + self.memory[-remaining_lookback:]

    def retrieve_all(self) -> list:
        """
        Retrieves all values from memory.
        """
        return copy.copy(self.memory)

    def retrieve_relevant(self, relevance_target: str, top_k:int) -> list:
        """
        Retrieves top-k values from memory that are most relevant to a given target.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_first(self, n: int, include_omission_info:bool=True) -> list:
        """
        Retrieves the first n values from memory.
        """
        omisssion_info = [EpisodicMemory.MEMORY_BLOCK_OMISSION_INFO] if include_omission_info else []
        
        return self.memory[:n] + omisssion_info
    
    def retrieve_last(self, n: int, include_omission_info:bool=True) -> list:
        """
        Retrieves the last n values from memory.
        """
        omisssion_info = [EpisodicMemory.MEMORY_BLOCK_OMISSION_INFO] if include_omission_info else []

        return omisssion_info + self.memory[-n:]


@utils.post_init
class SemanticMemory(TinyMemory):
    """
    In Cognitive Psychology, semantic memory is the memory of meanings, understandings, and other concept-based knowledge unrelated to specific 
    experiences. It is not ordered temporally, and it is not about remembering specific events or episodes. This class provides a simple implementation
    of semantic memory, where the agent can store and retrieve semantic information.
    """

    serializable_attrs = ["memories"]

    def __init__(self, memories: list=None) -> None:
        self.memories = memories

        # @post_init ensures that _post_init is called after the __init__ method

    def _post_init(self): 
        """
        This will run after __init__, since the class has the @post_init decorator.
        It is convenient to separate some of the initialization processes to make deserialize easier.
        """

        if not hasattr(self, 'memories') or self.memories is None:
            self.memories = []

        self.semantic_grounding_connector = BaseSemanticGroundingConnector("Semantic Memory Storage")
        self.semantic_grounding_connector.add_documents(self._build_documents_from(self.memories))
    
        
    def _preprocess_value_for_storage(self, value: dict) -> Any:
        engram = None 

        if value['type'] == 'action':
            engram = f"# Fact\n" +\
                     f"I have performed the following action at date and time {value['simulation_timestamp']}:\n\n"+\
                     f" {value['content']}"
        
        elif value['type'] == 'stimulus':
            engram = f"# Stimulus\n" +\
                     f"I have received the following stimulus at date and time {value['simulation_timestamp']}:\n\n"+\
                     f" {value['content']}"

        # else: # Anything else here?

        return engram

    def _store(self, value: Any) -> None:
        engram_doc = self._build_document_from(self._preprocess_value_for_storage(value))
        self.semantic_grounding_connector.add_document(engram_doc)
    
    def retrieve_relevant(self, relevance_target:str, top_k=20) -> list:
        """
        Retrieves all values from memory that are relevant to a given target.
        """
        return self.semantic_grounding_connector.retrieve_relevant(relevance_target, top_k)

    #####################################
    # Auxiliary compatibility methods
    #####################################

    def _build_document_from(memory) -> Document:
        # TODO: add any metadata as well?
        return Document(text=str(memory))
    
    def _build_documents_from(self, memories: list) -> list:
        return [self._build_document_from(memory) for memory in memories]
    
   