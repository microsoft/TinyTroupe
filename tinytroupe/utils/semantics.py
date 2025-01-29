"""
Semantic-related mechanisms.
"""
from tinytroupe.utils import llm

@llm()
def rephrase(observation, rule) -> str:
    """
    Given an observation and a rule, this function rephrases or completely changes the observation in accordance with what the rule
    specifies.


    ## Examples

        Observation: "You know, I am so sad these days."
        Rule: "I am always happy and depression is unknown to me"
        Modified observation: "You know, I am so happy these days."

    Args:
        observation: The observation that should be rephrased or changed. Something that is said or done, or a description of events or facts.
        rule: The rule that specifies what the modidfied observation should comply with.        
    
    Returns:
        str: The rephrased or modified observation.
    """
    # llm decorator will handle the body of this function

@llm()
def restructure_as_observed_vs_expected(description) -> str:
    """
    Given the description of something (either a real event or abstract concept), but that violates an expectation, this function 
    extracts the following elements from it:

        - OBSERVED: The observed event or statement.
        - BROKEN EXPECTATION: The expectation that was broken by the observed event.
        - REASONING: The reasoning behind the expectation that was broken.
    
    If in reality the description does not mention any expectation violation, then the function should instead extract
    the following elements:

        - OBSERVED: The observed event.
        - MET EXPECTATION: The expectation that was met by the observed event.
        - REASONING: The reasoning behind the expectation that was met.

    This way of restructuring the description can be useful for downstream processing, making it easier to analyze or
    modify system outputs, for example.

    ## Examples

        Input: "Ana mentions she loved the proposed new food, a spicier flavor of gazpacho. However, this goes agains her known dislike
                of spicy food."
        Output: 
            "OBSERVED: Ana mentions she loved the proposed new food, a spicier flavor of gazpacho.
             BROKEN EXPECTATION: Ana should have mentioned that she disliked the proposed spicier gazpacho.
             REASONING: Ana has a known dislike of spicy food."

             
        Input: "Carlos traveled to Firenzi and was amazed by the beauty of the city. This was in line with his love for art and architecture."
        Output: 
            "OBSERVED: Carlos traveled to Firenzi and was amazed by the beauty of the city.
             MET EXPECTATION: Carlos should have been amazed by the beauty of the city.
             REASONING: Carlos loves art and architecture."

    Args:
        description (str): A description of an event or concept that either violates or meets an expectation.
    
    Returns:
        str: The restructured description.
    """
    # llm decorator will handle the body of this function