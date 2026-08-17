
import json
from datetime import datetime, timedelta

from tinytroupe.tools import logger, TinyTool
import tinytroupe.utils as utils


class TinyCalendar(TinyTool):
    serializable_attributes = ["name", "description", "real_world_side_effects", "calendar"]

    def __init__(self, owner=None, world=None):
        super().__init__("calendar", "A basic calendar tool that allows agents to keep track meetings and appointments.", owner=owner, real_world_side_effects=False)
        
        # maps date to list of events. Each event itself is a dictionary with keys "title", "description", "owner", "mandatory_attendees", "optional_attendees", "start_time", "end_time"
        self.calendar = {}
        # optional reference to the TinyWorld for cross-agent notifications
        self.world = world
    
    def add_event(self, date, title, description=None, owner=None, mandatory_attendees=None, optional_attendees=None, start_time=None, end_time=None):
        if date not in self.calendar:
            self.calendar[date] = []
        self.calendar[date].append({"title": title, "description": description, "owner": owner, "mandatory_attendees": mandatory_attendees, "optional_attendees": optional_attendees, "start_time": start_time, "end_time": end_time})
    
    def find_events(self, year, month, day, hour=None, minute=None):
        """
        Finds events for a given date. Optionally filters by hour and minute.
        Returns a list of event dicts matching the criteria.
        """
        date_key = f"{year:04d}-{month:02d}-{day:02d}"
        events_on_date = self.calendar.get(date_key, [])

        if hour is None and minute is None:
            return events_on_date

        # Filter by time if specified
        matched = []
        for event in events_on_date:
            start = event.get("start_time")
            if start is None:
                # Events without a start time match any time filter
                matched.append(event)
            else:
                try:
                    event_hour, event_minute = start.split(":")
                    event_hour, event_minute = int(event_hour), int(event_minute)
                    if event_hour == hour and (minute is None or event_minute == minute):
                        matched.append(event)
                except (ValueError, AttributeError):
                    matched.append(event)
        return matched
    
    def list_events(self, max_results=None):
        """
        Lists all events across all dates, sorted chronologically.
        Returns a list of dicts, each with a "date" key plus the event data.
        
        Args:
            max_results: Maximum number of events to return. None means all.
        """
        all_events = []
        for date_key in sorted(self.calendar.keys()):
            for event in self.calendar[date_key]:
                entry = {"date": date_key, **event}
                all_events.append(entry)
        
        if max_results is not None:
            return all_events[:max_results]
        return all_events
    
    def delete_event(self, date, title, start_time=None):
        """
        Deletes an event by date, title, and optionally start_time.
        Returns True if an event was removed, False otherwise.
        """
        if date not in self.calendar:
            return False
        
        original_count = len(self.calendar[date])
        if start_time is not None:
            self.calendar[date] = [
                e for e in self.calendar[date]
                if not (e["title"] == title and e["start_time"] == start_time)
            ]
        else:
            self.calendar[date] = [
                e for e in self.calendar[date]
                if e["title"] != title
            ]
        
        removed = original_count - len(self.calendar[date])
        # Clean up empty date entries
        if len(self.calendar[date]) == 0:
            del self.calendar[date]
        
        return removed > 0

    def _process_action(self, agent, action) -> bool:
        action_type = action['type']
        
        if action_type == "CREATE_EVENT" and action.get('content') is not None:
            # parse content json
            event_content = json.loads(action['content'])
            
            # checks whether there are any kwargs that are not valid
            valid_keys = ["date", "title", "description", "owner", "mandatory_attendees", "optional_attendees", "start_time", "end_time"]
            utils.check_valid_fields(event_content, valid_keys)

            # uses the kwargs to create a new event
            self.add_event(**event_content)

            # Notify attendees if a world reference is available
            attendees = []
            if event_content.get("mandatory_attendees"):
                attendees.extend(event_content["mandatory_attendees"])
            if event_content.get("optional_attendees"):
                attendees.extend(event_content["optional_attendees"])
            
            if attendees and self.world is not None:
                from tinytroupe.environment.tiny_world import TinyWorld
                for attendee_name in attendees:
                    attendee_agent = self.world.get_agent_by_name(attendee_name)
                    if attendee_agent is not None:
                        # Make agents mutually accessible for interaction
                        attendee_agent.make_agent_accessible(agent)
                        agent.make_agent_accessible(attendee_agent)
                        # Social notification
                        attendee_agent.socialize(
                            f"You have been invited to the event '{event_content.get('title', 'Untitled')}' "
                            f"on {event_content.get('date', 'unknown date')} "
                            f"by {event_content.get('owner', agent.name)}.",
                            source=agent
                        )
                    else:
                        logger.warning(f"Attendee '{attendee_name}' not found in the world.")
            
            agent.think(f"I have created a new event '{event_content.get('title', 'Untitled')}' on {event_content.get('date', 'unknown date')} in my calendar.")

            return True

        elif action_type == "FIND_EVENTS" and action.get('content') is not None:
            query = json.loads(action['content'])
            valid_keys = ["year", "month", "day", "hour", "minute"]
            utils.check_valid_fields(query, valid_keys)
            
            events = self.find_events(
                year=query.get("year"),
                month=query.get("month"),
                day=query.get("day"),
                hour=query.get("hour"),
                minute=query.get("minute")
            )
            
            if events:
                summary = "; ".join([f"{e['title']} at {e.get('start_time', 'all day')}" for e in events])
                agent.think(f"I found {len(events)} event(s) in my calendar on {query['year']}-{query['month']:02d}-{query['day']:02d}: {summary}.")
            else:
                agent.think(f"I found no events in my calendar on {query['year']}-{query['month']:02d}-{query['day']:02d}.")
            
            return True

        elif action_type == "LIST_EVENTS":
            max_results = None
            if action.get('content') is not None:
                params = json.loads(action['content'])
                max_results = params.get("max_results", None)
            
            events = self.list_events(max_results=max_results)
            
            if events:
                summary = "; ".join([f"[{e['date']}] {e['title']} at {e.get('start_time', 'all day')}" for e in events])
                agent.think(f"I have {len(events)} upcoming event(s) in my calendar: {summary}.")
            else:
                agent.think("I have no events in my calendar.")
            
            return True

        elif action_type == "DELETE_EVENT" and action.get('content') is not None:
            query = json.loads(action['content'])
            valid_keys = ["date", "title", "start_time"]
            utils.check_valid_fields(query, valid_keys)
            
            removed = self.delete_event(
                date=query.get("date"),
                title=query.get("title"),
                start_time=query.get("start_time")
            )
            
            if removed:
                agent.think(f"I have deleted the event '{query['title']}' from my calendar.")
            else:
                agent.think(f"I could not find an event '{query['title']}' on {query.get('date', 'any date')} in my calendar.")
            
            return True

        else:
            return False

    def actions_definitions_prompt(self) -> str:
        prompt = \
            """
              - CREATE_EVENT: You can create a new event in your calendar. The content of the event has many fields, and you should use a JSON format to specify them. Here are the possible fields:
                * date: The date of the event, in "YYYY-MM-DD" format. Mandatory.
                * title: The title of the event. Mandatory.
                * description: A brief description of the event. Optional.
                * owner: The name of the person creating or owning the event. Optional.
                * mandatory_attendees: A list of agent names who must attend the event. Optional.
                * optional_attendees: A list of agent names who are invited to the event, but are not required to attend. Optional.
                * start_time: The start time of the event, in "HH:MM" format (24-hour). Optional.
                * end_time: The end time of the event, in "HH:MM" format (24-hour). Optional.
              - FIND_EVENTS: You can search for events on a specific date. The content must be a JSON with these fields:
                * year: The year to search (e.g., 2025). Mandatory.
                * month: The month to search (1-12). Mandatory.
                * day: The day to search (1-31). Mandatory.
                * hour: Optional hour filter (0-23).
                * minute: Optional minute filter (0-59).
              - LIST_EVENTS: You can list all upcoming events in your calendar. Optionally, you can specify a JSON content with a "max_results" field to limit the number of events returned.
              - DELETE_EVENT: You can delete an event from your calendar. The content must be a JSON with these fields:
                * date: The date of the event to delete, in "YYYY-MM-DD" format. Mandatory.
                * title: The title of the event to delete. Mandatory.
                * start_time: Optional start time to disambiguate if multiple events have the same title.
            """
        # Attendee notification is handled in _process_action when a world reference is available.
        # The world must be set via the constructor (world= parameter) for cross-agent notifications to work.
        # Attendees receive a socialize() notification and both agents are made mutually accessible.

        return utils.dedent(prompt)
        
    
    def actions_constraints_prompt(self) -> str:
        prompt = \
            """
              - When you CREATE_EVENT, you **must** specify at least a title and a date in JSON format.
              - The date **must** be a string in the format "YYYY-MM-DD".
              - The start_time and end_time **must** be strings in the format "HH:MM" (24-hour format).
              - The mandatory_attendees and optional_attendees, if provided, **must** be lists of agent names.
              - When you include attendees in a CREATE_EVENT, those agents will be notified automatically if possible. If notification fails (e.g., agent not found), you will see a warning but the event is still created.
              - You should CREATE_EVENT when you need to schedule a meeting, appointment, or any timed activity.
              - You should FIND_EVENTS when you need to check what events exist on a particular date.
              - You should LIST_EVENTS when you need an overview of all your upcoming events.
              - You should DELETE_EVENT when an event is cancelled or no longer relevant.
            """

        return utils.dedent(prompt)
    

