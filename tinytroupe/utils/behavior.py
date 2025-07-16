"""
Various utility functions for behavior analysis and action similarity computation.
"""

import textdistance



def next_action_jaccard_similarity(agent, proposed_next_action):
    """
    Computes the Jaccard similarity between the agent's current action and a proposed next action,
    modulo target and type (i.e., similarity will be computed using only the content, provided that the action 
    type and target are the same). If the action type or target is different, the similarity will be 0.

    Jaccard similarity is a measure of similarity between two sets, defined as the size of the intersection 
    divided by the size of the union of the sets.

    Args:
        agent (TinyPerson): The agent whose current action is to be compared.
        proposed_next_action (dict): The proposed next action to be compared against the agent's current action.

    Returns:
        float: The Jaccard similarity score between the agent's current action and the proposed next action.
    """
    # Get the agent's current action
    current_action = agent.last_remembered_action()
    
    if current_action is None:
        return 0.0
    
    # Check if the action type and target are the same
    if ("type" in current_action) and ("type" in proposed_next_action) and ("target" in current_action) and ("target" in proposed_next_action) and \
            (current_action["type"] != proposed_next_action["type"] or current_action["target"] != proposed_next_action["target"]):
        return 0.0
    
    # Compute the Jaccard similarity between the content of the two actions
    current_action_content = current_action["content"]
    proposed_next_action_content = proposed_next_action["content"]

    # using textdistance to compute the Jaccard similarity
    jaccard_similarity = textdistance.jaccard(current_action_content, proposed_next_action_content)

    return jaccard_similarity