import json

from tinytroupe.agent import logger
from tinytroupe.agent.mental_faculty import TinyMentalFaculty
from tinytroupe.agent.grounding import BaseSemanticGroundingConnector
import tinytroupe.utils as utils


from llama_index.core import Document
from typing import Any
import copy
from typing import Union

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
        logger.debug(f"Storing {len(values)} values in memory: {values}")
        for i, value in enumerate(values):
            logger.debug(f"Storing value #{i}: {value}")
            self.store(value)

    def retrieve(self, first_n: int, last_n: int, include_omission_info:bool=True, item_type:str=None) -> list:
        """
        Retrieves the first n and/or last n values from memory. If n is None, all values are retrieved.

        Args:
            first_n (int): The number of first values to retrieve.
            last_n (int): The number of last values to retrieve.
            include_omission_info (bool): Whether to include an information message when some values are omitted.
            item_type (str, optional): If provided, only retrieve memories of this type.

        Returns:
            list: The retrieved values.
        
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_recent(self, item_type:str=None) -> list:
        """
        Retrieves the n most recent values from memory.

        Args:
            item_type (str, optional): If provided, only retrieve memories of this type.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_all(self, item_type:str=None) -> list:
        """
        Retrieves all values from memory.

        Args:
            item_type (str, optional): If provided, only retrieve memories of this type.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_relevant(self, relevance_target:str, top_k=20) -> list:
        """
        Retrieves all values from memory that are relevant to a given target.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def summarize_relevant_via_full_scan(self, relevance_target: str, batch_size: int = 20, item_type: str = None) -> str:
        """
        Performs a full scan of the memory, extracting and accumulating information relevant to a query.
        
        This function processes all memories (or memories of a specific type if provided),
        extracts information relevant to the query from each memory, and accumulates this
        information into a coherent response.
    
        Args:
            relevance_target (str): The query specifying what information to extract from memories.

            item_type (str, optional): If provided, only process memories of this type.
            batch_size (int): The number of memories to process in each extraction step. The larger it is, the faster the scan, but possibly less accurate.
              Also, a too large value may lead to prompt length overflows, though current models can handle quite large prompts.
    
        Returns:
            str: The accumulated information relevant to the query.
        """
        logger.debug(f"Starting FULL SCAN for relevance target: {relevance_target}, item type: {item_type}")

        # Retrieve all memories of the specified type
        memories = self.retrieve_all(item_type=item_type)
        
        # Initialize accumulation
        accumulated_info = ""

        # Process memories in batches of qty_of_memories_per_extraction
        for i in range(0, len(memories), batch_size):
            batch = memories[i:i + batch_size]
            logger.debug(f"Processing memory batch #{i} in full scan")

            # Concatenate memory texts for the batch
            batch_text = "# Memories to be processed\n\n"
            batch_text += "\n\n   ".join(str(memory) for memory in batch)

            # Extract information relevant to the query from the batch
            extracted_info = utils.semantics.extract_information_from_text(
                relevance_target,
                batch_text,
                context="""
                You are extracting information from the an agent's memory, 
                which might include actions, stimuli, and other types of events. You want to focus on the agent's experience, NOT on the agent's cognition or internal processes.
                
                Assume that:
                 - "actions" refer to behaviors produced by the agent,
                 - "stimulus" refer to events or information from the environment or other agents that the agent perceived.
                 
                 If you read about "assistant" and "user" roles, you can ignore them, as they refer to the agent's internal implementation mechanisms, not to the agent's experience.
                 In any case, anything related to "assistant" is the agent's output, and anything related to "user" is the agent's input. But you never refer to these roles in the report,
                 as they are an internal implementation detail of the agent, not part of the agent's experience.
                """
            )

            logger.debug(f"Extracted information from memory batch: {extracted_info}")

            # Skip if no relevant information was found
            if not extracted_info:
                continue

            # Accumulate the extracted information
            accumulated_info = utils.semantics.accumulate_based_on_query(
                query=relevance_target,
                new_entry=extracted_info,
                current_accumulation=accumulated_info,
                context="""
                You are producing a report based on information from an agent's memory. 
                You will put together all facts and experiences found that are relevant for the query, as a kind of summary of the agent's experience. 
                The report will later be used to guide further agent action. You focus on the agent's experience, NOT on the agent's cognition or internal processes.

                Assume that:
                  - "actions" refer to behaviors produced by the agent,
                  - "stimulus" refer to events or information from the environment or other agents that the agent perceived.
                  - if you read about "assistant" and "user" roles, you can ignore them, as they refer to the agent's internal implementation mechanisms, not to the agent's experience.
                    In any case, anything related to "assistant" is the agent's output, and anything related to "user" is the agent's input. But you never refer to these roles in the report,
                    as they are an internal implementation detail of the agent, not part of the agent's experience.
                
                Additional instructions for the accumulation process:
                  - If the new entry is redundant with respect to some information in the current accumulation, you update the current accumulation by adding to a special counter right by
                    the side of where the redundant information is found, so that the final report can later be used to guide further agent action (i.e., know which elements appeared more often).
                    The special counter **must** be formated like this: "[NOTE: this information appeared X times in the memory in different forms]". If the counter was not there originally, you add it. If it was there, you update
                    it with the new count.
                      * Example (first element was found 3 times, the second element only once, so no counter): 
                           "I play with and feed my cat [NOTE: this information appeared 3 times in the memory in different forms]. Cats are proud animals descendant from big feline hunters.". 
                       
                """
            )
            logger.debug(f"Accumulated information so far: {accumulated_info}")

        logger.debug(f"Total accumulated information after full scan: {accumulated_info}")
        
        return accumulated_info
        

    ###################################
    # Auxiliary methods
    ###################################

    def filter_by_item_type(self, memories:list, item_type:str) -> list:
        """
        Filters a list of memories by item type.

        Args:
            memories (list): The list of memories to filter.
            item_type (str): The item type to filter by.

        Returns:
            list: The filtered list of memories.
        """
        return [memory for memory in memories if memory["type"] == item_type]

    def filter_by_item_types(self, memories:list, item_types:list) -> list:
        """
        Filters a list of memories by multiple item types.

        Args:
            memories (list): The list of memories to filter.
            item_types (list): The list of item types to filter by.

        Returns:
            list: The filtered list of memories containing any of the specified types.
        """
        return [memory for memory in memories if memory["type"] in item_types]


class EpisodicMemory(TinyMemory):
    """
    Provides episodic memory capabilities to an agent. Cognitively, episodic memory is the ability to remember specific events,
    or episodes, in the past. This class provides a simple implementation of episodic memory, where the agent can store and retrieve
    messages from memory.
    
    Subclasses of this class can be used to provide different memory implementations.
    """

    MEMORY_BLOCK_OMISSION_INFO = {'role': 'assistant', 'content': "Info: there were other messages here, but they were omitted for brevity.", 'simulation_timestamp': None}

    def __init__(
        self, fixed_prefix_length: int = 20, lookback_length: int = 100
    ) -> None:
        """
        Initializes the memory.

        Args:
            fixed_prefix_length (int): The fixed prefix length. Defaults to 20.
            lookback_length (int): The lookback length. Defaults to 100.
        """
        self.fixed_prefix_length = fixed_prefix_length
        self.lookback_length = lookback_length

        # the definitive memory that records all episodic events
        self.memory = []
        
        # the current episode buffer, which is used to store messages during an episode
        self.episodic_buffer = []


    def commit_episode(self):
        """
        Ends the current episode, storing the episodic buffer in memory.
        """
        self.memory.extend(self.episodic_buffer)
        self.episodic_buffer = []
    
    def get_current_episode(self, item_types:list=None) -> list:
        """
        Returns the current episode buffer, which is used to store messages during an episode.

        Args:
            item_types (list, optional): If provided, only retrieve memories of these types. Defaults to None, which retrieves all types.

        Returns:
            list: The current episode buffer.
        """
        result = copy.copy(self.episodic_buffer)
        result = self.filter_by_item_types(result, item_types) if item_types is not None else result
        return result

    def count(self) -> int:
        """
        Returns the number of values in memory.
        """
        return len(self._memory_with_current_buffer())

    def clear(self, max_prefix_to_clear:int=None, max_suffix_to_clear:int=None):
        """
        Clears the memory, generating a permanent "episodic amnesia". 
        If max_prefix_to_clear is not None, it clears the first n values from memory.
        If max_suffix_to_clear is not None, it clears the last n values from memory. If both are None,
        it clears all values from memory.

        Args:
            max_prefix_to_clear (int): The number of first values to clear.
            max_suffix_to_clear (int): The number of last values to clear.
        """

        # clears all episodic buffer messages
        self.episodic_buffer = []

        # then clears the memory according to the parameters
        if max_prefix_to_clear is not None:
            self.memory = self.memory[max_prefix_to_clear:]

        if max_suffix_to_clear is not None:
            self.memory = self.memory[:-max_suffix_to_clear]

        if max_prefix_to_clear is None and max_suffix_to_clear is None:
            self.memory = []
    
    def _memory_with_current_buffer(self) -> list:
        """
        Returns the current memory, including the episodic buffer.
        This is useful for retrieving the most recent memories, including the current episode.
        """
        return self.memory + self.episodic_buffer
        
    ######################################
    # General memory methods
    ######################################
    def _store(self, value: Any) -> None:
        """
        Stores a value in memory.
        """
        self.episodic_buffer.append(value)

    def retrieve(self, first_n: int, last_n: int, include_omission_info:bool=True, item_type:str=None) -> list:
        """
        Retrieves the first n and/or last n values from memory. If n is None, all values are retrieved.

        Args:
            first_n (int): The number of first values to retrieve.
            last_n (int): The number of last values to retrieve.
            include_omission_info (bool): Whether to include an information message when some values are omitted.
            item_type (str, optional): If provided, only retrieve memories of this type.

        Returns:
            list: The retrieved values.
        
        """

        omisssion_info = [EpisodicMemory.MEMORY_BLOCK_OMISSION_INFO] if include_omission_info else []

        # use the other methods in the class to implement
        if first_n is not None and last_n is not None:
            return self.retrieve_first(first_n, include_omission_info=False, item_type=item_type) + omisssion_info + self.retrieve_last(last_n, include_omission_info=False, item_type=item_type)
        elif first_n is not None:
            return self.retrieve_first(first_n, include_omission_info, item_type=item_type)
        elif last_n is not None:
            return self.retrieve_last(last_n, include_omission_info, item_type=item_type)
        else:
            return self.retrieve_all(item_type=item_type)

    def retrieve_recent(self, include_omission_info:bool=True, item_type:str=None) -> list:
        """
        Retrieves the n most recent values from memory.

        Args:
            include_omission_info (bool): Whether to include an information message when some values are omitted.
            item_type (str, optional): If provided, only retrieve memories of this type.
        """
        omisssion_info = [EpisodicMemory.MEMORY_BLOCK_OMISSION_INFO] if include_omission_info else []
        
        # Filter memories if item_type is provided
        memories = self._memory_with_current_buffer() if item_type is None else self.filter_by_item_type(self._memory_with_current_buffer(), item_type)

        # compute fixed prefix
        fixed_prefix = memories[: self.fixed_prefix_length] + omisssion_info

        # how many lookback values remain?
        remaining_lookback = min(
            len(memories) - len(fixed_prefix) + (1 if include_omission_info else 0), self.lookback_length
        )

        # compute the remaining lookback values and return the concatenation
        if remaining_lookback <= 0:
            return fixed_prefix
        else:
            return fixed_prefix + memories[-remaining_lookback:]

    def retrieve_all(self, item_type:str=None) -> list:
        """
        Retrieves all values from memory.

        Args:
            item_type (str, optional): If provided, only retrieve memories of this type.
        """
        memories = self._memory_with_current_buffer() if item_type is None else self.filter_by_item_type(self._memory_with_current_buffer(), item_type)
        return copy.copy(memories)

    def retrieve_relevant(self, relevance_target: str, top_k:int) -> list:
        """
        Retrieves top-k values from memory that are most relevant to a given target.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_first(self, n: int, include_omission_info:bool=True, item_type:str=None) -> list:
        """
        Retrieves the first n values from memory.

        Args:
            n (int): The number of values to retrieve.
            include_omission_info (bool): Whether to include an information message when some values are omitted.
            item_type (str, optional): If provided, only retrieve memories of this type.
        """
        omisssion_info = [EpisodicMemory.MEMORY_BLOCK_OMISSION_INFO] if include_omission_info else []
        
        memories = self._memory_with_current_buffer() if item_type is None else self.filter_by_item_type(self._memory_with_current_buffer(), item_type)
        return memories[:n] + omisssion_info
    
    def retrieve_last(self, n: int=None, include_omission_info:bool=True, item_type:str=None) -> list:
        """
        Retrieves the last n values from memory.

        Args:
            n (int): The number of values to retrieve, or None to retrieve all values.
            include_omission_info (bool): Whether to include an information message when some values are omitted.
            item_type (str, optional): If provided, only retrieve memories of this type.
        """
        omisssion_info = [EpisodicMemory.MEMORY_BLOCK_OMISSION_INFO] if include_omission_info else []

        memories = self._memory_with_current_buffer() if item_type is None else self.filter_by_item_type(self._memory_with_current_buffer(), item_type)
        memories = memories[-n:] if n is not None else memories
                            
        return omisssion_info + memories  


@utils.post_init
class SemanticMemory(TinyMemory):
    """
    In Cognitive Psychology, semantic memory is the memory of meanings, understandings, and other concept-based knowledge unrelated to specific 
    experiences. It is not ordered temporally, and it is not about remembering specific events or episodes. This class provides a simple implementation
    of semantic memory, where the agent can store and retrieve semantic information.
    """

    serializable_attributes = ["memories", "semantic_grounding_connector"]

    def __init__(self, memories: list=None) -> None:
        self.memories = memories
       
        self.semantic_grounding_connector = None

        # @post_init ensures that _post_init is called after the __init__ method

    def _post_init(self): 
        """
        This will run after __init__, since the class has the @post_init decorator.
        It is convenient to separate some of the initialization processes to make deserialize easier.
        """

        if not hasattr(self, 'memories') or self.memories is None:
            self.memories = []

        if not hasattr(self, 'semantic_grounding_connector') or self.semantic_grounding_connector is None:
            self.semantic_grounding_connector = BaseSemanticGroundingConnector("Semantic Memory Storage")
            
            # TODO remove?
            #self.semantic_grounding_connector.add_documents(self._build_documents_from(self.memories))
    
        
    def _preprocess_value_for_storage(self, value: dict) -> Any:
        logger.debug(f"Preprocessing value for storage: {value}")

        if isinstance(value, dict):
            engram = {"role": "assistant",
                    "content": value['content'],
                    "type": value.get("type", "information"),  # Default to 'information' if type is not specified
                    "simulation_timestamp": value.get("simulation_timestamp", None)}

            # Refine the content of the engram is built based on the type of the value to make it more meaningful.
            if value['type'] == 'action':
                engram['content'] = f"# Action performed\n" +\
                        f"I have performed the following action at date and time {value['simulation_timestamp']}:\n\n"+\
                        f" {value['content']}"
            
            elif value['type'] == 'stimulus':
                engram['content'] = f"# Stimulus\n" +\
                        f"I have received the following stimulus at date and time {value['simulation_timestamp']}:\n\n"+\
                        f" {value['content']}"
            elif value['type'] == 'feedback':
                engram['content'] = f"# Feedback\n" +\
                        f"I have received the following feedback at date and time {value['simulation_timestamp']}:\n\n"+\
                        f" {value['content']}"
            elif value['type'] == 'consolidated':
                engram['content'] = f"# Consolidated Memory\n" +\
                        f"I have consolidated the following memory at date and time {value['simulation_timestamp']}:\n\n"+\
                        f" {value['content']}"
            elif value['type'] == 'reflection':
                engram['content'] = f"# Reflection\n" +\
                        f"I have reflected on the following memory at date and time {value['simulation_timestamp']}:\n\n"+\
                        f" {value['content']}"
            else:
                engram['content'] = f"# Information\n" +\
                        f"I have obtained following information at date and time {value['simulation_timestamp']}:\n\n"+\
                        f" {value['content']}"

            # else: # Anything else here?
            
        else:
            # If the value is not a dictionary, we just store it as is, but we still wrap it in an engram
            engram = {"role": "assistant",
                    "content": value,
                    "type": "information",  # Default to 'information' if type is not specified
                    "simulation_timestamp": None}

        logger.debug(f"Engram created for storage: {engram}")

        return engram

    def _store(self, value: Any) -> None:
        logger.debug(f"Preparing engram for semantic memory storage, input value: {value}")
        self.memories.append(value)  # Store the value in the local memory list

        # then econduct the value to a Document and store it in the semantic grounding connector
        # This is the actual storage in the semantic memory to allow semantic retrieval
        engram_doc = self._build_document_from(value)
        logger.debug(f"Storing engram in semantic memory: {engram_doc}")
        self.semantic_grounding_connector.add_document(engram_doc)
    
    def retrieve_relevant(self, relevance_target:str, top_k=20) -> list:
        """
        Retrieves all values from memory that are relevant to a given target.
        """
        return self.semantic_grounding_connector.retrieve_relevant(relevance_target, top_k)

    def retrieve_all(self, item_type:str=None) -> list:
        """
        Retrieves all values from memory.

        Args:
            item_type (str, optional): If provided, only retrieve memories of this type.
        """

        memories = []

        logger.debug(f"Retrieving all documents from semantic memory connector, a total of {len(self.semantic_grounding_connector.documents)} documents.")
        for document in self.semantic_grounding_connector.documents:
            logger.debug(f"Retrieving document from semantic memory: {document}")
            memory_text = document.text
            logger.debug(f"Document text retrieved: {memory_text}")

            try:
                memory = json.loads(memory_text)
                logger.debug(f"Memory retrieved: {memory}")
                memories.append(memory)                

            except json.JSONDecodeError as e:
                logger.warning(f"Could not decode memory from document text: {memory_text}. Error: {e}")

        if item_type is not None:
            memories = self.filter_by_item_type(memories, item_type)
        
        return memories
    
    #####################################
    # Auxiliary compatibility methods
    #####################################

    def _build_document_from(self, memory) -> Document:
        # TODO: add any metadata as well?
        
        # make sure we are dealing with a dictionary
        if not isinstance(memory, dict):
            memory = {"content": memory, "type": "information"}

        # ensures double quotes are used for JSON serialization, and maybe other formatting details
        memory_txt = json.dumps(memory, ensure_ascii=False)
        logger.debug(f"Building document from memory: {memory_txt}")
        
        return Document(text=memory_txt)

    def _build_documents_from(self, memories: list) -> list:
        return [self._build_document_from(memory) for memory in memories]


###################################################################################################
# Memory consolidation and optimization mechanisms
###################################################################################################
class MemoryProcessor:
    """
    Base class for memory consolidation and optimization mechanisms.
    """

    def process(self, memories: list, timestamp: str=None, context:Union[str, list, dict] = None, persona:Union[str, dict] = None, sequential: bool = True) -> list:
        """
        Transforms the given memories. Transformation can be anything from consolidation to optimization, depending on the implementation.
        
        Each memory is a dictionary of the form:
        {
          'role': role, 
          'content': content, 
           'type': 'action'/'stimulus'/'feedback', 
           'simulation_timestamp': timestamp
         }

        Args:
            memories (list): The list of memories to consolidate.
            sequential (bool): Whether the provided memories are to be interpreted sequentially (e.g., episodes in sequence) or not (e.g., abstract facts).
        
        Returns:
            list: A list with the consolidated memories, following the same format as the input memories, but different in content.
        """
        raise NotImplementedError("Subclasses must implement this method.")

class EpisodicConsolidator(MemoryProcessor):
    """
    Consolidates episodic memories into a more abstract representation, such as a summary or an abstract fact.
    """

    def process(self, memories: list, timestamp: str=None, context:Union[str, list, dict] = None, persona:Union[str, dict] = None, sequential: bool = True) -> list:
        logger.debug(f"STARTING MEMORY CONSOLIDATION: {len(memories)} memories to consolidate")

        enriched_context = f"CURRENT COGNITIVE CONTEXT OF THE AGENT: {context}" if context else "No specific context provided for consolidation."

        result = self._consolidate(memories, timestamp, enriched_context, persona)
        logger.debug(f"Consolidated {len(memories)} memories into: {result}")
        
        return result

    @utils.llm(enable_json_output_format=True, enable_justification_step=False)
    def _consolidate(self, memories: list, timestamp: str, context:str, persona:str) -> dict:
        """
        Given a list of input episodic memories, this method consolidates them into more organized structured representations, which however preserve all information and important details. 

        For this process, you assume:
          - This consolidation is being carried out by an agent, so the memories are from the agent's perspective. "Actions" refer to behaviors produced by the agent,
            while  "stimulus" refer to events or information from the environment or other agents that the agent has perceived.
                * Thus, in the consoldation you write "I have done X" or "I have perceived Y", not "the agent has done X" or "the agent has perceived Y".
          - The purpose of consolidation is to restructure and organize the most relevant information from the episodic memories, so that any facts learned therein can be used in future reasoning processes.
                * If a `context` is provided, you can use it to guide the consolidation process, making sure that the memories are consolidated in the most useful way under the given context.
                  For example, if the agent is looking for a specific type of information, you can focus the consolidation on that type of information, preserving more details about it
                  than you would otherwise.
                * If a `persona` is provided, you can use it to guide the consolidation process, making sure that the memories are consolidated in a way that is consistent with the persona.
                  For example, if the persona is that of a cat lover, you can focus the consolidation on the agent's experiences with cats, preserving more details about them than you would otherwise.
          - If the memory contians a `content` field, that's where the relevant information is found. Otherwise, consider the whole memory as relevant information.

        The consolidation process follows these rules:
          - Each consolidated memory groups together all similar entries: so actions are grouped together, stimuli go together, facts are grouped together, impressions are grouped together, 
            learned processes are grouped together, and ad-hoc elements go together too. Noise, minor details and irrelevant elements are discarded. 
            In all, you will produce at most the following consolidated entries (you can avoid some if appropriate, but not add more):
              * Actions: all actions are grouped together, giving an account of what the agent has done.
              * Stimuli: all stimuli are grouped together, giving an account of what the agent has perceived.
              * Facts: facts are extracted from the actions and stimuli, and then grouped together in a single entry, consolidating learning of objective facts.
              * Impressions: impressions, feelings, or other subjective experiences are also extracted,  and then grouped together in a single entry, consolidating subjective experiences.
              * Procedural: learned processes (e.g., how to do certain things) are also extracted, formatted in an algorithmic way (i.e., pseudo-code that is self-explanatory), and then grouped together in a 
                single entry, consolidating learned processes.
              * Ad-Hoc: important elements that do not correspond to these options are also grouped together in an ad-hoc single entry, consolidating other types of information.
          - Each consolidated memory is a comprehensive report of the relevant information from the input memories, preserving all details. The consolidation merely reorganizes the information,
            but does not remove any relevant information. The consolidated memories are not summaries, but rather a more organized and structured representation of the information in the input memories.
          

        Each input memory is a dictionary of the form:
            ```
            {
            "role": role, 
            "content": content, 
            "type": "action"/"stimulus"/"feedback"/"reflection", 
            "simulation_timestamp": timestamp
            }
            ``` 

        Each consolidated output memory is a dictionary of the form:
            ```
            {
            "content": content, 
            "type": "consolidated", 
            "simulation_timestamp": timestamp of the consolidation
            }  
            ```


         So the final value outputed **must** be a JSON composed of a list of dictionaries, each representing a consolidated memory, **always** with the following structure:
            ```
            {"consolidation":
                [
                    {
                        "content": content_1, 
                        "type": "consolidated", 
                        "simulation_timestamp": timestamp of the consolidation
                    },
                    {
                        "content": content_2, 
                        "type": "consolidated", 
                        "simulation_timestamp": timestamp of the consolidation
                    },
                    ...
                ]
            }
            ```

        Note:
          - because the output is a JSON, you must use double quotes for the keys and string values.
        ## Example (simplified)

        Here's a simplified example. Suppose the following memory contents are provided as input (simplifying here as just a bullet list of contents):
         - stimulus: "I have seen a cat, walking beautifully in the street"
         - stimulus: "I have seen a dog, barking loudly at a passerby, looking very aggressive"
         - action: "I have petted the cat, run around with him (or her?), saying a thousand times how cute it is, and how much I seem to like cats"
         - action: "I just realized that I like cats more than dogs. For example, look at this one, it is so cute, so civilized, so noble, so elegant, an inspiring animal! I had never noted this before! "
         - stimulus: "The cat is meowing very loudly, it seems to be hungry"
         - stimulus: "Somehow a big capivara has appeared in the room, it is looking at me with curiosity"

        Then, this would be a possible CORRECT output of the consolidation process (again, simplified, showing only contents in bullet list format):
          - consolidated actions: "I have petted the cat, run around with it, and expressed my admiration for cats."
          - consolidated stimuli: "I have seen a beautiful but hungry cat, a loud and agressive-looking dog, and - surprisingly - a capivara"
          - consolidated impressions: "I felt great admiration for the cat, they look like such noble and elegant animals."
          - consolidated facts: "I like cats more than dogs because they are cute and noble creatures."

        These are correct because they focus on the agent's experience. In contrast, this would be an INCORRECT output of the consolidation process:
          - consolidated actions: "the user sent messages about a cat, a dog and a capivara, and about playing with the cat."
          - consolidated facts: "the assistant has received various messages at different times, and has performed actions in response to them."

        These are incorrect because they focus on the agent's cognition and internal implementation mechanisms, not on the agent's experience.

        Args:
            memories (list): The list of memories to consolidate.
            timestamp (str): The timestamp of the consolidation, which will be used in the consolidated memories instead of any original timestamp.
            context (str, optional): Additional context to guide the consolidation process. This can be used to provide specific instructions or constraints for the consolidation.
            persona (str, optional): The persona of the agent, which can be used to guide the consolidation process. This can be used to provide specific instructions or constraints for the consolidation.

        Returns:
            dict: A dictionary with a single key "consolidation", whose value is a list of consolidated memories, each represented as a dictionary with the structure described above.
        """
        # llm annotation will handle the implementation
        
# TODO work in progress below         

class ReflectionConsolidator(MemoryProcessor):
    """
    Memory reflection mechanism.
    """

    def process(self, memories: list, timestamp: str=None, context:Union[str, list, dict] = None, persona:Union[str, dict] = None, sequential: bool = True) -> list:
        return self._reflect(memories, timestamp)

    def _reflect(self, memories: list, timestamp: str) -> list:
        """
        Given a list of input episodic memories, this method reflects on them and produces a more abstract representation, such as a summary or an abstract fact.
        The reflection process follows these rules:
          - Objective facts or knowledge that are present in the set of memories are grouped together, abstracted (if necessary) and summarized. The aim is to
            produce a semantic memory.
          - Impressions, feelings, or other subjective experiences are summarized into a more abstract representation, such as a summary or an abstract subjective fact.
          - Timestamps in the consolidated memories refer to the moment of the reflection, not to the source events that produced the original episodic memories.
          - No episodic memory is generated, all memories are consolidated as more abstract semantic memories.
          - In general, the reflection process aims to reduce the number of memories while preserving the most relevant information and removing redundant or less relevant information.
        """
        pass # TODO
    def _reflect(self, memories: list, timestamp: str) -> list:
        """
        Given a list of input episodic memories, this method reflects on them and produces a more abstract representation, such as a summary or an abstract fact.
        The reflection process follows these rules:
          - Objective facts or knowledge that are present in the set of memories are grouped together, abstracted (if necessary) and summarized. The aim is to
            produce a semantic memory.
          - Impressions, feelings, or other subjective experiences are summarized into a more abstract representation, such as a summary or an abstract subjective fact.
          - Timestamps in the consolidated memories refer to the moment of the reflection, not to the source events that produced the original episodic memories.
          - No episodic memory is generated, all memories are consolidated as more abstract semantic memories.
          - In general, the reflection process aims to reduce the number of memories while preserving the most relevant information and removing redundant or less relevant information.
        """
        pass # TODO

