
import json

from tinytroupe.tools import logger, TinyTool
from tinytroupe.tools.services import TinyService
from tinytroupe.tools.tiny_tool import parse_action_namespace
import tinytroupe.utils as utils


# Valid responses to a meeting invitation.
VALID_RESPONSES = ("accepted", "declined", "tentative", "no_response")


class CalendarService(TinyService):
    """
    Shared calendar service: holds each person's calendar, mints event ids, and delivers meeting
    invitations and cancellations asynchronously (next simulation step) via :meth:`flush`.
    """

    serializable_attributes = ["name", "_calendars", "_pending", "_event_counter"]

    def __init__(self, name: str = None):
        super().__init__(name)
        # person_name -> list of event dicts (their calendar)
        self._calendars = {}
        # queued (notification_text, recipient_name, tinytool_uri_resolver) deliveries
        self._pending = []
        self._event_counter = 0

    # ------------------------------------------------------------------ #
    # Scheduling
    # ------------------------------------------------------------------ #
    def schedule_meeting(self, organizer, title, description=None, start_time=None,
                         end_time=None, location=None, mandatory_attendees=None,
                         optional_attendees=None, directory=None):
        """Creates a meeting, places it on every attendee's calendar, and queues invitations."""
        mandatory_attendees = self._resolve_all(mandatory_attendees or [], directory)
        optional_attendees = self._resolve_all(optional_attendees or [], directory)

        self._event_counter += 1
        all_attendees = [organizer] + [a for a in (mandatory_attendees + optional_attendees) if a != organizer]
        event = {
            "id": f"evt_{self._event_counter}",
            "organizer": organizer,
            "title": title,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "mandatory_attendees": mandatory_attendees,
            "optional_attendees": optional_attendees,
            "responses": {organizer: "accepted"},
            "cancelled": False,
        }
        for attendee in all_attendees:
            if attendee != organizer:
                event["responses"].setdefault(attendee, "no_response")
            # each attendee keeps their own copy
            self._calendars.setdefault(attendee, []).append(dict(event))
            if attendee != organizer:
                self._pending.append(
                    (attendee, f"Meeting invitation from {organizer}: \"{title}\" "
                               f"(starts {start_time}). Event id {event['id']}.")
                )
        logger.debug(f"[{self.name}] Scheduled {event['id']} '{title}' by {organizer} for {all_attendees}.")
        return event

    def respond_to_invite(self, person_name, event_id, response):
        """Records a person's response to a meeting invitation across all stored copies."""
        if response not in VALID_RESPONSES:
            raise ValueError(f"Invalid response '{response}'. Must be one of {VALID_RESPONSES}.")
        event = self.get_event(person_name, event_id)
        if event is None:
            return None
        # update the response on this person's copy and, when known, the organizer's copy
        event["responses"][person_name] = response
        organizer = event["organizer"]
        organizer_copy = self.get_event(organizer, event_id)
        if organizer_copy is not None:
            organizer_copy["responses"][person_name] = response
            self._pending.append(
                (organizer, f"{person_name} {response} your meeting \"{event['title']}\" ({event_id}).")
            )
        return event

    def cancel_meeting(self, organizer, event_id):
        """Cancels a meeting and notifies its attendees."""
        organizer_copy = self.get_event(organizer, event_id)
        if organizer_copy is None:
            return False
        attendees = list(organizer_copy["responses"].keys())
        for attendee in attendees:
            ev = self.get_event(attendee, event_id)
            if ev is not None:
                ev["cancelled"] = True
            if attendee != organizer:
                self._pending.append(
                    (attendee, f"{organizer} cancelled the meeting \"{organizer_copy['title']}\" ({event_id}).")
                )
        return True

    # ------------------------------------------------------------------ #
    def _resolve_all(self, refs, directory):
        from tinytroupe.utils import targeting
        resolved = []
        for ref in refs or []:
            if directory is not None:
                resolved.append(directory.resolve_recipient(ref, channel="email"))
            else:
                resolved.append(targeting.parse_uri(ref)[1])
        seen, unique = set(), []
        for n in resolved:
            if n is not None and n not in seen:
                seen.add(n)
                unique.append(n)
        return unique

    # ------------------------------------------------------------------ #
    # Calendar access
    # ------------------------------------------------------------------ #
    def calendar(self, person_name):
        """Returns the list of events on a person's calendar."""
        return self._calendars.get(person_name, [])

    def get_event(self, person_name, event_id):
        """Returns a specific event from a person's calendar, or ``None``."""
        for e in self._calendars.get(person_name, []):
            if e["id"] == event_id:
                return e
        return None

    # ------------------------------------------------------------------ #
    # Delivery (async, next-step)
    # ------------------------------------------------------------------ #
    def flush(self, world) -> None:
        if not self._pending:
            return
        pending, self._pending = self._pending, []
        # batch per recipient
        batched = {}
        for recipient, text in pending:
            batched.setdefault(recipient, []).append(text)
        for recipient, texts in batched.items():
            agent = self._resolve_agent(world, recipient)
            if agent is None:
                continue
            tool_uri = self._client_uri_for(agent)
            text = texts[0] if len(texts) == 1 else f"You have {len(texts)} calendar updates: " + " | ".join(texts)
            agent.notify(text, tinytool=tool_uri, source=world)

    def _client_uri_for(self, agent):
        for faculty in getattr(agent, "_mental_faculties", []):
            for tool in getattr(faculty, "tools", []):
                if isinstance(tool, TinyCalendar):
                    return tool.uri()
        return None


class TinyCalendar(TinyTool):
    """
    A per-agent calendar client backed by a shared :class:`CalendarService`. Lets an agent
    schedule meetings, respond to invitations, inspect their calendar, and cancel meetings.
    """

    action_namespace = "TINYCALENDAR"

    def __init__(self, owner=None, service: CalendarService = None, directory=None, id=None, name=None):
        super().__init__(
            id=id,
            name=name if name is not None else "calendar",
            description="A calendar tool to schedule meetings and track appointments.",
            owner=owner,
            real_world_side_effects=False,
        )
        self.service = service
        self.directory = directory

    def _get_service(self, agent):
        if self.service is not None:
            return self.service
        world = getattr(agent, "environment", None)
        if world is not None:
            return world.get_service(CalendarService)
        raise ValueError(
            f"Calendar {self.id} has no CalendarService and the agent is not in a world that provides one."
        )

    def _get_directory(self, agent):
        if self.directory is not None:
            return self.directory
        world = getattr(agent, "environment", None)
        if world is not None:
            from tinytroupe.tools.tiny_contacts_directory import TinyContactsDirectory
            return world.get_service(TinyContactsDirectory, required=False)
        return None

    @staticmethod
    def _parse_content(action):
        content = action.get("content")
        if isinstance(content, str):
            return utils.extract_json(content)
        return content or {}

    def _process_action(self, agent, action) -> bool:
        _namespace, verb = parse_action_namespace(action.get("type"))
        service = self._get_service(agent)
        directory = self._get_directory(agent)
        person = agent.name

        if verb == "SCHEDULE_MEETING":
            spec = self._parse_content(action)
            utils.check_valid_fields(
                spec,
                ["title", "description", "start_time", "end_time", "location",
                 "mandatory_attendees", "optional_attendees"],
            )
            mandatory = spec.get("mandatory_attendees", [])
            optional = spec.get("optional_attendees", [])
            # Per the unified targeting convention, the action's target/targets ARE the
            # recipients/invitees. Honor them as mandatory attendees when the content lists none,
            # so meeting routing stays consistent with every other action.
            if not mandatory and not optional:
                from tinytroupe.utils import targeting
                mandatory = targeting.recipient_names(action)

            title = spec.get("title", "")
            # Reject unusable schedules (e.g. malformed JSON content that parsed to nothing)
            # rather than silently creating an empty meeting. Returning False lets the agent
            # perceive the failure and retry with well-formed content.
            if not title and not mandatory and not optional:
                logger.warning(
                    f"[{agent.name}] SCHEDULE_MEETING ignored: no title and no attendees could be "
                    f"parsed from the action content {action.get('content')!r}."
                )
                return False

            service.schedule_meeting(
                organizer=person,
                title=title,
                description=spec.get("description"),
                start_time=spec.get("start_time"),
                end_time=spec.get("end_time"),
                location=spec.get("location"),
                mandatory_attendees=mandatory,
                optional_attendees=optional,
                directory=directory,
            )
            return True

        if verb == "RESPOND_TO_INVITE":
            spec = self._parse_content(action)
            utils.check_valid_fields(spec, ["event_id", "response"])
            result = service.respond_to_invite(person, spec.get("event_id"), spec.get("response"))
            if result is None:
                logger.warning(f"[{agent.name}] RESPOND_TO_INVITE: event {spec.get('event_id')} not found.")
                return False
            return True

        if verb == "CHECK_CALENDAR":
            events = [
                {k: e[k] for k in ("id", "title", "start_time", "end_time", "organizer", "cancelled")}
                for e in service.calendar(person)
            ]
            agent.receive_inspection(
                {"calendar": events, "count": len(events)},
                tinytool=self.uri(),
                source=getattr(agent, "environment", None),
            )
            return True

        if verb == "CANCEL_MEETING":
            spec = self._parse_content(action)
            utils.check_valid_fields(spec, ["event_id"])
            return service.cancel_meeting(person, spec.get("event_id"))

        return False

    def actions_definitions_prompt(self) -> str:
        prompt = \
            """
            - TINYCALENDAR::SCHEDULE_MEETING: schedule a meeting and invite people. The content **must** be a JSON object with fields:
                * title: the meeting title. Mandatory.
                * description: a brief description. Optional.
                * start_time: the start time (in the simulation's date/time). Optional but recommended.
                * end_time: the end time. Optional.
                * location: where the meeting happens (e.g. a room or a video call). Optional.
                * mandatory_attendees: a JSON list of people who must attend (use their names). Optional.
                * optional_attendees: a JSON list of people invited but not required. Optional.
            - TINYCALENDAR::RESPOND_TO_INVITE: respond to a meeting invitation. JSON fields:
                * event_id: the id of the meeting (e.g. "evt_2"). Mandatory.
                * response: one of "accepted", "declined", "tentative". Mandatory.
            - TINYCALENDAR::CHECK_CALENDAR: list the meetings on your calendar (you will perceive the result shortly). No content needed.
            - TINYCALENDAR::CANCEL_MEETING: cancel a meeting you organized. JSON field:
                * event_id: the id of the meeting to cancel. Mandatory.
            """
        return utils.dedent(prompt)

    def actions_constraints_prompt(self) -> str:
        prompt = \
            """
            - Meeting invitations are delivered **asynchronously**: invitees will perceive them on a later turn.
            - All meeting times refer to the **simulation's** date and time, never the real-world time.
            - To see your meetings, first TINYCALENDAR::CHECK_CALENDAR, then respond to or cancel specific meetings by their event id.
            - Whenever you provide calendar content, you **must** embed it in a valid JSON object, using only valid escape sequences.
            """
        return utils.dedent(prompt)

