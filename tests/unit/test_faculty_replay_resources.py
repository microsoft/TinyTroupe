"""Replay persists faculty state without discarding caller-owned tool resources."""

import json

import pytest

from tinytroupe import control
from tinytroupe.agent import CustomMentalFaculty, TinyPerson, TinyToolUse
from tinytroupe.enrichment import TinyEnricher
from tinytroupe.extraction import ArtifactExporter
from tinytroupe.tools import TinyCalendar, TinyTool, TinyWordProcessor


@pytest.fixture(autouse=True)
def isolated_resources(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("faculty restore must not use a provider")

    monkeypatch.setattr("openai.OpenAI.__init__", forbidden)
    control.reset()
    TinyPerson.clear_agents()
    yield
    control.reset()
    TinyPerson.clear_agents()


def test_live_tools_and_faculties_keep_ownership_and_runtime_resources(tmp_path):
    owner, outsider = TinyPerson("Owner"), TinyPerson("Outsider")
    exporter = ArtifactExporter(base_output_folder=str(tmp_path))
    enricher = TinyEnricher()
    calendar = TinyCalendar(owner=owner)
    writer = TinyWordProcessor(owner=owner, exporter=exporter, enricher=enricher)
    faculty = TinyToolUse([calendar, writer])
    other = CustomMentalFaculty("Planning", constraints={"rule": "persisted"})
    owner._mental_faculties = [other, faculty]
    state = json.loads(json.dumps(owner.encode_complete_state()))
    calendar.description = "changed live description"
    faculty.tools.reverse()
    owner._mental_faculties.reverse()
    owner.decode_complete_state(state)
    restored = owner._mental_faculties[1]
    assert restored is faculty
    assert owner._mental_faculties[0] is other
    assert restored.tools[0] is calendar and restored.tools[1] is writer
    assert calendar.owner is writer.owner is owner
    assert writer.exporter is exporter and writer.enricher is enricher
    assert calendar.description != "changed live description"
    action = {"type": "UNRELATED_ACTION", "content": None}
    assert restored.process_action(owner, action) is False
    with pytest.raises(ValueError, match="does not own"):
        restored.process_action(outsider, action)
    owner.decode_complete_state(state)
    assert owner._mental_faculties[1] is faculty
    assert faculty.tools[1].exporter is exporter


@pytest.mark.parametrize("tool_class", [TinyCalendar, TinyWordProcessor])
def test_missing_standard_tools_get_normal_runtime_defaults(tool_class):
    person = TinyPerson("Owner", mental_faculties=[TinyToolUse([tool_class()])])
    state = json.loads(json.dumps(person.encode_complete_state()))
    person._mental_faculties = []
    person.decode_complete_state(state)
    tool = person._mental_faculties[0].tools[0]
    assert type(tool) is tool_class
    assert tool.owner is tool.exporter is tool.enricher is None
    assert (
        tool.process_action(person, {"type": "UNRELATED_ACTION", "content": None})
        is False
    )


class ResourceTool(TinyTool):
    def __init__(self, resource):
        super().__init__("resource", "Tool with a caller-managed resource")
        self.resource = resource

    def _process_action(self, agent, action):
        return False

    def actions_definitions_prompt(self):
        return ""

    def actions_constraints_prompt(self):
        return ""


def test_custom_tool_uses_live_resource_or_reports_missing_runtime_explicitly():
    resource = object()
    tool = ResourceTool(resource)
    person = TinyPerson("Owner", mental_faculties=[TinyToolUse([tool])])
    state = json.loads(json.dumps(person.encode_complete_state()))
    person.decode_complete_state(state)
    assert person._mental_faculties[0].tools[0] is tool
    assert tool.resource is resource
    person._mental_faculties = []
    with pytest.raises(ValueError, match="ResourceTool.*runtime"):
        person.decode_complete_state(state)
