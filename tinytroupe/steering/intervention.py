from typing import Union, List
from tinytroupe.extraction import logger
# Ensure JsonSerializableRegistry is imported
from tinytroupe.utils import JsonSerializableRegistry
from tinytroupe.experimentation import Proposition
from tinytroupe.agent import TinyPerson
import tinytroupe.utils as utils

DEFAULT_FIRST_N = 10
DEFAULT_LAST_N = 100

class InterventionBatch:
    """
    A wrapper around multiple Intervention instances that allows chaining set_* methods.
    """
    
    def __init__(self, interventions):
        self.interventions = interventions
    
    def __iter__(self):
        """Makes the batch iterable and compatible with list()"""
        return iter(self.interventions)
        
    def set_textual_precondition(self, text):
        for intervention in self.interventions:
            intervention.set_textual_precondition(text)
        return self
        
    def set_functional_precondition(self, func):
        for intervention in self.interventions:
            intervention.set_functional_precondition(func)
        return self
        
    def set_effect(self, effect_func):
        for intervention in self.interventions:
            intervention.set_effect(effect_func)
        return self
        
    def set_propositional_precondition(self, proposition, threshold=None):
        for intervention in self.interventions:
            intervention.set_propositional_precondition(proposition, threshold)
        return self
        
    def as_list(self):
        """Return the list of individual interventions."""
        return self.interventions



class Intervention(JsonSerializableRegistry):
    """
    Event-based intervention on agents or worlds. Only name, text_precondition,
    first_n, and last_n are serialized.

    Serialization limitations: After deserialization, the following attributes
    are NOT restored and must be rehydrated manually if needed:
      - targets: Re-assign with intervention.targets = [agent1, agent2, ...]
      - precondition_func: Re-assign with intervention.set_functional_precondition(func)
      - effect_func: Re-assign with intervention.set_effect(effect_func)
      - _last_text_precondition_proposition: Internal cache; will be repopulated on next check
    """

    serializable_attributes = ["name", "text_precondition", "first_n", "last_n"]

    def __init__(
        self,
        targets: Union[TinyPerson, "TinyWorld", List[TinyPerson], List["TinyWorld"]],
        first_n: int = DEFAULT_FIRST_N,
        last_n: int = DEFAULT_LAST_N,
        name: str = None,
    ):
        """
        Initialize the intervention.

        Args:
            targets: The target(s) to intervene on (TinyPerson or TinyWorld).
            first_n: Number of first interactions to consider in context.
            last_n: Number of last (most recent) interactions to consider.
            name: Name of the intervention.
        """
        
        self.targets = targets
        
        # initialize the possible preconditions
        self.text_precondition = None
        self.precondition_func = None

        # effects
        self.effect_func = None

        # which events to pay attention to?
        self.first_n = first_n
        self.last_n = last_n

        # name
        if name is None:
            self.name = self.name = f"Intervention {utils.fresh_id(self.__class__.__name__)}"
        else:
            self.name = name
        
        # the most recent precondition proposition used to check the precondition
        self._last_text_precondition_proposition = None
        self._last_functional_precondition_check = None

        # propositional precondition (optional)
        self.propositional_precondition = None
        self.propositional_precondition_threshold = None
        self._last_propositional_precondition_check = None

    ################################################################################################
    # Intervention flow
    ################################################################################################     
    @classmethod
    def create_for_each(cls, targets, first_n=DEFAULT_FIRST_N, last_n=DEFAULT_LAST_N, name=None):
        """
        Create separate interventions for each target in the list.
        
        Args:
            targets (list): List of targets (TinyPerson or TinyWorld instances)
            first_n (int): the number of first interactions to consider in the context
            last_n (int): the number of last interactions (most recent) to consider in the context
            name (str): the name of the intervention
            
        Returns:
            InterventionBatch: A wrapper that allows chaining set_* methods that will apply to all interventions
        """
        if not isinstance(targets, list):
            targets = [targets]
            
        interventions = [cls(target, first_n=first_n, last_n=last_n, 
                            name=f"{name}_{i}" if name else None) 
                        for i, target in enumerate(targets)]
        return InterventionBatch(interventions)
    
    def __call__(self):
        """
        Execute the intervention.

        Returns:
            bool: whether the intervention effect was applied.
        """
        return self.execute()

    def execute(self):
        """
        Execute the intervention. It first checks the precondition, and if it is met, applies the effect.
        This is the simplest method to run the intervention.

        Returns:
            bool: whether the intervention effect was applied.
        """
        logger.debug(f"Executing intervention: {self}")
        if self.check_precondition():
            self.apply_effect()
            logger.debug(f"Precondition was true, intervention effect was applied.")
            return True
        
        logger.debug(f"Precondition was false, intervention effect was not applied.")
        return False

    def check_precondition(self):
        """
        Check if the precondition for the intervention is met.
        """

        if self.text_precondition is not None: # Only create if text_precondition is set
            self._last_text_precondition_proposition = Proposition(self.targets, self.text_precondition, first_n=self.first_n, last_n=self.last_n)
            llm_precondition_check = self._last_text_precondition_proposition.check()
        else:
            llm_precondition_check = True # If no text precondition, it's considered met for this part

        
        #
        # Functional precondition
        #
        if self.precondition_func is not None:
            self._last_functional_precondition_check = self.precondition_func(self.targets)
        else:
            self._last_functional_precondition_check = True # default to True if no functional precondition is set
        

        return llm_precondition_check and self._last_functional_precondition_check


    def apply_effect(self):
        """
        Apply the intervention's effects. This won't check the precondition, 
        so it should be called after check_precondition.
        """
        if self.effect_func is not None: # Ensure effect_func is set
            self.effect_func(self.targets)
        else:
            logger.warning(f"Intervention {self.name} has no effect_func to apply.")
    

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
        return self # for chaining
    
    def set_functional_precondition(self, func):
        """
        Set a precondition as a function, to be evaluated by the code.

        Args:
            func (function): the function of the precondition. 
              Must have the a single argument, targets (either a TinyWorld or TinyPerson, or a list). Must return a boolean.
        """
        self.precondition_func = func
        return self # for chaining
    
    def set_effect(self, effect_func):
        """
        Set the effect of the intervention.

        Args:
            effect (str): the effect function of the intervention
        """
        self.effect_func = effect_func
        return self # for chaining
    
    def set_propositional_precondition(self, proposition:Proposition, threshold:int=None):
        """
        Set a propositional precondition using the Proposition class,
        optionally with a score threshold.
        """
        
        self.propositional_precondition = proposition
        self.propositional_precondition_threshold = threshold
        return self

    ################################################################################################
    # Inspection
    ################################################################################################

    def precondition_justification(self):
        """
        Get the justification for the precondition.
        """
        justification = ""

        # text precondition justification
        if self._last_text_precondition_proposition is not None and self._last_text_precondition_proposition.value is not None:
            justification += f"Textual Precondition ('{self.text_precondition}') evaluated to {self._last_text_precondition_proposition.value}. "
            justification += f"Justification: {self._last_text_precondition_proposition.justification} (Confidence: {self._last_text_precondition_proposition.confidence})\n"
        elif self.text_precondition is not None:
            justification += f"Textual Precondition ('{self.text_precondition}') was not evaluated yet or its evaluation failed.\n"

        # functional precondition justification
        if self.precondition_func is not None:

            justification += f"Functional precondition evaluated to {self._last_functional_precondition_check}.\n"
        
        if not justification:
            return "Preconditions have not been checked yet or no preconditions are defined."


        return justification.strip()
