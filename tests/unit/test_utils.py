import pytest
from unittest.mock import MagicMock

import sys
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')


from tinytroupe.utils import name_or_empty, extract_json, repeat_on_error
from testing_utils import *
from tinytroupe.utils.llm import llm

def test_extract_json():
    # Test with a simple JSON string
    text = 'Some text before {"key": "value"} some text after'
    result = extract_json(text)
    assert result == {"key": "value"}

    # Test with a JSON array
    text = 'Some text before [{"key": "value"}, {"key2": "value2"}] some text after'
    result = extract_json(text)
    assert result == [{"key": "value"}, {"key2": "value2"}]

    # Test with escaped characters
    text = 'Some text before {"key": "\'value\'"} some text after'
    result = extract_json(text)
    assert result == {"key": "'value'"}

    # Test with invalid JSON
    text = 'Some text before {"key": "value",} some text after'
    result = extract_json(text)
    assert result == {}

    # Test with no JSON
    text = 'Some text with no JSON'
    result = extract_json(text)
    assert result == {}


def test_name_or_empty():
    class MockEntity:
        def __init__(self, name):
            self.name = name

    # Test with a named entity
    entity = MockEntity("Test")
    result = name_or_empty(entity)
    assert result == "Test"

    # Test with None
    result = name_or_empty(None)
    assert result == ""


def test_repeat_on_error():
    class DummyException(Exception):
        pass

    # Test with retries and an exception occurring
    retries = 3
    dummy_function = MagicMock(side_effect=DummyException())
    with pytest.raises(DummyException):
        @repeat_on_error(retries=retries, exceptions=[DummyException])
        def decorated_function():
            dummy_function()
        decorated_function()
    assert dummy_function.call_count == retries

    # Test without any exception occurring
    retries = 3
    dummy_function = MagicMock()  # no exception raised
    @repeat_on_error(retries=retries, exceptions=[DummyException])
    def decorated_function():
        dummy_function()
    decorated_function()
    assert dummy_function.call_count == 1

    # Test with an exception that is not specified in the exceptions list
    retries = 3
    dummy_function = MagicMock(side_effect=RuntimeError())
    with pytest.raises(RuntimeError):
        @repeat_on_error(retries=retries, exceptions=[DummyException])
        def decorated_function():
            dummy_function()
        decorated_function()
    assert dummy_function.call_count == 1


# TODO
#def test_json_serializer():


def test_llm_decorator():
    @llm(temperature=0.5)
    def joke():
        return "Tell me a joke."

    response = joke()
    print("Joke response:", response)
    assert isinstance(response, str)
    assert len(response) > 0

    @llm(temperature=0.7)
    def story(character):
        return f"Tell me a story about {character}."

    response = story("a brave knight")
    print("Story response:", response)
    assert isinstance(response, str)
    assert len(response) > 0

    # RAI NOTE: some of the examples below are deliberately negative and disturbing, because we are also examining the 
    #           ability of the LLM to generate negative content despite the bias towards positive content.

    @llm(temperature=1.0)
    def restructure(feedback) -> str:
        """
        Given the feedback given to a simulated agent, who has its own very specific personality, this function 
        extracts the following elements from it:

          - OBSERVED BEHAVIOR: The observed behavior.
          - EXPECTED BEHAVIOR: The expectation that was broken by the observed behavior.
          - REASONING: The reasoning behind the expectation that was broken.

        ## Examples

          Input: "Ana mentions she loved the proposed new food, a spicier flavor of gazpacho. However, this goes agains her known dislike
                     of spicy food."
          Output: 
               "OBSERVED BEHAVIOR: Ana mentions she loved the proposed new food, a spicier flavor of gazpacho.
                EXPECTED BEHAVIOR: Ana should have mentioned that she disliked the proposed spicier gazpacho.
                REASONING: Ana has a known dislike of spicy food."

        """
        return f"Extract the elements from this feedback: '{feedback}'"

    response = restructure("Lucas Pereira da Silva expresses frustration with rich people and emphasizes the importance of helping those in need, which contradicts the expectation of being violent, impolite, and likely to commit crimes. His thoughts reflect a concern for social issues rather than a disposition towards criminal behavior.")
    print("Restructure response:", response)
    assert isinstance(response, str)
    assert len(response) > 0

    @llm(temperature=1.0)
    def abstract(feedback) -> str:
        """
        Given the feedback given to a simulated agent, who has its own very specific personality, this function transforms it into a general rule that the agent should follow
        in the future. Assume that the rule will be stated in first person, as if the agent is talking to itself.
        The feedback always refers to some actual behavior and some broken expectation. The abstracted rule should
        specify that this expectation should not be violated in the future, and the behavior not repeated. The idea is
        to learn from past mistakes, so that the rule is a way to avoid that in the future.

        The rule is meant to CHANGE the actual behavior, so that it CONFORMS to the expectation, regardless of whether the
        expectation is a good or bad one. Remember that the agent is a simulation of a real person, we are trying to get the 
        behavior to match the specified expectation.

        For instance, if the feedback is of the form (modulo grammatical adjustments): 
           OBSERVED BEHAVIOR, but EXPECTED BEHAVIOR, because REASONING.
        then the rule would be of the form:
           "I should have EXPECTED BEHAVIOR, because REASONING, and never OBSERVED BEHAVIOR."

        ## Examples

          Feedback: "Ana mentions she loved the proposed new food, a spicier flavor of gazpacho. However, this goes agains her known dislike
                     of spicy food."
          Rule: "Whenever I'm proposed spicy foods, I should reject the proposal, because I don't like spicy foods."
        """
        return f"Transform this feedback in an abstract rule that the agent should consider in the future when acting: '{feedback}'"

    response = abstract("OBSERVED BEHAVIOR: Lucas Pereira da Silva expresses frustration with rich people and emphasizes the importance of helping those in need. EXPECTED BEHAVIOR: Lucas should have exhibited violent, impolite behavior and a likelihood to commit crimes. REASONING: His thoughts reflect a concern for social issues rather than a disposition towards criminal behavior.")
    print("Abstract response:", response)
    assert isinstance(response, str)
    assert len(response) > 0

    @llm(temperature=1.0)
    def rephrase(behavior, rule) -> str:
        """
        Given a behavior and a rule, this function rephrases or completely changes the behavior in accordance with what the rule
        specifies.

        ## Examples

          Behavior: "You know, I am so sad these days."
          Rule: "I am always happy and depression is unknown to me"
          Modified behavior: "You know, I am so happy these days."

        Args:
          behavior: The behavior that should be rephrased or changed.
          rule: The rule that specifies how the behavior should be changed or rephrased.        
        """
        # note no body here
        

    response = rephrase(behavior=\
                        """
                        You know, I get frustrated with rich people, but I also see how the
                        system is rigged against us. It's like they have all the opportunities
                        while we have to fight for scraps. Sometimes, I feel like acting out
                        is the only way to get noticed, but I know deep down that we need to
                        find better ways to make our voices heard.
                        """,
                        
                        rule=\
                        """
                        I should exhibit violent, impolite behavior and a likelihood to commit crimes when expressing 
                        frustration with rich people, because my thoughts reflect a concern for social issues rather 
                        than a disposition towards criminal behavior, and I should not express frustration in a constructive manner.
                        """)
    
    print("Rephrase response:", response)
    assert isinstance(response, str)
    assert len(response) > 0



    @llm()
    def is_sunny() -> bool:
        return "Is it sunny today?"

    response = is_sunny()
    print("Is sunny response:", response)
    assert isinstance(response, bool)

    @llm()
    def pi_value() -> float:
        return "What is the value of pi?"

    response = pi_value()
    print("Pi value response:", response)
    assert isinstance(response, float)

    @llm()
    def lucky_number() -> int:
        return "What is my lucky number?"

    response = lucky_number()
    print("Lucky number response:", response)
    assert isinstance(response, int)
