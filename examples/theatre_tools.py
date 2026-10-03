from tinytroupe.tools import TinyTool
from tinytroupe.utils.llm import LLMChat
from tinytroupe.agent import TinyPerson

class ScriptwritingTool(TinyTool):
    def __init__(self):
        super().__init__(
            name="Scriptwriter's Desk",
            description="A tool to write, edit, and format scripts based on creative briefs."
        )

    def use(self, creative_brief: str, scene_number: int) -> str:
        """Generates a script scene as a JSON object based on a creative brief."""
        chat = LLMChat(
            system_prompt=f"You are a professional screenwriter. Write a compelling script for scene {scene_number} based on the following brief. The output must be a valid JSON object with keys 'scene_number', 'setting', and 'dialogue' (a list of objects with 'character' and 'line' keys).",
            user_prompt=creative_brief,
            response_format={"type": "json_object"}
        )
        return chat.call()

    def actions_definitions_prompt(self) -> str:
        return "- USE_TOOL: to write a script. The 'content' should be 'Scriptwriter's Desk', and the 'target' should be a creative brief for the script."

    def actions_constraints_prompt(self) -> str:
        return "- When writing a script, you must use the Scriptwriter's Desk tool."

    def _process_action(self, agent: TinyPerson, action: dict) -> bool:
        if action['type'] == 'USE_TOOL' and action['content'] == self.name:
            script_json = self.use(creative_brief=action['target'], scene_number=1)
            agent.think(f"I have drafted a script: {script_json}")
            agent.store_in_memory({'role': 'system', 'content': {'tool_output': script_json}, 'type': 'tool_output', 'simulation_timestamp': agent.iso_datetime(), 'parent_event_id': agent.environment.current_step_id if agent.environment else None})
            return True
        return False

class MusicCompositionTool(TinyTool):
    def __init__(self):
        super().__init__(
            name="Composer's Studio",
            description="A tool to conceptualize and describe musical scores."
        )

    def use(self, musical_brief: str) -> str:
        """Generates a description of a musical score as a JSON object based on a brief."""
        chat = LLMChat(
            system_prompt="You are a film and theatre composer. Describe the musical score based on the following brief as a JSON object. The JSON should have keys for 'mood', 'instrumentation', 'tempo_bpm', and 'key_themes'.",
            user_prompt=musical_brief,
            response_format={"type": "json_object"}
        )
        return chat.call()

    def actions_definitions_prompt(self) -> str:
        return "- USE_TOOL: to compose music. The 'content' should be 'Composer's Studio', and the 'target' should be a musical brief for the score."

    def actions_constraints_prompt(self) -> str:
        return "- When composing music, you must use the Composer's Studio tool."

    def _process_action(self, agent: TinyPerson, action: dict) -> bool:
        if action['type'] == 'USE_TOOL' and action['content'] == self.name:
            music_json = self.use(musical_brief=action['target'])
            agent.think(f"I have conceptualized a score: {music_json}")
            agent.store_in_memory({'role': 'system', 'content': {'tool_output': music_json}, 'type': 'tool_output', 'simulation_timestamp': agent.iso_datetime(), 'parent_event_id': agent.environment.current_step_id if agent.environment else None})
            return True
        return False

class StagingTool(TinyTool):
    def __init__(self):
        super().__init__(
            name="Director's Viewfinder",
            description="A tool to plan the 2D blocking and staging of a scene."
        )

    def use(self, scene_script: str) -> str:
        """Generates 2D blocking information for a scene as a JSON object."""
        chat = LLMChat(
            system_prompt="You are a theatre director. Based on the provided script, describe the 2D blocking of the scene. The output must be a valid JSON object. The root object should be a 'stage' with 'width' and 'height' properties. It should contain a list of 'characters' with their 'name', and initial 'x' and 'y' coordinates. It should also contain a list of 'props' with their 'name' and 'x' and 'y' coordinates.",
            user_prompt=scene_script,
            response_format={"type": "json_object"}
        )
        return chat.call()

    def actions_definitions_prompt(self) -> str:
        return "- USE_TOOL: to create a staging plan. The 'content' should be 'Director's Viewfinder', and the 'target' should be the script for the scene."

    def actions_constraints_prompt(self) -> str:
        return "- When creating a staging plan, you must use the Director's Viewfinder tool."

    def _process_action(self, agent: TinyPerson, action: dict) -> bool:
        if action['type'] == 'USE_TOOL' and action['content'] == self.name:
            staging_json = self.use(scene_script=action['target'])
            agent.think(f"I have created a staging plan: {staging_json}")
            agent.store_in_memory({'role': 'system', 'content': {'tool_output': staging_json}, 'type': 'tool_output', 'simulation_timestamp': agent.iso_datetime(), 'parent_event_id': agent.environment.current_step_id if agent.environment else None})
            return True
        return False

class PracticeTool(TinyTool):
    def __init__(self):
        super().__init__(
            name="Practice Room",
            description="A tool for an agent to practice and improve a specific skill."
        )

    def use(self, skill_name: str, agent: TinyPerson) -> str:
        """Simulates practicing a skill and updates the agent's proficiency."""
        # Simulate practice effect (e.g., increase skill by a small amount)
        current_proficiency = agent.get(f'persona.skills.{skill_name}', 0.0)
        new_proficiency = min(1.0, current_proficiency + 0.05) # Increase by 0.05, max 1.0
        agent.define(f'persona.skills.{skill_name}', new_proficiency)
        return f"Successfully practiced {skill_name}. New proficiency: {new_proficiency:.2f}"

    def actions_definitions_prompt(self) -> str:
        return "- USE_TOOL: to practice a skill. The 'content' should be 'Practice Room', and the 'target' should be the name of the skill to practice."

    def actions_constraints_prompt(self) -> str:
        return "- When practicing a skill, you must use the Practice Room tool and specify the skill name."

    def _process_action(self, agent: TinyPerson, action: dict) -> bool:
        if action['type'] == 'USE_TOOL' and action['content'] == self.name:
            result_message = self.use(skill_name=action['target'], agent=agent)
            agent.think(result_message)
            agent.store_in_memory({'role': 'system', 'content': {'tool_output': result_message}, 'type': 'tool_output', 'simulation_timestamp': agent.iso_datetime(), 'parent_event_id': agent.environment.current_step_id if agent.environment else None})
            return True
        return False
