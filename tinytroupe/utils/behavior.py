"""
Various utility functions for behavior analysis and action similarity computation.
"""

import textdistance


def _compute_single_action_jaccard_similarity(current_action, proposed_action):
    """
    Helper function to compute Jaccard similarity between two single actions.
    
    Args:
        current_action (dict): The current action to compare against.
        proposed_action (dict): The proposed action to compare.
        
    Returns:
        float: The Jaccard similarity score.
    """
    # Check if the action type and target are the same
    if ("type" in current_action) and ("type" in proposed_action) and ("target" in current_action) and ("target" in proposed_action) and \
            (current_action["type"] != proposed_action["type"] or current_action["target"] != proposed_action["target"]):
        return 0.0
    
    # Compute the Jaccard similarity between the content of the two actions
    current_action_content = current_action.get("content", "")
    proposed_action_content = proposed_action.get("content", "")

    # using textdistance to compute the Jaccard similarity
    jaccard_similarity = textdistance.jaccard(current_action_content, proposed_action_content)

    return jaccard_similarity


def next_action_jaccard_similarity(agent, proposed_next_action):
    """
    Computes the Jaccard similarity between the agent's current action and a proposed next action,
    modulo target and type (i.e., similarity will be computed using only the content, provided that the action 
    type and target are the same). If the action type or target is different, the similarity will be 0.

    Jaccard similarity is a measure of similarity between two sets, defined as the size of the intersection 
    divided by the size of the union of the sets.

    Args:
        agent (TinyPerson): The agent whose current action is to be compared.
        proposed_next_action (dict or list): The proposed next action (or list of actions) to be compared 
            against the agent's current action. If a list is provided, returns the maximum similarity 
            across all actions in the list.

    Returns:
        float: The Jaccard similarity score between the agent's current action and the proposed next action.
            If proposed_next_action is a list, returns the maximum similarity among all actions.
    """
    # Get the agent's current action
    current_action = agent.last_remembered_action()
    
    if current_action is None:
        return 0.0
    
    # Handle the case where proposed_next_action is a list of actions
    if isinstance(proposed_next_action, list):
        if not proposed_next_action:
            return 0.0
        # Return the maximum similarity across all actions in the list
        max_similarity = 0.0
        for action in proposed_next_action:
            if isinstance(action, dict):
                similarity = _compute_single_action_jaccard_similarity(current_action, action)
                max_similarity = max(max_similarity, similarity)
        return max_similarity
    
    # Single action case
    return _compute_single_action_jaccard_similarity(current_action, proposed_next_action)
