from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.openai_utils import LLMRequest

class Proposition:

    def __init__(self, target, claim:str, first_n:int=None, last_n:int=None):
        """ 
        Define a proposition as a (textual) claim about a target, which can be a TinyWorld, a TinyPerson or several of any.

        Args:
            target (TinyWorld, TinyPerson, list): the target or targets of the proposition
            claim (str): the claim of the proposition
            first_n (int): the number of first interactions to consider in the context
            last_n (int): the number of last interactions (most recent) to consider in the context

        """
        
        if isinstance(target, TinyWorld) or isinstance(target, TinyPerson):
            self.targets = [target]
        elif isinstance(target, list) and all(isinstance(t, TinyWorld) or isinstance(t, TinyPerson) for t in target):
            self.targets = target
        else:
            raise ValueError("Target must be a TinyWorld, a TinyPerson or a list of them.")
        
        self.claim = claim

        self.first_n = first_n
        self.last_n = last_n

        self.value = None
        self.justification = None
        self.confidence = None
    
    def __call__(self, additional_context=None):
        return self.check(additional_context=additional_context)

    def check(self, additional_context="No additional context available."):

        context = ""

        for target in self.targets:
            target_trajectory = target.pretty_current_interactions(max_content_length=None, first_n=self.first_n, last_n=self.last_n)

            if isinstance(target, TinyPerson):
                context += f"## Agent '{target.name}' Simulation Trajectory\n\n"
            elif isinstance(target, TinyWorld):
                context += f"## Environment '{target.name}' Simulation Trajectory\n\n"

            context += target_trajectory + "\n\n"

        llm_request = LLMRequest(system_prompt="""
                                    You are a system that evaluates whether a proposition is true or false with respect to a given context. This context
                                    always refers to a multi-agent simulation. The proposition is a claim about the behavior of the agents or the state of their environment
                                    in the simulation.
                                
                                    The context you receive can contain one or more of the following:
                                    - the trajectory of a simulation of one or more agents. This means what agents said, did, thought, or perceived at different times.
                                    - the state of the environment at a given time.
                                
                                    Your output **must**:
                                      - necessarily start with the word "True" or "False";
                                      - optionally be followed by a justification.
                                 
                                    For example, the output could be of the form: "True, because <REASON HERE>." or merely "True" if no justification is needed.
                                    """, 

                                    user_prompt=f"""
                                    Evaluate the following proposition with respect to the context provided. Is it True or False?

                                    # Proposition

                                    This is the proposition you must evaluate:
                                    {self.claim}

                                    # Context

                                    The context you must consider is the following.

                                    {context}

                                    # Additional Context (if any)

                                    {additional_context}   
                                    """,

                                    output_type=bool)
        

        self.value = llm_request()
        self.justification = llm_request.response_justification      
        self.confidence = llm_request.response_confidence

        self.raw_llm_response = llm_request.response_raw

        return self.value
        

def check_proposition(target, claim:str, additional_context="No additional context available.",
                      first_n:int=None, last_n:int=None):
    """
    Check whether a propositional claim holds for the given target(s). This is meant as a
    convenience method to avoid creating a Proposition object (which you might not need
    if you are not interested in the justification or confidence of the claim, or will
    not use it again).

    Args:
        target (TinyWorld, TinyPerson, list): the target or targets of the proposition
        claim (str): the claim of the proposition
        additional_context (str): additional context to provide to the LLM
        first_n (int): the number of first interactions to consider in the context
        last_n (int): the number of last interactions (most recent) to consider in the context

    Returns:
        bool: whether the proposition holds for the given target(s)
    """

    proposition = Proposition(target, claim, first_n=first_n, last_n=last_n)
    return proposition.check(additional_context=additional_context)