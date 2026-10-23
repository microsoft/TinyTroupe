# Web evidence with TinyWebSearch

`TinyWebSearch` gives an explicitly equipped persona web search and source-page
excerpts through [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp).
Search uses Fast mode without a Parallel account or API key. Normal TinyTroupe
model configuration still applies; this tool does not configure model inference.

Install the optional MCP dependency from a checkout:

```shell
pip install ".[web-search]"
```

Or install directly from the repository:

```shell
pip install "tinytroupe[web-search] @ git+https://github.com/microsoft/TinyTroupe.git@main"
```

## Attach and dispatch

Existing personas and their tools remain unchanged. Attach this tool only when
outside evidence belongs in your experiment. Queries and URLs are sent to an
external service, so keep private persona details and secrets out of them.

This example supplies an action directly to the normal tool dispatcher, then
reads the resulting thought from the persona's memory. It does not ask a model
to choose an action.

```python
from tinytroupe.agent import TinyPerson, TinyToolUse
from tinytroupe.tools import TinyWebSearch

researcher = TinyPerson("Web researcher")
web = TinyWebSearch(owner=researcher, timeout=30)
tools = TinyToolUse([web])
researcher.add_mental_faculty(tools)

tools.process_action(researcher, {
    "type": "SEARCH_WEB",
    "content": {
        "objective": "Find the TinyTroupe project and its purpose",
        "search_queries": ["Microsoft TinyTroupe persona simulation"],
    },
})
print(researcher.retrieve_recent_memories())

tools.process_action(researcher, {
    "type": "FETCH_WEB",
    "content": {
        "urls": ["https://github.com/microsoft/TinyTroupe"],
        "objective": "Understand the project's purpose",
        "search_queries": ["Microsoft TinyTroupe persona simulation"],
    },
})
```

`SEARCH_WEB` requires a focused `objective` and a nonempty `search_queries` list.
Use related keyword queries of about 3 to 6 words each. `FETCH_WEB` requires 1 to
20 HTTP(S) `urls`; `objective` (up to 200 characters) and `search_queries` are
optional. Action content may be a dictionary or a JSON string. Fetch returns
excerpts rather than complete pages. Each result is limited to 20,000 characters
before being stored as a thought, with an explicit truncation marker when needed.

Web content is untrusted evidence. Review it and retain source URLs when drawing
conclusions. Fresh outside information can change experimental results; record
the retrieved evidence with your experiment and distinguish it from simulated
beliefs.

## Controls and research sessions

- Leave the tool unattached to keep a persona without web search. Set
  `web.enabled = False` to disable an attached tool and remove its action prompts.
  Attempting to dispatch a disabled web action raises an error without a request.
- Set `owner` to restrict use to that persona, or leave it unset for a shared tool.
  `web.set_owner(person)` changes ownership; `web.set_owner(None)` removes it.
  Serialized tools preserve the owner's name, the disable setting and the timeout.
- The timeout bounds connection setup, discovery and the tool request together.
  Errors propagate without automatic retries or a fallback provider. Free service
  quotas apply; an experimenter may retry after the service's stated retry period.
- Related searches, fetches and explicit retries reuse an opaque research ID on
  the persona. Sharing a tool between personas keeps their IDs separate. Call
  `web.start_research(researcher)` before a new research conversation on the same
  persona, after earlier requests have completed. Creating or loading a persona
  starts with a fresh ID. Clearing memory alone does not start a new research run.

The tool uses the official MCP SDK's Streamable HTTP transport to
`https://search.parallel.ai/mcp`. It works from synchronous scripts and notebook
cells with an existing event loop. It does not read Parallel credentials or alter
other configured tools. Installations that do not use this tool do not need the
`web-search` extra.
