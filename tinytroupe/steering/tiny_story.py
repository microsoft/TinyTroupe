from typing import List

from tinytroupe.extraction import logger
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
import tinytroupe.utils as utils
from tinytroupe import openai_utils

class TinyStory:
    """
    Every simulation tells a story. This class provides helper mechanisms to help with crafting appropriate stories in TinyTroupe.
    """


    def __init__(self, environment:TinyWorld=None, agent:TinyPerson=None, purpose:str="Be a realistic simulation.", context:str="",
                 first_n=10, last_n=20, include_omission_info:bool=True) -> None:
        """
        Initialize the story. The story can be about an environment or an agent. It also has a purpose, which
        is used to guide the story generation. Stories are aware that they are related to simulations, so one can
        specify simulation-related purposes.

        Args:
            environment (TinyWorld, optional): The environment in which the story takes place. Defaults to None.
            agent (TinyPerson, optional): The agent in the story. Defaults to None.
            purpose (str, optional): The purpose of the story. Defaults to "Be a realistic simulation.".
            context (str, optional): The current story context. Defaults to "". The actual story will be appended to this context.
            first_n (int, optional): The number of first interactions to include in the story. Defaults to 10.
            last_n (int, optional): The number of last interactions to include in the story. Defaults to 20.
            include_omission_info (bool, optional): Whether to include information about omitted interactions. Defaults to True.
        """
        
        # exactly one of these must be provided
        if environment and agent:
            raise Exception("Either 'environment' or 'agent' should be provided, not both")
        if not (environment or agent):
            raise Exception("At least one of the parameters should be provided")
        
        self.environment = environment
        self.agent = agent

        self.purpose = purpose

        self.current_story = context

        self.first_n = first_n
        self.last_n = last_n
        self.include_omission_info = include_omission_info
    
    def start_story(self, requirements="Start some interesting story about the agents.", number_of_words:int=100, include_plot_twist:bool=False) -> str:
        """
        Start a new story.
        """
        
        rendering_configs = {
                             "purpose": self.purpose,
                             "requirements": requirements,
                             "current_simulation_trace": self._current_story(),
                             "number_of_words": number_of_words,
                             "include_plot_twist": include_plot_twist
                            }

        messages = utils.compose_initial_LLM_messages_with_templates("story.start.system.mustache", "story.start.user.mustache", 
                                                                     base_module_folder="steering",
                                                                     rendering_configs=rendering_configs)
        next_message = openai_utils.client().send_message(messages, temperature=1.5)

        start = next_message["content"]

        self.current_story += utils.dedent(\
            f"""

            ## The story begins

            {start}

            """
            )

        return start
    
    def continue_story(self, requirements="Continue the story in an interesting way.", number_of_words:int=100, include_plot_twist:bool=False) -> str:
        """
        Propose a continuation of the story.
        """
        
        rendering_configs = {
                             "purpose": self.purpose,
                             "requirements": requirements,
                             "current_simulation_trace": self._current_story(),
                             "number_of_words": number_of_words,
                             "include_plot_twist": include_plot_twist
                            }

        messages = utils.compose_initial_LLM_messages_with_templates("story.continuation.system.mustache", "story.continuation.user.mustache", 
                                                                     base_module_folder="steering",
                                                                     rendering_configs=rendering_configs)
        next_message = openai_utils.client().send_message(messages)#, temperature=1.5)

        continuation = next_message["content"]

        self.current_story += utils.dedent(\
            f"""

            ## The story continues

            {continuation}

            """
            )

        return continuation

    def _current_story(self) -> str:
        """
        Get the current story.
        """
        interaction_history = ""
        
        if self.agent is not None:
            interaction_history += self.agent.pretty_current_interactions(first_n=self.first_n, last_n=self.last_n, include_omission_info=self.include_omission_info)
        elif self.environment is not None:
            interaction_history += self.environment.pretty_current_interactions(first_n=self.first_n, last_n=self.last_n, include_omission_info=self.include_omission_info)

        tmp_current_story = self.current_story
        tmp_current_story += utils.dedent(\
            f"""

            ## New simulation interactions to consider

            {interaction_history}

            """
            )
            
        return tmp_current_story
            
        

