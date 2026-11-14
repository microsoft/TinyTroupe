import pytest
import logging
logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.tools import TinyCalendar
from tinytroupe.examples import create_oscar_the_architect, create_lisa_the_data_scientist
from testing_utils import *


def test_calendar_initialization(setup):
    """Test TinyCalendar initialization."""
    calendar = TinyCalendar()
    assert calendar.name == "calendar"
    assert calendar.description is not None
    assert calendar.owner is None
    assert calendar.real_world_side_effects == False
    assert calendar.calendar == {}


def test_calendar_add_event(setup):
    """Test adding events directly via add_event()."""
    calendar = TinyCalendar()

    # Add an event on a specific date
    calendar.add_event(
        date="2025-03-15",
        title="Team meeting",
        description="Weekly sync",
        owner="Oscar",
        mandatory_attendees=["Oscar", "Lisa"],
        optional_attendees=["Marcos"],
        start_time="10:00",
        end_time="11:00"
    )

    assert "2025-03-15" in calendar.calendar
    assert len(calendar.calendar["2025-03-15"]) == 1

    event = calendar.calendar["2025-03-15"][0]
    assert event["title"] == "Team meeting"
    assert event["description"] == "Weekly sync"
    assert event["owner"] == "Oscar"
    assert event["mandatory_attendees"] == ["Oscar", "Lisa"]
    assert event["optional_attendees"] == ["Marcos"]
    assert event["start_time"] == "10:00"
    assert event["end_time"] == "11:00"


def test_calendar_add_multiple_events_same_date(setup):
    """Test adding multiple events on the same date."""
    calendar = TinyCalendar()

    calendar.add_event("2025-03-15", "Morning standup", start_time="09:00")
    calendar.add_event("2025-03-15", "Lunch break", start_time="12:00")
    calendar.add_event("2025-03-15", "Afternoon review", start_time="15:00")

    assert len(calendar.calendar["2025-03-15"]) == 3


def test_calendar_add_events_different_dates(setup):
    """Test adding events on different dates."""
    calendar = TinyCalendar()

    calendar.add_event("2025-03-15", "Event on 15th")
    calendar.add_event("2025-03-16", "Event on 16th")
    calendar.add_event("2025-03-17", "Event on 17th")

    assert len(calendar.calendar) == 3
    assert len(calendar.calendar["2025-03-15"]) == 1
    assert len(calendar.calendar["2025-03-16"]) == 1
    assert len(calendar.calendar["2025-03-17"]) == 1


def test_process_action_creates_event(setup):
    """Test that _process_action handles a valid CREATE_EVENT action."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()

    action = {
        "type": "CREATE_EVENT",
        "content": '{"date": "2025-06-01", "title": "Project kickoff", "description": "Initial meeting", "start_time": "09:00", "end_time": "10:30"}'
    }

    result = calendar._process_action(agent, action)
    assert result == True

    assert "2025-06-01" in calendar.calendar
    event = calendar.calendar["2025-06-01"][0]
    assert event["title"] == "Project kickoff"
    assert event["start_time"] == "09:00"
    assert event["end_time"] == "10:30"


def test_process_action_with_owner(setup):
    """Test CREATE_EVENT with owner field."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()

    action = {
        "type": "CREATE_EVENT",
        "content": '{"date": "2025-06-01", "title": "Design review", "owner": "Oscar"}'
    }

    result = calendar._process_action(agent, action)
    assert result == True

    event = calendar.calendar["2025-06-01"][0]
    assert event["owner"] == "Oscar"


def test_process_action_with_attendees(setup):
    """Test CREATE_EVENT with attendee lists."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()

    action = {
        "type": "CREATE_EVENT",
        "content": '{"date": "2025-06-01", "title": "Team sync", "mandatory_attendees": ["Oscar", "Lisa"], "optional_attendees": ["Marcos"]}'
    }

    result = calendar._process_action(agent, action)
    assert result == True

    event = calendar.calendar["2025-06-01"][0]
    assert event["mandatory_attendees"] == ["Oscar", "Lisa"]
    assert event["optional_attendees"] == ["Marcos"]


def test_process_action_invalid_field(setup):
    """Test CREATE_EVENT with an invalid field raises ValueError."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()

    action = {
        "type": "CREATE_EVENT",
        "content": '{"date": "2025-06-01", "title": "Bad event", "invalid_field": "should fail"}'
    }

    with pytest.raises(ValueError, match="Invalid key"):
        calendar._process_action(agent, action)


def test_process_action_missing_content(setup):
    """Test CREATE_EVENT with None content returns False."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()

    action = {"type": "CREATE_EVENT", "content": None}

    result = calendar._process_action(agent, action)
    assert result == False


def test_process_action_wrong_type(setup):
    """Test non-CREATE_EVENT action returns False."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()

    action = {"type": "TALK", "content": "Hello"}
    result = calendar._process_action(agent, action)
    assert result == False


def test_find_events_by_date(setup):
    """Test find_events returns events for a specific date."""
    calendar = TinyCalendar()
    calendar.add_event("2025-07-04", "Independence day BBQ")
    calendar.add_event("2025-07-04", "Fireworks show", start_time="21:00")
    calendar.add_event("2025-07-05", "Recovery brunch")

    events = calendar.find_events(2025, 7, 4)
    assert len(events) == 2


def test_find_events_no_match(setup):
    """Test find_events returns empty list when no events exist."""
    calendar = TinyCalendar()
    calendar.add_event("2025-07-04", "Some event")

    events = calendar.find_events(2025, 12, 25)
    assert len(events) == 0


def test_find_events_with_hour_filter(setup):
    """Test find_events with hour filtering."""
    calendar = TinyCalendar()
    calendar.add_event("2025-07-04", "Morning", start_time="09:00")
    calendar.add_event("2025-07-04", "Afternoon", start_time="14:00")
    calendar.add_event("2025-07-04", "Evening", start_time="18:00")

    events = calendar.find_events(2025, 7, 4, hour=14)
    assert len(events) == 1
    assert events[0]["title"] == "Afternoon"


def test_find_events_with_hour_and_minute_filter(setup):
    """Test find_events with hour and minute filtering."""
    calendar = TinyCalendar()
    calendar.add_event("2025-07-04", "Standup", start_time="09:00")
    calendar.add_event("2025-07-04", "Detail meeting", start_time="09:30")
    calendar.add_event("2025-07-04", "Workshop", start_time="10:00")

    events = calendar.find_events(2025, 7, 4, hour=9, minute=30)
    assert len(events) == 1
    assert events[0]["title"] == "Detail meeting"


def test_find_events_events_without_time(setup):
    """Test find_events with time filter includes events without start_time."""
    calendar = TinyCalendar()
    calendar.add_event("2025-07-04", "All-day event", start_time=None)
    calendar.add_event("2025-07-04", "Timed event", start_time="10:00")

    # Time filter should include events without a start time
    events = calendar.find_events(2025, 7, 4, hour=10)
    assert len(events) == 2


def test_actions_definitions_prompt(setup):
    """Test actions_definitions_prompt returns a non-empty string mentioning CREATE_EVENT."""
    calendar = TinyCalendar()
    prompt = calendar.actions_definitions_prompt()
    assert len(prompt) > 0
    assert "CREATE_EVENT" in prompt


def test_actions_constraints_prompt(setup):
    """Test actions_constraints_prompt returns a non-empty string."""
    calendar = TinyCalendar()
    prompt = calendar.actions_constraints_prompt()
    assert len(prompt) > 0
    assert "CREATE_EVENT" in prompt


def test_calendar_ownership(setup):
    """Test TinyCalendar inherits ownership enforcement from TinyTool."""
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()

    calendar = TinyCalendar(owner=oscar)

    # Oscar can use the calendar
    action = {
        "type": "CREATE_EVENT",
        "content": '{"date": "2025-06-01", "title": "Oscar\'s event"}'
    }
    result = calendar.process_action(oscar, action)
    assert result == True

    # Lisa should not be able to use Oscar's calendar
    with pytest.raises(ValueError, match="does not own"):
        calendar.process_action(lisa, action)


def test_calendar_serializable_attributes(setup):
    """Test that TinyCalendar includes calendar state in serializable attributes."""
    calendar = TinyCalendar()
    calendar.add_event("2025-08-01", "Test event")
    assert "calendar" in calendar.serializable_attributes

    calendar.add_event("2025-08-01", "Another event")
    assert len(calendar.calendar["2025-08-01"]) == 2


def test_calendar_serialization_to_json(setup):
    """Test that TinyCalendar can serialize/deserialize its state via to_json / from_json."""
    calendar = TinyCalendar()
    calendar.add_event("2025-08-01", "Test event", start_time="10:00")
    calendar.add_event("2025-08-01", "Another event", start_time="14:00")
    calendar.add_event("2025-09-15", "Future event")

    serialized = calendar.to_json()

    # Check that calendar data was serialized
    assert "calendar" in serialized
    assert "2025-08-01" in serialized["calendar"]
    assert len(serialized["calendar"]["2025-08-01"]) == 2
    assert serialized["calendar"]["2025-08-01"][0]["title"] == "Test event"
    assert serialized["calendar"]["2025-08-01"][1]["start_time"] == "14:00"
    assert serialized["calendar"]["2025-09-15"][0]["title"] == "Future event"

    # Deserialize into a new calendar
    calendar2 = TinyCalendar.from_json(serialized)

    # Check that events were restored
    assert "2025-08-01" in calendar2.calendar
    assert "2025-09-15" in calendar2.calendar
    assert len(calendar2.calendar["2025-08-01"]) == 2
    assert calendar2.calendar["2025-08-01"][0]["title"] == "Test event"


# ===== New action types: FIND_EVENTS =====

def test_process_action_find_events_found(setup):
    """Test FIND_EVENTS returns events via agent.think()."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()
    calendar.add_event("2025-07-04", "BBQ", start_time="12:00")
    calendar.add_event("2025-07-04", "Fireworks", start_time="21:00")

    action = {
        "type": "FIND_EVENTS",
        "content": '{"year": 2025, "month": 7, "day": 4}'
    }
    result = calendar._process_action(agent, action)
    assert result == True
    # agent.think() was called — no crash means success


def test_process_action_find_events_not_found(setup):
    """Test FIND_EVENTS with no matching date."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()
    calendar.add_event("2025-07-04", "BBQ")

    action = {
        "type": "FIND_EVENTS",
        "content": '{"year": 2025, "month": 12, "day": 25}'
    }
    result = calendar._process_action(agent, action)
    assert result == True


def test_process_action_find_events_with_hour(setup):
    """Test FIND_EVENTS with hour filter."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()
    calendar.add_event("2025-07-04", "Morning", start_time="09:00")
    calendar.add_event("2025-07-04", "Afternoon", start_time="14:00")

    action = {
        "type": "FIND_EVENTS",
        "content": '{"year": 2025, "month": 7, "day": 4, "hour": 14}'
    }
    result = calendar._process_action(agent, action)
    assert result == True


def test_process_action_find_events_invalid_field(setup):
    """Test FIND_EVENTS with invalid field raises ValueError."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()

    action = {
        "type": "FIND_EVENTS",
        "content": '{"year": 2025, "month": 7, "day": 4, "invalid": "bad"}'
    }
    with pytest.raises(ValueError, match="Invalid key"):
        calendar._process_action(agent, action)


# ===== New action types: LIST_EVENTS =====

def test_process_action_list_events_with_data(setup):
    """Test LIST_EVENTS returns events across dates."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()
    calendar.add_event("2025-07-04", "BBQ")
    calendar.add_event("2025-07-05", "Brunch")

    action = {"type": "LIST_EVENTS"}
    result = calendar._process_action(agent, action)
    assert result == True


def test_process_action_list_events_empty(setup):
    """Test LIST_EVENTS with no events."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()

    action = {"type": "LIST_EVENTS"}
    result = calendar._process_action(agent, action)
    assert result == True


def test_process_action_list_events_with_max_results(setup):
    """Test LIST_EVENTS with max_results filter."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()
    calendar.add_event("2025-01-01", "Event 1")
    calendar.add_event("2025-01-02", "Event 2")
    calendar.add_event("2025-01-03", "Event 3")

    action = {
        "type": "LIST_EVENTS",
        "content": '{"max_results": 2}'
    }
    result = calendar._process_action(agent, action)
    assert result == True


# ===== New action types: DELETE_EVENT =====

def test_process_action_delete_event_found(setup):
    """Test DELETE_EVENT removes an event."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()
    calendar.add_event("2025-07-04", "BBQ")

    action = {
        "type": "DELETE_EVENT",
        "content": '{"date": "2025-07-04", "title": "BBQ"}'
    }
    result = calendar._process_action(agent, action)
    assert result == True
    assert "2025-07-04" not in calendar.calendar  # date key cleaned up


def test_process_action_delete_event_not_found(setup):
    """Test DELETE_EVENT when event does not exist."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()

    action = {
        "type": "DELETE_EVENT",
        "content": '{"date": "2025-07-04", "title": "Nonexistent"}'
    }
    result = calendar._process_action(agent, action)
    assert result == True  # still returns True (action was valid), but think() reports failure


def test_process_action_delete_event_with_start_time(setup):
    """Test DELETE_EVENT with start_time disambiguation."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()
    calendar.add_event("2025-07-04", "Meeting", start_time="09:00")
    calendar.add_event("2025-07-04", "Meeting", start_time="14:00")

    action = {
        "type": "DELETE_EVENT",
        "content": '{"date": "2025-07-04", "title": "Meeting", "start_time": "09:00"}'
    }
    result = calendar._process_action(agent, action)
    assert result == True
    assert len(calendar.calendar["2025-07-04"]) == 1
    assert calendar.calendar["2025-07-04"][0]["start_time"] == "14:00"


def test_process_action_delete_event_invalid_field(setup):
    """Test DELETE_EVENT with invalid field raises ValueError."""
    calendar = TinyCalendar()
    agent = create_oscar_the_architect()

    action = {
        "type": "DELETE_EVENT",
        "content": '{"date": "2025-07-04", "title": "X", "bad_field": "bad"}'
    }
    with pytest.raises(ValueError, match="Invalid key"):
        calendar._process_action(agent, action)


# ===== list_events() and delete_event() programmatic API =====

def test_list_events_all(setup):
    """Test list_events returns all events sorted chronologically."""
    calendar = TinyCalendar()
    calendar.add_event("2025-03-02", "Second")
    calendar.add_event("2025-03-01", "First")
    calendar.add_event("2025-03-03", "Third")

    events = calendar.list_events()
    assert len(events) == 3
    assert events[0]["title"] == "First"
    assert events[1]["title"] == "Second"
    assert events[2]["title"] == "Third"


def test_list_events_max_results(setup):
    """Test list_events with max_results."""
    calendar = TinyCalendar()
    calendar.add_event("2025-03-01", "First")
    calendar.add_event("2025-03-02", "Second")
    calendar.add_event("2025-03-03", "Third")

    events = calendar.list_events(max_results=2)
    assert len(events) == 2
    assert events[0]["title"] == "First"
    assert events[1]["title"] == "Second"


def test_list_events_empty(setup):
    """Test list_events returns empty list when no events."""
    calendar = TinyCalendar()
    events = calendar.list_events()
    assert events == []


def test_delete_event_by_title(setup):
    """Test delete_event removes by title."""
    calendar = TinyCalendar()
    calendar.add_event("2025-07-04", "BBQ")
    calendar.add_event("2025-07-04", "Cleanup")

    result = calendar.delete_event("2025-07-04", "BBQ")
    assert result == True
    assert len(calendar.calendar["2025-07-04"]) == 1
    assert calendar.calendar["2025-07-04"][0]["title"] == "Cleanup"


def test_delete_event_not_found(setup):
    """Test delete_event returns False when no match."""
    calendar = TinyCalendar()
    calendar.add_event("2025-07-04", "BBQ")

    result = calendar.delete_event("2025-07-04", "Nonexistent")
    assert result == False
    assert len(calendar.calendar["2025-07-04"]) == 1


def test_delete_event_date_not_found(setup):
    """Test delete_event returns False when date doesn't exist."""
    calendar = TinyCalendar()

    result = calendar.delete_event("2025-07-04", "BBQ")
    assert result == False


def test_delete_event_removes_empty_date(setup):
    """Test delete_event cleans up empty date keys."""
    calendar = TinyCalendar()
    calendar.add_event("2025-07-04", "Only event")

    calendar.delete_event("2025-07-04", "Only event")
    assert "2025-07-04" not in calendar.calendar