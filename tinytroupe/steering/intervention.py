from tinytroupe.extraction import logger

# TODO under development
class Intervention:

    def __init__(self, agent=None, agents:list=None, environment=None, environments:list=None):
        """
        Initialize the intervention.

        Args:
            agent (TinyPerson): the agent to intervene on
            environment (TinyWorld): the environment to intervene on
        """
        # at least one of the parameters should be provided. Further, either a single entity or a list of them.
        if agent and agents:
            raise Exception("Either 'agent' or 'agents' should be provided, not both")
        if environment and environments:
            raise Exception("Either 'environment' or 'environments' should be provided, not both")
        if not (agent or agents or environment or environments):
            raise Exception("At least one of the parameters should be provided")

        # initialize the possible entities
        self.agents = None
        self.environments = None
        if agent is not None:
            self.agents = [self.agent]
        elif environment is not None:
            self.environments = [self.environment]

        # initialize the possible preconditions
        self.text_precondition = None
        self.precondition_func = None

        # effects
        self.effect_func = None

    ################################################################################################
    # Intervention flow
    ################################################################################################     
        
    def check_precondition(self):
        """
        Check if the precondition for the intervention is met.
        """
        raise NotImplementedError("TO-DO")

    def apply(self):
        """
        Apply the intervention.
        """
        self.effect_func(self.agents, self.environments)

    ################################################################################################
    # Pre and post conditions
    ################################################################################################

    def set_textual_precondition(self, text):
        """
        Set a precondition as text, to be interpreted by a language model.

        Args:
            text (str): the text of the precondition
        """
        self.text_precondition = text
    
    def set_functional_precondition(self, func):
        """
        Set a precondition as a function, to be evaluated by the code.

        Args:
            func (function): the function of the precondition. 
              Must have the arguments: agent, agents, environment, environments.
        """
        self.precondition_func = func
    
    def set_effect(self, effect_func):
        """
        Set the effect of the intervention.

        Args:
            effect (str): the effect function of the intervention
        """
        self.effect_func = effect_func
