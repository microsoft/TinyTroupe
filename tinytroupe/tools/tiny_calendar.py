
import textwrap
import json
from datetime import datetime

from tinytroupe.tools import logger, TinyTool
import tinytroupe.utils as utils


class TinyCalendar(TinyTool):
    """
    A basic calendar tool that allows agents to track meetings and appointments.
    """

    def __init__(self, owner=None):
        super().__init__(
            "calendar",
            "A basic calendar tool that allows agents to keep track meetings and appointments.",
            owner=owner,
            real_world_side_effects=False,
        )
        # maps date (YYYY-MM-DD string) to list of events
        self.calendar = {}

    def add_event(
        self,
        date=None,
        title=None,
        description=None,
        owner=None,
        mandatory_attendees=None,
        optional_attendees=None,
        start_time=None,
        end_time=None,
    ):
        """Add an event. Accepts either (date, title, ...) or a single dict: add_event(event_dict)."""
        if isinstance(date, dict):
            ev = date
            date = ev.get("date", datetime.now().strftime("%Y-%m-%d"))
            event = {
                "title": ev.get("title", "Untitled"),
                "description": ev.get("description"),
                "owner": ev.get("owner"),
                "mandatory_attendees": ev.get("mandatory_attendees"),
                "optional_attendees": ev.get("optional_attendees"),
                "start_time": ev.get("start_time"),
                "end_time": ev.get("end_time"),
            }
        else:
            event = {
                "title": title,
                "description": description,
                "owner": owner,
                "mandatory_attendees": mandatory_attendees,
                "optional_attendees": optional_attendees,
                "start_time": start_time,
                "end_time": end_time,
            }
        if date not in self.calendar:
            self.calendar[date] = []
        self.calendar[date].append(event)

    def find_events(self, year, month, day, hour=None, minute=None):
        """Find events on the given date, optionally filtered by hour/minute."""
        date_key = f"{year:04d}-{month:02d}-{day:02d}"
        events = self.calendar.get(date_key, [])
        result = []
        for ev in events:
            if hour is not None or minute is not None:
                st = ev.get("start_time")
                if st:
                    try:
                        dt = datetime.fromisoformat(st) if isinstance(st, str) else st
                        if hour is not None and dt.hour != hour:
                            continue
                        if minute is not None and dt.minute != minute:
                            continue
                    except (ValueError, TypeError):
                        pass
            result.append(ev)
        return result

    def _process_action(self, agent, action) -> bool:
        if action["type"] == "CREATE_EVENT" and action["content"] is not None:
            event_content = json.loads(action["content"])
            valid_keys = [
                "date",
                "title",
                "description",
                "mandatory_attendees",
                "optional_attendees",
                "start_time",
                "end_time",
            ]
            utils.check_valid_fields(event_content, valid_keys)
            self.add_event(event_content)
            return True
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
        prompt = """
        Actions must be CREATE_EVENT or use find_events. For CREATE_EVENT, provide
        content as JSON with at least date and title; optional: description,
        mandatory_attendees, optional_attendees, start_time, end_time.
        """
        return textwrap.dedent(prompt)
    

