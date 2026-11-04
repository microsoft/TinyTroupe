"""Real simulation/cache lifecycle and concurrency without network inference."""

import json
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from threading import Barrier, Lock

import pytest

from tinytroupe import control
from tinytroupe.agent import CustomMentalFaculty, TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.factory.tiny_factory import TinyFactory


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def no_provider(*args, **kwargs):
        raise AssertionError("unexpected provider use in native replay test")

    monkeypatch.setattr(
        "tinytroupe.clients.openai_client.OpenAIClient.send_message", no_provider
    )
    monkeypatch.setattr(
        "tinytroupe.clients.ollama_client.OllamaClient.send_message", no_provider
    )
    monkeypatch.setattr(TinyPerson, "communication_display", False)
    monkeypatch.setattr(TinyWorld, "communication_display", False)
    control.reset()
    yield
    control.reset()
    TinyPerson.clear_agents()
    TinyWorld.clear_environments()
    TinyFactory.clear_factories()


def setup_graph(path):
    control.begin(str(path))
    sim = control.current_simulation()
    alice = TinyPerson("Alice")
    bob = TinyPerson("Bob")
    world = TinyWorld("Office", [alice, bob], initial_datetime=datetime(2025, 1, 1))
    factory = TinyFactory()
    sim.add_environment(world)
    sim.add_factory(factory)
    return sim, alice, bob, world, factory


def public_call(graph, body, *args):
    sim, owner, *_ = graph
    return control.Transaction(owner, sim, body, *args).execute(parallel_id="owner")


def record_result(alice, bob, world, factory):
    alice._persona["occupation"] = "Architect"
    alice._mental_faculties = [
        CustomMentalFaculty("planning", constraints={"rule": "saved"})
    ]
    world.current_datetime += timedelta(minutes=5)
    return {"participants": (alice, [bob, alice]), "world": world, "factory": factory}


def replay_in_fresh_process(path, result_path):
    # This process reconstructs objects independently, so pickle cannot conceal
    # a stale object reference carried from the writer's interpreter.
    TinyPerson.communication_display = TinyWorld.communication_display = False
    control.reset()
    graph = setup_graph(path)
    sim, alice, bob, world, factory = graph
    with patch(
        "tinytroupe.clients.openai_client.OpenAIClient.send_message",
        side_effect=AssertionError("provider forbidden"),
    ):
        result = public_call(graph, record_result, alice, bob, world, factory)
    Path(result_path).write_text(
        json.dumps(
            {
                "alice_identity": result["participants"][0] is alice,
                "bob_identity": result["participants"][1][0] is bob,
                "alias_identity": result["participants"][1][1] is alice,
                "world_identity": result["world"] is world,
                "factory_identity": result["factory"] is factory,
                "occupation": alice.get("occupation"),
                "rule": alice._mental_faculties[0].constraints["rule"],
                "time": world.current_datetime.isoformat(),
                "hits": sim.cache_hits,
                "length": len(sim.execution_trace),
            }
        )
    )
    control.reset()


def test_native_cache_roundtrip_preserves_graph_and_detaches_output(tmp_path):
    path = tmp_path / "state.json"
    first = setup_graph(path)
    _, alice, bob, world, factory = first
    result = public_call(first, record_result, alice, bob, world, factory)
    result["participants"][1].append("external mutation")
    control.checkpoint()
    payload = json.loads(path.read_text())
    assert len(payload) == 1
    control.end()
    control.reset()
    second = setup_graph(path)
    sim, alice2, bob2, world2, factory2 = second
    replayed = public_call(second, record_result, alice2, bob2, world2, factory2)
    assert replayed["participants"] == (alice2, [bob2, alice2])
    assert replayed["participants"][0] is TinyPerson.get_agent_by_name("Alice")
    assert replayed["world"] is world2
    assert replayed["factory"] is factory2
    assert world2.agents == [alice2, bob2]
    assert alice2.environment is world2 and bob2.environment is world2
    assert alice2.get("occupation") == "Architect"
    assert alice2._mental_faculties[0].constraints == {"rule": "saved"}
    assert world2.current_datetime == datetime(2025, 1, 1, 0, 5)
    assert sim.cache_hits == 1 and sim.cache_misses == 0
    assert len(sim.execution_trace) == 1


def test_cache_replay_in_spawned_interpreter_resolves_its_own_registries(tmp_path):
    path, results = tmp_path / "state.json", tmp_path / "result.json"
    graph = setup_graph(path)
    public_call(graph, record_result, *graph[1:])
    control.checkpoint()
    control.end()
    control.reset()
    context = multiprocessing.get_context("spawn")
    process = context.Process(target=replay_in_fresh_process, args=(path, results))
    try:
        process.start()
        process.join(timeout=30)
        assert process.exitcode == 0
    finally:
        if process.is_alive():
            process.terminate()
        if process.pid is not None:
            process.join(timeout=5)
    assert json.loads(results.read_text()) == {
        "alice_identity": True,
        "bob_identity": True,
        "alias_identity": True,
        "world_identity": True,
        "factory_identity": True,
        "occupation": "Architect",
        "rule": "saved",
        "time": "2025-01-01T00:05:00",
        "hits": 1,
        "length": 1,
    }


class BoundaryClient:
    """Only the real factory's model response boundary is substituted."""

    def __init__(self):
        self.calls = 0
        self.lock = Lock()

    def send_message(self, *args, **kwargs):
        with self.lock:
            name = ["Generated Alice", "Generated Bob"][self.calls]
            self.calls += 1
        return {"role": "assistant", "content": json.dumps({"name": name, "age": 30})}


def prepare_factory(path):
    control.begin(str(path))
    factory = TinyPersonFactory(
        context="Offline factory replay regression", total_population_size=2
    )
    factory.remaining_characteristics_sample = [
        {"name": "Generated Alice"},
        {"name": "Generated Bob"},
    ]
    return factory


@pytest.mark.parametrize("parallel", [False, True])
def test_real_person_factory_replays_after_json_checkpoint_without_model_calls(
    tmp_path, monkeypatch, parallel
):
    path = tmp_path / "factory.json"
    boundary = BoundaryClient()
    monkeypatch.setattr(
        "tinytroupe.factory.tiny_person_factory.client", lambda: boundary
    )
    factory = prepare_factory(path)
    original = factory.generate_people(number_of_people=2, parallelize=parallel)
    assert {person.name for person in original} == {"Generated Alice", "Generated Bob"}
    assert boundary.calls == 2
    control.checkpoint()
    control.end()
    control.reset()
    factory2 = prepare_factory(path)
    restored = factory2.generate_people(number_of_people=2, parallelize=parallel)
    assert {person.name for person in restored} == {"Generated Alice", "Generated Bob"}
    assert boundary.calls == 2
    assert all(
        person is TinyPerson.get_agent_by_name(person.name) for person in restored
    )
    sim = control.current_simulation()
    assert all(person is sim.name_to_agent[person.name] for person in restored)
    assert all(person.get("age") == 30 for person in restored)
    assert not sim.is_under_parallel_transactions()
    assert not any(sim._under_transaction.values())
    assert sim.cache_hits > 0 and sim.cache_misses == 0


def test_parallel_segment_replay_uses_cached_outputs_and_no_extra_trace_suffix(
    tmp_path,
):
    graph = setup_graph(tmp_path / "parallel.json")
    sim, alice, bob, *_ = graph
    calls = []
    barrier = Barrier(2)

    def compute(person):
        calls.append(person.name)
        return {"person": person, "values": ([person.name],)}

    def segment():
        def worker(person):
            barrier.wait(timeout=5)
            return control.Transaction(person, sim, compute, person).execute(
                parallel_id=person.name
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, [alice, bob]))

    first = control.Transaction(alice, sim, segment).execute(
        begin_parallel=True, parallel_id="owner"
    )
    assert set(calls) == {"Alice", "Bob"}
    assert len(first) == 2
    assert len(sim.cached_trace) == len(sim.execution_trace) == 2
    assert len(sim.cached_trace[0]) == 2
    control.checkpoint()
    original = json.loads((tmp_path / "parallel.json").read_text())
    sim.cached_trace = original
    sim.execution_trace = []
    second = control.Transaction(alice, sim, segment).execute(
        begin_parallel=True, parallel_id="owner"
    )
    assert len(calls) == 2
    assert second[0]["person"] is alice and second[1]["person"] is bob
    assert len(sim.execution_trace) == len(sim.cached_trace) == 2
    assert sim.cached_trace == original
    assert sim.cache_hits == 3


def test_parallel_worker_state_is_snapshotted_only_after_workers_join(
    tmp_path, monkeypatch
):
    graph = setup_graph(tmp_path / "parallel.json")
    sim, alice, bob, *_ = graph
    original = sim._encode_simulation_state
    snapshots = []

    def snapshot():
        assert not sim.is_under_parallel_transactions()
        snapshots.append(True)
        return original()

    monkeypatch.setattr(sim, "_encode_simulation_state", snapshot)

    def segment():
        with ThreadPoolExecutor(max_workers=2) as pool:

            def worker(person):
                return control.Transaction(
                    person, sim, lambda person: {"person": person}, person
                ).execute(parallel_id=person.name)

            return list(pool.map(worker, [alice, bob]))

    result = control.Transaction(alice, sim, segment).execute(
        begin_parallel=True, parallel_id="owner"
    )
    assert [value["person"] for value in result] == [alice, bob]
    assert snapshots == [True]
    assert len(sim.cached_trace) == 2


def test_failed_parallel_replay_does_not_mutate_original_cached_segment(tmp_path):
    graph = setup_graph(tmp_path / "parallel.json")
    sim, alice, *_ = graph
    prefix = (
        None,
        "prefix",
        {"type": "JSON", "value": True},
        sim._encode_simulation_state(),
    )
    sim.cached_trace = [prefix, {"old worker": {"encoded_output": None}}]
    sim.execution_trace = [prefix]
    original = json.loads(json.dumps(sim.cached_trace))

    def segment():
        control.Transaction(alice, sim, lambda: "new worker").execute(
            parallel_id="child"
        )
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        control.Transaction(alice, sim, segment).execute(
            begin_parallel=True, parallel_id="owner"
        )
    assert json.loads(json.dumps(sim.cached_trace)) == original
    assert len(sim.execution_trace) == 1
    assert not sim.is_under_parallel_transactions()
    assert not sim.is_under_transaction("child")


def test_replay_reconstructs_generated_world_with_canonical_generated_agents(tmp_path):
    path = tmp_path / "created.json"
    control.begin(str(path))
    owner = TinyPerson("Owner")
    sim = control.current_simulation()

    def create_graph():
        guest = TinyPerson("Guest")
        world = TinyWorld("Generated World", [owner, guest])
        sim.add_environment(world)
        return {"guest": guest, "world": world}

    first = control.Transaction(owner, sim, create_graph).execute(parallel_id="owner")
    control.checkpoint()
    control.end()
    control.reset()
    control.begin(str(path))
    sim = control.current_simulation()
    owner = TinyPerson("Owner")
    restored = control.Transaction(owner, sim, create_graph).execute(
        parallel_id="owner"
    )
    assert restored["world"] is TinyWorld.get_environment_by_name("Generated World")
    assert restored["guest"] is TinyPerson.get_agent_by_name("Guest")
    assert restored["guest"] is sim.name_to_agent["Guest"]
    assert restored["world"].agents == [owner, restored["guest"]]
    assert owner.environment is restored["world"]
    assert sim.cache_hits == 1 and sim.cache_misses == 0
    assert first["world"] is not restored["world"]


def test_parallel_final_snapshot_failure_discards_segment_and_allows_retry(
    tmp_path, monkeypatch
):
    graph = setup_graph(tmp_path / "parallel.json")
    sim, alice, *_ = graph
    calls = []

    def compute():
        calls.append("computed")
        return "worker output"

    def segment():
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(
                lambda: control.Transaction(alice, sim, compute).execute(
                    parallel_id="child"
                )
            ).result(timeout=5)

    def fail_snapshot():
        raise RuntimeError("final state unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(sim, "_encode_simulation_state", fail_snapshot)
        with pytest.raises(RuntimeError, match="final state unavailable"):
            control.Transaction(alice, sim, segment).execute(
                begin_parallel=True, parallel_id="owner"
            )
    assert sim.execution_trace == sim.cached_trace == []
    assert not sim.is_under_parallel_transactions()
    assert not any(sim._under_transaction.values())
    assert (
        control.Transaction(alice, sim, segment).execute(
            begin_parallel=True, parallel_id="owner"
        )
        == "worker output"
    )
    assert calls == ["computed", "computed"]
    assert len(sim.execution_trace) == len(sim.cached_trace) == 2


def test_reconstruction_reuses_preexisting_free_objects_without_provider_initialization(
    tmp_path,
):
    graph = setup_graph(tmp_path / "existing.json")
    sim, alice, bob, world, factory = graph
    state = sim._encode_simulation_state()
    # The objects exist globally but have not yet been captured in the replay's
    # local simulation maps. Reconstructing must capture, never replace, them.
    sim.agents = []
    sim.name_to_agent = {}
    sim.environments = []
    sim.name_to_environment = {}
    alice.simulation_id = bob.simulation_id = world.simulation_id = None
    with patch(
        "openai.OpenAI", side_effect=AssertionError("provider initialization forbidden")
    ):
        sim._decode_simulation_state(state)
    assert sim.name_to_agent == {"Alice": alice, "Bob": bob}
    assert sim.name_to_environment["Office"] is world
    assert world.agents[0] is alice and world.agents[1] is bob
    assert sim.name_to_factory[factory.name] is factory
    assert alice.environment is bob.environment is world
    # Repeated restoration also leaves the canonical objects and map sizes stable.
    sim._decode_simulation_state(state)
    assert sim.agents == [alice, bob]
    assert sim.environments == [world]
