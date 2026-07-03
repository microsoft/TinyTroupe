# Office Tools: Simulating Workplace Communication

TinyTroupe agents can use *tools* to take concrete, simulated actions beyond simply talking. This
guide covers the **office communication suite** — email, calendar, and the word processor — and the
conventions that make these tools coherent with the rest of TinyTroupe.

> [!NOTE]
> These tools require LLM calls to be driven by agents. As with all such functionality, test your
> own scenarios with real models and review the produced artifacts.

## Mental model: clients and services

Most office tools follow a **client + service** architecture, mirroring how a real Outlook or Teams
client talks to a shared server:

- A **tool** (e.g. `TinyEmailClient`, `TinyCalendar`) is a *per-agent client* — each agent owns its
  own instance, addressable as `tinytool:<id>`.
- A **service** (e.g. `EmailService`, `CalendarService`) is a *single shared backend* registered in
  the `TinyWorld`. It holds the cross-agent state (inboxes, calendars), mints stable ids, and
  delivers messages.

Tools that need no shared state — like `TinyWordProcessor` — are simply per-agent and have no
service. Shared, ownerless tools (an information kiosk, an ATM) are also supported via `owner=None`.

## Setting up an office

```python
from tinytroupe.agent import TinyToolUse
from tinytroupe.environment import TinyWorld
from tinytroupe.tools import (
    TinyEmailClient, EmailService,
    TinyCalendar, CalendarService,
    TinyContactsDirectory,
)
from tinytroupe.examples import create_lisa_the_data_scientist, create_oscar_the_architect

lisa = create_lisa_the_data_scientist()
oscar = create_oscar_the_architect()

# Shared backends live in the world.
email_service = EmailService()
calendar_service = CalendarService()
directory = TinyContactsDirectory(domain="simcorp.tt")

# Each agent gets its own clients.
for agent in (lisa, oscar):
    agent.add_mental_faculties([TinyToolUse(tools=[
        TinyEmailClient(owner=agent, service=email_service, directory=directory),
        TinyCalendar(owner=agent, service=calendar_service, directory=directory),
    ])])
    directory.register(agent.name, "email")

world = TinyWorld("Office", [lisa, oscar])
world.register_service(email_service)
world.register_service(calendar_service)
world.register_service(directory)
world.make_everyone_accessible()

world.run(3)
```

## Key conventions

### Namespaced actions

Every tool action is namespaced as `TOOLNAME::VERB`, e.g. `TINYEMAILCLIENT::SEND_EMAIL`,
`TINYCALENDAR::SCHEDULE_MEETING`, `TINYWORDPROCESSOR::WRITE_DOCUMENT`. The namespace (plus ownership)
determines which of the agent's own tools handles the action, so an agent can only ever act through
its own instances.

### Targets are recipients

An action's `target` (a single URI) or `targets` (a list) name **who the action is directed at** —
the recipients in the simulated social graph — using a uniform URI scheme:

- `tinyperson:<name>` — a person (a bare `<name>` is also accepted and treated as a person).
- `tinytool:<id>` — a tool (for actions that operate *on* a tool itself).

For communication tools, the recipients can be given either in the action's `targets` or in
channel-specific content fields (email `to`/`cc`/`bcc`, calendar `mandatory_attendees`/
`optional_attendees`); the tool reconciles them.

### Realistic addresses

While routing uses canonical identities, the rendered artifacts use realistic addresses
(`lisa.carter@simcorp.tt`). The `TinyContactsDirectory` bridges the two, and can answer in-world
questions like "what is Lisa's email address?".

### Asynchronous, simulation-time delivery

Communications are delivered on the **next** simulation step (modeling real delays). When a message
arrives, the recipient perceives a `NOTIFICATION`. When an agent deliberately inspects a tool (e.g.
`TINYEMAILCLIENT::CHECK_INBOX`), the result arrives as an `INSPECTION` on its following turn — so a
*check → read → reply* flow naturally spans several turns. All times are the `TinyWorld` clock, never
wall-clock time.

## Available actions

**Email (`TINYEMAILCLIENT`)**: `SEND_EMAIL`, `REPLY_EMAIL`, `FORWARD_EMAIL`, `CHECK_INBOX`,
`READ_EMAIL`, `DELETE_EMAIL`.

**Calendar (`TINYCALENDAR`)**: `SCHEDULE_MEETING`, `RESPOND_TO_INVITE`, `CHECK_CALENDAR`,
`CANCEL_MEETING`.

**Word processor (`TINYWORDPROCESSOR`)**: `WRITE_DOCUMENT`.

## Upgrading from older versions

The tool framework changed in incompatible ways; update existing programs as follows:

- **Tools are per-agent.** Construct a separate tool instance per agent (pass `owner=agent`) instead
  of sharing one instance across agents. Shared tools are still possible with `owner=None`.
- **`TinyTool` constructor is keyword-based**: `TinyTool(id=..., name=..., description=..., owner=...)`.
  `name` is now a cosmetic label; the new immutable `id` is the canonical identifier.
- **Actions are namespaced.** `WRITE_DOCUMENT` is now `TINYWORDPROCESSOR::WRITE_DOCUMENT`, etc.
- Communication tools require their shared services to be registered in the world with
  `world.register_service(...)`.
