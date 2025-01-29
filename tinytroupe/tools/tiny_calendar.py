
import textwrap
import json

from tinytroupe.tools import logger, TinyTool
import tinytroupe.utils as utils


# TODO under development
class TinyCalendar(TinyTool):

    def __init__(self, owner=None):
        super().__init__("calendar", "A basic calendar tool that allows agents to keep track meetings and appointments.", owner=owner, real_world_side_effects=False)
        
        # maps date to list of events. Each event itself is a dictionary with keys "title", "description", "owner", "mandatory_attendees", "optional_attendees", "start_time", "end_time"
        self.calenar = {}
    
    def add_event(self, date, title, description=None, owner=None, mandatory_attendees=None, optional_attendees=None, start_time=None, end_time=None):
        if date not in self.calendar:
            self.calendar[date] = []
        self.calendar[date].append({"title": title, "description": description, "owner": owner, "mandatory_attendees": mandatory_attendees, "optional_attendees": optional_attendees, "start_time": start_time, "end_time": end_time})
    
    def find_events(self, year, month, day, hour=None, minute=None):
        # TODO
        pass

    def _process_action(self, agent, action) -> bool:
        if action['type'] == "CREATE_EVENT" and action['content'] is not None:
            # parse content json
            event_content = json.loads(action['content'])
            
            # checks whether there are any kwargs that are not valid
            valid_keys = ["title", "description", "mandatory_attendees", "optional_attendees", "start_time", "end_time"]
            utils.check_valid_fields(event_content, valid_keys)

            # uses the kwargs to create a new event
            self.add_event(event_content)

            return True

        else:
            return False

    def actions_definitions_prompt(self) -> str:
        prompt = \
            """
              - CREATE_EVENT: You can create a new event in your calendar. The content of the event has many fields, and you should use a JSON format to specify them. Here are the possible fields:
                * title: The title of the event. Mandatory.
                * description: A brief description of the event. Optional.
                * mandatory_attendees: A list of agent names who must attend the event. Optional.
                * optional_attendees: A list of agent names who are invited to the event, but are not required to attend. Optional.
                * start_time: The start time of the event. Optional.
                * end_time: The end time of the event. Optional.
            """
        # TODO how the atendee list will be handled? How will they be notified of the invitation? I guess they must also have a calendar themselves. <-------------------------------------

        return utils.dedent(prompt)
        
    
    def actions_constraints_prompt(self) -> str:
        prompt = \
            """
              
            """
            # TODO

        return textwrap.dedent(prompt)
    

