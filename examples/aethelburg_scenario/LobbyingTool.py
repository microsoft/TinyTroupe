
from tinytroupe.tools import TinyTool
from tinytroupe.agent import TinyPerson
from tinytroupe.control import transactional

class LobbyingTool(TinyTool):
    def __init__(self):
        super().__init__(
            name="LobbyingTool",
            description="Schedule and conduct private meetings with influential figures to advocate for specific outcomes."
        )

    def actions_definitions_prompt(self):
        return "- USE_TOOL: to use the LobbyingTool. The 'content' should be the name of the person to lobby, and the 'target' should be the key message of the lobbying effort."

    def actions_constraints_prompt(self):
        return "- When using the LobbyingTool, you must specify a target person and a message."

    @transactional()
    def use(self, agent: TinyPerson, target_person_name: str, message: str):
        """Simulates a private lobbying meeting."""
        target_agent = TinyPerson.get_agent_by_name(target_person_name)
        if target_agent:
            # Simulate a private conversation by having the target agent 'listen' to the message
            # from the lobbying agent, but without broadcasting it to the entire world.
            target_agent.listen(f'(Private meeting) {message}', source=agent)
            return f"Successfully lobbied {target_person_name}."
        else:
            return f"Could not find {target_person_name} to lobby."
