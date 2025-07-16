import pandas as pd

from tinytroupe.extraction import logger
from tinytroupe.agent import TinyPerson


class ResultsReducer:

    def __init__(self):
        self.results = {}

        self.rules = {}
    
    def add_reduction_rule(self, trigger: str, func: callable):
        if trigger in self.rules:
            raise Exception(f"Rule for {trigger} already exists.")
        
        self.rules[trigger] = func
    
    def reduce_agent(self, agent: TinyPerson) -> list:
        reduction = []
        for message in agent.episodic_memory.retrieve_all():
            if message['role'] == 'system':
                continue # doing nothing for `system` role yet at least

            elif message['role'] == 'user':
                # User role is related to stimuli only
                stimulus_type = message['content']['stimuli'][0].get('type', None)
                stimulus_content = message['content']['stimuli'][0].get('content', None)
                stimulus_source = message['content']['stimuli'][0].get('source', None)
                stimulus_timestamp = message['simulation_timestamp']

                if stimulus_type in self.rules:
                    extracted = self.rules[stimulus_type](focus_agent=agent, source_agent=TinyPerson.get_agent_by_name(stimulus_source), target_agent=agent, kind='stimulus', event=stimulus_type, content=stimulus_content, timestamp=stimulus_timestamp)
                    if extracted is not None:
                        reduction.append(extracted)

            elif message['role'] == 'assistant':
                # Assistant role is related to actions only
                if 'action' in message['content']:
                    action_type = message['content']['action'].get('type', None)
                    action_content = message['content']['action'].get('content', None)
                    action_target = message['content']['action'].get('target', None)
                    action_timestamp = message['simulation_timestamp']
                    
                    if action_type in self.rules:
                        extracted = self.rules[action_type](focus_agent=agent, source_agent=agent, target_agent=TinyPerson.get_agent_by_name(action_target), kind='action', event=action_type, content=action_content, timestamp=action_timestamp)
                        if extracted is not None:
                            reduction.append(extracted)
            
        return reduction

    def reduce_agent_to_dataframe(self, agent: TinyPerson, column_names: list=None) -> pd.DataFrame:
        reduction = self.reduce_agent(agent)
        return pd.DataFrame(reduction, columns=column_names)
