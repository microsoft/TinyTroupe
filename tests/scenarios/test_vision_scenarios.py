"""
Scenario tests for the vision modality in TinyTroupe.

These tests exercise the full end-to-end flow of the vision feature:
  - An agent seeing real images and reacting to them.
  - Two agents sharing images via the SHOW action in a TinyWorld.

The scenarios use actual test images of diverse subjects (product photos,
historical photography, art, medical imagery) to validate that the LLM
vision pipeline produces semantically appropriate reactions.

Scientifically, these scenarios exercise the *visual perception → cognition →
action* loop described in Cognitive Psychology: an external visual stimulus is
perceived, a mental representation is formed (here via the LLM description),
and the agent's subsequent behavior reflects the content of that perception
(cf. Marr, 1982; Biederman, 1987).
"""

import pytest
import os
import logging

logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

import tinytroupe
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.examples import (
    create_oscar_the_architect,
    create_lisa_the_data_scientist,
    create_marcos_the_physician,
)
import tinytroupe.control as control
from tinytroupe.control import Simulation

from testing_utils import *


# ---------------------------------------------------------------------------
# Paths to test images
# ---------------------------------------------------------------------------
_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "images")

GAZPACHO_JPG = os.path.join(_IMAGES_DIR, "spanish_bottled_gazpacho.jpg")
GAZPACHO_PNG_1 = os.path.join(_IMAGES_DIR, "spanish_bottled_gazpacho_cleaned-1.png")
ALDRIN_JPG = os.path.join(_IMAGES_DIR, "Aldrin_Looks_Back_at_Tranquility_Base_-_GPN-2000-001102.jpg")
TURNER_JPG = os.path.join(_IMAGES_DIR, "Turner,_J._M._W._-_The_Fighting_Téméraire_tugged_to_her_last_Berth_to_be_broken.jpg")
XRAY_JPG = os.path.join(_IMAGES_DIR, "X-ray_pneumonia.JPG")


class TestVisionScenarios:
    """
    End-to-end scenarios validating that vision perception leads to
    contextually appropriate cognition and action.
    """

    @pytest.mark.core
    def test_agent_sees_product_photo_and_reacts(self):
        """
        Oscar the architect sees a photo of bottled gazpacho. His reaction
        should reflect what he actually sees in the image — a food product,
        packaging design, bottle, etc. This validates the full pipeline:
        image → LLM description → stimulus → action generation.
        """
        control.reset()
        control.begin()

        oscar = create_oscar_the_architect()
        oscar.see(
            images=GAZPACHO_JPG,
            description="A product photograph shown to you for evaluation.",
        )
        actions = oscar.act(return_actions=True)

        assert len(actions) >= 1, "Oscar should produce at least one action after seeing an image."
        assert contains_action_type(actions, "THINK"), \
            "Oscar should THINK after seeing an interesting image."

        # The image is of bottled gazpacho — oscar's thoughts should relate to
        # the visual content (bottle, food, product, design, etc.)
        for action in actions:
            if action["action"]["type"] == "THINK":
                content = action["action"]["content"]
                assert proposition_holds(
                    f"The following text is someone reacting to or thinking about "
                    f"a food product, bottle, packaging, or soup: '{content}'"
                ), f"Oscar should react to the gazpacho image but thought: {content}"
                break

        control.end()

    @pytest.mark.core
    def test_agent_sees_painting_and_reacts(self):
        """
        Oscar the architect sees Turner's 'The Fighting Temeraire'. As an
        architect with artistic sensibility, he should react to the painting's
        visual qualities — light, composition, maritime scene, etc.
        """
        control.reset()
        control.begin()

        oscar = create_oscar_the_architect()
        oscar.see(
            images=TURNER_JPG,
            description="A painting shown to you at an art gallery.",
        )
        actions = oscar.act(return_actions=True)

        assert len(actions) >= 1
        assert contains_action_type(actions, "THINK"), \
            "Oscar should THINK about the painting."

        for action in actions:
            if action["action"]["type"] == "THINK":
                content = action["action"]["content"]
                assert proposition_holds(
                    f"The following text is someone thinking about or reacting to "
                    f"a painting, artwork, or visual art piece: '{content}'"
                ), f"Oscar should react to the painting but thought: {content}"
                break

        control.end()

    @pytest.mark.core
    def test_two_agents_share_image_via_world(self):
        """
        Oscar sees a product photo and then shares it with Lisa via the
        SHOW action in a TinyWorld. Lisa should then react to the image.

        This tests the full social vision loop: perception → action (SHOW) →
        environment dispatch → second agent's perception → reaction.
        """
        control.reset()
        control.begin()

        oscar = create_oscar_the_architect()
        lisa = create_lisa_the_data_scientist()
        world = TinyWorld("Product Review", [oscar, lisa])

        # Oscar sees the image first
        oscar.see(
            images=GAZPACHO_JPG,
            description="A product photo for a new bottled soup. Please show it to Lisa and ask for her opinion.",
        )

        # Let the world run a couple of steps so Oscar can act (and potentially SHOW).
        # Use return_actions=True because world.run() internally pops each
        # agent's action buffer to dispatch environment semantics.
        all_actions = world.run(steps=2, return_actions=True)

        # Verify Oscar produced actions (across any step)
        oscar_actions = []
        for step in all_actions:
            oscar_actions.extend(step.get(oscar.name, []))
        assert len(oscar_actions) >= 1, "Oscar should have acted."

        # Regardless of whether the LLM chose SHOW, manually trigger a SHOW
        # to test the dispatch mechanism deterministically
        show_action = {
            "type": "SHOW",
            "content": "What do you think of this product photo?",
            "target": lisa.name,
            "images": ["img_1"],  # registered by oscar.see()
        }
        world._handle_show(oscar, show_action, lisa.name)

        # Lisa should now have a visual stimulus
        lisa_episodes = lisa.episodic_memory.retrieve_all()
        visual_stimuli = [
            s for ep in lisa_episodes
            if ep["role"] == "user"
            for s in ep.get("content", {}).get("stimuli", [])
            if s["type"] == "VISUAL"
        ]
        assert len(visual_stimuli) >= 1, \
            "Lisa should have received at least one visual stimulus via SHOW."

        control.end()

    def test_agent_sees_multiple_images_and_compares(self):
        """
        Oscar sees two versions of the same product photo and is asked to
        compare them. This tests multi-image input.
        """
        control.reset()
        control.begin()

        oscar = create_oscar_the_architect()
        oscar.see(
            images=[GAZPACHO_JPG, GAZPACHO_PNG_1],
            description="Two versions of a product photo. Please compare them.",
        )
        actions = oscar.act(return_actions=True)

        assert len(actions) >= 1, "Oscar should act after seeing two images."
        # Check that Oscar registered both images
        assert "img_1" in oscar._image_registry
        assert "img_2" in oscar._image_registry

        control.end()

    @pytest.mark.core
    def test_group_discusses_and_reinterprets_image(self):
        """
        A small group (Oscar & Lisa) view the same image and are then asked
        multiple times to reinterpret it from different angles.

        This validates the **image recall** mechanism: after the initial
        ``see()``, subsequent ``listen()`` + ``act()`` turns should still
        have access to the image pixels because
        ``_stimuli_payloads_for_current_turn()`` re-injects recent
        image-bearing stimuli as user messages.

        Scientifically, this exercises the *re-examination* aspect of visual
        working memory (Baddeley, 2003): a previously perceived image can be
        brought back to the focus of attention for further analysis when
        prompted, even after intervening verbal stimuli.
        """
        control.reset()
        control.begin()

        oscar = create_oscar_the_architect()
        lisa = create_lisa_the_data_scientist()

        # --- Round 1: both agents see the painting ---
        oscar.see(
            images=TURNER_JPG,
            description="A painting you are studying in an art critique session.",
        )
        lisa.see(
            images=TURNER_JPG,
            description="A painting you are studying in an art critique session.",
        )

        oscar_r1 = oscar.act(return_actions=True)
        lisa_r1 = lisa.act(return_actions=True)

        assert len(oscar_r1) >= 1, "Oscar should react to the painting."
        assert len(lisa_r1) >= 1, "Lisa should react to the painting."

        # --- Round 2: ask each to reinterpret the same image ---
        # The key test: after this listen(), the latest stimulus is
        # CONVERSATION — but the image should still be re-injected.
        oscar.listen("Now look at the painting again and describe the use of light and color.")
        oscar_r2 = oscar.act(return_actions=True)

        lisa.listen("Now look at the painting again and describe what emotions it evokes.")
        lisa_r2 = lisa.act(return_actions=True)

        assert len(oscar_r2) >= 1, "Oscar should produce a second interpretation."
        assert len(lisa_r2) >= 1, "Lisa should produce a second interpretation."

        # --- Round 3: yet another angle ---
        oscar.listen("Finally, look at it one more time. What architectural elements can you identify in the scene?")
        oscar_r3 = oscar.act(return_actions=True)

        assert len(oscar_r3) >= 1, "Oscar should produce a third interpretation."

        # Verify the image is still in the registry (not lost)
        assert len(oscar._image_registry) >= 1
        assert len(lisa._image_registry) >= 1

        # Verify that the stimulus dict in episodic memory carries image_refs
        # (proving persistence of the original file path)
        all_oscar_eps = oscar.episodic_memory.retrieve_all()
        visual_stimuli_with_refs = [
            s for ep in all_oscar_eps
            if ep.get("role") == "user"
            for s in ep.get("content", {}).get("stimuli", [])
            if s.get("image_refs")
        ]
        assert len(visual_stimuli_with_refs) >= 1, \
            "Oscar's episodic memory should contain at least one stimulus with image_refs."

        # Verify the image_refs point to the actual file path
        first_refs = visual_stimuli_with_refs[0]["image_refs"]
        ref_values = list(first_refs.values())
        assert any(TURNER_JPG in v or os.path.basename(TURNER_JPG) in v for v in ref_values), \
            f"image_refs should contain the Turner painting path, got: {first_refs}"

        control.end()
