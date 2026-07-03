import pytest
import logging
logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.utils import targeting
from tinytroupe.tools.tiny_tool import (
    TinyTool, parse_action_namespace, namespaced_action_type, _slugify,
)
from tinytroupe.tools import (
    TinyWordProcessor, TinyCalendar, CalendarService,
    TinyEmailClient, EmailService, TinyContactsDirectory,
)
from tinytroupe.agent.mental_faculty import TinyToolUse
from tinytroupe.environment import TinyWorld
from tinytroupe.examples import create_oscar_the_architect, create_lisa_the_data_scientist
from testing_utils import *


# --------------------------------------------------------------------------- #
# Target URI utilities
# --------------------------------------------------------------------------- #
@pytest.mark.core
def test_target_uri_parsing(setup):
    assert targeting.parse_uri("Lisa Carter") == ("tinyperson", "Lisa Carter")
    assert targeting.parse_uri("tinyperson:Oscar") == ("tinyperson", "Oscar")
    assert targeting.parse_uri("tinytool:lisa-carter.email") == ("tinytool", "lisa-carter.email")
    assert targeting.parse_uri("") == ("", "")
    assert targeting.parse_uri(None) == ("", "")
    # unknown prefix is treated as a bare person name (robustness)
    assert targeting.parse_uri("mailto:x")[0] == "tinyperson"


@pytest.mark.core
def test_target_uri_extraction_and_conflict(setup):
    assert targeting.extract_target_uris({"target": "tinyperson:Oscar"}) == ["tinyperson:Oscar"]
    assert targeting.extract_target_uris({"targets": ["tinyperson:A", "tinytool:b"]}) == ["tinyperson:A", "tinytool:b"]
    assert targeting.extract_target_uris({"target": ""}) == []
    assert targeting.recipient_names({"targets": ["tinyperson:A", "tinytool:b"]}) == ["A"]
    with pytest.raises(ValueError):
        targeting.extract_target_uris({"target": "a", "targets": ["b"]})


def test_action_namespacing():
    assert parse_action_namespace("TINYEMAILCLIENT::SEND_EMAIL") == ("TINYEMAILCLIENT", "SEND_EMAIL")
    assert parse_action_namespace("TALK") == (None, "TALK")
    assert namespaced_action_type("FOO", "BAR") == "FOO::BAR"
    assert _slugify("Lisa Carter") == "lisa-carter"


# --------------------------------------------------------------------------- #
# TinyTool identity
# --------------------------------------------------------------------------- #
@pytest.mark.core
def test_tool_identity_and_uri(setup):
    oscar = create_oscar_the_architect()
    wp = TinyWordProcessor(owner=oscar)
    # id derived from owner + class kind; name is cosmetic
    assert wp.id == "oscar.wordprocessor"
    assert wp.name == "wordprocessor"
    assert wp.uri() == "tinytool:oscar.wordprocessor"

    shared = TinyWordProcessor()
    assert shared.id == "shared.wordprocessor"
    assert shared.owner is None

    explicit = TinyWordProcessor(owner=oscar, id="custom.id", name="Oscar's Writer")
    assert explicit.id == "custom.id"
    assert explicit.name == "Oscar's Writer"


@pytest.mark.core
def test_tool_id_immutable_on_owner_change(setup):
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()
    wp = TinyWordProcessor(owner=oscar)
    original_id = wp.id
    wp.set_owner(lisa)
    assert wp.owner == lisa
    assert wp.id == original_id  # id is immutable across ownership changes


def test_tool_handles_action():
    wp = TinyWordProcessor()
    assert wp.handles_action({"type": "TINYWORDPROCESSOR::WRITE_DOCUMENT"}) is True
    assert wp.handles_action({"type": "TALK"}) is False
    assert wp.handles_action({"type": "TINYEMAILCLIENT::SEND_EMAIL"}) is False


# --------------------------------------------------------------------------- #
# TinyToolUse namespace dispatch
# --------------------------------------------------------------------------- #
@pytest.mark.core
def test_tooluse_namespace_dispatch(setup):
    oscar = create_oscar_the_architect()
    wp = TinyWordProcessor(owner=oscar)
    faculty = TinyToolUse(tools=[wp])

    # un-namespaced action -> not a tool action
    assert faculty.process_action(oscar, {"type": "TALK", "content": "hi", "target": ""}) is False
    # namespaced action with no matching tool -> False (clean miss)
    assert faculty.process_action(oscar, {"type": "TINYEMAILCLIENT::SEND_EMAIL", "content": "{}"}) is False
    # matching namespaced action -> dispatched
    action = {"type": "TINYWORDPROCESSOR::WRITE_DOCUMENT",
              "content": {"title": "T", "content": "body", "author": "Oscar"}}
    assert faculty.process_action(oscar, action) is True


def test_tool_ownership_enforced(setup):
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()
    wp = TinyWordProcessor(owner=oscar)
    # Lisa cannot drive Oscar's tool directly
    with pytest.raises(ValueError, match="does not own tool"):
        wp.process_action(lisa, {"type": "TINYWORDPROCESSOR::WRITE_DOCUMENT",
                                 "content": {"title": "T", "content": "b"}})


# --------------------------------------------------------------------------- #
# Contacts directory
# --------------------------------------------------------------------------- #
def test_contacts_directory_resolution():
    d = TinyContactsDirectory(domain="simcorp.tt")
    assert d.address_of("Lisa Carter", "email") == "lisa.carter@simcorp.tt"
    d.register("Oscar", "email", address="oscar.silva@simcorp.tt", tool_uri="tinytool:oscar-silva.email")
    assert d.person_of_address("email", "oscar.silva@simcorp.tt") == "Oscar"
    assert d.tool_uri_of("Oscar", "email") == "tinytool:oscar-silva.email"
    assert d.resolve_recipient("tinyperson:Lisa Carter", "email") == "Lisa Carter"
    assert d.resolve_recipient("oscar.silva@simcorp.tt", "email") == "Oscar"


def test_contacts_directory_name_reconciliation():
    d = TinyContactsDirectory(domain="simcorp.tt")
    d.register("Oscar", "email")
    d.register("Lisa Carter", "email")
    # informal/embellished name reconciles to the canonical registered person
    assert d.resolve_recipient("Oscar Silva", "email") == "Oscar"
    assert d.resolve_recipient("tinyperson:Oscar Silva", "email") == "Oscar"
    # shorter form reconciles to the longer registered name (first-name basis)
    assert d.resolve_recipient("Lisa", "email") == "Lisa Carter"
    # case-insensitive
    assert d.resolve_recipient("oscar", "email") == "Oscar"
    # unknown stays unchanged
    assert d.resolve_recipient("Stranger Danger", "email") == "Stranger Danger"


# --------------------------------------------------------------------------- #
# Email service (logic-level, fake world)
# --------------------------------------------------------------------------- #
class _FakeAgent:
    def __init__(self, name):
        self.name = name
        self._mental_faculties = []
        self.notifications = []
    def notify(self, text, tinytool=None, source=None):
        self.notifications.append((text, tinytool))
    def iso_datetime(self):
        return "2026-06-08T10:00:00"


class _FakeWorld:
    def __init__(self, agents):
        self._agents = {a.name: a for a in agents}
        self.name = "FakeWorld"
    def get_agent_by_name(self, name):
        return self._agents.get(name)


def test_email_service_next_step_delivery():
    lisa, oscar = _FakeAgent("Lisa Carter"), _FakeAgent("Oscar")
    world = _FakeWorld([lisa, oscar])
    d = TinyContactsDirectory()
    svc = EmailService()

    msg = svc.send("Lisa Carter", "Design review", "Let's meet.",
                   to=["tinyperson:Oscar"], directory=d, timestamp="t")
    # not delivered until the next flush (async, next-step)
    assert svc.inbox("Oscar") == []
    svc.flush(world)
    assert len(svc.inbox("Oscar")) == 1
    assert svc.inbox("Oscar")[0]["subject"] == "Design review"
    assert svc.inbox("Oscar")[0]["read"] is False
    assert len(oscar.notifications) == 1
    assert msg["from_address"] == "lisa.carter@simcorp.tt"


def test_email_service_read_and_delete():
    oscar = _FakeAgent("Oscar")
    world = _FakeWorld([oscar])
    svc = EmailService()
    svc.send("Lisa Carter", "S", "B", to=["Oscar"])
    svc.flush(world)
    mid = svc.inbox("Oscar")[0]["id"]
    assert svc.mark_read("Oscar", mid)["read"] is True
    assert svc.delete_message("Oscar", mid) is True
    assert svc.inbox("Oscar") == []


# --------------------------------------------------------------------------- #
# Calendar service (logic-level, fake world)
# --------------------------------------------------------------------------- #
def test_calendar_service_invite_respond_cancel():
    lisa, oscar = _FakeAgent("Lisa Carter"), _FakeAgent("Oscar")
    world = _FakeWorld([lisa, oscar])
    svc = CalendarService()
    event = svc.schedule_meeting("Lisa Carter", "Design review",
                                 start_time="2026-06-09T10:00:00",
                                 mandatory_attendees=["Oscar"])
    # organizer auto-accepts; attendee has the meeting with no response yet
    assert event["responses"]["Lisa Carter"] == "accepted"
    assert svc.get_event("Oscar", event["id"])["responses"]["Oscar"] == "no_response"
    # invitation delivered next-step
    assert oscar.notifications == []
    svc.flush(world)
    assert len(oscar.notifications) == 1

    svc.respond_to_invite("Oscar", event["id"], "accepted")
    assert svc.get_event("Lisa Carter", event["id"])["responses"]["Oscar"] == "accepted"

    assert svc.cancel_meeting("Lisa Carter", event["id"]) is True
    assert svc.get_event("Oscar", event["id"])["cancelled"] is True

    with pytest.raises(ValueError):
        svc.respond_to_invite("Oscar", event["id"], "maybe")


@pytest.mark.core
def test_calendar_attendees_from_action_targets(setup):
    """SCHEDULE_MEETING honors the action's target/targets as invitees when content lists none."""
    lisa = create_lisa_the_data_scientist()
    oscar = create_oscar_the_architect()
    calendar_service = CalendarService()
    directory = TinyContactsDirectory()
    for agent in (lisa, oscar):
        client = TinyCalendar(owner=agent, service=calendar_service, directory=directory)
        agent.add_mental_faculties([TinyToolUse(tools=[client])])
        directory.register(agent.name, "email", tool_uri=client.uri())
    world = TinyWorld("Office4", [lisa, oscar])
    world.register_service(calendar_service)
    world.register_service(directory)

    lisa._mental_faculties[-1].process_action(lisa, {
        "type": "TINYCALENDAR::SCHEDULE_MEETING",
        "targets": ["tinyperson:Oscar"],
        "content": {"title": "Kickoff", "start_time": "2026-06-15T10:00:00"},
    })
    assert len(calendar_service.calendar("Oscar")) == 1
    assert calendar_service.calendar("Oscar")[0]["organizer"] == "Lisa Carter"


@pytest.mark.core
def test_calendar_rejects_unusable_schedule(setup):
    """An empty/malformed schedule (no title, no attendees) is rejected, not silently created."""
    lisa = create_lisa_the_data_scientist()
    calendar_service = CalendarService()
    directory = TinyContactsDirectory()
    client = TinyCalendar(owner=lisa, service=calendar_service, directory=directory)
    lisa.add_mental_faculties([TinyToolUse(tools=[client])])
    world = TinyWorld("Office5", [lisa])
    world.register_service(calendar_service)
    world.register_service(directory)

    # Malformed content that parses to nothing usable and no targets -> action fails cleanly.
    handled = lisa._mental_faculties[-1].process_action(lisa, {
        "type": "TINYCALENDAR::SCHEDULE_MEETING",
        "content": "garbage that is not json",
    })
    assert handled is False
    assert calendar_service.calendar("Lisa Carter") == []


# --------------------------------------------------------------------------- #
# World service registry
# --------------------------------------------------------------------------- #
@pytest.mark.core
def test_world_service_registry(setup):
    world = TinyWorld("Services world")
    svc = EmailService()
    world.register_service(svc)
    assert world.get_service(EmailService) is svc
    assert world.get_service("EmailService") is svc
    assert world.get_service(CalendarService, required=False) is None
    with pytest.raises(ValueError):
        world.get_service(CalendarService)


# --------------------------------------------------------------------------- #
# End-to-end: real agents, per-agent clients, one emails the other (no LLM)
# --------------------------------------------------------------------------- #
@pytest.mark.core
def test_email_end_to_end_per_agent(setup):
    lisa = create_lisa_the_data_scientist()
    oscar = create_oscar_the_architect()

    email_service = EmailService()
    directory = TinyContactsDirectory(domain="simcorp.tt")

    for agent in (lisa, oscar):
        client = TinyEmailClient(owner=agent, service=email_service, directory=directory)
        agent.add_mental_faculties([TinyToolUse(tools=[client])])
        directory.register(agent.name, "email", tool_uri=client.uri())

    world = TinyWorld("Office", [lisa, oscar])
    world.register_service(email_service)
    world.register_service(directory)

    # Lisa sends an email to Oscar through her own client's faculty.
    lisa_faculty = lisa._mental_faculties[-1]
    send_action = {
        "type": "TINYEMAILCLIENT::SEND_EMAIL",
        "content": {"subject": "Welcome", "body": "Hello Oscar!", "to": ["Oscar"]},
    }
    assert lisa_faculty.process_action(lisa, send_action) is True

    # Not yet in Oscar's inbox (next-step delivery)...
    assert email_service.inbox("Oscar") == []
    # ...until services are flushed (as happens at the start of each world step).
    world._flush_services()
    assert len(email_service.inbox("Oscar")) == 1
    received = email_service.inbox("Oscar")[0]
    assert received["subject"] == "Welcome"
    assert received["from"] == "Lisa Carter"

    # Oscar replies via his own client.
    oscar_faculty = oscar._mental_faculties[-1]
    reply_action = {
        "type": "TINYEMAILCLIENT::REPLY_EMAIL",
        "content": {"message_id": received["id"], "body": "Thanks Lisa!"},
    }
    assert oscar_faculty.process_action(oscar, reply_action) is True
    world._flush_services()
    lisa_inbox = email_service.inbox("Lisa Carter")
    assert len(lisa_inbox) == 1
    assert lisa_inbox[0]["subject"] == "Re: Welcome"
    assert lisa_inbox[0]["from"] == "Oscar"


@pytest.mark.core
def test_email_recipients_from_action_targets(setup):
    """SEND_EMAIL honors the action's target/targets as recipients when content.to is absent."""
    lisa = create_lisa_the_data_scientist()
    oscar = create_oscar_the_architect()
    email_service = EmailService()
    directory = TinyContactsDirectory()
    for agent in (lisa, oscar):
        client = TinyEmailClient(owner=agent, service=email_service, directory=directory)
        agent.add_mental_faculties([TinyToolUse(tools=[client])])
        directory.register(agent.name, "email", tool_uri=client.uri())
    world = TinyWorld("Office3", [lisa, oscar])
    world.register_service(email_service)
    world.register_service(directory)

    # No "to" in content; recipient is given via the generic targets field.
    lisa._mental_faculties[-1].process_action(lisa, {
        "type": "TINYEMAILCLIENT::SEND_EMAIL",
        "targets": ["tinyperson:Oscar"],
        "content": {"subject": "Via targets", "body": "hi"},
    })
    world._flush_services()
    assert len(email_service.inbox("Oscar")) == 1
    assert email_service.inbox("Oscar")[0]["subject"] == "Via targets"


@pytest.mark.core
def test_separate_clients_have_separate_inboxes(setup):
    lisa = create_lisa_the_data_scientist()
    oscar = create_oscar_the_architect()
    email_service = EmailService()
    directory = TinyContactsDirectory()

    clients = {}
    for agent in (lisa, oscar):
        client = TinyEmailClient(owner=agent, service=email_service, directory=directory)
        clients[agent.name] = client
        agent.add_mental_faculties([TinyToolUse(tools=[client])])

    # Each agent owns a distinct client instance with a distinct id.
    assert clients["Lisa Carter"].id != clients["Oscar"].id

    world = TinyWorld("Office2", [lisa, oscar])
    world.register_service(email_service)
    world.register_service(directory)

    lisa._mental_faculties[-1].process_action(lisa, {
        "type": "TINYEMAILCLIENT::SEND_EMAIL",
        "content": {"subject": "Only for Oscar", "body": "x", "to": ["Oscar"]},
    })
    world._flush_services()
    assert len(email_service.inbox("Oscar")) == 1
    assert email_service.inbox("Lisa Carter") == []
