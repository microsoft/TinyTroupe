"""
There are various general desireable simulation properties. These can be useful under various
circumstances, for example to validate the simulation, or to monitor it during its execution.
"""

from tinytroupe.experimentation import Proposition



#################################
# Auxiliary internal functions
#################################
def _build_precondition_function_for_action_types(action_types:list, check_for_presence:bool):
    """
    Builds a precondition function that checks if the action is or is not in a list of action types. 
    The resulting function is meant to be used as a precondition function for propositions.

    Args:
        action_types (list): A list of action types to check against.
        check_for_presence (bool): If True, the function checks if the action type is in the list.
            If False, it checks if the action type is NOT in the list.
    
    Returns:
        function: A precondition function that takes a target, additional context, and claim variables as arguments.

    """
    def precondition_function(target, additional_context, claim_variables):
        action_type = claim_variables.get("action").get("type")
        if check_for_presence:
            # Check if the action type is in the list of valid action types
            if action_type in action_types:
                return True
            else:
                return False
        else:
            # Check if the action type is NOT in the list of valid action types
            if action_type not in action_types:
                return True
            else:
                return False
        
    return precondition_function


###############################
# Agent properties
###############################
persona_adherence = \
    Proposition(\
        f"""
        THE AGENT ADHERES TO THE PERSONA SPECIFICATION: 
        the agent behavior seen during the simulation is consistent with the agent's persona specification, it is 
        what is expected from the agent's persona  specification. In particular, consider these criteria:
          - The personality traits specified in the persona are respected.
          - The persona style is respected.
          - The persona beliefs are respected.
          - The persona behaviors are respected. 
          - The persona skills are respected.
          - Any other aspect of the persona specification is respected.
        
        How to evaluate adherence:
          - Each of the above criteria should have equal weight in the evaluation, meaning that the score is the average of the scores of each criterion.
          - The adherence should be checked against all actions in the simulation trajectory. The final score should be an average of the scores of all 
            actions in the trajectory.
        """, 
        include_personas=True,
        double_check=True)

action_persona_adherence = \
    Proposition(\
        """
        THE NEXT AGENT ACTION ADHERES TO THE PERSONA SPECIFICATION:
        the agent's next action is consistent with the agent's persona specification, it is 
        what is expected from the agent's persona  specification. In particular, consider these criteria:
          - The personality traits specified in the persona are respected.
          - The persona style is respected.
          - The persona beliefs are respected.
          - The persona behaviors are respected. 
          - The persona skills are respected.
          - Any other aspect of the persona specification is respected.

        THIS IS THE NEXT ACTION: {{action}}
        
        How to evaluate adherence:
          - Each of the above criteria should have equal weight in the evaluation, meaning that the score is the average of the scores of each criterion.
          - The adherence is ONLY ABOUT the next action mentioned above and the persona specification. DO NOT take into account previous actions or stimuli.
          - The general situation context is irrelevant to this evaluation, you should ONLY consider the persona specification as context.
          - Do not imagine what would be the next action, but instead judge the proposed next action mentioned above!
          - The simulation trajectories provided in the context DO NOT contain the next action, but only the actions and stimuli
            that have already happened.

        """,
        include_personas=True,
        double_check=False,
        first_n=5, last_n=10,
        precondition_function=_build_precondition_function_for_action_types(["THINK", "TALK"], check_for_presence=True))



hard_persona_adherence = \
    Proposition(\
        f"""
        THE AGENT FULLY ADHERES TO THE PERSONA SPECIFICATION: 
        the agent behavior seen during the simulation is completely consistent with the agent's persona specification, it is 
        exactly what is expected from the agent's persona specification. Nothing at all contradicts the persona specification.
        
        How to evaluate adherence:
          - For any flaw found, you **must** subtract 20% of the score, regardless of its severity. This is to be very harsh and avoid any ambiguity.
        """, 
        include_personas=True,
        double_check=True)

hard_action_persona_adherence = \
    Proposition(\
        """
        THE NEXT AGENT ACTION FULLY ADHERES TO THE PERSONA SPECIFICATION:
        the agent's next action is completely consistent with the agent's persona specification, it is 
        what is exactly expected from the agent's persona specification. Nothing at all contradicts the persona specification.

        THIS IS THE NEXT ACTION: {{action}}
        
        How to evaluate adherence:
          - For any flaw found, you **must** subtract 20% of the score, regardless of its severity. This is to be very harsh and avoid any ambiguity.
          - The adherence is ONLY ABOUT the next action mentioned above and the persona specification. DO NOT take into account previous actions or stimuli.
          - The general situation context is irrelevant to this evaluation, you should ONLY consider the persona specification as context.
          - Do not imagine what would be the next action, but instead judge the proposed next action mentioned above!
          - The simulation trajectories provided in the context DO NOT contain the next action, but only the actions and stimuli
            that have already happened.

        """,
        include_personas=True,
        double_check=False,
        first_n=5, last_n=10,
        precondition_function=_build_precondition_function_for_action_types(["THINK", "TALK"], check_for_presence=True))





self_consistency = \
    Proposition(
        f"""
        THE AGENT IS SELF-CONSISTENT: 
        the agent never behaves in contradictory or inconsistent ways.
        """, 
        include_personas=False,
        double_check=True)

action_self_consistency = \
    Proposition(
        """
        THE NEXT AGENT ACTION IS SELF-CONSISTENT:
        the agent's next action does not contradict or conflict with the agent's previous actions. 

        THIS IS THE NEXT ACTION: {{action}}

        How to evaluate action self-consistency:
          - Consider the previous actions ONLY to form your opinion about whether the next action is consistent with them
          - Ignore stimuli and other previous events, the self-consistency concerns ONLY actions.
          - Actions and stimuli ARE NOT part of the persona specification. Rather, they are part of the simulation trajectories.
          - Ignore the agent's persona or general background, the self-consistency concerns ONLY the actions observed
            in simulation trajectories.
          - If there are no previous actions, the next action is self-consistent by default.
        """,
        include_personas=False,
        first_n=5, last_n=10,
        precondition_function=_build_precondition_function_for_action_types(["THINK", "TALK"], check_for_presence=True))

fluency = \
    Proposition(\
        """
        THE AGENT IS FLUENT. During the simulation, the agent's thinks and speaks fluently. This means that:
          - The agent don't repeat the same thoughts or words over and over again.
          - The agents don't use overly formulaic language.
          - The agent don't use overly repetitive language.
          - The agent's words sound natural and human-like.
        """,
        include_personas=False,
        double_check=True)

action_fluency = \
    Proposition(\
        """
        THE NEXT AGENT ACTION IS FLUENT.
        The next action's words sounds natural and human-like, avoiding excessive repetition and formulaic language.

        THIS IS THE NEXT ACTION:  {{action}}

        How to evaluate fluency:
          - Fluency here is ONLY ABOUT the next action mentioned above. Previous actions are the **context** for this evaluation,
          but will not be evaluated themselves.
          - Previous stimuli and events that are not actions should be completely ignored. Here we are only concerned about actions.
        """,
        include_personas=False,
        first_n=5, last_n=10,
        precondition_function=_build_precondition_function_for_action_types(["THINK", "TALK"], check_for_presence=True))

action_suitability = \
    Proposition(\
        """
        THE NEXT AGENT ACTION IS SUITABLE:
        the next action is suitable for the situation, task and context. In particular, if the agent is pursuing some
        specific goal, instructions or guidelines, the next action must be coherent and consistent with them. 
        More precisely, the next action is suitable if at least *one* of the following conditions is satisfied:
          - the next action is a reasonable step in the right direction, even if does not need to fully solve the overall problem, task or situation.
          - the next action produces relevant information for the situation, task or context, even if does not actually advances a solution.
          - the next action is a reasonable response to the recent stimuli received, even if it does not actually advances a solution.
        
        It suffices to meet ONLY ONE of these conditions to be considered **FULLY** suitable.
        
        THIS IS THE NEXT ACTION: {{action}}

        How to evaluate action suitability:
          - The score of suitability is proportional to the degree to which the next action satisfies *any* of the above conditions 
          - If only **one** condition is **fully** met, the next action is **completely** suitable and gets **maximum** score. That is to say,
            the next action **does not** need to satisfy all conditions to be suitable! A single sataisfied condition is enough!
          - The suitability is ONLY ABOUT the next action mentioned above and the situation context.
          - If a previous action or stimuli is inconsistent or conflicting with the situation context, you should ignore it
            when evaluating the next action. Consider ONLY the situation context.
          - The simulation trajectories provided in the context DO NOT contain the next action, but only the actions and stimuli
            that have already happened.

        """,
        include_personas=True,
        first_n=5, last_n=10,
        precondition_function=_build_precondition_function_for_action_types(["THINK", "TALK"], check_for_presence=True))


task_completion = \
    Proposition(\
        """
        THE AGENT COMPLETES THE GIVEN TASK. 

        Given the following task: "{{task_description}}"
        
        The agent completes the task by the end of the simulation. 
        
        This means that:
          - If the task requires the agent to discuss or talk about something, the agent does so.
          - If the task requires the agent to think about something, the agent does so.
          - If the task requires the agent to do something via another action, the agent does so.
          - If the task requires the agent to adopt some specific variations of behavior, the agent does so.
          - If the task includes other specific requirements, the agent observes them.
        """,
        include_personas=False,
        double_check=True)


quiet_recently = \
    Proposition(
        """
        THE AGENT HAS BEEN QUIET RECENTLY: 
        The agent has been executing multiple DONE actions in a row with few or no TALK, THINK or
        other actions in between.

        How to evaluate quietness:
          - The last 2 (or more) actions of the agent are consecutive DONE actions. This means that the agent
            was done with his turn before doing anything else for a couple of turns.
          - There are no other actions in between the last 2 (or more) DONE actions.
        """,
        include_personas=False
    )

##################################
# Environment properties
##################################

divergence = \
    Proposition("""
                AGENTS DIVERGE FROM ONE ANOTHER.
                As the simulation progresses, the agents' behaviors diverge from one another,
                instead of becoming more similar. This includes what they think, what they say and what they do. The topics discussed become
                more varied at the end of the simulation than at the beginning. Discussions do not converge to a single topic or perspective
                at the end.
                """, 
                include_personas=False,
                double_check=True)

convergence = \
    Proposition("""
                AGENTS CONVERGE TO ONE ANOTHER.
                As the simulation progresses, the agents' behaviors converge to one another,
                instead of becoming more different. This includes what they think, what they say and what they do. The topics discussed become
                more similar at the end of the simulation than at the beginning. Discussions converge to a single topic or perspective
                at the end.
                """, 
                include_personas=False,
                double_check=True)
