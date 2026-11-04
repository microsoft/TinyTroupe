"""Deterministic transaction replay contracts; no provider calls are allowed."""

import copy
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from tinytroupe import control
from tinytroupe.agent import CustomMentalFaculty, TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.factory.tiny_factory import TinyFactory


@pytest.fixture(autouse=True)
def isolated_simulation(tmp_path, monkeypatch):
    def no_provider(*args, **kwargs):
        raise AssertionError("transaction replay must not call a provider")

    monkeypatch.setattr(
        "tinytroupe.clients.openai_client.OpenAIClient.send_message", no_provider
    )
    monkeypatch.setattr(
        "tinytroupe.clients.ollama_client.OllamaClient.send_message", no_provider
    )
    monkeypatch.setattr(TinyPerson, "communication_display", False)
    monkeypatch.setattr(TinyWorld, "communication_display", False)
    control.reset()
    control.begin(str(tmp_path / "trace.json"))
    yield control.current_simulation()
    control.reset()
    TinyPerson.clear_agents()
    TinyWorld.clear_environments()
    TinyFactory.clear_factories()


@pytest.fixture
def graph(isolated_simulation):
    alice, bob = TinyPerson("Alice"), TinyPerson("Bob")
    world = TinyWorld("Office", [alice, bob])
    factory = TinyFactory()
    isolated_simulation.add_environment(world)
    isolated_simulation.add_factory(factory)
    return isolated_simulation, alice, bob, world, factory


def transaction(graph, function=lambda: None):
    sim, alice, *_ = graph
    return control.Transaction(alice, sim, function)


@pytest.mark.parametrize("kind", ["person", "world", "factory"])
@pytest.mark.parametrize("depth", [0, 1, 3])
def test_json_roundtrip_resolves_canonical_references_at_every_depth(
    graph, kind, depth
):
    _, alice, _, world, factory = graph
    value = {"person": alice, "world": world, "factory": factory}[kind]
    nested = value
    for _ in range(depth):
        nested = {"payload": [nested]}
    codec = transaction(graph)
    encoded = json.loads(json.dumps(codec._encode_function_output(nested)))
    restored = codec._decode_function_output(encoded)
    for _ in range(depth):
        restored = restored["payload"][0]
    assert restored is value


@pytest.mark.parametrize("container", ["list", "dict", "tuple"])
def test_encoded_output_is_owned_by_the_cache_not_its_caller(graph, container):
    leaf = {"history": ["original"]}
    value = {"list": [leaf], "dict": {"leaf": leaf}, "tuple": (leaf,)}[container]
    codec = transaction(graph)
    encoded = codec._encode_function_output(value)
    leaf["history"].append("caller mutation")
    restored = codec._decode_function_output(encoded)
    leaf_after = restored["leaf"] if container == "dict" else restored[0]
    assert leaf_after == {"history": ["original"]}
    assert isinstance(restored, {"list": list, "dict": dict, "tuple": tuple}[container])


@pytest.mark.parametrize("legacy", [False, True])
def test_decoded_mutable_output_cannot_poison_the_next_replay(graph, legacy):
    codec = transaction(graph)
    encoded = (
        {"type": "JSON", "value": {"history": ["original"]}}
        if legacy
        else codec._encode_function_output({"history": ["original"]})
    )
    first = codec._decode_function_output(encoded)
    first["history"].append("replay mutation")
    assert codec._decode_function_output(encoded) == {"history": ["original"]}


def test_nested_tuple_types_and_json_scalar_mapping_keys_survive_disk_roundtrip(graph):
    codec = transaction(graph)
    value = {7: ("hello", [None, False, 2.5]), None: {False: "bool key"}}
    restored = codec._decode_function_output(
        json.loads(json.dumps(codec._encode_function_output(value)))
    )
    assert restored == value
    assert isinstance(restored[7], tuple)
    assert list(restored) == [7, None]


def test_user_dictionary_type_fields_are_plain_data_not_reference_tags(graph):
    codec = transaction(graph)
    value = {"type": "TinyPersonRef", "name": "absent", "nested": {"type": "List"}}
    restored = codec._decode_function_output(
        json.loads(json.dumps(codec._encode_function_output(value)))
    )
    assert restored == value


@pytest.mark.parametrize(
    "reference", ["TinyPersonRef", "TinyWorldRef", "TinyFactoryRef"]
)
def test_missing_registered_reference_is_an_error_instead_of_silent_none(
    graph, reference
):
    codec = transaction(graph)
    with pytest.raises(ValueError, match="absent"):
        codec._decode_function_output({"type": reference, "name": "absent"})


@pytest.mark.parametrize("shape", ["list", "dict", "indirect"])
def test_output_cycles_fail_before_trace_publication(graph, shape):
    sim, *_ = graph
    if shape == "list":
        output = []
        output.append(output)
    elif shape == "dict":
        output = {}
        output["self"] = output
    else:
        output = []
        output.append({"back": output})
    with pytest.raises(ValueError, match="[Cc]ycl"):
        transaction(graph, lambda: output).execute(parallel_id="worker")
    assert sim.execution_trace == []
    assert sim.cached_trace == []
    assert not sim.is_under_transaction("worker")


def test_repeated_acyclic_container_is_supported_without_aliasing_cache_data(graph):
    codec = transaction(graph)
    shared = ["value"]
    encoded = codec._encode_function_output([shared, shared])
    restored = codec._decode_function_output(json.loads(json.dumps(encoded)))
    assert restored == [["value"], ["value"]]
    restored[0].append("mutation")
    assert codec._decode_function_output(encoded) == [["value"], ["value"]]


@pytest.mark.parametrize("output", [{"nested": object()}, [set([1])]])
def test_unsupported_nested_output_never_leaves_transaction_scope_active(graph, output):
    sim, *_ = graph
    with pytest.raises(ValueError, match="Unsupported"):
        transaction(graph, lambda: output).execute(parallel_id="worker")
    assert not sim.is_under_transaction("worker")
    assert sim.cached_trace == sim.execution_trace == []
    assert transaction(graph, lambda: 42).execute(parallel_id="worker") == 42
    assert len(sim.cached_trace) == 1


@pytest.mark.parametrize("exception", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_failed_function_releases_ownership_and_next_call_is_cached(graph, exception):
    sim, *_ = graph

    def fail():
        raise exception("interrupted")

    with pytest.raises(exception):
        transaction(graph, fail).execute(parallel_id="worker")
    assert not sim.is_under_transaction("worker")
    assert sim.execution_trace == sim.cached_trace == []
    assert (
        transaction(graph, lambda: "recovered").execute(parallel_id="worker")
        == "recovered"
    )
    assert len(sim.cached_trace) == len(sim.execution_trace) == 1


def test_state_encoding_error_releases_transaction_and_keeps_existing_trace(
    graph, monkeypatch
):
    sim, *_ = graph
    transaction(graph, lambda: "first").execute(parallel_id="worker")
    before = copy.deepcopy(sim.cached_trace)

    def fail():
        raise ValueError("snapshot unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(sim, "_encode_simulation_state", fail)
        with pytest.raises(ValueError, match="snapshot unavailable"):
            transaction(graph, lambda: "second").execute(parallel_id="worker")
    assert not sim.is_under_transaction("worker")
    assert sim.cached_trace == sim.execution_trace == before
    transaction(graph, lambda: "third").execute(parallel_id="worker")
    assert len(sim.cached_trace) == 2


@pytest.mark.parametrize("failure", ["state", "output"])
def test_failed_replay_does_not_consume_position_or_increment_hits(
    graph, monkeypatch, failure
):
    sim, *_ = graph

    def compute():
        return {"answer": [42]}

    transaction(graph, compute).execute(parallel_id="worker")
    sim.execution_trace = []
    before = copy.deepcopy(sim.cached_trace)
    method = (
        "_decode_simulation_state" if failure == "state" else "_decode_function_output"
    )
    owner = sim if failure == "state" else control.Transaction

    def fail(*args):
        raise ValueError("replay interrupted")

    with monkeypatch.context() as patch:
        patch.setattr(owner, method, fail)
        with pytest.raises(ValueError, match="replay interrupted"):
            transaction(graph, compute).execute(parallel_id="worker")
    assert sim.execution_trace == []
    assert sim.cached_trace == before
    assert sim.cache_hits == 0
    assert transaction(graph, compute).execute(parallel_id="worker") == {"answer": [42]}
    assert len(sim.execution_trace) == 1
    assert sim.cache_hits == 1


def test_reentrant_call_never_consumes_a_future_matching_cache_entry(graph):
    sim, alice, *_ = graph
    events = []

    def inner():
        events.append("inner executed")
        return 5

    def outer():
        return control.Transaction(alice, sim, inner).execute(parallel_id="worker")

    inner_hash = sim._function_call_hash("inner")
    sim.cached_trace = [
        (
            None,
            inner_hash,
            {"type": "JSON", "value": 999},
            sim._encode_simulation_state(),
        )
    ]
    assert transaction(graph, outer).execute(parallel_id="worker") == 5
    assert events == ["inner executed"]
    assert len(sim.execution_trace) == len(sim.cached_trace) == 1
    assert sim.cached_trace[0][1] == sim._function_call_hash("outer")
    assert sim.cache_hits == 0


def test_caught_reentrant_failure_keeps_outer_ownership_and_commits_once(graph):
    sim, alice, *_ = graph

    def inner():
        raise RuntimeError("expected inner failure")

    def outer():
        with pytest.raises(RuntimeError):
            control.Transaction(alice, sim, inner).execute(parallel_id="worker")
        assert sim.is_under_transaction("worker")
        return "outer completed"

    assert transaction(graph, outer).execute(parallel_id="worker") == "outer completed"
    assert not sim.is_under_transaction("worker")
    assert len(sim.cached_trace) == len(sim.execution_trace) == 1


def test_replay_restores_faculties_including_added_removed_and_reordered_entries(graph):
    sim, alice, *_ = graph
    alice._mental_faculties = [
        CustomMentalFaculty("plan", constraints={"rule": "cached"}),
        CustomMentalFaculty("review", constraints={"rule": "second"}),
    ]
    state = sim._encode_simulation_state()
    alice._mental_faculties = [CustomMentalFaculty("replacement")]
    sim._decode_simulation_state(state)
    assert [faculty.name for faculty in alice._mental_faculties] == ["plan", "review"]
    assert alice._mental_faculties[0].constraints == {"rule": "cached"}
    alice._mental_faculties[0].constraints["rule"] = "mutated replay"
    sim._decode_simulation_state(state)
    assert alice._mental_faculties[0].constraints == {"rule": "cached"}
    state["agents"][0]["_mental_faculties"] = []
    sim._decode_simulation_state(state)
    assert alice._mental_faculties == []


def test_failed_parallel_segment_releases_scope_and_drops_partial_trace(graph):
    sim, alice, *_ = graph
    transaction(graph, lambda: "prefix").execute(parallel_id="owner")
    previous = copy.deepcopy(sim.cached_trace)

    def segment():
        with ThreadPoolExecutor(max_workers=2) as pool:
            pool.submit(
                lambda: control.Transaction(alice, sim, lambda: "partial").execute(
                    parallel_id="child"
                )
            ).result(timeout=5)
        raise RuntimeError("segment failed")

    with pytest.raises(RuntimeError, match="segment failed"):
        transaction(graph, segment).execute(begin_parallel=True, parallel_id="owner")
    assert not sim.is_under_parallel_transactions()
    assert not sim.is_under_transaction("child")
    assert sim.cached_trace == sim.execution_trace == previous
    assert (
        transaction(graph, lambda: "after failure").execute(parallel_id="owner")
        == "after failure"
    )
    assert len(sim.cached_trace) == 2


@pytest.mark.parametrize(
    "encoded, expected",
    [
        (None, None),
        ({"type": "JSON", "value": 0}, 0),
        ({"type": "JSON", "value": False}, False),
        ({"type": "JSON", "value": "text"}, "text"),
        (
            {"type": "JSON", "value": {"type": "TinyPersonRef", "name": "data"}},
            {"type": "TinyPersonRef", "name": "data"},
        ),
        ({"type": "JSON", "value": [[1], {"two": 2}]}, [[1], {"two": 2}]),
        ({"type": "List", "value": [None, {"type": "JSON", "value": 3}]}, [None, 3]),
    ],
)
def test_legacy_output_envelopes_remain_readable(graph, encoded, expected):
    codec = transaction(graph)
    assert codec._decode_function_output(json.loads(json.dumps(encoded))) == expected


def test_legacy_flat_reference_list_resolves_all_entity_types(graph):
    _, alice, _, world, factory = graph
    encoded = {
        "type": "List",
        "value": [
            {"type": "TinyPersonRef", "name": "Alice"},
            {"type": "TinyWorldRef", "name": "Office"},
            {"type": "TinyFactoryRef", "name": factory.name},
            {"type": "JSON", "value": {"plain": [1]}},
        ],
    }
    result = transaction(graph)._decode_function_output(json.loads(json.dumps(encoded)))
    assert result[0] is alice and result[1] is world and result[2] is factory
    assert result[3] == {"plain": [1]}
