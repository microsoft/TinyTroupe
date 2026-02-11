import copy
import hashlib
import json
import os
import textwrap  # to dedent strings
import threading
from typing import Any

import chevron  # to parse Mustache templates
from rich import print

import tinytroupe.utils as utils
import tinytroupe.utils.llm
from tinytroupe import config_manager
from tinytroupe.agent import AgentOrWorld, CognitiveActionModel, Self, logger
from tinytroupe.agent.memory import EpisodicConsolidator, EpisodicMemory, SemanticMemory
from tinytroupe.control import current_simulation, transactional
from tinytroupe.utils import LLMChat  # Import LLMChat from the appropriate module
from tinytroupe.utils import JsonSerializableRegistry, name_or_empty, repeat_on_error

# to protect from race conditions when running agents in parallel
concurrent_agent_action_lock = threading.Lock()


#######################################################################################################################
# TinyPerson itself
#######################################################################################################################
@utils.post_init
class TinyPerson(JsonSerializableRegistry):
    """A simulated person in the TinyTroupe universe."""

    # The maximum number of actions that an agent is allowed to perform before DONE.
    # This prevents the agent from acting without ever stopping.
    MAX_ACTIONS_BEFORE_DONE = 15

    # The maximum similarity between consecutive actions. If the similarity is too high, the action is discarded and replaced by a DONE.
    # Set this to None to disable the check.
    MAX_ACTION_SIMILARITY = 0.85

    MIN_EPISODE_LENGTH = config_manager.get(
        "min_episode_length", 10
    )  # The minimum number of messages in an episode before it is considered valid.
    MAX_EPISODE_LENGTH = config_manager.get(
        "max_episode_length", 15
    )  # The maximum number of messages in an episode before it is considered valid.

    # Maximum number of recent image-bearing stimuli to re-inject as user
    # messages each turn, enabling agents to re-examine previously seen images.
    # The most recent stimuli are kept (recency bias — Murdock, 1962).
    MAX_IMAGE_STIMULI_TO_RECALL = config_manager.get(
        "max_image_stimuli_to_recall", 3
    )

    PP_TEXT_WIDTH = 100

    serializable_attributes = [
        "_persona",
        "_mental_state",
        "_mental_faculties",
        "_current_episode_event_count",
        "episodic_memory",
        "semantic_memory",
        "_image_registry",
        "_image_id_counter",
    ]
    serializable_attributes_renaming = {
        "_mental_faculties": "mental_faculties",
        "_persona": "persona",
        "_mental_state": "mental_state",
        "_current_episode_event_count": "current_episode_event_count",
    }

    # A dict of all agents instantiated so far.
    all_agents = {}  # name -> agent

    # Whether to display the communication or not. True is for interactive applications, when we want to see simulation
    # outputs as they are produced.
    communication_display: bool = True

    def __init__(
        self,
        name: str = None,
        action_generator=None,
        episodic_memory=None,
        semantic_memory=None,
        mental_faculties: list = None,
        enable_basic_action_repetition_prevention: bool = True,
    ):
        """
        Creates a TinyPerson.

        Args:
            name (str): The name of the TinyPerson. Either this or spec_path must be specified.
            action_generator (ActionGenerator, optional): The action generator to use. Defaults to ActionGenerator().
            episodic_memory (EpisodicMemory, optional): The memory implementation to use. Defaults to EpisodicMemory().
            semantic_memory (SemanticMemory, optional): The memory implementation to use. Defaults to SemanticMemory().
            mental_faculties (list, optional): A list of mental faculties to add to the agent. Defaults to None.
            enable_basic_action_repetition_prevention (bool, optional): Whether to enable basic action repetition prevention. Defaults to True.
        """

        # NOTE: default values will be given in the _post_init method, as that's shared by
        #       direct initialization as well as via deserialization.

        if action_generator is not None:
            self.action_generator = action_generator

        if episodic_memory is not None:
            self.episodic_memory = episodic_memory

        if semantic_memory is not None:
            self.semantic_memory = semantic_memory

        # Mental faculties
        if mental_faculties is not None:
            self._mental_faculties = mental_faculties

        if enable_basic_action_repetition_prevention:
            self.enable_basic_action_repetition_prevention = (
                enable_basic_action_repetition_prevention
            )

        assert name is not None, "A TinyPerson must have a name."
        self.name = name

        # @post_init makes sure that _post_init is called after __init__

    def _post_init(self, **kwargs):
        """
        This will run after __init__, since the class has the @post_init decorator.
        It is convenient to separate some of the initialization processes to make deserialize easier.
        """

        from tinytroupe.agent.action_generator import (
            ActionGenerator,
        )  # import here to avoid circular import issues

        ############################################################
        # Default values
        ############################################################

        self.current_messages = []

        # the current environment in which the agent is acting
        self.environment = None

        # The list of actions that this agent has performed so far, but which have not been
        # consumed by the environment yet.
        self._actions_buffer = []

        # The list of agents that this agent can currently interact with.
        # This can change over time, as agents move around the world.
        self._accessible_agents = []

        # the buffer of communications that have been displayed so far, used for
        # saving these communications to another output form later (e.g., caching)
        self._displayed_communications_buffer = []

        if not hasattr(self, "_current_episode_event_count"):
            self._current_episode_event_count = 0  # the number of events in the current episode, used to limit the episode length

        if not hasattr(self, "action_generator"):
            # This default value MUST NOT be in the method signature, otherwise it will be shared across all instances.
            self.action_generator = ActionGenerator(
                max_attempts=config_manager.get("action_generator_max_attempts"),
                enable_quality_checks=config_manager.get(
                    "action_generator_enable_quality_checks"
                ),
                enable_regeneration=config_manager.get(
                    "action_generator_enable_regeneration"
                ),
                enable_direct_correction=config_manager.get(
                    "action_generator_enable_direct_correction"
                ),
                enable_quality_check_for_persona_adherence=config_manager.get(
                    "action_generator_enable_quality_check_for_persona_adherence"
                ),
                enable_quality_check_for_selfconsistency=config_manager.get(
                    "action_generator_enable_quality_check_for_selfconsistency"
                ),
                enable_quality_check_for_fluency=config_manager.get(
                    "action_generator_enable_quality_check_for_fluency"
                ),
                enable_quality_check_for_suitability=config_manager.get(
                    "action_generator_enable_quality_check_for_suitability"
                ),
                enable_quality_check_for_similarity=config_manager.get(
                    "action_generator_enable_quality_check_for_similarity"
                ),
                continue_on_failure=config_manager.get(
                    "action_generator_continue_on_failure"
                ),
                quality_threshold=config_manager.get(
                    "action_generator_quality_threshold"
                ),
            )

        if not hasattr(self, "episodic_memory"):
            # This default value MUST NOT be in the method signature, otherwise it will be shared across all instances.
            self.episodic_memory = EpisodicMemory(
                fixed_prefix_length=config_manager.get(
                    "episodic_memory_fixed_prefix_length"
                ),
                lookback_length=config_manager.get("episodic_memory_lookback_length"),
            )

        if not hasattr(self, "semantic_memory"):
            # This default value MUST NOT be in the method signature, otherwise it will be shared across all instances.
            self.semantic_memory = SemanticMemory()

        # _mental_faculties
        if not hasattr(self, "_mental_faculties"):
            # This default value MUST NOT be in the method signature, otherwise it will be shared across all instances.
            self._mental_faculties = []

        # basic action repetition prevention
        if not hasattr(self, "enable_basic_action_repetition_prevention"):
            self.enable_basic_action_repetition_prevention = True

        # create the persona configuration dictionary
        if not hasattr(self, "_persona"):
            self._persona = {
                "name": self.name,
                "age": None,
                "nationality": None,
                "country_of_residence": None,
                "occupation": None,
            }

        if not hasattr(self, "name"):
            self.name = self._persona["name"]

        # create the mental state dictionary
        if not hasattr(self, "_mental_state"):
            self._mental_state = {
                "datetime": None,
                "location": None,
                "context": [],
                "goals": [],
                "attention": None,
                "emotions": "Feeling nothing in particular, just calm.",
                "working_semantic_memory": None,
                "accessible_agents": [],  # [{"agent": agent_1, "relation": "My friend"}, {"agent": agent_2, "relation": "My colleague"}, ...]
            }

        if not hasattr(self, "_extended_agent_summary"):
            self._extended_agent_summary = None

        if not hasattr(self, "actions_count"):
            self.actions_count = 0

        if not hasattr(self, "stimuli_count"):
            self.stimuli_count = 0

        # Image registry for the vision modality: maps image IDs (e.g. "img_1") to
        # their original references (file paths or URLs).  Persisted across serialization.
        if not hasattr(self, "_image_registry"):
            self._image_registry: dict[str, str] = {}
        if not hasattr(self, "_image_id_counter"):
            self._image_id_counter: int = 0

        # Class-level cache for LLM-generated image descriptions, keyed by content hash.
        # Shared across all agents to avoid redundant vision API calls for the same image.
        if not hasattr(TinyPerson, "_image_description_cache"):
            TinyPerson._image_description_cache: dict[str, str] = {}

        self._prompt_template_path = os.path.join(
            os.path.dirname(__file__), "prompts/tiny_person.v2.mustache"
        )
        self._init_system_message = None  # initialized later

        ############################################################
        # Special mechanisms used during deserialization
        ############################################################

        # rename agent to some specific name?
        if kwargs.get("new_agent_name") is not None:
            self._rename(kwargs.get("new_agent_name"))

        # If auto-rename, use the given name plus some new number ...
        if kwargs.get("auto_rename") is True:
            new_name = self.name  # start with the current name
            rename_succeeded = False
            while not rename_succeeded:
                try:
                    self._rename(new_name)
                    TinyPerson.add_agent(self)
                    rename_succeeded = True
                except ValueError:
                    new_id = utils.fresh_id(self.__class__.__name__)
                    new_name = f"{self.name}_{new_id}"

        # ... otherwise, just register the agent
        else:
            # register the agent in the global list of agents
            TinyPerson.add_agent(self)

        # start with a clean slate
        self.reset_prompt()

        # it could be the case that the agent is being created within a simulation scope, in which case
        # the simulation_id must be set accordingly
        if current_simulation() is not None:
            current_simulation().add_agent(self)
        else:
            self.simulation_id = None

    def _rename(self, new_name: str):
        self.name = new_name
        self._persona["name"] = self.name

    def generate_agent_system_prompt(self):
        with open(
            self._prompt_template_path, "r", encoding="utf-8", errors="replace"
        ) as f:
            agent_prompt_template = f.read()

        # let's operate on top of a copy of the configuration, because we'll need to add more variables, etc.
        template_variables = self._persona.copy()
        template_variables["persona"] = json.dumps(self._persona.copy(), indent=4)

        # add mental state to the template variables
        template_variables["mental_state"] = json.dumps(self._mental_state, indent=4)

        # Prepare additional action definitions and constraints
        actions_definitions_prompt = ""
        actions_constraints_prompt = ""
        for faculty in self._mental_faculties:
            actions_definitions_prompt += f"{faculty.actions_definitions_prompt()}\n"
            actions_constraints_prompt += f"{faculty.actions_constraints_prompt()}\n"

        # Make the additional prompt pieces available to the template.
        # Identation here is to align with the text structure in the template.
        template_variables["actions_definitions_prompt"] = textwrap.indent(
            actions_definitions_prompt.strip(), "  "
        )
        template_variables["actions_constraints_prompt"] = textwrap.indent(
            actions_constraints_prompt.strip(), "  "
        )

        # RAI prompt components, if requested
        template_variables = utils.add_rai_template_variables_if_enabled(
            template_variables
        )

        # include recent episodic memory as part of the system prompt
        try:
            working_episodic_memory_text = (
                self._render_recent_episodic_memories_for_prompt()
            )
        except Exception:
            working_episodic_memory_text = "(No recent episodic memories available)"
        template_variables["working_episodic_memory"] = textwrap.indent(
            working_episodic_memory_text.strip(), "  "
        )

        return chevron.render(agent_prompt_template, template_variables)

    def _render_recent_episodic_memories_for_prompt(self) -> str:
        """
        Builds a concise text block describing recent episodic events (oldest to newest),
        suitable to be embedded inside the system prompt.
        """
        max_len = config_manager.get("max_content_display_length")
        episodes = self.retrieve_recent_memories(max_content_length=max_len)
        if not episodes:
            return "(No recent episodic memories available)"

        lines = []
        for msg in episodes:
            try:
                role = msg.get("role")
                timestamp = msg.get("simulation_timestamp", None)
                timestamp_str = f" [@{timestamp}]" if timestamp else ""
                if role == "user":
                    for s in msg.get("content", {}).get("stimuli", []):
                        src = s.get("source") or "ENV"
                        typ = s.get("type", "?")
                        cnt = utils.break_text_at_length(
                            s.get("content", ""), max_length=max_len
                        )
                        # Note image IDs without re-injecting actual image data
                        image_ids = s.get("images")
                        img_note = f" [images: {', '.join(image_ids)}]" if image_ids else ""
                        lines.append(
                            f"- [STIMULUS:{typ}] from {src}{timestamp_str}: {cnt}{img_note}"
                        )
                elif role == "assistant":
                    action = msg.get("content", {}).get("action", {}) or {}
                    typ = action.get("type", "?")
                    tgt = action.get("target") or ""
                    cnt = utils.break_text_at_length(
                        action.get("content", "") or "", max_length=max_len
                    )
                    target_str = f" to {tgt}" if tgt else ""
                    lines.append(f"- [ACTION:{typ}]{target_str}{timestamp_str}: {cnt}")
                # system messages are ignored in the episodic memory prompt
            except Exception:
                continue

        return "\n".join(lines) if lines else "(No recent episodic memories available)"

    def reset_prompt(self):
        # render the template with the current configuration
        self._init_system_message = self.generate_agent_system_prompt()

        # - reset system message
        # - make it clear that the provided events are past events and have already had their effects
        self.current_messages = [
            {"role": "system", "content": self._init_system_message}
        ]

        # NOTE: Episodic memories are now part of the system message (see template's 'Episodic Memory' section).

        self.current_messages.append(
            {
                "role": "user",
                "content": "You can now produce your next sequence of actions for this turn, in order, and finish with DONE.",
            }
        )

    #########################################################################
    # Persona definitions
    #########################################################################

    #
    # Conveniences to access the persona configuration via dictionary-like syntax using
    # the [] operator. e.g., agent["nationality"] = "American"
    #
    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.define(key, value)

    #
    # Conveniences to import persona definitions via the '+' operator,
    #  e.g., agent + {"nationality": "American", ...}
    #
    #  e.g., agent + "path/to/fragment.json"
    #
    def __add__(self, other):
        """
        Allows using the '+' operator to add persona definitions or import a fragment.
        If 'other' is a dict, calls include_persona_definitions().
        If 'other' is a string, calls import_fragment().
        """
        if isinstance(other, dict):
            self.include_persona_definitions(other)
        elif isinstance(other, str):
            self.import_fragment(other)
        else:
            raise TypeError(
                "Unsupported operand type for +. Must be a dict or a string path to fragment."
            )
        return self

    #
    # Various other conveniences to manipulate the persona configuration
    #

    def get(self, key):
        """
        Returns the value of a key in the TinyPerson's persona configuration.
        Supports dot notation for nested keys (e.g., "address.city").
        """
        keys = key.split(".")
        value = self._persona
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, None)
            else:
                return None  # If the path is invalid, return None
        return value

    @transactional()
    def import_fragment(self, path):
        """
        Imports a fragment of a persona configuration from a JSON file.
        """
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            fragment = json.load(f)

        # check the type is "Fragment" and that there's also a "persona" key
        if (
            fragment.get("type", None) == "Fragment"
            and fragment.get("persona", None) is not None
        ):
            self.include_persona_definitions(fragment["persona"])
        else:
            raise ValueError(
                "The imported JSON file must be a valid fragment of a persona configuration."
            )

        # must reset prompt after adding to configuration
        self.reset_prompt()

    @transactional()
    def include_persona_definitions(self, additional_definitions: dict):
        """
        Imports a set of definitions into the TinyPerson. They will be merged with the current configuration.
        It is also a convenient way to include multiple bundled definitions into the agent.

        Args:
            additional_definitions (dict): The additional definitions to import.
        """

        self._persona = utils.merge_dicts(self._persona, additional_definitions)

        # must reset prompt after adding to configuration
        self.reset_prompt()

    @transactional()
    def define(self, key, value, merge=False, overwrite_scalars=True):
        """
        Define a value to the TinyPerson's persona configuration. Value can either be a scalar or a dictionary.
        If the value is a dictionary or list, you can choose to merge it with the existing value or replace it.
        If the value is a scalar, you can choose to overwrite the existing value or not.

        Args:
            key (str): The key to define.
            value (Any): The value to define.
            merge (bool, optional): Whether to merge the dict/list values with the existing values or replace them. Defaults to False.
            overwrite_scalars (bool, optional): Whether to overwrite scalar values or not. Defaults to True.
        """

        # dedent value if it is a string
        if isinstance(value, str):
            value = textwrap.dedent(value)

        # if the value is a dictionary, we can choose to merge it with the existing value or replace it
        if isinstance(value, dict) or isinstance(value, list):
            if merge:
                self._persona = utils.merge_dicts(self._persona, {key: value})
            else:
                self._persona[key] = value

        # if the value is a scalar, we can choose to overwrite it or not
        elif overwrite_scalars or (key not in self._persona):
            self._persona[key] = value

        else:
            raise ValueError(
                f"The key '{key}' already exists in the persona configuration and overwrite_scalars is set to False."
            )

        # must reset prompt after adding to configuration
        self.reset_prompt()

    @transactional()
    def define_relationships(self, relationships, replace=True):
        """
        Defines or updates the TinyPerson's relationships.

        Args:
            relationships (list or dict): The relationships to add or replace. Either a list of dicts mapping agent names to relationship descriptions,
              or a single dict mapping one agent name to its relationship description.
            replace (bool, optional): Whether to replace the current relationships or just add to them. Defaults to True.
        """

        if (replace == True) and (isinstance(relationships, list)):
            self._persona["relationships"] = relationships

        elif replace == False:
            current_relationships = self._persona["relationships"]
            if isinstance(relationships, list):
                for r in relationships:
                    current_relationships.append(r)

            elif (
                isinstance(relationships, dict) and len(relationships) == 2
            ):  # {"Name": ..., "Description": ...}
                current_relationships.append(relationships)

            else:
                raise Exception(
                    "Only one key-value pair is allowed in the relationships dict."
                )

        else:
            raise Exception("Invalid arguments for define_relationships.")

    ##############################################################################
    # Relationships
    ##############################################################################

    @transactional()
    def clear_relationships(self):
        """
        Clears the TinyPerson's relationships.
        """
        self._persona["relationships"] = []

        return self

    @transactional()
    def related_to(self, other_agent, description, symmetric_description=None):
        """
        Defines a relationship between this agent and another agent.

        Args:
            other_agent (TinyPerson): The other agent.
            description (str): The description of the relationship.
            symmetric (bool): Whether the relationship is symmetric or not. That is,
              if the relationship is defined for both agents.

        Returns:
            TinyPerson: The agent itself, to facilitate chaining.
        """
        self.define_relationships(
            [{"Name": other_agent.name, "Description": description}], replace=False
        )
        if symmetric_description is not None:
            other_agent.define_relationships(
                [{"Name": self.name, "Description": symmetric_description}],
                replace=False,
            )

        return self

    ############################################################################

    def add_mental_faculties(self, mental_faculties):
        """
        Adds a list of mental faculties to the agent.
        """
        for faculty in mental_faculties:
            self.add_mental_faculty(faculty)

        return self

    def add_mental_faculty(self, faculty):
        """
        Adds a mental faculty to the agent.
        """
        # check if the faculty is already there or not
        if faculty not in self._mental_faculties:
            self._mental_faculties.append(faculty)
        else:
            raise Exception(
                f"The mental faculty {faculty} is already present in the agent."
            )

        return self

    @transactional()
    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def act(
        self,
        until_done=True,
        n=None,
        return_actions=False,
        max_content_length=None,
        communication_display: bool = None,
    ):
        """
        Acts in the environment and updates its internal cognitive state.
        Either acts until the agent is done and needs additional stimuli, or acts a fixed number of times,
        but not both.

        Args:
            until_done (bool): Whether to keep acting until the agent is done and needs additional stimuli.
            n (int): The number of actions to perform. Defaults to None.
            return_actions (bool): Whether to return the actions or not. Defaults to False.
            max_content_length (int): The maximum length of the content to display. Defaults to None, which uses the global configuration value.
            communication_display (bool): Whether to display the communication or not, will override the global setting if provided. Defaults to None.
        """

        # either act until done or act a fixed number of times, but not both
        assert not (until_done and n is not None)
        if n is not None:
            assert n < TinyPerson.MAX_ACTIONS_BEFORE_DONE

        contents = []

        # A separate function to run before each action, which is not meant to be repeated in case of errors.
        def aux_pre_act():
            pass

        # Helper to persist a single action and its side-effects
        def _commit_action(action, role, content):
            # check similarity quickly and replace by DONE if excessively repetitive
            next_action_similarity = utils.next_action_jaccard_similarity(self, action)
            if (
                self.enable_basic_action_repetition_prevention
                and (TinyPerson.MAX_ACTION_SIMILARITY is not None)
                and (next_action_similarity > TinyPerson.MAX_ACTION_SIMILARITY)
            ):
                logger.warning(
                    f"[{self.name}] Action similarity is too high ({next_action_similarity}), replacing it with DONE."
                )
                action = {"type": "DONE", "content": "", "target": ""}

                # Store a system feedback about the replacement
                self.store_in_memory(
                    {
                        "role": "system",
                        "content": f"""
                                        # EXCESSIVE ACTION SIMILARITY WARNING

                                        You were about to generate a repetitive action (jaccard similarity = {next_action_similarity}).
                                        Thus, the action was discarded and replaced by an artificial DONE.

                                        DO NOT BE REPETITIVE. This is not a human-like behavior, therefore you **must** avoid this in the future.
                                        Your alternatives are:
                                        - produce more diverse actions.
                                        - aggregate similar actions into a single, larger, action and produce it all at once.
                                        - as a **last resort only**, you may simply not acting at all by issuing a DONE.

                                        
                                        """,
                        "type": "feedback",
                        "simulation_timestamp": self.iso_datetime(),
                    }
                )

            # Build a minimal content record for memory (single action)
            content_for_memory = {"action": action}
            if isinstance(content, dict) and "cognitive_state" in content:
                content_for_memory["cognitive_state"] = content["cognitive_state"]

            # Commit to episodic memory
            self.store_in_memory(
                {
                    "role": role,
                    "content": content_for_memory,
                    "type": "action",
                    "simulation_timestamp": self.iso_datetime(),
                }
            )

            # buffer action for environment consumption
            self._actions_buffer.append(action)

            # Update mental state
            if isinstance(content, dict) and "cognitive_state" in content:
                cognitive_state = content["cognitive_state"]
                logger.debug(f"[{self.name}] Cognitive state: {cognitive_state}")
                self._update_cognitive_state(
                    goals=cognitive_state.get("goals", None),
                    context=cognitive_state.get("context", None),
                    attention=cognitive_state.get("emotions", None),
                    emotions=cognitive_state.get("emotions", None),
                )

            # Display
            contents.append(
                {
                    "action": action,
                    "cognitive_state": content_for_memory.get("cognitive_state", {}),
                }
            )
            if utils.first_non_none(
                communication_display, TinyPerson.communication_display
            ):
                self._display_communication(
                    role=role,
                    content={
                        "action": action,
                        "cognitive_state": content_for_memory.get(
                            "cognitive_state", {}
                        ),
                    },
                    kind="action",
                    simplified=True,
                    max_content_length=max_content_length,
                )

            # Side-effects via mental faculties
            for faculty in self._mental_faculties:
                faculty.process_action(self, action)

            # count
            self.actions_count += 1

        @repeat_on_error(retries=5, exceptions=[KeyError, TypeError])
        def aux_act_once_sequence():
            # ensure we have the latest prompt
            self.reset_prompt()

            # ----------------------------------------------------------------
            # Build the list of stimulus payloads to send as user messages.
            #
            # Cognitive motivation (recency bias — Murdock, 1962):
            #   The most recent image-bearing stimuli are re-injected so that
            #   the agent can re-examine previously seen images even after
            #   intervening non-visual stimuli.  Only the *most recent*
            #   ``MAX_IMAGE_STIMULI_TO_RECALL`` image-bearing stimuli are
            #   kept, reflecting the primacy of recent experience in
            #   short-term visual memory.
            #
            # The returned list is in chronological order so that the LLM
            # sees older context first and the newest stimulus last.
            # ----------------------------------------------------------------
            def _stimuli_payloads_for_current_turn():
                """Return a chronologically ordered list of stimulus payloads.

                The list always ends with the latest stimulus (of any type).
                Before it, up to ``MAX_IMAGE_STIMULI_TO_RECALL`` recent
                image-bearing stimuli are included (unless the latest is
                already one of them — no duplicates).
                """
                try:
                    recent = self.episodic_memory.retrieve_recent()
                except Exception:
                    return []

                if not recent:
                    return []

                # --- locate the latest stimulus ---
                latest_payload = None
                latest_idx = None
                for i, msg in enumerate(reversed(recent)):
                    if msg.get("role") == "user" and msg.get("type") == "stimulus":
                        latest_payload = msg.get("content")
                        latest_idx = len(recent) - 1 - i
                        break

                if latest_payload is None:
                    return []

                # --- collect image-bearing stimuli (chronological order) ---
                max_recall = TinyPerson.MAX_IMAGE_STIMULI_TO_RECALL
                image_payloads = []   # list of (idx, payload)
                for idx, msg in enumerate(recent):
                    if msg.get("role") != "user" or msg.get("type") != "stimulus":
                        continue
                    content = msg.get("content")
                    if not isinstance(content, dict):
                        continue
                    # Check if any stimulus in this message carries images
                    for stim in content.get("stimuli", []):
                        if stim.get("images"):
                            image_payloads.append((idx, content))
                            break

                # Keep only the most recent N (recency bias)
                if len(image_payloads) > max_recall:
                    image_payloads = image_payloads[-max_recall:]

                # --- merge into chronological list, avoiding duplicates ---
                payloads = []
                seen_indices = set()
                for idx, payload in image_payloads:
                    if idx != latest_idx and idx not in seen_indices:
                        payloads.append(payload)
                        seen_indices.add(idx)
                # Latest always comes last
                payloads.append(latest_payload)
                return payloads

            for payload in _stimuli_payloads_for_current_turn():
                self.current_messages.append(
                    {
                        "role": "user",
                        "content": payload,  # dict will be JSON-serialized by the generator
                    }
                )

            actions_or_action, role, content, all_negative_feedbacks = (
                self.action_generator.generate_next_actions(self, self.current_messages)
            )

            # Normalize to list
            actions = (
                actions_or_action
                if isinstance(actions_or_action, list)
                else [actions_or_action]
            )

            # Enforce a reasonable cap per turn
            if len(actions) > 0 and len(actions) > TinyPerson.MAX_ACTIONS_BEFORE_DONE:
                actions = actions[: TinyPerson.MAX_ACTIONS_BEFORE_DONE]
                if actions[-1] is not None and isinstance(actions[-1], dict) and actions[-1].get("type") != "DONE":
                    actions[-1] = {"type": "DONE", "content": "", "target": ""}

            # Commit each action in order
            for action in actions:
                # Skip None or non-dict actions
                if action is None or not isinstance(action, dict):
                    logger.warning(f"[{self.name}] Skipping invalid action: {action}")
                    continue
                _commit_action(action, role, content)
                if action.get("type") == "DONE":
                    break

        # Option 1: run N actions (may span multiple turns if model emits only one)
        if n is not None:
            remaining = n
            while remaining > 0:
                aux_pre_act()
                # run one inference producing a sequence, but stop after committing the requested number
                before = self.actions_count
                aux_act_once_sequence()
                produced = self.actions_count - before
                remaining -= produced
                if remaining <= 0:
                    break
                # If the last committed action was DONE, the turn ended; next loop will start a new turn

        # Option 2: run until DONE for this turn
        elif until_done:
            aux_pre_act()
            aux_act_once_sequence()

        # End of turn => consolidate episode memories
        self.consolidate_episode_memories()

        if return_actions:
            return contents

    @transactional()
    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def listen(
        self,
        speech,
        source: AgentOrWorld = None,
        max_content_length=None,
        communication_display: bool = None,
    ):
        """
        Listens to another agent (artificial or human) and updates its internal cognitive state.

        Args:
            speech (str): The speech to listen to.
            source (AgentOrWorld, optional): The source of the speech. Defaults to None.
            max_content_length (int, optional): The maximum length of the content to display. Defaults to None, which uses the global configuration value.
            communication_display (bool): Whether to display the communication or not, will override the global setting if provided. Defaults to None.

        """

        return self._observe(
            stimulus={
                "type": "CONVERSATION",
                "content": speech,
                "source": name_or_empty(source),
            },
            max_content_length=max_content_length,
            communication_display=communication_display,
        )

    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def socialize(
        self,
        social_description: str,
        source: AgentOrWorld = None,
        max_content_length=None,
    ):
        """
        Perceives a social stimulus through a description and updates its internal cognitive state.

        Args:
            social_description (str): The description of the social stimulus.
            source (AgentOrWorld, optional): The source of the social stimulus. Defaults to None.
        """
        return self._observe(
            stimulus={
                "type": "SOCIAL",
                "content": social_description,
                "source": name_or_empty(source),
            },
            max_content_length=max_content_length,
        )

    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def see(
        self,
        images=None,
        description: str = None,
        source: AgentOrWorld = None,
        max_content_length=None,
    ):
        """
        Perceives a visual stimulus — optionally including actual images — and updates
        the agent's internal cognitive state.

        This is the sole entry point for visual stimuli.  When ``images`` are provided,
        the agent will:

        1. Register each image in its internal ``_image_registry`` (assigning short IDs
           such as ``img_1``, ``img_2``, …).
        2. Generate a text description of the images via the vision model (cached by
           content hash to avoid redundant API calls).
        3. Combine the user-supplied ``description`` and the LLM-generated description
           into the stimulus ``content``.
        4. Include ``image_description`` and ``image_refs`` (mapping IDs to file
           paths / URLs) in the stimulus dict so that they are persisted in
           episodic memory and available for later consolidation into semantic
           memory.

        When no ``images`` are provided the method behaves exactly like the previous
        text-only ``see()``.

        Args:
            images: ``None``, a single image reference (file path / URL / data URI),
                or a list of image references.
            description (str, optional): A textual description of what the agent is looking at.
            source (AgentOrWorld, optional): The source of the visual stimulus.
            max_content_length (int, optional): Maximum content length for display.

        Returns:
            TinyPerson: ``self``, to allow method chaining.
        """
        from tinytroupe.utils.media import normalize_image_refs

        image_refs = normalize_image_refs(images)

        # ----- text-only path (backward-compatible) -----
        if not image_refs:
            return self._observe(
                stimulus={
                    "type": "VISUAL",
                    "content": description or "",
                    "source": name_or_empty(source),
                },
                max_content_length=max_content_length,
            )

        # ----- vision path -----
        image_ids = self._register_images(image_refs)
        llm_description = self._describe_images(image_refs, user_context=description)

        # Combine user description + LLM description
        parts = []
        if description:
            parts.append(description)
        if llm_description:
            parts.append(llm_description)
        content = "\n\n".join(parts) if parts else ""

        # NOTE: image descriptions are NOT stored eagerly in semantic memory.
        # Instead, they are carried inside the stimulus dict and extracted during
        # consolidation (see ``_extract_and_store_image_descriptions_from_episode``).
        # This keeps the semantic-memory formation path uniform across all
        # stimulus types — consistent with the consolidation pattern used by
        # every other memory kind.

        # Include image IDs in the stimulus so prompts can reference them
        ids_note = ", ".join(f"[{iid}]" for iid in image_ids)
        content_with_ids = f"{content}\n\nImage reference IDs: {ids_note}" if content else f"Image reference IDs: {ids_note}"

        # Build a mapping from short IDs to actual file paths / URLs so that
        # image references are fully preserved in episodic memory and can be
        # used for later re-examination or consolidation.
        image_refs_map = {iid: ref for iid, ref in zip(image_ids, image_refs)}

        return self._observe(
            stimulus={
                "type": "VISUAL",
                "content": content_with_ids,
                "source": name_or_empty(source),
                "images": image_ids,
                "image_description": llm_description or "",
                "image_refs": image_refs_map,
            },
            max_content_length=max_content_length,
        )

    # ------------------------------------------------------------------
    # Image registry helpers
    # ------------------------------------------------------------------

    def _register_images(self, image_refs: list[str]) -> list[str]:
        """
        Assign short IDs to a list of image references and store them in the
        agent's ``_image_registry``.

        Args:
            image_refs: A list of image file paths, URLs, or data URIs.

        Returns:
            A list of the assigned image IDs (e.g. ``["img_1", "img_2"]``).
        """
        ids: list[str] = []
        for ref in image_refs:
            self._image_id_counter += 1
            img_id = f"img_{self._image_id_counter}"
            self._image_registry[img_id] = ref
            ids.append(img_id)
        return ids

    def _describe_images(
        self,
        image_refs: list[str],
        user_context: str = None,
    ) -> str:
        """
        Generate a concise text description of one or more images using the vision
        model.  Results are cached by image content hash to avoid redundant API calls.

        Args:
            image_refs: A list of image file paths, URLs, or data URIs.
            user_context: Optional user-supplied context to help the model.

        Returns:
            A string containing the LLM-generated description.
        """
        from tinytroupe.utils.media import build_multimodal_content_array, hash_image
        from tinytroupe.clients import client

        # Build a combined cache key from all image hashes
        hashes = sorted(hash_image(ref) for ref in image_refs)
        cache_key = hashlib.sha256("|".join(hashes).encode()).hexdigest()

        if cache_key in TinyPerson._image_description_cache:
            logger.debug(f"[{self.name}] Image description cache hit for {cache_key[:12]}…")
            return TinyPerson._image_description_cache[cache_key]

        # Build the vision prompt
        prompt_text = (
            "Describe the image(s) below concisely and factually in a few sentences. "
            "Focus on the most salient visual content."
        )
        if user_context:
            prompt_text += f"\n\nAdditional context from the viewer: {user_context}"

        vision_detail = config_manager.get("vision_detail", "auto")
        content_array = build_multimodal_content_array(
            text=prompt_text,
            image_refs=image_refs,
            detail=vision_detail,
        )

        vision_model = config_manager.get_with_fallback("vision_model", "model")

        messages = [
            {"role": "user", "content": content_array},
        ]

        logger.debug(f"[{self.name}] Requesting image description via model {vision_model}")
        response = client().send_message(
            messages,
            model=vision_model,
            dedent_messages=False,  # content is a list, not a string
        )

        description_text = ""
        if response and isinstance(response, dict):
            description_text = response.get("content", "")
        elif response and isinstance(response, str):
            description_text = response

        # Cache the result
        TinyPerson._image_description_cache[cache_key] = description_text
        logger.debug(f"[{self.name}] Cached image description ({cache_key[:12]}…): {description_text[:100]}…")

        return description_text

    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def think(self, thought, max_content_length=None):
        """
        Forces the agent to think about something and updates its internal cognitive state.

        """
        return self._observe(
            stimulus={
                "type": "THOUGHT",
                "content": thought,
                "source": name_or_empty(self),
            },
            max_content_length=max_content_length,
        )

    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def internalize_goal(self, goal, max_content_length=None):
        """
        Internalizes a goal and updates its internal cognitive state.
        """
        return self._observe(
            stimulus={
                "type": "INTERNAL_GOAL_FORMULATION",
                "content": goal,
                "source": name_or_empty(self),
            },
            max_content_length=max_content_length,
        )

    @transactional()
    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def _observe(
        self, stimulus, max_content_length=None, communication_display: bool = None
    ):
        """
        Observes a stimulus and updates its internal cognitive state.

        Args:
            stimulus (dict): The stimulus to observe. It must contain a 'type' and 'content' keys.
            max_content_length (int, optional): The maximum length of the content to display. Defaults to None, which uses the global configuration value.
            communication_display (bool): Whether to display the communication or not, will override the global setting if provided. Defaults to None.
        """
        stimuli = [stimulus]

        content = {"stimuli": stimuli}

        logger.debug(f"[{self.name}] Observing stimuli: {content}")

        # whatever comes from the outside will be interpreted as coming from 'user', simply because
        # this is the counterpart of 'assistant'

        self.store_in_memory(
            {
                "role": "user",
                "content": content,
                "type": "stimulus",
                "simulation_timestamp": self.iso_datetime(),
            }
        )

        if utils.first_non_none(
            communication_display, TinyPerson.communication_display
        ):
            self._display_communication(
                role="user",
                content=content,
                kind="stimuli",
                simplified=True,
                max_content_length=max_content_length,
            )

        # count the stimuli as this can be useful for taking decisions later
        self.stimuli_count += 1

        return self  # allows easier chaining of methods

    @transactional()
    def listen_and_act(
        self,
        speech,
        return_actions=False,
        max_content_length=None,
        communication_display: bool = None,
    ):
        """
        Convenience method that combines the `listen` and `act` methods.
        """

        self.listen(
            speech,
            max_content_length=max_content_length,
            communication_display=communication_display,
        )
        return self.act(
            return_actions=return_actions,
            max_content_length=max_content_length,
            communication_display=communication_display,
        )

    @transactional()
    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def see_and_act(
        self,
        images=None,
        description=None,
        return_actions=False,
        max_content_length=None,
    ):
        """
        Convenience method that combines the `see` and `act` methods.
        """

        self.see(images=images, description=description, max_content_length=max_content_length)
        return self.act(
            return_actions=return_actions, max_content_length=max_content_length
        )

    @transactional()
    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def think_and_act(
        self,
        thought,
        return_actions=False,
        max_content_length=None,
    ):
        """
        Convenience method that combines the `think` and `act` methods.
        """

        self.think(thought, max_content_length=max_content_length)
        return self.act(
            return_actions=return_actions, max_content_length=max_content_length
        )

    def read_documents_from_folder(self, documents_path: str):
        """
        Reads documents from a directory and loads them into the semantic memory.
        """
        logger.info(
            f"Setting documents path to {documents_path} and loading documents."
        )

        self.semantic_memory.add_documents_path(documents_path)

    def read_document_from_file(self, file_path: str):
        """
        Reads a document from a file and loads it into the semantic memory.
        """
        logger.info(f"Reading document from file: {file_path}")

        self.semantic_memory.add_document_path(file_path)

    def read_documents_from_web(self, web_urls: list):
        """
        Reads documents from web URLs and loads them into the semantic memory.
        """
        logger.info(f"Reading documents from the following web URLs: {web_urls}")

        self.semantic_memory.add_web_urls(web_urls)

    def read_document_from_web(self, web_url: str):
        """
        Reads a document from a web URL and loads it into the semantic memory.
        """
        logger.info(f"Reading document from web URL: {web_url}")

        self.semantic_memory.add_web_url(web_url)

    @transactional()
    def move_to(self, location, context=[]):
        """
        Moves to a new location and updates its internal cognitive state.
        """
        self._mental_state["location"] = location

        # context must also be updated when moved, since we assume that context is dictated partly by location.
        self.change_context(context)

    @transactional()
    def change_context(self, context: list):
        """
        Changes the context and updates its internal cognitive state.
        """
        self._mental_state["context"] = {"description": item for item in context}

        self._update_cognitive_state(context=context)

    @transactional()
    def make_agent_accessible(
        self,
        agent: Self,
        relation_description: str = "An agent I can currently interact with.",
    ):
        """
        Makes an agent accessible to this agent.
        """
        if agent not in self._accessible_agents:
            self._accessible_agents.append(agent)
            self._mental_state["accessible_agents"].append(
                {"name": agent.name, "relation_description": relation_description}
            )
        else:
            logger.warning(
                f"[{self.name}] Agent {agent.name} is already accessible to {self.name}."
            )

    @transactional()
    def make_agents_accessible(
        self,
        agents: list,
        relation_description: str = "An agent I can currently interact with.",
    ):
        """
        Makes a list of agents accessible to this agent.
        """
        for agent in agents:
            self.make_agent_accessible(agent, relation_description)

    @transactional()
    def make_agent_inaccessible(self, agent: Self):
        """
        Makes an agent inaccessible to this agent.
        """
        if agent in self._accessible_agents:
            self._accessible_agents.remove(agent)
        else:
            logger.warning(
                f"[{self.name}] Agent {agent.name} is already inaccessible to {self.name}."
            )

    @transactional()
    def make_all_agents_inaccessible(self):
        """
        Makes all agents inaccessible to this agent.
        """
        self._accessible_agents = []
        self._mental_state["accessible_agents"] = []

    @property
    def accessible_agents(self):
        """
        Property to access the list of accessible agents.
        """
        return self._accessible_agents

    ###########################################################
    # Internal cognitive state changes
    ###########################################################
    @transactional()
    def _update_cognitive_state(
        self, goals=None, context=None, attention=None, emotions=None
    ):
        """
        Update the TinyPerson's cognitive state.
        """

        # Update current datetime. The passage of time is controlled by the environment, if any.
        if (
            self.environment is not None
            and self.environment.current_datetime is not None
        ):
            self._mental_state["datetime"] = utils.pretty_datetime(
                self.environment.current_datetime
            )

        # update current goals
        if goals is not None:
            self._mental_state["goals"] = goals

        # update current context
        if context is not None:
            self._mental_state["context"] = context

        # update current attention
        if attention is not None:
            self._mental_state["attention"] = attention

        # update current emotions
        if emotions is not None:
            self._mental_state["emotions"] = emotions

        # update relevant memories for the current situation. These are memories that come to mind "spontaneously" when the agent is in a given context,
        # so avoiding the need to actively trying to remember them.
        current_working_semantic_memory = (
            self.retrieve_relevant_memories_for_current_context()
        )
        self._mental_state["working_semantic_memory"] = current_working_semantic_memory

        self.reset_prompt()

    ###########################################################
    # Memory management
    ###########################################################

    def store_in_memory(self, value: Any) -> None:
        """
        Stores a value in episodic memory and manages episode length.

        Args:
            value: The memory item to store (e.g., action, stimulus, thought)

        Returns:
            None
        """
        self.episodic_memory.store(value)

        self._current_episode_event_count += 1
        logger.debug(
            f"[{self.name}] Current episode event count: {self._current_episode_event_count}."
        )

        if self._current_episode_event_count >= self.MAX_EPISODE_LENGTH:
            # commit the current episode to memory, if it is long enough
            logger.warning(
                f"[{self.name}] Episode length exceeded {self.MAX_EPISODE_LENGTH} events. Committing episode to memory. Please check whether this was expected or not."
            )
            self.consolidate_episode_memories()

    def consolidate_episode_memories(self) -> bool:
        """
        Applies all memory consolidation or transformation processes appropriate to the conclusion of one simulation episode.

        Returns:
            bool: True if memories were successfully consolidated, False otherwise.
        """
        # a minimum length of the episode is required to consolidate it, to avoid excessive fragments in the semantic memory
        if self._current_episode_event_count > self.MIN_EPISODE_LENGTH:
            logger.debug(
                f"[{self.name}] ***** Consolidating current episode memories into semantic memory *****"
            )

            # Consolidate latest episodic memories into semantic memory
            if config_manager.get("enable_memory_consolidation"):

                # Extract and store any image descriptions found in the episode
                # as ``image_description`` engrams in semantic memory. This is
                # the deferred counterpart of what used to be an eager store in
                # see(); doing it here keeps the semantic-memory formation path
                # uniform across all stimulus types.
                episode_for_images = self.episodic_memory.get_current_episode(
                    item_types=["stimulus"],
                )
                self._extract_and_store_image_descriptions_from_episode(episode_for_images)

                episodic_consolidator = EpisodicConsolidator()
                episode = self.episodic_memory.get_current_episode(
                    item_types=["action", "stimulus"],
                )
                logger.debug(f"[{self.name}] Current episode: {episode}")
                consolidated_memories = episodic_consolidator.process(
                    episode,
                    timestamp=self._mental_state["datetime"],
                    context=self._mental_state,
                    persona=self.minibio(),
                ).get("consolidation", None)
                if consolidated_memories is not None:
                    logger.info(
                        f"[{self.name}] Consolidating current {len(episode)} episodic events as consolidated semantic memories."
                    )
                    logger.debug(
                        f"[{self.name}] Consolidated memories: {consolidated_memories}"
                    )
                    self.semantic_memory.store_all(consolidated_memories)
                else:
                    logger.warning(
                        f"[{self.name}] No memories to consolidate from the current episode."
                    )

            else:
                logger.warning(
                    f"[{self.name}] Memory consolidation is disabled. Not consolidating current episode memories into semantic memory."
                )

            # commit the current episode to episodic memory
            self.episodic_memory.commit_episode()
            self._current_episode_event_count = 0
            logger.debug(
                f"[{self.name}] Current episode event count reset to 0 after consolidation."
            )

            # TODO reflections, optimizations, etc.

    def _extract_and_store_image_descriptions_from_episode(self, episode: list) -> None:
        """
        Scan an episode for stimulus messages that carry an ``image_description``
        field and store each as an ``image_description`` engram in semantic memory.

        This is the deferred path for image semantic memory formation: ``see()``
        attaches the LLM-generated description to the stimulus dict, and this
        method harvests those descriptions during consolidation so that the
        semantic-memory formation pipeline remains uniform across all stimulus
        types (cf. levels-of-processing framework — Craik & Lockhart, 1972).

        If ``image_refs`` are present they are included in the engram content so
        that the original file paths / URLs remain discoverable.

        Args:
            episode: A list of episodic memory items (as returned by
                ``episodic_memory.get_current_episode``).
        """
        for mem in episode:
            content = mem.get("content")
            if not isinstance(content, dict):
                continue
            for stim in content.get("stimuli", []):
                desc = stim.get("image_description")
                if not desc:
                    continue

                # Build a combined content string that includes the image refs
                refs = stim.get("image_refs", {})
                if refs:
                    refs_note = ", ".join(
                        f"{iid}: {path}" for iid, path in refs.items()
                    )
                    combined = f"{desc}\n\nImage sources: {refs_note}"
                else:
                    combined = desc

                self.semantic_memory.store({
                    "content": combined,
                    "type": "image_description",
                    "simulation_timestamp": mem.get("simulation_timestamp", self.iso_datetime()),
                })

    def optimize_memory(self):
        pass  # TODO

    def clear_episodic_memory(self, max_prefix_to_clear=None, max_suffix_to_clear=None):
        """
        Clears the episodic memory, causing a permanent "episodic amnesia". Note that this does not
        change other memories, such as semantic memory.
        """
        self.episodic_memory.clear(
            max_prefix_to_clear=max_prefix_to_clear,
            max_suffix_to_clear=max_suffix_to_clear,
        )

    def retrieve_memories(
        self,
        first_n: int,
        last_n: int,
        include_omission_info: bool = True,
        max_content_length: int = None,
    ) -> list:
        episodes = self.episodic_memory.retrieve(
            first_n=first_n, last_n=last_n, include_omission_info=include_omission_info
        )

        if max_content_length is not None:
            episodes = utils.truncate_actions_or_stimuli(episodes, max_content_length)

        return episodes

    def retrieve_recent_memories(self, max_content_length: int = None) -> list:
        episodes = self.episodic_memory.retrieve_recent()

        if max_content_length is not None:
            episodes = utils.truncate_actions_or_stimuli(episodes, max_content_length)

        return episodes

    def retrieve_relevant_memories(self, relevance_target: str, top_k=20) -> list:
        relevant = self.semantic_memory.retrieve_relevant(relevance_target, top_k=top_k)

        return relevant

    def retrieve_relevant_memories_for_current_context(self, top_k=7) -> list:
        """
        Retrieves memories relevant to the current context by combining current state with recent memories.

        Args:
            top_k (int): Number of top relevant memories to retrieve. Defaults to 7.

        Returns:
            list: List of relevant memories for the current context.
        """
        # Check if continuous contextual semantic memory retrieval is enabled
        if not config_manager.get(
            "enable_continuous_contextual_semantic_memory_retrieval"
        ):
            return []

        # Extract current mental state components
        context = self._mental_state.get("context", "")
        goals = self._mental_state.get("goals", "")
        attention = self._mental_state.get("attention", "")
        emotions = self._mental_state.get("emotions", "")

        # Retrieve recent memories efficiently
        recent_memories_list = self.retrieve_memories(
            first_n=10, last_n=20, max_content_length=500
        )
        recent_memories = "\n".join(
            [f"  - {m.get('content', '')}" for m in recent_memories_list]
        )

        # Build contextual target for memory retrieval using textwrap.dedent for cleaner formatting
        target = textwrap.dedent(
            f"""
        Current Context: {context}
        Current Goals: {goals}
        Current Attention: {attention}
        Current Emotions: {emotions}
        Selected Episodic Memories (from oldest to newest):
        {recent_memories}
        """
        ).strip()

        logger.debug(
            f"[{self.name}] Retrieving relevant memories for contextual target: {target}"
        )

        return self.retrieve_relevant_memories(target, top_k=top_k)

    def summarize_relevant_memories_via_full_scan(
        self, relevance_target: str, item_type: str = None
    ) -> str:
        """
        Summarizes relevant memories for a given target by scanning the entire semantic memory.

        Args:
            relevance_target (str): The target to retrieve relevant memories for.
            item_type (str, optional): The type of items to summarize. Defaults to None.
            max_summary_length (int, optional): The maximum length of the summary. Defaults to 1000.

        Returns:
            str: The summary of relevant memories.
        """
        return self.semantic_memory.summarize_relevant_via_full_scan(
            relevance_target, item_type=item_type
        )

    ###########################################################
    # Inspection conveniences
    ###########################################################

    def last_remembered_action(self, ignore_done: bool = True):
        """
        Returns the last remembered action.

        Args:
            ignore_done (bool): Whether to ignore the "DONE" action or not. Defaults to True.

        Returns:
            dict or None: The last remembered action, or None if no suitable action found.
        """
        action = None

        memory_items_list = self.episodic_memory.retrieve_last(
            include_omission_info=False, item_type="action"
        )

        if len(memory_items_list) > 0:
            # iterate from last to first while the action type is not "DONE"
            for candidate_item in memory_items_list[::-1]:
                action_content = candidate_item.get("content", {}).get("action", {})
                action_type = action_content.get("type", "")

                if not ignore_done or action_type != "DONE":
                    action = action_content
                    break

        return action

    ###########################################################
    # Communication display and action execution
    ###########################################################

    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def _display_communication(
        self, role, content, kind, simplified=True, max_content_length=None
    ):
        """
        Displays the current communication and stores it in a buffer for later use.
        """
        # CONCURRENT PROTECTION, as we'll access shared display buffers
        with concurrent_agent_action_lock:
            if kind == "stimuli":
                rendering = self._pretty_stimuli(
                    role=role,
                    content=content,
                    simplified=simplified,
                    max_content_length=max_content_length,
                )
                source = content["stimuli"][0].get("source", None)
                target = self.name

            elif kind == "action":
                rendering = self._pretty_action(
                    role=role,
                    content=content,
                    simplified=simplified,
                    max_content_length=max_content_length,
                )
                source = self.name
                target = content["action"].get("target", None)

            else:
                raise ValueError(f"Unknown communication kind: {kind}")

            # if the agent has no parent environment, then it is a free agent and we can display the communication.
            # otherwise, the environment will display the communication instead. This is important to make sure that
            # the communication is displayed in the correct order, since environments control the flow of their underlying
            # agents.
            if self.environment is None:
                self._push_and_display_latest_communication(
                    {
                        "kind": kind,
                        "rendering": rendering,
                        "content": content,
                        "source": source,
                        "target": target,
                    }
                )
            else:
                self.environment._push_and_display_latest_communication(
                    {
                        "kind": kind,
                        "rendering": rendering,
                        "content": content,
                        "source": source,
                        "target": target,
                    }
                )

    def _push_and_display_latest_communication(self, communication):
        """
        Pushes the latest communications to the agent's buffer.
        """
        self._displayed_communications_buffer.append(communication)
        print(communication["rendering"])

    def pop_and_display_latest_communications(self):
        """
        Pops the latest communications and displays them.
        """
        communications = self._displayed_communications_buffer
        self._displayed_communications_buffer = []

        for communication in communications:
            print(communication["rendering"])

        return communications

    def clear_communications_buffer(self):
        """
        Cleans the communications buffer.
        """
        self._displayed_communications_buffer = []

    @transactional()
    def pop_latest_actions(self) -> list:
        """
        Returns the latest actions performed by this agent. Typically used
        by an environment to consume the actions and provide the appropriate
        environmental semantics to them (i.e., effects on other agents).
        """
        actions = self._actions_buffer
        self._actions_buffer = []
        return actions

    @transactional()
    def pop_actions_and_get_contents_for(
        self, action_type: str, only_last_action: bool = True
    ) -> list:
        """
        Returns the contents of actions of a given type performed by this agent.
        Typically used to perform inspections and tests.

        Args:
            action_type (str): The type of action to look for.
            only_last_action (bool, optional): Whether to only return the contents of the last action. Defaults to False.
        """
        actions = self.pop_latest_actions()
        # Filter the actions by type
        actions = [action for action in actions if action["type"] == action_type]

        # If interested only in the last action, return the latest one
        if only_last_action:
            return actions[-1].get("content", "")

        # Otherwise, return all contents from the filtered actions
        return "\n".join([action.get("content", "") for action in actions])

    #############################################################################################
    # Formatting conveniences
    #
    # For rich colors,
    #    see: https://rich.readthedocs.io/en/latest/appendix/colors.html#appendix-colors
    #############################################################################################

    def __repr__(self):
        return f"TinyPerson(name='{self.name}')"

    @transactional()
    def minibio(self, extended=True, requirements=None):
        """
        Returns a mini-biography of the TinyPerson.

        Args:
            extended (bool): Whether to include extended information or not.
            requirements (str): Additional requirements for the biography (e.g., focus on a specific aspect relevant for the scenario).

        Returns:
            str: The mini-biography.
        """

        # if occupation is a dict and has a "title" key, use that as the occupation
        if (
            isinstance(self._persona["occupation"], dict)
            and "title" in self._persona["occupation"]
        ):
            occupation = self._persona["occupation"]["title"]
        else:
            occupation = self._persona["occupation"]

        residence = self.get("residence") or "an unspecified location"
        base_biography = f"{self.name} is a {self._persona['age']} year old {occupation}, {self._persona['nationality']}, currently living in {residence}."

        if self._extended_agent_summary is None and extended:
            logger.debug(f"Generating extended agent summary for {self.name}.")
            self._extended_agent_summary = LLMChat(
                system_prompt=f"""
                                                You are given a short biography of an agent, as well as a detailed specification of his or her other characteristics
                                                You must then produce a short paragraph (3 or 4 sentences) that **complements** the short biography, adding details about
                                                personality, interests, opinions, skills, etc. Do not repeat the information already given in the short biography.
                                                repeating the information already given. The paragraph should be coherent, consistent and comprehensive. All information
                                                must be grounded on the specification, **do not** create anything new.

                                                {"Additional constraints: "+ requirements if requirements is not None else ""}
                                                """,
                user_prompt=f"""
                                                **Short biography:** {base_biography}

                                                **Detailed specification:** {self._persona}
                                                """,
            ).call()

        if extended:
            biography = f"{base_biography} {self._extended_agent_summary}"
        else:
            biography = base_biography

        return biography

    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def pp_current_interactions(
        self,
        simplified=True,
        skip_system=True,
        max_content_length=None,
        first_n=None,
        last_n=None,
        include_omission_info: bool = True,
    ):
        """
        Pretty prints the current messages.
        """
        print(
            self.pretty_current_interactions(
                simplified=simplified,
                skip_system=skip_system,
                max_content_length=max_content_length,
                first_n=first_n,
                last_n=last_n,
                include_omission_info=include_omission_info,
            )
        )

    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def pp_last_interactions(
        self,
        n=3,
        simplified=True,
        skip_system=True,
        max_content_length=None,
        include_omission_info: bool = True,
    ):
        """
        Pretty prints the last n messages. Useful to examine the conclusion of an experiment.
        """
        print(
            self.pretty_current_interactions(
                simplified=simplified,
                skip_system=skip_system,
                max_content_length=max_content_length,
                first_n=None,
                last_n=n,
                include_omission_info=include_omission_info,
            )
        )

    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def pretty_current_interactions(
        self,
        simplified=True,
        skip_system=True,
        max_content_length=None,
        first_n=None,
        last_n=None,
        include_omission_info: bool = True,
    ):
        """
        Returns a pretty, readable, string with the current messages.
        """
        lines = [f"**** BEGIN SIMULATION TRAJECTORY FOR {self.name} ****"]
        last_step = 0
        for i, message in enumerate(
            self.episodic_memory.retrieve(
                first_n=first_n,
                last_n=last_n,
                include_omission_info=include_omission_info,
            )
        ):
            try:
                if not (skip_system and message["role"] == "system"):
                    msg_simplified_type = ""
                    msg_simplified_content = ""
                    msg_simplified_actor = ""

                    last_step = i
                    lines.append(f"Agent simulation trajectory event #{i}:")
                    lines.append(
                        self._pretty_timestamp(
                            message["role"], message["simulation_timestamp"]
                        )
                    )

                    if message["role"] == "system":
                        msg_simplified_actor = "SYSTEM"
                        msg_simplified_type = message["role"]
                        msg_simplified_content = message["content"]

                        lines.append(
                            f"[dim] {msg_simplified_type}: {msg_simplified_content}[/]"
                        )

                    elif message["role"] == "user":
                        lines.append(
                            self._pretty_stimuli(
                                role=message["role"],
                                content=message["content"],
                                simplified=simplified,
                                max_content_length=max_content_length,
                            )
                        )

                    elif message["role"] == "assistant":
                        lines.append(
                            self._pretty_action(
                                role=message["role"],
                                content=message["content"],
                                simplified=simplified,
                                max_content_length=max_content_length,
                            )
                        )
                    else:
                        lines.append(f"{message['role']}: {message['content']}")
            except:
                # print(f"ERROR: {message}")
                continue

        lines.append(
            f"The last agent simulation trajectory event number was {last_step}, thus the current number of the NEXT POTENTIAL TRAJECTORY EVENT is {last_step + 1}."
        )
        lines.append(f"**** END SIMULATION TRAJECTORY FOR {self.name} ****\n\n")
        return "\n".join(lines)

    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def _pretty_stimuli(
        self,
        role,
        content,
        simplified=True,
        max_content_length=None,
    ) -> list:
        """
        Pretty prints stimuli.
        """

        lines = []
        msg_simplified_actor = "USER"
        for stimus in content["stimuli"]:
            if simplified:
                if stimus["source"] != "":
                    msg_simplified_actor = stimus["source"]

                else:
                    msg_simplified_actor = "USER"

                msg_simplified_type = stimus["type"]
                msg_simplified_content = utils.break_text_at_length(
                    stimus["content"], max_length=max_content_length
                )

                # Append image ID note if present
                image_ids = stimus.get("images")
                if image_ids:
                    ids_str = ", ".join(image_ids)
                    msg_simplified_content += f"\n[+ {len(image_ids)} image(s): {ids_str}]"

                indent = " " * len(msg_simplified_actor) + "      > "
                msg_simplified_content = textwrap.fill(
                    msg_simplified_content,
                    width=TinyPerson.PP_TEXT_WIDTH,
                    initial_indent=indent,
                    subsequent_indent=indent,
                )

                #
                # Using rich for formatting. Let's make things as readable as possible!
                #

                rich_style = utils.RichTextStyle.get_style_for(
                    "stimulus", msg_simplified_type
                )
                lines.append(
                    f"[{rich_style}][underline]{msg_simplified_actor}[/] --> [{rich_style}][underline]{self.name}[/]: [{msg_simplified_type}] \n{msg_simplified_content}[/]"
                )
            else:
                lines.append(f"{role}: {content}")

        return "\n".join(lines)

    @config_manager.config_defaults(max_content_length="max_content_display_length")
    def _pretty_action(
        self,
        role,
        content,
        simplified=True,
        max_content_length=None,
    ) -> str:
        """
        Pretty prints an action.
        """
        if simplified:
            msg_simplified_actor = self.name
            msg_simplified_type = content["action"]["type"]
            msg_simplified_content = utils.break_text_at_length(
                content["action"].get("content", ""), max_length=max_content_length
            )

            # Append image ID note for SHOW actions
            action_images = content["action"].get("images")
            if action_images:
                ids_str = ", ".join(action_images)
                msg_simplified_content += f"\n[images: {ids_str}]"

            indent = " " * len(msg_simplified_actor) + "      > "
            msg_simplified_content = textwrap.fill(
                msg_simplified_content,
                width=TinyPerson.PP_TEXT_WIDTH,
                initial_indent=indent,
                subsequent_indent=indent,
            )

            #
            # Using rich for formatting. Let's make things as readable as possible!
            #
            rich_style = utils.RichTextStyle.get_style_for(
                "action", msg_simplified_type
            )
            return f"[{rich_style}][underline]{msg_simplified_actor}[/] acts: [{msg_simplified_type}] \n{msg_simplified_content}[/]"

        else:
            return f"{role}: {content}"

    def _pretty_timestamp(
        self,
        role,
        timestamp,
    ) -> str:
        """
        Pretty prints a timestamp.
        """
        return f">>>>>>>>> Date and time of events: {timestamp}"

    def iso_datetime(self) -> str:
        """
        Returns the current datetime of the environment, if any.

        Returns:
            datetime: The current datetime of the environment in ISO forat.
        """
        if (
            self.environment is not None
            and self.environment.current_datetime is not None
        ):
            return self.environment.current_datetime.isoformat()
        else:
            return None

    ###########################################################
    # IO
    ###########################################################

    def save_specification(
        self,
        path,
        include_mental_faculties=True,
        include_memory=False,
        include_mental_state=False,
    ):
        """
        Saves the current configuration to a JSON file.
        """

        suppress_attributes = []

        # should we include the mental faculties?
        if not include_mental_faculties:
            suppress_attributes.append("_mental_faculties")

        # should we include the memory?
        if not include_memory:
            suppress_attributes.append("episodic_memory")
            suppress_attributes.append("semantic_memory")

        # should we include the mental state?
        if not include_mental_state:
            suppress_attributes.append("_mental_state")

        self.to_json(
            suppress=suppress_attributes,
            file_path=path,
            serialization_type_field_name="type",
        )

    @staticmethod
    def load_specification(
        path_or_dict,
        suppress_mental_faculties=False,
        suppress_memory=False,
        suppress_mental_state=False,
        auto_rename_agent=False,
        new_agent_name=None,
    ):
        """
        Loads a JSON agent specification.

        Args:
            path_or_dict (str or dict): The path to the JSON file or the dictionary itself.
            suppress_mental_faculties (bool, optional): Whether to suppress loading the mental faculties. Defaults to False.
            suppress_memory (bool, optional): Whether to suppress loading the memory. Defaults to False.
            suppress_memory (bool, optional): Whether to suppress loading the memory. Defaults to False.
            suppress_mental_state (bool, optional): Whether to suppress loading the mental state. Defaults to False.
            auto_rename_agent (bool, optional): Whether to auto rename the agent. Defaults to False.
            new_agent_name (str, optional): The new name for the agent. Defaults to None.
        """

        suppress_attributes = []

        # should we suppress the mental faculties?
        if suppress_mental_faculties:
            suppress_attributes.append("_mental_faculties")

        # should we suppress the memory?
        if suppress_memory:
            suppress_attributes.append("episodic_memory")
            suppress_attributes.append("semantic_memory")

        # should we suppress the mental state?
        if suppress_mental_state:
            suppress_attributes.append("_mental_state")

        return TinyPerson.from_json(
            json_dict_or_path=path_or_dict,
            suppress=suppress_attributes,
            serialization_type_field_name="type",
            post_init_params={
                "auto_rename_agent": auto_rename_agent,
                "new_agent_name": new_agent_name,
            },
        )

    @staticmethod
    def load_specifications_from_folder(
        folder_path: str,
        file_suffix=".agent.json",
        suppress_mental_faculties=False,
        suppress_memory=False,
        suppress_mental_state=False,
        auto_rename_agent=False,
        new_agent_name=None,
    ) -> list:
        """
        Loads all JSON agent specifications from a folder.

        Args:
            folder_path (str): The path to the folder containing the JSON files.
            file_suffix (str, optional): The suffix of the JSON files. Defaults to ".agent.json".
            suppress_mental_faculties (bool, optional): Whether to suppress loading the mental faculties. Defaults to False.
            suppress_memory (bool, optional): Whether to suppress loading the memory. Defaults to False.
            suppress_mental_state (bool, optional): Whether to suppress loading the mental state. Defaults to False.
            auto_rename_agent (bool, optional): Whether to auto rename the agent. Defaults to False.
            new_agent_name (str, optional): The new name for the agent. Defaults to None.
        """

        agents = []
        for file in os.listdir(folder_path):
            if file.endswith(file_suffix):
                file_path = os.path.join(folder_path, file)
                agent = TinyPerson.load_specification(
                    file_path,
                    suppress_mental_faculties=suppress_mental_faculties,
                    suppress_memory=suppress_memory,
                    suppress_mental_state=suppress_mental_state,
                    auto_rename_agent=auto_rename_agent,
                    new_agent_name=new_agent_name,
                )
                agents.append(agent)

        return agents

    def encode_complete_state(self) -> dict:
        """
        Encodes the complete state of the TinyPerson, including the current messages, accessible agents, etc.
        This is meant for serialization and caching purposes, not for exporting the state to the user.
        """
        to_copy = copy.copy(self.__dict__)

        # delete the logger and other attributes that cannot be serialized
        del to_copy["environment"]
        del to_copy["_mental_faculties"]
        del to_copy["action_generator"]

        to_copy["_accessible_agents"] = [
            agent.name for agent in self._accessible_agents
        ]
        to_copy["episodic_memory"] = self.episodic_memory.to_json()
        to_copy["semantic_memory"] = self.semantic_memory.to_json()
        to_copy["_mental_faculties"] = [
            faculty.to_json() for faculty in self._mental_faculties
        ]

        state = copy.deepcopy(to_copy)

        return state

    def decode_complete_state(self, state: dict) -> Self:
        """
        Loads the complete state of the TinyPerson, including the current messages,
        and produces a new TinyPerson instance.
        """
        state = copy.deepcopy(state)

        self._accessible_agents = [
            TinyPerson.get_agent_by_name(name) for name in state["_accessible_agents"]
        ]
        self.episodic_memory = EpisodicMemory.from_json(state["episodic_memory"])
        self.semantic_memory = SemanticMemory.from_json(state["semantic_memory"])

        for i, faculty in enumerate(self._mental_faculties):
            faculty = faculty.from_json(state["_mental_faculties"][i])

        # delete fields already present in the state
        del state["_accessible_agents"]
        del state["episodic_memory"]
        del state["semantic_memory"]
        del state["_mental_faculties"]

        # restore other fields
        self.__dict__.update(state)

        return self

    def create_new_agent_from_current_spec(self, new_name: str) -> Self:
        """
        Creates a new agent from the current agent's specification.

        Args:
            new_name (str): The name of the new agent. Agent names must be unique in the simulation,
              this is why we need to provide a new name.
        """
        new_agent = TinyPerson(name=new_name, spec_path=None)

        new_persona = copy.deepcopy(self._persona)
        new_persona["name"] = new_name

        new_agent._persona = new_persona

        return new_agent

    @staticmethod
    def add_agent(agent):
        """
        Adds an agent to the global list of agents. Agent names must be unique,
        so this method will raise an exception if the name is already in use.
        """
        if agent.name in TinyPerson.all_agents:
            raise ValueError(f"Agent name {agent.name} is already in use.")
        else:
            TinyPerson.all_agents[agent.name] = agent

    @staticmethod
    def has_agent(agent_name: str):
        """
        Checks if an agent is already registered.
        """
        return agent_name in TinyPerson.all_agents

    @staticmethod
    def set_simulation_for_free_agents(simulation):
        """
        Sets the simulation if it is None. This allows free agents to be captured by specific simulation scopes
        if desired.
        """
        for agent in TinyPerson.all_agents.values():
            if agent.simulation_id is None:
                simulation.add_agent(agent)

    @staticmethod
    def get_agent_by_name(name):
        """
        Gets an agent by name.
        """
        if name in TinyPerson.all_agents:
            return TinyPerson.all_agents[name]
        else:
            return None

    @staticmethod
    def all_agents_names():
        """
        Returns the names of all agents.
        """
        return list(TinyPerson.all_agents.keys())

    @staticmethod
    def clear_agents():
        """
        Clears the global list of agents.
        """
        TinyPerson.all_agents = {}

    #######################################################################
    # Cost statistics methods
    #######################################################################

    @staticmethod
    def get_global_cost_stats():
        """
        Gets global cost statistics for all agents based on the current OpenAI client stats.

        Returns:
            dict: A dictionary containing:
                - base_stats: Raw stats from the OpenAI client
                - total_agents: Total number of agents
                - per_agent: Average resources per agent
        """
        from tinytroupe.clients import client

        base_stats = client().get_cost_stats()
        num_agents = len(TinyPerson.all_agents)

        result = {"base_stats": base_stats, "total_agents": num_agents}

        # Per-agent statistics
        if num_agents > 0:
            result["per_agent"] = {
                "input_tokens": base_stats["input_tokens"] / num_agents,
                "output_tokens": base_stats["output_tokens"] / num_agents,
                "total_tokens": base_stats["total_tokens"] / num_agents,
                "model_calls": base_stats["model_calls"] / num_agents,
                "cached_calls": base_stats["cached_calls"] / num_agents,
            }
        else:
            result["per_agent"] = None

        return result

    @staticmethod
    def pretty_print_global_cost_stats():
        """
        Pretty prints global cost statistics for all agents.
        """
        stats = TinyPerson.get_global_cost_stats()

        print("\n" + "=" * 70)
        print("GLOBAL COST STATISTICS (ALL AGENTS)")
        print("=" * 70)

        print(f"\nGlobal Context:")
        print(f"  Total agents:     {stats['total_agents']}")

        base = stats["base_stats"]
        print(f"\nTotal Resources Used:")
        print(f"  Input tokens:     {base['input_tokens']:,}")
        print(f"  Output tokens:    {base['output_tokens']:,}")
        print(f"  Total tokens:     {base['total_tokens']:,}")
        print(f"  Model calls:      {base['model_calls']:,}")
        print(f"  Cached calls:     {base['cached_calls']:,}")

        if stats["per_agent"] is not None:
            pa = stats["per_agent"]
            print(f"\nAverage Per Agent:")
            print(f"  Input tokens:     {pa['input_tokens']:,.1f}")
            print(f"  Output tokens:    {pa['output_tokens']:,.1f}")
            print(f"  Total tokens:     {pa['total_tokens']:,.1f}")
            print(f"  Model calls:      {pa['model_calls']:,.1f}")
            print(f"  Cached calls:     {pa['cached_calls']:,.1f}")

        print("=" * 70 + "\n")
