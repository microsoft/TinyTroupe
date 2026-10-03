
from tinytroupe.tools import TinyTool
from tinytroupe.agent import TinyPerson
from tinytroupe.control import transactional

class CommunityRallyTool(TinyTool):
    def __init__(self):
        super().__init__(
            name="CommunityRallyTool",
            description="Organize and hold a community rally to raise awareness and support for a cause."
        )

    def actions_definitions_prompt(self):
        return "- USE_TOOL: to use the CommunityRallyTool. The 'content' should be the key message of the rally."

    def actions_constraints_prompt(self):
        return "- When using the CommunityRallyTool, you must provide a key message for the rally."

    @transactional()
    def use(self, agent: TinyPerson, message: str):
        """Simulates a community rally."""
        if agent.environment:
            # Broadcast the rally message to all agents in the same environment zone
            for other_agent in agent.environment.agents:
                if other_agent.environment and other_agent.environment.zones.get(other_agent.name) == agent.environment.zones.get(agent.name):
                    other_agent.listen(f'(Community Rally) {message}', source=agent)
            return "Successfully held a community rally."
        else:
            return "Could not hold a rally because the agent is not in an environment."
