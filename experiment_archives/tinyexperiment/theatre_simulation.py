import os
import json
import asyncio

from tinytroupe.environment import TinyWorld
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.agent import TinyPerson
from tinytroupe.extraction import ResultsExtractor
from examples.theatre_tools import ScriptwritingTool, MusicCompositionTool, StagingTool, PracticeTool
from tinytroupe.persistence.database import TinyTroupeDatabase
from tinytroupe import config_manager

async def run_simulation():
    # --- World State and Constraints ---
    world_state = {
        'project_brief': 'Create a 30-second TV spot for Quantum Fizz, a new energy drink. The client wants something energetic, futuristic, and slightly humorous.',
        'budget': 50000,
        'deadline': 'EOD Friday'
    }

    # Define the world's zones with properties
    zones = {
        'Workshop': {'size': 'Large', 'ambient_noise_level': 'Low', 'description': 'A large, open space with whiteboards and scattered chairs.'},
        "Writer's Room": {'size': 'Small', 'ambient_noise_level': 'Very Low', 'description': 'A cramped, quiet room with a single desk and a large window.'},
        "Composer's Studio": {'size': 'Medium', 'ambient_noise_level': 'Medium', 'description': 'A sound-proofed room filled with musical instruments and audio equipment.'},
        'Main Stage': {'size': 'Very Large', 'ambient_noise_level': 'High', 'description': 'A vast, empty stage under the glare of work lights.'}
    }

    # Create a theatre world with ambient stimuli and zones
    theatre_world = TinyWorld(
        name="The Grand Stage",
        ambient_stimuli=[
            'The sound of a distant siren wails.',
            'The coffee machine in the corner gurgles loudly.',
            'A phone buzzes on a nearby table.'
        ],
        zones=zones
    )

    # Instantiate the database
    db = TinyTroupeDatabase()
    db.clear_history() # Clear previous history for a clean run

    # Create a factory for our actors
    actor_factory = TinyPersonFactory(context="A professional theatre company working on a tight deadline and budget.")

    # Generate the core troupe
    director = actor_factory.generate_person(agent_particularities="An experienced, visionary director named Elias Vance. He is feeling the pressure of the deadline.")
    writer = actor_factory.generate_person(agent_particularities="A sharp, witty writer named Lena Petrova. She thrives under pressure.")
    actor1 = actor_factory.generate_person(agent_particularities="A versatile and charismatic lead actor named Julian Croft. He is concerned about the budget.")
    actor2 = actor_factory.generate_person(agent_particularities="A character actor with a knack for physical comedy named Chloe Jenkins. She is excited by the creative challenge.")
    composer = actor_factory.generate_person(agent_particularities="An innovative composer named Mateo Diaz, who is known for working fast.")

    # Add depth to personas and initial skills
    director.define('long_term_goals', ['To deliver this project on time and under budget.'])
    director.define('persona.skills.directing', 0.8)
    writer.define('personality', {'traits': ['Perfectionist', 'Witty', 'Focused']})
    writer.define('persona.skills.scriptwriting', 0.7)
    actor1.define('persona.beliefs', ['A good performance can save a weak script.', 'Every dollar on screen matters.'])
    actor1.define('persona.skills.acting', 0.9)
    actor2.define('persona.preferences', {'likes': ['Improvisation', 'Collaboration']})
    actor2.define('persona.skills.acting', 0.7)
    actor2.define('persona.skills.comedy', 0.8)
    composer.define('long_term_goals', ['To create a memorable jingle.'])
    composer.define('persona.skills.composing', 0.8)

    # Define relationships with affinity scores
    director.related_to(writer, 'My most trusted collaborator.', 0.9, 'He pushes me to be better.', 0.8)
    actor1.related_to(actor2, 'A talented rival, keeps me on my toes.', 0.6, 'He gets all the good lines, but I get all the laughs.', 0.7)

    # Create and assign tools
    script_tool = ScriptwritingTool()
    music_tool = MusicCompositionTool()
    staging_tool = StagingTool()
    practice_tool = PracticeTool()
    writer.add_mental_faculty(script_tool)
    composer.add_mental_faculty(music_tool)
    director.add_mental_faculty(staging_tool)
    actor1.add_mental_faculty(practice_tool)
    actor2.add_mental_faculty(practice_tool)

    # Add ReputationObserver to all agents
    from tinytroupe.agent.reputation_observer import ReputationObserver
    reputation_observer = ReputationObserver()
    director.add_mental_faculty(reputation_observer)
    writer.add_mental_faculty(reputation_observer)
    actor1.add_mental_faculty(reputation_observer)
    actor2.add_mental_faculty(reputation_observer)
    composer.add_mental_faculty(reputation_observer)

    # Add the troupe to the world
    theatre_world.add_agents([director, writer, actor1, actor2, composer])

    # Make everyone accessible to each other
    theatre_world.make_everyone_accessible()

    # --- Simulation Start ---

    # Initialize the world's current step ID for initial actions
    theatre_world.current_step_id = 'initial_setup'

    # Phase 1: Goal-Driven Brainstorming
    director.move_to('Workshop')
    theatre_world.broadcast_context_change([f"Project Brief: {world_state['project_brief']}", f"Budget: ${world_state['budget']}"])
    director.internalize_goal("Lead a brainstorming session to generate a winning concept for the Quantum Fizz commercial, keeping the client's brief and budget in mind.")
    await theatre_world.run(4)
    db.save_simulation_state(theatre_world) # Save state after Phase 1

    # Phase 2: Autonomous Creative Development
    writer.move_to("Writer's Room")
    composer.move_to("Composer's Studio")
    director.listen("Great session. Lena, I trust you to write a script that captures the 'Quantum Leap' idea. Mateo, you know what to do for the score. Let's see what you've got by midday.")
    writer.internalize_goal("Write a script for the Quantum Fizz commercial based on the 'Quantum Leap' concept.")
    composer.internalize_goal("Compose a futuristic, retro-vibe score for the commercial.")
    await theatre_world.run(3) # Allow agents to autonomously use their tools
    db.save_simulation_state(theatre_world) # Save state after Phase 2

    # Demonstrate skill practice
    actor1.internalize_goal("Practice my acting skills to improve my performance.")
    await actor1.act()
    actor2.internalize_goal("Practice my comedy skills to enhance my stage presence.")
    await actor2.act()
    db.save_simulation_state(theatre_world) # Save state after skill practice

    # Phase 3: Staging and Rehearsal
    director.internalize_goal("Review the script and create a staging plan.")
    await theatre_world.run(3)
    db.save_simulation_state(theatre_world) # Save state after Phase 3

    # --- Demonstrate Loading State ---
    print("\n--- Loading Latest State ---\n")
    loaded_world = TinyWorld.load_state(db)
    if loaded_world:
        print(f"Successfully loaded world: {loaded_world.name}")
        # You can now continue the simulation from this loaded state or inspect its properties
        # For example, print the loaded director's goals
        loaded_director = loaded_world.get_agent_by_name("Elias Vance")
        if loaded_director:
            print(f"Loaded Director's goals: {loaded_director.get('goals')}")
    else:
        print("Failed to load world state.")

    # Extract and print the structured conversation, now including staging information and causal links
    extractor = ResultsExtractor()
    conversation_graph = extractor.extract_detailed_conversation(world=theatre_world, include_actions=['TALK', 'PERFORM', 'USE_TOOL'], include_cognitive_state=True, include_causal_links=True, include_visualization_hooks=True)
    print(json.dumps(conversation_graph, indent=2))

if __name__ == "__main__":
    asyncio.run(run_simulation())