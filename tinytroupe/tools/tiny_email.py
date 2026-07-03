"""
Email: a per-agent :class:`TinyEmailClient` backed by a shared :class:`EmailService`.

This is the reference implementation of the office-communications pattern:

  - The **service** (``EmailService``) is a single shared object registered in the
    :class:`TinyWorld`. It holds every agent's inbox, mints stable message ids, tracks
    read/unread state, and delivers messages **asynchronously** (next simulation step) via
    :meth:`EmailService.flush`.
  - The **client** (``TinyEmailClient``) is a per-agent tool (owned by the agent, addressable
    as ``tinytool:<id>``) that turns ``TINYEMAILCLIENT::*`` actions into service calls.

Recipients are carried as person references (``tinyperson:`` URIs, bare names, or email
addresses) inside the action content's ``to``/``cc``/``bcc`` fields; their union is the action's
social-graph destination set. Realistic ``From``/``To`` addresses in the rendered artifact are
resolved through the :class:`TinyContactsDirectory`.
"""

import json

from tinytroupe.tools import logger, TinyTool
from tinytroupe.tools.services import TinyService
from tinytroupe.tools.tiny_tool import parse_action_namespace
import tinytroupe.utils as utils


class EmailService(TinyService):
    """
    Shared mail server: holds inboxes, mints message ids, and delivers email next-step.
    """

    serializable_attributes = ["name", "_inboxes", "_pending", "_message_counter"]

    def __init__(self, name: str = None):
        super().__init__(name)
        # person_name -> list of message dicts (their inbox)
        self._inboxes = {}
        # messages enqueued this step, delivered on the next flush (async, next-step delivery)
        self._pending = []
        self._message_counter = 0

    # ------------------------------------------------------------------ #
    # Sending
    # ------------------------------------------------------------------ #
    def send(self, sender_name, subject, body, to, cc=None, bcc=None,
             directory=None, timestamp=None, in_reply_to=None):
        """
        Composes a message and enqueues it for next-step delivery.

        Args:
            sender_name (str): The sending person's name.
            subject (str): The email subject.
            body (str): The email body.
            to (list[str]): Primary recipient references (names/URIs/addresses).
            cc (list[str], optional): Cc recipient references.
            bcc (list[str], optional): Bcc recipient references.
            directory (TinyContactsDirectory, optional): Used to resolve recipients to canonical
                person names and to render realistic addresses.
            timestamp (str, optional): Simulation-time ISO timestamp of sending.
            in_reply_to (str, optional): The id of the message being replied to, if any.

        Returns:
            dict: The composed message (already enqueued).
        """
        to = self._resolve_all(to, directory)
        cc = self._resolve_all(cc or [], directory)
        bcc = self._resolve_all(bcc or [], directory)

        self._message_counter += 1
        message = {
            "id": f"eml_{self._message_counter}",
            "from": sender_name,
            "from_address": self._address_of(sender_name, directory),
            "to": to,
            "cc": cc,
            "bcc": bcc,
            "to_addresses": [self._address_of(n, directory) for n in to],
            "cc_addresses": [self._address_of(n, directory) for n in cc],
            "subject": subject,
            "body": body,
            "timestamp": timestamp,
            "in_reply_to": in_reply_to,
        }
        self._pending.append(message)
        logger.debug(f"[{self.name}] Enqueued email {message['id']} from {sender_name} to {to} (cc={cc}, bcc={bcc}).")
        return message

    def _resolve_all(self, refs, directory):
        from tinytroupe.utils import targeting
        resolved = []
        for ref in refs or []:
            if directory is not None:
                resolved.append(directory.resolve_recipient(ref, channel="email"))
            else:
                kind, identifier = targeting.parse_uri(ref)
                resolved.append(identifier)
        # de-duplicate while preserving order
        seen = set()
        unique = []
        for n in resolved:
            if n is not None and n not in seen:
                seen.add(n)
                unique.append(n)
        return unique

    def _address_of(self, person_name, directory):
        if directory is not None:
            return directory.address_of(person_name, channel="email")
        return person_name

    # ------------------------------------------------------------------ #
    # Delivery (async, next-step)
    # ------------------------------------------------------------------ #
    def flush(self, world) -> None:
        """Delivers all pending messages to recipients' inboxes and notifies them."""
        if not self._pending:
            return

        pending = self._pending
        self._pending = []

        # Batch notifications: recipient_name -> list of (sender, subject)
        notifications = {}

        for message in pending:
            recipients = list(message["to"]) + list(message["cc"]) + list(message["bcc"])
            for recipient in recipients:
                inbox = self._inboxes.setdefault(recipient, [])
                # Each recipient gets their own copy with independent read state.
                delivered = dict(message)
                delivered["read"] = False
                inbox.append(delivered)
                notifications.setdefault(recipient, []).append(
                    (message["from"], message["subject"])
                )

        # Emit one batched NOTIFICATION per recipient per flush.
        for recipient, items in notifications.items():
            agent = self._resolve_agent(world, recipient)
            if agent is None:
                continue
            tool_uri = self._client_uri_for(agent)
            if len(items) == 1:
                sender, subject = items[0]
                text = f"You have a new email from {sender}: \"{subject}\"."
            else:
                lines = "; ".join(f"{s} (\"{subj}\")" for s, subj in items)
                text = f"You have {len(items)} new emails: {lines}."
            agent.notify(text, tinytool=tool_uri, source=world)

    def _client_uri_for(self, agent):
        """Finds the agent's email client URI, if it has one, for notification attribution."""
        for faculty in getattr(agent, "_mental_faculties", []):
            for tool in getattr(faculty, "tools", []):
                if isinstance(tool, TinyEmailClient):
                    return tool.uri()
        return None

    # ------------------------------------------------------------------ #
    # Inbox access
    # ------------------------------------------------------------------ #
    def inbox(self, person_name):
        """Returns the list of messages in a person's inbox (empty list if none)."""
        return self._inboxes.get(person_name, [])

    def get_message(self, person_name, message_id):
        """Returns a specific message from a person's inbox, or ``None``."""
        for m in self._inboxes.get(person_name, []):
            if m["id"] == message_id:
                return m
        return None

    def mark_read(self, person_name, message_id):
        """Marks a message as read in a person's inbox."""
        m = self.get_message(person_name, message_id)
        if m is not None:
            m["read"] = True
        return m

    def delete_message(self, person_name, message_id):
        """Deletes a message from a person's inbox. Returns True if it existed."""
        inbox = self._inboxes.get(person_name, [])
        for i, m in enumerate(inbox):
            if m["id"] == message_id:
                del inbox[i]
                return True
        return False


class TinyEmailClient(TinyTool):
    """
    A per-agent email client. Translates ``TINYEMAILCLIENT::*`` actions into calls on the shared
    :class:`EmailService`. Read actions (CHECK_INBOX, READ_EMAIL) return their result as an
    INSPECTION stimulus the agent will perceive on its next turn.
    """

    action_namespace = "TINYEMAILCLIENT"

    def __init__(self, owner=None, service: EmailService = None, directory=None, id=None, name=None):
        super().__init__(
            id=id,
            name=name if name is not None else "email",
            description="An email client for asynchronous, multi-recipient written communication.",
            owner=owner,
            real_world_side_effects=False,
        )
        self.service = service
        self.directory = directory

    # ------------------------------------------------------------------ #
    def _get_service(self, agent):
        """Returns the email service, resolving it from the world when not directly held."""
        if self.service is not None:
            return self.service
        world = getattr(agent, "environment", None)
        if world is not None:
            return world.get_service(EmailService)
        raise ValueError(
            f"Email client {self.id} has no EmailService and the agent is not in a world that provides one."
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

    def _timestamp(self, agent):
        try:
            return agent.iso_datetime()
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    def _process_action(self, agent, action) -> bool:
        _namespace, verb = parse_action_namespace(action.get("type"))
        service = self._get_service(agent)
        directory = self._get_directory(agent)
        sender = agent.name

        if verb == "SEND_EMAIL":
            spec = self._parse_content(action)
            utils.check_valid_fields(spec, ["subject", "body", "to", "cc", "bcc"])
            to = spec.get("to", [])
            # Per the unified targeting convention, the action's target/targets ARE the
            # recipients. If the LLM placed recipients there (instead of in content.to), honor
            # them so email routing stays consistent with every other action.
            if not to:
                from tinytroupe.utils import targeting
                to = targeting.recipient_names(action)
            service.send(
                sender_name=sender,
                subject=spec.get("subject", ""),
                body=spec.get("body", ""),
                to=to,
                cc=spec.get("cc", []),
                bcc=spec.get("bcc", []),
                directory=directory,
                timestamp=self._timestamp(agent),
            )
            return True

        if verb == "REPLY_EMAIL":
            spec = self._parse_content(action)
            utils.check_valid_fields(spec, ["message_id", "body", "reply_all"])
            original = service.get_message(sender, spec.get("message_id"))
            if original is None:
                logger.warning(f"[{agent.name}] REPLY_EMAIL: message {spec.get('message_id')} not found.")
                return False
            to = [original["from"]]
            cc = []
            if spec.get("reply_all"):
                cc = [n for n in (original["to"] + original["cc"]) if n != sender]
            service.send(
                sender_name=sender,
                subject=self._reply_subject(original["subject"]),
                body=spec.get("body", ""),
                to=to,
                cc=cc,
                directory=directory,
                timestamp=self._timestamp(agent),
                in_reply_to=original["id"],
            )
            return True

        if verb == "FORWARD_EMAIL":
            spec = self._parse_content(action)
            utils.check_valid_fields(spec, ["message_id", "to", "body"])
            original = service.get_message(sender, spec.get("message_id"))
            if original is None:
                logger.warning(f"[{agent.name}] FORWARD_EMAIL: message {spec.get('message_id')} not found.")
                return False
            forwarded_body = (spec.get("body", "") or "") + \
                f"\n\n---------- Forwarded message ----------\nFrom: {original['from']}\nSubject: {original['subject']}\n\n{original['body']}"
            service.send(
                sender_name=sender,
                subject=self._forward_subject(original["subject"]),
                body=forwarded_body,
                to=spec.get("to", []),
                directory=directory,
                timestamp=self._timestamp(agent),
            )
            return True

        if verb == "CHECK_INBOX":
            preview = [
                {"id": m["id"], "from": m["from"], "subject": m["subject"], "read": m.get("read", False)}
                for m in service.inbox(sender)
            ]
            agent.receive_inspection(
                {"inbox": preview, "count": len(preview)},
                tinytool=self.uri(),
                source=getattr(agent, "environment", None),
            )
            return True

        if verb == "READ_EMAIL":
            spec = self._parse_content(action)
            utils.check_valid_fields(spec, ["message_id"])
            message = service.mark_read(sender, spec.get("message_id"))
            if message is None:
                logger.warning(f"[{agent.name}] READ_EMAIL: message {spec.get('message_id')} not found.")
                return False
            agent.receive_inspection(
                {"email": message},
                tinytool=self.uri(),
                source=getattr(agent, "environment", None),
            )
            return True

        if verb == "DELETE_EMAIL":
            spec = self._parse_content(action)
            utils.check_valid_fields(spec, ["message_id"])
            return service.delete_message(sender, spec.get("message_id"))

        return False

    @staticmethod
    def _reply_subject(subject):
        return subject if subject.lower().startswith("re:") else f"Re: {subject}"

    @staticmethod
    def _forward_subject(subject):
        return subject if subject.lower().startswith("fwd:") else f"Fwd: {subject}"

    # ------------------------------------------------------------------ #
    def actions_definitions_prompt(self) -> str:
        prompt = \
            """
            - TINYEMAILCLIENT::SEND_EMAIL: send a new email. The content **must** be a JSON object with fields:
                * subject: the email subject. Mandatory.
                * body: the email body, in plain text or Markdown. Mandatory.
                * to: a JSON list of recipients. Use each person's name **exactly as you know them in this simulation** (do not invent surnames). Mandatory.
                * cc: a JSON list of carbon-copy recipients. Optional.
                * bcc: a JSON list of blind carbon-copy recipients. Optional.
            - TINYEMAILCLIENT::REPLY_EMAIL: reply to an email you received. JSON fields:
                * message_id: the id of the email being replied to (e.g. "eml_3"). Mandatory.
                * body: the reply body. Mandatory.
                * reply_all: true to also reply to the other recipients. Optional (default false).
            - TINYEMAILCLIENT::FORWARD_EMAIL: forward an email. JSON fields:
                * message_id: the id of the email to forward. Mandatory.
                * to: a JSON list of recipients. Mandatory.
                * body: an optional note to prepend. Optional.
            - TINYEMAILCLIENT::CHECK_INBOX: list the emails currently in your inbox (you will perceive the result shortly). No content needed.
            - TINYEMAILCLIENT::READ_EMAIL: open and read a specific email. JSON field:
                * message_id: the id of the email to read. Mandatory.
            - TINYEMAILCLIENT::DELETE_EMAIL: delete an email. JSON field:
                * message_id: the id of the email to delete. Mandatory.
            """
        return utils.dedent(prompt)

    def actions_constraints_prompt(self) -> str:
        prompt = \
            """
            - Email is **asynchronous**: after you SEND_EMAIL or REPLY_EMAIL, the recipient will only perceive it on a later turn, so do not expect an immediate reply.
            - Use email (instead of TALK) for written, durable, or multi-recipient communication, or to reach people you cannot talk to directly.
            - To know what is in your inbox, first TINYEMAILCLIENT::CHECK_INBOX, then TINYEMAILCLIENT::READ_EMAIL the specific message you care about before replying to it.
            - When you SEND_EMAIL, the `to`/`cc`/`bcc` lists identify the recipients; together they are everyone who will receive the email.
            - Whenever you provide email content, you **must** embed it in a valid JSON object, using only valid escape sequences.
            """
        return utils.dedent(prompt)
