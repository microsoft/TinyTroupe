"""
Scenario tests for the office communication tools, exercised with **real LLM calls**.

Per the project's guidelines, functionality that depends on LLM calls to operate must be tested
end-to-end with real models (cached to reduce cost). Here we verify that real agents, given the
tool prompts, actually drive the email client correctly: composing and sending an email, having
the recipient perceive a NOTIFICATION, checking/reading the inbox (INSPECTION), and replying --
with asynchronous (next-step) delivery handled by the shared service inside the world.

Note on the turn model: a tool result (e.g. the inbox listing from CHECK_INBOX) is delivered as
an INSPECTION stimulus the agent perceives on its *next* turn. Therefore a check -> read -> reply
flow naturally spans several turns, which these tests accommodate by letting the agent act
multiple times.
"""

import pytest
import logging

logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

import tinytroupe
from tinytroupe.agent import TinyToolUse
from tinytroupe.environment import TinyWorld
from tinytroupe.tools import (
    TinyEmailClient, EmailService, TinyContactsDirectory,
    TinyCalendar, CalendarService,
)
from tinytroupe.examples import create_lisa_the_data_scientist, create_oscar_the_architect

from testing_utils import *


def _build_office(agents):
    """Equips each agent with its own email client and registers the shared services in a world."""
    email_service = EmailService()
    directory = TinyContactsDirectory(domain="simcorp.tt")

    for agent in agents:
        client = TinyEmailClient(owner=agent, service=email_service, directory=directory)
        agent.add_mental_faculties([TinyToolUse(tools=[client])])
        directory.register(agent.name, "email", tool_uri=client.uri())

    world = TinyWorld("Office", agents)
    world.register_service(email_service)
    world.register_service(directory)
    world.make_everyone_accessible()
    return world, email_service


def _act_until(agent, world, predicate, max_turns=6):
    """Lets an agent take up to ``max_turns`` turns, flushing services between turns, until
    ``predicate()`` holds. Returns True if the predicate was satisfied."""
    if predicate():
        return True
    for _ in range(max_turns):
        agent.act()
        world._flush_services()
        if predicate():
            return True
    return False


@pytest.mark.core
def test_email_send_and_receive_scenario(setup):
    """A real agent composes and sends an email; the recipient receives it after delivery."""
    lisa = create_lisa_the_data_scientist()
    oscar = create_oscar_the_architect()
    world, email_service = _build_office([lisa, oscar])

    lisa.listen(
        "Please send a short email to Oscar inviting him to a project kickoff meeting. "
        "Use your email tool (TINYEMAILCLIENT::SEND_EMAIL) to actually send it now."
    )

    delivered = _act_until(
        lisa, world,
        lambda: any(m["from"] == "Lisa Carter" for m in email_service.inbox("Oscar")),
        max_turns=4,
    )

    assert delivered, "Oscar should have received an email from Lisa after she sent it."


@pytest.mark.core
def test_email_reply_scenario(setup):
    """End-to-end: Lisa emails Oscar; Oscar checks, reads, and replies; Lisa receives the reply."""
    lisa = create_lisa_the_data_scientist()
    oscar = create_oscar_the_architect()
    world, email_service = _build_office([lisa, oscar])

    # Seed an email from Lisa directly through the service (deterministic setup),
    # then let the real LLM-driven Oscar discover and reply to it.
    email_service.send(
        sender_name="Lisa Carter",
        subject="Project kickoff",
        body="Hi Oscar, can we meet next week to kick off the project? Please reply with your availability.",
        to=["Oscar"],
        directory=world.get_service(TinyContactsDirectory),
        timestamp=lisa.iso_datetime(),
    )

    # Deliver the seeded email (flush realizes next-step delivery).
    world._flush_services()
    assert len(email_service.inbox("Oscar")) >= 1

    oscar.listen(
        "You have received a new email. Check your inbox (TINYEMAILCLIENT::CHECK_INBOX), read the "
        "message (TINYEMAILCLIENT::READ_EMAIL), and reply to it (TINYEMAILCLIENT::REPLY_EMAIL) with "
        "your availability for next week."
    )

    # The check -> read -> reply flow spans several turns (each tool result arrives next turn).
    replied = _act_until(
        oscar, world,
        lambda: any(m["from"] == "Oscar" for m in email_service.inbox("Lisa Carter")),
        max_turns=6,
    )

    assert replied, "Lisa should have received Oscar's reply after he checked, read and replied."


@pytest.mark.core
def test_calendar_schedule_meeting_scenario(setup):
    """A real agent schedules a meeting; the invitee receives the invitation on a later turn."""
    lisa = create_lisa_the_data_scientist()
    oscar = create_oscar_the_architect()

    calendar_service = CalendarService()
    directory = TinyContactsDirectory(domain="simcorp.tt")
    for agent in (lisa, oscar):
        client = TinyCalendar(owner=agent, service=calendar_service, directory=directory)
        agent.add_mental_faculties([TinyToolUse(tools=[client])])
        directory.register(agent.name, "email", tool_uri=client.uri())

    world = TinyWorld("Office", [lisa, oscar])
    world.register_service(calendar_service)
    world.register_service(directory)
    world.make_everyone_accessible()

    lisa.listen(
        "Use your calendar tool to schedule a meeting titled 'Kickoff' with Oscar. "
        "Issue a TINYCALENDAR::SCHEDULE_MEETING action now, putting Oscar in the attendees."
    )

    scheduled = _act_until(
        lisa, world,
        lambda: len(calendar_service.calendar("Oscar")) >= 1,
        max_turns=6,
    )

    assert scheduled, "Oscar should have a meeting on his calendar after Lisa scheduled it."
    event = calendar_service.calendar("Oscar")[0]
    assert event["organizer"] == "Lisa Carter", "The meeting should have been organized by Lisa."
