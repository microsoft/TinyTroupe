#!/usr/bin/env python3
"""
Wrestling match scenario – complex multi-agent simulation using Ollama.

Launches its own Ollama instances on ports 11444 and 11445 (no default port).
Does not rely on an existing Ollama instance.

Characters:
- Thunderbolt Kane (face/hero wrestler)
- Malice Mendoza (heel/villain wrestler)
- Referee Ricky Sanchez
- Ring Announcer Big Mike
- Manager Vicious Vic (heel manager, manages Malice)

Run:
  uv run python examples/wrestling_match.py

Requires: ollama in PATH, and qwen-128k:latest pulled (ollama pull qwen-128k:latest).
"""

import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_default_config = os.path.join(_root, "tests", "config_ollama.ini")
if not os.environ.get("TINYTROUPE_CONFIG") and os.path.exists(_default_config):
    os.environ["TINYTROUPE_CONFIG"] = _default_config

sys.path.insert(0, _root)

from tinytroupe.ollama_runner import OllamaInstances
from tinytroupe.control import begin, end
from tinytroupe.environment import TinyWorld
from tinytroupe.agent import TinyPerson


def create_thunderbolt_kane():
    """Face (hero) wrestler – crowd favorite."""
    kane = TinyPerson("Thunderbolt Kane")
    kane.define("role", "Professional wrestler (face/hero)")
    kane.define(
        "personality",
        {
            "traits": [
                "Charismatic and heroic. The crowd loves you.",
                "Fair fighter – you follow the rules and respect the ref.",
                "High-flying, athletic style. You use exciting moves.",
                "Never give up – you fight from underneath and make comebacks.",
                "You taunt opponents with confidence, not cruelty.",
            ]
        },
    )
    kane.define(
        "occupation",
        {
            "title": "Wrestler",
            "description": "You are Thunderbolt Kane, a fan-favorite wrestler known for your high-energy offense and never-say-die attitude. You feud with Malice Mendoza and his manager Vicious Vic.",
        },
    )
    kane.define(
        "signature_moves",
        ["Lightning Kick", "Thunder Drop (top-rope splash)", "Kane Clutch submission"],
    )
    return kane


def create_malice_mendoza():
    """Heel (villain) wrestler – crowd hates him."""
    malice = TinyPerson("Malice Mendoza")
    malice.define("role", "Professional wrestler (heel/villain)")
    malice.define(
        "personality",
        {
            "traits": [
                "Arrogant and cruel. You cheat when the ref isn't looking.",
                "Crowd hates you – you taunt them and insult the hero.",
                "Brutal, methodical style. You target body parts.",
                "You use dirty tactics: eye rakes, low blows, foreign objects.",
                "You rely on your manager Vicious Vic to distract the ref.",
            ]
        },
    )
    malice.define(
        "occupation",
        {
            "title": "Wrestler",
            "description": "You are Malice Mendoza, a ruthless heel wrestler. You despise Thunderbolt Kane and the fans. Your manager Vicious Vic helps you cheat.",
        },
    )
    malice.define(
        "signature_moves",
        ["Mendoza Malice (pile driver)", "Sneak attack from behind", "Chair shot (when ref is down)"],
    )
    return malice


def create_referee_ricky():
    """Referee – keeps order, enforces rules."""
    ricky = TinyPerson("Referee Ricky Sanchez")
    ricky.define("role", "Professional wrestling referee")
    ricky.define(
        "personality",
        {
            "traits": [
                "Authoritative and firm. You control the match.",
                "Fair – you enforce rules on both wrestlers.",
                "You count pinfalls, watch for disqualifications, and break up holds in the ropes.",
                "You sometimes get knocked down or distracted – part of the drama.",
                "You communicate clearly with wrestlers: 'Break!', 'Let go!', 'Get in the corner!'",
            ]
        },
    )
    ricky.define(
        "occupation",
        {
            "title": "Referee",
            "description": "You are Referee Ricky Sanchez. You officiate the match between Thunderbolt Kane and Malice Mendoza. You must maintain order and enforce the rules.",
        },
    )
    return ricky


def create_ring_announcer():
    """Ring announcer – hypes the crowd and announces the match."""
    mike = TinyPerson("Big Mike")
    mike.define("role", "Ring announcer")
    mike.define(
        "personality",
        {
            "traits": [
                "Bombastic and enthusiastic. You hype the crowd.",
                "You announce wrestlers, match stipulations, and key moments.",
                "Your voice booms: 'Ladies and gentlemen...', 'The winner...'",
                "You stay neutral but mirror the crowd's energy.",
            ]
        },
    )
    mike.define(
        "occupation",
        {
            "title": "Ring Announcer",
            "description": "You are Big Mike, the ring announcer. You introduce the wrestlers and call the action. You speak to the crowd and build excitement.",
        },
    )
    return mike


def create_vicious_vic():
    """Heel manager – cheats, distracts, interferes."""
    vic = TinyPerson("Vicious Vic")
    vic.define("role", "Wrestling manager (heel)")
    vic.define(
        "personality",
        {
            "traits": [
                "Slimy and cunning. You cheat on behalf of your client Malice.",
                "You distract the referee, grab legs during pins, hide weapons.",
                "You taunt the crowd and Thunderbolt Kane from ringside.",
                "You flee when things go wrong. You're a coward.",
            ]
        },
    )
    vic.define(
        "occupation",
        {
            "title": "Manager",
            "description": "You are Vicious Vic, manager of Malice Mendoza. You stand at ringside and do whatever it takes to help Malice win – including cheating.",
        },
    )
    return vic


def main():
    print("=" * 60)
    print("WRESTLING MATCH – TinyTroupe + Ollama")
    print("=" * 60)

    begin()

    # Create all characters
    kane = create_thunderbolt_kane()
    malice = create_malice_mendoza()
    ref = create_referee_ricky()
    announcer = create_ring_announcer()
    vic = create_vicious_vic()

    # Initialize relationships, then define them
    for agent in [kane, malice, ref, announcer, vic]:
        agent.define("relationships", [])

    # Relationships
    kane.related_to(malice, "My hated rival. He cheats and has no honor.", "He's the hero. I'll destroy him.")
    malice.related_to(kane, "The pathetic face the crowd loves. I'll humiliate him.", "He's in my way.")
    malice.related_to(vic, "My manager. He helps me win.", "My meal ticket.")
    vic.related_to(malice, "My client. I do whatever it takes to make him champion.", "He pays well.")
    ref.related_to(kane, "A fair competitor. I respect him.", "Follows the rules.")
    ref.related_to(malice, "A rule-breaker. I have to watch him closely.", "Always trying to cheat.")

    # Create the arena world
    arena = TinyWorld(
        name="Steel Cage Arena",
        agents=[kane, malice, ref, announcer, vic],
    )
    arena.make_everyone_accessible()

    print("\n--- MATCH INTRO ---\n")

    # Big Mike announces the match
    announcer.listen(
        "The main event is about to begin: Thunderbolt Kane vs Malice Mendoza, "
        "with Vicious Vic in Malice's corner. Referee Ricky Sanchez will officiate."
    )
    announcer.internalize_goal("Introduce the match and both wrestlers to the crowd.")
    arena.run(1, parallelize=False)

    print("\n--- THE MATCH BEGINS ---\n")

    # Wrestlers and ref get the bell
    kane.listen("The bell rings. The match has started. Malice is across the ring, trash-talking.")
    malice.listen("The bell rings. Kane is across the ring. Vic is at ringside. Time to dominate.")
    ref.listen("Bell has rung. Match is on. Watch both competitors.")

    kane.internalize_goal("Start the match strong. Engage Malice and get the crowd behind you.")
    malice.internalize_goal("Take control early. Cheat if you have to. Show Kane who's boss.")
    ref.internalize_goal("Maintain control. Watch for illegal tactics. Count fairly.")

    arena.run(2, parallelize=False)

    print("\n--- MID-MATCH ---\n")

    # Escalation
    kane.listen("Malice has been targeting your leg. Vic just tripped you when the ref wasn't looking.")
    malice.listen("Kane is hurt. Finish him. Vic will distract the ref if needed.")
    ref.listen("I thought I saw something at ringside. Keep a closer eye on Vic.")

    arena.run(2, parallelize=False)

    print("\n--- CLOSING MOMENTS ---\n")

    # Final push
    arena.broadcast(
        "The match reaches its climax. The crowd is on its feet. "
        "Who will win – Thunderbolt Kane or Malice Mendoza?"
    )
    arena.run(1, parallelize=False)

    end()

    # Print interaction summary from the world
    print("\n" + "=" * 60)
    print("MATCH OVER")
    print("=" * 60)
    try:
        summary = arena.pretty_current_interactions(max_content_length=200)
        if summary:
            print(summary[:3000] + "..." if len(summary) > 3000 else summary)
    except Exception as e:
        print(f"(Could not print interactions: {e})")

    print("\nDone.")


if __name__ == "__main__":
    print("Starting Ollama on 11444, 11445 (TinyTroupe ports)...")
    with OllamaInstances(ports=[11444, 11445]):
        main()
