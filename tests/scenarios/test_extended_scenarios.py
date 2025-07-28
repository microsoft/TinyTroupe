import pytest
import logging
logger = logging.getLogger("tinytroupe")

import sys
import os
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

import tinytroupe
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld, TinySocialNetwork
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.extraction import ResultsExtractor

from tinytroupe.examples import create_lisa_the_data_scientist, create_oscar_the_architect, create_marcos_the_physician

import tinytroupe.control as control
from tinytroupe.control import Simulation

from testing_utils import *


def test_story_telling_scenario(setup):
    """
    Test that agents can collaborate to create and sustain a narrative story.
    Based on the Story telling notebook but simplified for quick test execution.
    """
    control.reset()

    # Create a small group of diverse characters
    factory = TinyPersonFactory("A creative writing workshop with diverse participants.")
    
    writer = factory.generate_person("A creative writer who loves storytelling, and always insists in including dogs in all stories.")
    editor = factory.generate_person("An editor with strong narrative sense, and always insists in including cats in all stories.")

    # print minibios
    print("Writer:", writer.minibio())
    print("Editor:", editor.minibio())

    world = TinyWorld("Creative Writing Workshop", [writer, editor])
    world.make_everyone_accessible()

    # Start a collaborative story
    story_beginning = """
    You are all participating in a collaborative storytelling exercise. The story begins:
    'On a rainy Tuesday morning, Sarah discovered an old letter hidden in her grandmother's attic...'
    
    Continue this story together, taking turns to add to the narrative. Make it engaging and creative.
    """

    world.broadcast(story_beginning)
    writer.think("Let me suggest a dog somewhere of course.")
    editor.think("Let me suggest a cat somewhere of course.")

    world.run(3)

    # Extract the story content
    extractor = ResultsExtractor()
    story_content = extractor.extract_results_from_world(world, 
                                                        extraction_objective="Extract the collaborative story content that was created",
                                                        situation="A creative writing workshop where people are telling a story together")

    print("Story Content:", story_content)

    # Verify story elements exist
    assert proposition_holds(f"The following contains a narrative story with characters and plot: '{story_content}'"), "Story should contain narrative elements"
    assert proposition_holds(f"The following contains mentions of both cats and dogs: '{story_content}'"), "Should show collaborative storytelling"


def test_synthetic_conversation_generation(setup):
    """
    Test generation of synthetic conversation data between agents.
    Based on synthetic_data_generation notebook but focused on conversation quality.
    """
    control.reset()

    # Create agents for conversation generation
    factory = TinyPersonFactory("A workplace environment with knowledge workers.")
    
    agent1 = factory.generate_person("A project manager focused on deadlines and coordination.")
    agent2 = factory.generate_person("A software developer interested in technical solutions.")
    
    world = TinyWorld("Workplace", [agent1, agent2])
    world.make_everyone_accessible()

    # Generate workplace conversation by having them collaborate
    world.broadcast("You need to discuss the upcoming software project deadline. Share your perspectives and work together to find solutions.")
    world.run(3)

    # Extract conversations from episodic memory
    conversations = []
    for agent in world.agents:
        interactions = agent.episodic_memory.retrieve_all()
        for interaction in interactions:
            # Check if this is an action performed by the agent
            if interaction.get("role") == "assistant" and "action" in interaction.get("content", {}):
                action = interaction["content"]["action"]
                if action.get("type") == "TALK":
                    conversations.append({
                        "speaker": agent.name,
                        "content": action.get("content", "")
                    })

    # Verify conversation quality
    assert len(conversations) > 0, f"Should have generated conversations. Found {len(conversations)} conversations."
    
    # Check that conversations contain substantive content
    non_empty_conversations = [c for c in conversations if len(c["content"].strip()) > 10]
    assert len(non_empty_conversations) > 0, "Should have substantive conversation content"
    
    # Print conversations for debugging
    print(f"Generated {len(conversations)} conversations:")
    for conv in conversations:
        print(f"  {conv['speaker']}: {conv['content'][:100]}...")
    
    # Check total conversation content
    conversation_text = " ".join([c["content"] for c in conversations])
    assert len(conversation_text) > 50, "Should have generated substantial conversation text"


def test_product_market_research_scenario(setup):
    """
    Test market research for a new product using diverse consumer personas.
    Simplified version of Travel Product Market Research notebook.
    """
    control.reset()

    # Create diverse consumer personas
    factory = TinyPersonFactory("Random consumers from different demographics and backgrounds.")
    
    consumers = []
    # Create fewer consumers for quick testing
    for i in range(3):
        consumer = factory.generate_person(f"A consumer with distinct preferences and background, person {i+1}.")
        consumers.append(consumer)

    # Test product concept
    product_concept = """
    We are researching a new smart home device called 'HomeGenie' that uses AI to automatically 
    adjust lighting, temperature, and music based on your mood and activities. 
    Would you be interested in purchasing this product for $299? 
    Please respond with 'Yes', 'No', or 'Maybe' and explain your reasoning.
    """

    responses = []
    extractor = ResultsExtractor()

    for consumer in consumers:
        consumer.listen_and_act(product_concept)
        
        response = extractor.extract_results_from_agent(consumer,
                                                       extraction_objective="Extract the consumer's purchase decision and reasoning",
                                                       situation="Market research survey for smart home product",
                                                       fields=["decision", "reasoning"],
                                                       fields_hints={"decision": "Must be 'Yes', 'No', or 'Maybe'"})
        responses.append(response)

    # Verify market research results
    assert len(responses) == 3, "Should have 3 consumer responses"
    for response in responses:
        assert response["decision"] in ["Yes", "No", "Maybe"], f"Decision should be Yes/No/Maybe, got: {response['decision']}"
        assert len(response["reasoning"]) > 10, "Should provide reasoning for decision"


def test_political_opinion_polling_scenario(setup):
    """
    Test agents expressing political opinions on policy issues.
    Based on Political Compass notebook but simplified and focusing on policy discussion.
    """
    control.reset()

    # Create agents with different political leanings
    factory = TinyPersonFactory("American voters with diverse political perspectives.")
    
    conservative = factory.generate_person("A conservative-leaning voter concerned about traditional values and fiscal responsibility.")
    liberal = factory.generate_person("A liberal-leaning voter focused on social justice and environmental issues.")
    moderate = factory.generate_person("A moderate voter who considers multiple perspectives on issues.")

    # Test policy opinion
    policy_question = """
    What is your opinion on implementing a universal basic income program? 
    Please share your perspective considering economic impacts, social benefits, and practical concerns.
    Keep your response brief but thoughtful.
    """

    agents = [conservative, liberal, moderate]
    extractor = ResultsExtractor()
    opinions = []

    for agent in agents:
        agent.listen_and_act(policy_question)
        
        opinion = extractor.extract_results_from_agent(agent,
                                                      extraction_objective="Extract the agent's opinion on universal basic income",
                                                      situation="Political opinion polling on policy issues",
                                                      fields=["stance", "reasoning"],
                                                      fields_hints={"stance": "Overall position (support/oppose/mixed)"})
        opinions.append(opinion)

    # Verify political discourse quality
    assert len(opinions) == 3, "Should have 3 political opinions"
    assert proposition_holds(f"The following represents diverse political perspectives on universal basic income: {opinions}"), "Should show political diversity"


def test_multi_agent_problem_solving_scenario(setup):
    """
    Test multiple agents collaborating to solve a complex problem.
    Based on product brainstorming but focused on problem-solving process.
    """
    control.reset()

    # Create problem-solving team
    analyst = create_lisa_the_data_scientist()
    architect = create_oscar_the_architect() 
    doctor = create_marcos_the_physician()

    world = TinyWorld("Problem Solving Team", [analyst, architect, doctor])
    world.make_everyone_accessible()

    # Present complex problem
    problem = """
    Your team needs to design a solution for improving healthcare delivery in remote rural areas.
    Consider challenges like: limited internet connectivity, shortage of medical professionals, 
    transportation difficulties, and cost constraints.
    
    Work together to brainstorm practical solutions. Each person should contribute based on 
    their expertise and perspective.
    """

    world.broadcast(problem)
    world.run(3)

    # Ask for consolidated solution
    analyst.listen_and_act("Please summarize the key solutions our team has identified for rural healthcare delivery.")

    # Extract problem-solving results
    extractor = ResultsExtractor()
    solution = extractor.extract_results_from_agent(analyst,
                                                   extraction_objective="Extract the consolidated healthcare solutions",
                                                   situation="Multi-disciplinary team solving rural healthcare challenges")

    # Verify problem-solving quality
    assert proposition_holds(f"The following contains practical solutions for rural healthcare delivery: '{solution}'"), "Should contain healthcare solutions"
    assert proposition_holds(f"The following shows evidence of multi-disciplinary collaboration: '{solution}'"), "Should show collaborative problem-solving"
