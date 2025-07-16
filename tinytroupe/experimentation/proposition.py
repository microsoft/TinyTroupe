import json
from chevron import render

from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.utils import LLMChat, indent_at_current_level
from tinytroupe.experimentation import logger


from tinytroupe import default

class Proposition:

    MIN_SCORE = 0
    MAX_SCORE = 9

    def __init__(self, claim:str, target=None, include_personas:bool=False, first_n:int=None, last_n:int=None,
                 double_check:bool=False, use_reasoning_model:bool=False, precondition_function=None):
        """ 
        Define a proposition as a (textual) claim about a target, which can be a TinyWorld, a TinyPerson or several of any.
        The proposition's truth value can then either be checked as a boolean or computed as an integer score denoting the degree of truth.

        Sometimes a proposition is better used in an implicative way, i.e., as a claim that is true or false depending on the context. For example, when
        considering the latest agent action, the proposition might be applicable only to certain agent action types. To allow this,
        this class allows to define a precondition function, which effectivelly turns a proposition `P` into `Precondition --> P`. This is logically equivalent to
        `not P or Precondition`. In other words:
          - if the precondition is true, then the proposition is evaluated normally (as a boolean or a score).
          - if the precondition is false, then the proposition is always true (or with highest score).
          - if the precondition is None, then the proposition is evaluated normally (as a boolean or a score).
        

        Args:
            
            claim (str): the claim of the proposition
            target (TinyWorld, TinyPerson, list): the target or targets of the proposition. If not given, it will have to be specified later.
            include_personas (bool): whether to include the persona specifications of the agents in the context
            first_n (int): the number of first interactions to consider in the context
            last_n (int): the number of last interactions (most recent) to consider in the context
            double_check (bool): whether to ask the LLM to double check its answer. This tends to give more strict answers, but is slower and more expensive.
            use_reasoning_model (bool): whether to use a reasoning model to evaluate the proposition
            precondition_function (function): a Boolean function that indicates whether the proposition can be evaluated or not. This is useful to avoid evaluating propositions that are not relevant for the current context. If the precondition fails, the proposition is always interpreted as true (or with highest score). MUST have named arguments `target`, `additional_context`, and `claim_variables` (note: you can use a lambda for this too, e.g., `lambda target, additional_context, claim_variables: ...`).

        """
        
        self.claim = claim
        self.targets = self._target_as_list(target)
        self.include_personas = include_personas
        
        self.first_n = first_n
        self.last_n = last_n

        self.double_check = double_check

        self.use_reasoning_model = use_reasoning_model

        self.precondition_function = precondition_function

        # the chat with the LLM is preserved until the proposition is re-evaluated. While it is available,
        # the chat can be used to follow up on the proposition, e.g., to ask for more details about the evaluation.
        self.llm_chat = None
        
        self.value = None
        self.justification = None
        self.confidence = None
        self.recommendations = None

    def __copy__(self):
        """
        Create a shallow copy of the proposition without any evaluation state.
        
        Returns:
            Proposition: A new proposition with the same configuration parameters.
        """
        new_prop = Proposition(
            claim=self.claim,
            target=self.targets,
            include_personas=self.include_personas,
            first_n=self.first_n,
            last_n=self.last_n,
            double_check=self.double_check,
            use_reasoning_model=self.use_reasoning_model,
            precondition_function=self.precondition_function
        )
        return new_prop

    def copy(self):
        """
        Create a shallow copy of the proposition without any evaluation state.
        
        Returns:
            Proposition: A new proposition with the same configuration parameters.
        """
        return self.__copy__()
    

    def __call__(self, target=None, additional_context=None, claim_variables:dict={}, return_full_response:bool=False) -> bool:
        return self.check(target=target, additional_context=additional_context, claim_variables=claim_variables, return_full_response=return_full_response)
    

    def _check_precondition(self, target, additional_context:str, claim_variables:dict) -> bool:
        """
        Check whether the proposition can be evaluated or not.
        """

        if self.precondition_function is None:
            return True
        else:
            return self.precondition_function(target=target, additional_context=additional_context, claim_variables=claim_variables)

    def check(self, target=None, additional_context="No additional context available.", claim_variables:dict={}, return_full_response:bool=False) -> bool:
        """
        Check whether the proposition holds for the given target(s).
        """

        current_targets = self._determine_target(target)

        if self._check_precondition(target=current_targets, additional_context=additional_context, claim_variables=claim_variables) == False:
            self.value = True
            self.justification = "The proposition is trivially true due to the precondition being false."
            self.confidence = 1.0
            self.full_evaluation_response = {"value": True, "justification": self.justification, "confidence": self.confidence}
        
        else: # precondition is true or None

            context = self._build_context(current_targets)

            # might use a reasoning model, which could allow careful evaluation of the proposition.
            model = self._model(self.use_reasoning_model)

            #render self.claim using the claim_variables via chevron
            rendered_claim = render(self.claim, claim_variables)      

            self.llm_chat = LLMChat(system_prompt="""
                                        You are a system that evaluates whether a proposition is true or false with respect to a given context. This context
                                        always refers to a multi-agent simulation. The proposition is a claim about the behavior of the agents or the state of their environment
                                        in the simulation.
                                    
                                        The context you receive can contain one or more of the following:
                                        - the trajectory of a simulation of one or more agents. This means what agents said, did, thought, or perceived at different times.
                                        - the state of the environment at a given time.
                                    
                                        Your output **must**:
                                        - necessarily start with the word "True" or "False";
                                        - optionally be followed by a justification. Please provide a very detailed justifications, including very concrete and specific mentions to elements that contributed to reducing or increasing the score. Examples:
                                              * WRONG JUSTIFICATION (too abstract) example: " ... the agent behavior did not comply with key parts of its specification, thus a reduced score ... "
                                              * CORRECT JUSTIFICATION (very precise) example: " ... the agent behavior deviated from key parts of its specification, specifically: S_1 was not met because <reason>, ..., S_n was not met becasue <reason>. Thus, a reduced score ..."
                                        
                                        For example, the output could be of the form: "True, because <HIGHLY DETAILED, CONCRETE AND SPECIFIC REASONS HERE>." or merely "True" if no justification is needed.
                                        """, 

                                        user_prompt=f"""
                                        Evaluate the following proposition with respect to the context provided. Is it True or False?

                                        # Proposition

                                        This is the proposition you must evaluate:

                                            ```
                                            {indent_at_current_level(rendered_claim)}
                                            ```

                                        # Context

                                        The context you must consider is the following.

                                        {indent_at_current_level(context)}

                                        # Additional Context (if any)

                                        {indent_at_current_level(additional_context)}

                                        """,

                                        output_type=bool,
                                        enable_reasoning_step=True,

                                        temperature=0.5,
                                        frequency_penalty=0.0, 
                                        presence_penalty=0.0,
                                        model=model)
            
            self.value = self.llm_chat()

            if self.double_check:
                self.llm_chat.add_user_message("Are you sure? Please revise your evaluation to make is correct as possible.")
                revised_value = self.llm_chat()
                if revised_value != self.value:
                    logger.warning(f"The LLM revised its evaluation: from {self.value} to {revised_value}.")
                    self.value = revised_value

            self.reasoning = self.llm_chat.response_reasoning
            self.justification = self.llm_chat.response_justification      
            self.confidence = self.llm_chat.response_confidence

            self.full_evaluation_response = self.llm_chat.response_json

        # return the final result, either only the value or the full response
        if not return_full_response:
            return self.value
        else:
            return self.full_evaluation_response
        
    def score(self, target=None, additional_context="No additional context available.", claim_variables:dict={}, return_full_response:bool=False) -> int:
        """
        Compute the score for the proposition with respect to the given context.
        """

        current_targets = self._determine_target(target)

        if self._check_precondition(target=current_targets, additional_context=additional_context, claim_variables=claim_variables) == False:
            self.value = self.MAX_SCORE
            self.justification = "The proposition is trivially true due to the precondition being false."
            self.confidence = 1.0
            self.full_evaluation_response = {"value": self.value, "justification": self.justification, "confidence": self.confidence}
        
        else: # precondition is true or None

            # build the context with the appropriate targets
        
            context = self._build_context(current_targets)

            # might use a reasoning model, which could allow careful evaluation of the proposition.
            model = self._model(self.use_reasoning_model)

            #render self.claim using the claim_variables via chevron
            rendered_claim = render(self.claim, claim_variables)      

            self.llm_chat = LLMChat(system_prompt=f"""
                                        You are a system that computes an integer score (between {Proposition.MIN_SCORE} and {Proposition.MAX_SCORE}, inclusive) about how much a proposition is true or false with respect to a given context. 
                                        This context always refers to a multi-agent simulation. The proposition is a claim about the behavior of the agents or the state of their environment in the simulation.

                                        The minimum score of {Proposition.MIN_SCORE} means that the proposition is completely false in all of the simulation trajectories, while the maximum score of {Proposition.MAX_SCORE} means that the proposition is completely true in all of the simulation trajectories. Intermediate scores are used to express varying degrees of partially met expectations. When assigning a score, follow these guidelines:
                                        - If the data required to judge the proposition is not present, assign a score of {Proposition.MAX_SCORE}. That is to say, unless there is evidence to the contrary, the proposition is assumed to be true.
                                        - The maximum score of {Proposition.MAX_SCORE} should be assigned when the evidence is as good as it can be. That is to say, all parts of the observed simulation trajectory support the proposition, no exceptions.
                                        - The minimum score of {Proposition.MIN_SCORE} should be assigned when the evidence is as bad as it can be. That is to say, all parts of the observed simulation trajectory contradict the proposition, no exceptions.
                                        - Intermediate scores should be assigned when the evidence is mixed. The intermediary score should be proportional to the balance of evidence, according to these bands:
                                                  0 = The proposition is without any doubt completely false;
                                            1, 2, 3 = The proposition has little support and is mostly false;
                                               4, 5 = The evidence is mixed, and the proposition is as much true as it is false;
                                            6, 7, 8 = The proposition is well-supported and is mostly true;
                                                  9 = The proposition is without any doubt completely true.
                                        - You should be very rigorous in your evaluation and, when in doubt, assign a lower score.
                                        - If there are critical flaws in the evidence, you should move your score to a lower band entirely.
                                        - If the provided context has inconsistent information, you **must** consider **only** the information that gives the lowest score, since we want to be rigorous and if necessary err to the lower end.
                                          * If you are considering the relationship between an agent specification and a simulation trajectory, you should consider the worst possible interpretation of: the agent specification; the simulation trajectory; or the relationship between the two.
                                          * These contradictions can appear anywhere in the context. When they do, you **always** adopt the worst possible inteprpretation, because we want to be rigorous and if necessary err to the lower end. It does not matter if the contradiction shows only very rarely, or if it is very small. It is still a contradiction and should be considered as such.
                                          * DO NOT dismiss contradictions as specification errors. They are part of the evidence and should be considered as such. They **must** be **always** taken into account when computing the score. **Never** ignore them.
                                        
                                        Additionally, whenever you are considering the relationship between an agent specification and a simulation trajectory, the following additional scoring guidelines apply:
                                          - All observed behavior **must** be easily mapped back to clear elements of the agent specification. If you cannot do this, you should assign a lower score.
                                          - Evaluate **each** relevant elements in the simulation trajectory (e.g., actions, stimuli) one by one, and assign a score to each of them. The final score is the average of all the scores assigned to each element.
                                                                            
                                        The proposition you receive can contain one or more of the following:
                                          - A statement of fact, which you will score.
                                          - Additional context, which you will use to evaluate the proposition. In particular, it might refer or specify potentail parts
                                            of similation trajectories for consideration. These might be formatted differently than what is given in the main context, so
                                            make sure you read them carefully.
                                          - Additional instructions on how to evaluate the proposition.

                                        The context you receive can contain one or more of the following:
                                          - the persona specifications of the agents in the simulation. That is to say, what the agents **are**, not what they are **doing**.
                                          - the simulation trajectories of one or more agents. This means what agents said, did, thought, or perceived at different times.
                                            These trajectories **are not** part of the persona specification.
                                          - the state of the environment at a given time.
                                          - additional context that can vary from simulation to simulation.
                                        
                                        To interpret the simulation trajectories, use the following guidelines:
                                          - Agents can receive stimuli and produce actions. You might be concerned with both or only one of them, depending on the specific proposition.
                                          - Actions are clearly marked with the text "acts", e.g., "Agent A acts: [ACTION]". If it is not thus marked, it is not an action.
                                          - Stimuli are denoted by "--> Agent name: [STIMULUS]".
                                    
                                        Your output **must**:
                                          - necessarily start with an integer between {Proposition.MIN_SCORE} and {Proposition.MAX_SCORE}, inclusive;
                                          - be followed by a justification. Please provide a very detailed justifications, including very concrete and specific mentions to elements that contributed to reducing or increasing the score. Examples:
                                              * WRONG JUSTIFICATION (too abstract) example: " ... the agent behavior did not comply with key parts of its specification, thus a reduced score ... "
                                              * CORRECT JUSTIFICATION (very precise) example: " ... the agent behavior deviated from key parts of its specification, specifically: S_1 was not met because <reason>, ..., S_n was not met becasue <reason>. Thus, a reduced score ..."
                                        
                                        For example, the output could be of the form: "1, because <HIGHLY DETAILED, CONCRETE AND SPECIFIC REASONS HERE>."
                                        """, 

                                        user_prompt=f"""
                                        Compute the score for the following proposition with respect to the context provided. Think step-by-step to assign the most accurate score and provide a justification.

                                        # Proposition

                                        This is the proposition you must evaluate:
                                        
                                            ```
                                            {indent_at_current_level(rendered_claim)}
                                            ```

                                        # Context

                                        The context you must consider is the following.

                                        {indent_at_current_level(context)}

                                        # Additional Context (if any)

                                        {indent_at_current_level(additional_context)}   
                                        """,

                                        output_type=int,
                                        enable_reasoning_step=True,

                                        temperature=1.0,
                                        frequency_penalty=0.0, 
                                        presence_penalty=0.0,

                                        # Use a reasoning model, which allows careful evaluation of the proposition.
                                        model=model)
            

            self.value = self.llm_chat()

            if self.double_check:
                self.llm_chat.add_user_message("Are you sure? Please revise your evaluation to make is correct as possible.")
                revised_value = self.llm_chat()
                if revised_value != self.value:
                    logger.warning(f"The LLM revised its evaluation: from {self.value} to {revised_value}.")
                    self.value = revised_value

            self.reasoning = self.llm_chat.response_reasoning
            self.justification = self.llm_chat.response_justification      
            self.confidence = self.llm_chat.response_confidence

            self.full_evaluation_response = self.llm_chat.response_json
        
        # return the final result, either only the value or the full response
        if not return_full_response:
            return self.value
        else:
            return self.full_evaluation_response
    
    def recommendations_for_improvement(self):
        """
        Get recommendations for improving the proposition.
        """

        # TODO this is not working, let's try something else
        #
        #if self.llm_chat is None:
        #    raise ValueError("No evaluation has been performed yet. Please evaluate the proposition before getting recommendations.")
#
        #self.llm_chat.add_system_message(\
        #    """
        #    You will now act as a system that provides recommendations for the improvement of the scores previously assigned to propositions.
        #    You will now output text that contains analysises, recommendations and other information as requested by the user.
        #    """)
#
        #self.llm_chat.add_user_message(\
        #    """    
        #    To help improve the score next time, please list the following in as much detail as possible:
        #      - all recommendations for improvements based on the current score.
        #      - all criteria you are using to assign scores, and how to best satisfy them
#
        #    For both cases:
        #      - besides guidelines, make sure to provide plenty of concrete examples of what to be done in order to maximize each criterion.
        #      - avoid being generic or abstract. Instead, all of your criteria and recommendations should be given in very concrete terms that would work specifically for the case just considered.            
        #    
        #    Note that your output is a TEXT with the various recommendations, information and tips, not a JSON object.
#
        #    Recommendations:
        #    """)
        #
        #recommendation = self.llm_chat(output_type=str, enable_json_output_format=False)
        recommendation = "No additional recommendations at this time."
        return recommendation

    def _model(self, use_reasoning_model):
        if use_reasoning_model:
            return default["reasoning_model"]
        else:
            return default["model"]
    
    def _determine_target(self, target):
        """
        Determine the target for the proposition. If a target was provided during initialization, it must not be provided now (i.e., the proposition is immutable).
        If no target was provided during initialization, it must be provided now.
        """
       # If no target was provided during initialization, it must be provided now.
        if self.targets is None :
            if target is None:
                raise ValueError("No target specified. Please provide a target.")
            else:
                return self._target_as_list(target)

        # If it was provided during initialization, it must not be provided now (i.e., the proposition is immutable).
        else:
            if target is not None:
                raise ValueError("Target already specified. Please do not provide a target.")
            else:
                return self.targets
        
    def _build_context(self, current_targets):

        #
        # build the context with the appropriate targets
        #
        context = ""

        for target in current_targets:
            target_trajectory = target.pretty_current_interactions(max_content_length=None, first_n=self.first_n, last_n=self.last_n)

            if isinstance(target, TinyPerson):
                if self.include_personas:
                    context += f"## Agent '{target.name}' Persona Specification\n\n"
                    context += "Before presenting the actual simulation trajectory, here is the persona specification of the agent that was used to produce the simulation.\n\n"
                    context += "This IS NOT the actual simulation, but only the static persona specification of the agent.\n\n"
                    context += f"persona={json.dumps(target._persona, indent=4)}\n\n"
                
                context += f"## Agent '{target.name}' Simulation Trajectory (if any)\n\n"
            elif isinstance(target, TinyWorld):
                if self.include_personas:
                    context += f"## Environment '{target.name}' Personas Specifications\n\n"
                    context += "Before presenting the actual simulation trajectory, here are the persona specifications of the agents used to produce the simulation.\n\n"
                    context += "This IS NOT the actual simulation, but only the static persona specification of the agent.\n\n"
                    for agent in target.agents:
                        context += f"### Agent '{agent.name}' Persona Specification\n\n"
                        context += f"persona={json.dumps(agent._persona, indent=4)}\n\n"
                    
                context += f"## Environment '{target.name}' Simulation Trajectory (if any)\n\n"

            context += target_trajectory + "\n\n"

        return context

    def _target_as_list(self, target):
        if target is None:
            return None 
        elif isinstance(target, TinyWorld) or isinstance(target, TinyPerson):
            return [target]
        elif isinstance(target, list) and all(isinstance(t, TinyWorld) or isinstance(t, TinyPerson) for t in target):
            return target
        else:
            raise ValueError("Target must be a TinyWorld, a TinyPerson or a list of them.")


def check_proposition(target, claim:str, additional_context="No additional context available.",
                      first_n:int=None, last_n:int=None, 
                      return_full_response:bool=False):
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
        return_full_response (bool): whether to return the full response from the LLM, including justification and confidence

    Returns:
        bool: whether the proposition holds for the given target(s)
    """

    proposition = Proposition(claim, target, first_n=first_n, last_n=last_n)
    return proposition.check(additional_context=additional_context, return_full_response=return_full_response)


def compute_score(target, claim:str,
                      additional_context="No additional context available.",
                      first_n:int=None, last_n:int=None,
                      return_full_response:bool=False):
    """
    Compute a score about whether a claim holds for the given target(s). This is meant as a
    convenience method to avoid creating a Score object (which you might not need
    if you are not interested in the justification or confidence of the claim, or will
    not use it again).

    Args:
        target (TinyWorld, TinyPerson, list): the target or targets of the proposition
        claim (str): the claim of the proposition
        additional_context (str): additional context to provide to the LLM
        first_n (int): the number of first interactions to consider in the context
        last_n (int): the number of last interactions (most recent) to consider in the context
        return_full_response (bool): whether to return the full response from the LLM, including justification and confidence

    Returns:
        bool: whether the proposition holds for the given target(s)
    """

    score = Proposition(claim, target,
                  first_n=first_n, last_n=last_n)
    return score.compute(additional_context=additional_context, return_full_response=return_full_response)