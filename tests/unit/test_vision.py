"""
Unit tests for the vision modality in TinyTroupe.

Tests cover:
  - Image utilities (media.py)
  - Image registration and caching in TinyPerson
  - see() with images (backward compatibility and new image path)
  - SHOW action dispatch in TinyWorld
  - Consolidation stripping of image references
"""

import pytest
import os
import logging
import base64
import hashlib

logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.examples import create_oscar_the_architect, create_lisa_the_data_scientist
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.utils.media import (
    normalize_image_to_openai_url,
    build_multimodal_content_array,
    hash_image,
    normalize_image_refs,
    _mime_type_for_image,
)
from tinytroupe.agent.memory import EpisodicConsolidator

from testing_utils import *

# ---------------------------------------------------------------------------
# Paths to test images
# ---------------------------------------------------------------------------
_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "images")

GAZPACHO_JPG = os.path.join(_IMAGES_DIR, "spanish_bottled_gazpacho.jpg")
GAZPACHO_PNG_1 = os.path.join(_IMAGES_DIR, "spanish_bottled_gazpacho_cleaned-1.png")
GAZPACHO_PNG_2 = os.path.join(_IMAGES_DIR, "spanish_bottled_gazpacho_cleaned-2.png")
ALDRIN_JPG = os.path.join(_IMAGES_DIR, "Aldrin_Looks_Back_at_Tranquility_Base_-_GPN-2000-001102.jpg")
TURNER_JPG = os.path.join(_IMAGES_DIR, "Turner,_J._M._W._-_The_Fighting_Téméraire_tugged_to_her_last_Berth_to_be_broken.jpg")
XRAY_JPG = os.path.join(_IMAGES_DIR, "X-ray_pneumonia.JPG")


# ========================== media.py utilities ==============================

class TestMediaUtilities:
    """Tests for tinytroupe.utils.media helper functions."""

    def test_mime_type_for_image(self, setup):
        assert _mime_type_for_image("photo.jpg") == "image/jpeg"
        assert _mime_type_for_image("photo.jpeg") == "image/jpeg"
        assert _mime_type_for_image("photo.png") == "image/png"
        assert _mime_type_for_image("photo.gif") == "image/gif"
        assert _mime_type_for_image("photo.webp") == "image/webp"
        assert _mime_type_for_image("photo.JPG") == "image/jpeg"

    def test_normalize_image_refs_none(self, setup):
        assert normalize_image_refs(None) == []

    def test_normalize_image_refs_string(self, setup):
        assert normalize_image_refs("a.png") == ["a.png"]

    def test_normalize_image_refs_list(self, setup):
        refs = normalize_image_refs(["a.png", "b.png"])
        assert refs == ["a.png", "b.png"]

    def test_normalize_image_to_openai_url_local_file(self, setup):
        url = normalize_image_to_openai_url(GAZPACHO_JPG)
        assert url.startswith("data:image/jpeg;base64,")
        # Decode the base64 part to confirm it round-trips
        b64_part = url.split(",", 1)[1]
        decoded = base64.b64decode(b64_part)
        with open(GAZPACHO_JPG, "rb") as f:
            assert decoded == f.read()

    def test_normalize_image_to_openai_url_already_url(self, setup):
        original = "https://example.com/image.png"
        assert normalize_image_to_openai_url(original) == original

    def test_normalize_image_to_openai_url_data_uri(self, setup):
        original = "data:image/png;base64,abc123"
        assert normalize_image_to_openai_url(original) == original

    def test_build_multimodal_content_array(self, setup):
        arr = build_multimodal_content_array(
            text="Describe this",
            image_refs=[GAZPACHO_JPG],
            detail="low",
        )
        assert len(arr) == 2
        assert arr[0]["type"] == "text"
        assert arr[0]["text"] == "Describe this"
        assert arr[1]["type"] == "image_url"
        assert arr[1]["image_url"]["detail"] == "low"
        assert arr[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")

    def test_build_multimodal_content_array_multiple_images(self, setup):
        arr = build_multimodal_content_array(
            text="Compare",
            image_refs=[GAZPACHO_JPG, GAZPACHO_PNG_1],
            detail="auto",
        )
        assert len(arr) == 3  # 1 text + 2 images

    def test_hash_image_deterministic(self, setup):
        h1 = hash_image(GAZPACHO_JPG)
        h2 = hash_image(GAZPACHO_JPG)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest length

    def test_hash_image_different_files(self, setup):
        h1 = hash_image(GAZPACHO_JPG)
        h2 = hash_image(GAZPACHO_PNG_1)
        assert h1 != h2

    def test_hash_image_url(self, setup):
        h = hash_image("https://example.com/image.png")
        assert len(h) == 64


# ========================== TinyPerson image registry =======================

class TestImageRegistry:
    """Tests for the image registry and description caching in TinyPerson."""

    def test_register_images(self, setup):
        agent = create_oscar_the_architect()
        ids = agent._register_images([GAZPACHO_JPG, GAZPACHO_PNG_1])
        assert ids == ["img_1", "img_2"]
        assert agent._image_registry["img_1"] == GAZPACHO_JPG
        assert agent._image_registry["img_2"] == GAZPACHO_PNG_1
        assert agent._image_id_counter == 2

    def test_register_images_incremental(self, setup):
        agent = create_oscar_the_architect()
        ids1 = agent._register_images([GAZPACHO_JPG])
        ids2 = agent._register_images([GAZPACHO_PNG_1])
        assert ids1 == ["img_1"]
        assert ids2 == ["img_2"]
        assert len(agent._image_registry) == 2

    def test_image_registry_serializable(self, setup):
        """Image registry should survive serialization / deserialization."""
        agent = create_oscar_the_architect()
        agent._register_images([GAZPACHO_JPG])

        # Save specification
        path = get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/serialization/{agent.name}_vision.tinyperson.json")
        agent.save_specification(path, include_memory=True)

        loaded = TinyPerson.load_specification(path, new_agent_name=f"{agent.name}_v_loaded")
        assert loaded._image_registry["img_1"] == GAZPACHO_JPG
        assert loaded._image_id_counter == 1


# ========================== see() with images ===============================

class TestSeeWithImages:
    """Tests for the redesigned see() method with image support."""

    @pytest.mark.core
    def test_see_backward_compat(self, setup):
        """Text-only see() should still work as before (no images)."""
        agent = create_oscar_the_architect()
        agent.see(description="A beautiful sunset over the ocean.")
        last_episode = agent.episodic_memory.retrieve_all()[-1]

        assert last_episode["role"] == "user"
        assert last_episode["content"]["stimuli"][0]["type"] == "VISUAL"
        assert "sunset" in last_episode["content"]["stimuli"][0]["content"].lower()
        # No images key should be set, or it should be empty
        assert not last_episode["content"]["stimuli"][0].get("images")

    @pytest.mark.core
    def test_see_with_single_image(self, setup):
        """see() with a single image should register it and produce a description."""
        agent = create_oscar_the_architect()
        agent.see(images=GAZPACHO_JPG, description="A product photo")
        last_episode = agent.episodic_memory.retrieve_all()[-1]
        stimulus = last_episode["content"]["stimuli"][0]

        assert stimulus["type"] == "VISUAL"
        assert "img_1" in stimulus.get("images", [])
        assert "product photo" in stimulus["content"].lower() or "img_1" in stimulus["content"].lower()
        assert agent._image_registry["img_1"] == GAZPACHO_JPG

    @pytest.mark.core
    def test_see_with_multiple_images(self, setup):
        """see() with multiple images should register all of them."""
        agent = create_oscar_the_architect()
        agent.see(
            images=[GAZPACHO_JPG, GAZPACHO_PNG_1],
            description="Two product photos",
        )
        last_episode = agent.episodic_memory.retrieve_all()[-1]
        stimulus = last_episode["content"]["stimuli"][0]

        assert len(stimulus.get("images", [])) == 2
        assert "img_1" in stimulus["images"]
        assert "img_2" in stimulus["images"]

    @pytest.mark.core
    def test_see_image_description_caching(self, setup):
        """Description for the same image content should be cached across agents."""
        # Clear the class-level cache (use assignment in case no TinyPerson
        # was instantiated yet and the class attribute does not exist)
        TinyPerson._image_description_cache = {}

        agent1 = create_oscar_the_architect()
        agent1.see(images=GAZPACHO_JPG, description="A bottle")

        agent2 = create_lisa_the_data_scientist()
        agent2.see(images=GAZPACHO_JPG, description="A bottle")

        # Cache key is computed by _describe_images as sha256 of the sorted
        # image hashes joined with "|", so for a single image it is the
        # sha256 of the image's own hash string.
        img_hash = hash_image(GAZPACHO_JPG)
        cache_key = hashlib.sha256(img_hash.encode()).hexdigest()
        assert cache_key in TinyPerson._image_description_cache

    def test_see_diverse_images(self, setup):
        """Agent should be able to see diverse image types."""
        agent = create_oscar_the_architect()

        agent.see(images=ALDRIN_JPG, description="A historical photograph")
        assert "img_1" in agent._image_registry

        agent.see(images=TURNER_JPG, description="A painting")
        assert "img_2" in agent._image_registry

        agent.see(images=XRAY_JPG, description="A medical image")
        assert "img_3" in agent._image_registry

        assert len(agent._image_registry) == 3


# ========================== SHOW action in TinyWorld ========================

class TestShowAction:
    """Tests for the SHOW action dispatch in TinyWorld."""

    def test_handle_show_resolves_images(self, setup):
        """_handle_show should resolve image IDs and call see() on the target."""
        oscar = create_oscar_the_architect()
        lisa = create_lisa_the_data_scientist()

        world = TinyWorld("Test world", [oscar, lisa])

        # Pre-register an image on oscar
        oscar._register_images([GAZPACHO_JPG])

        # Simulate a SHOW action from oscar to lisa
        action = {
            "type": "SHOW",
            "content": "Look at this product photo",
            "target": lisa.name,
            "images": ["img_1"],
        }
        world._handle_show(oscar, action, lisa.name)

        # Lisa should now have a visual stimulus with the resolved image
        last_episode = lisa.episodic_memory.retrieve_all()[-1]
        stimulus = last_episode["content"]["stimuli"][0]
        assert stimulus["type"] == "VISUAL"
        assert stimulus.get("source") == oscar.name


# ========================== Consolidation stripping =========================

class TestConsolidationStripping:
    """Tests for stripping image references before consolidation."""

    def test_strip_image_references(self, setup):
        """Image IDs, image_description, and image_refs should be removed from memories before consolidation."""
        memories = [
            {
                "role": "user",
                "content": {
                    "stimuli": [
                        {
                            "type": "VISUAL",
                            "content": "A sunset",
                            "images": ["img_1", "img_2"],
                            "image_description": "A beautiful sunset over water.",
                            "image_refs": {"img_1": "/path/to/sunset1.jpg", "img_2": "/path/to/sunset2.jpg"},
                        },
                        {"type": "CONVERSATION", "content": "Hello"},
                    ]
                },
            },
            {
                "role": "assistant",
                "content": {
                    "action": {"type": "SHOW", "content": "Look at this", "images": ["img_3"]},
                },
            },
        ]

        cleaned = EpisodicConsolidator._strip_image_references(memories)

        # Original should be untouched
        assert "images" in memories[0]["content"]["stimuli"][0]
        assert "image_description" in memories[0]["content"]["stimuli"][0]
        assert "image_refs" in memories[0]["content"]["stimuli"][0]
        assert "images" in memories[1]["content"]["action"]

        # Cleaned should have no image-related keys
        assert "images" not in cleaned[0]["content"]["stimuli"][0]
        assert "image_description" not in cleaned[0]["content"]["stimuli"][0]
        assert "image_refs" not in cleaned[0]["content"]["stimuli"][0]
        assert "images" not in cleaned[1]["content"]["action"]
        # Non-image content preserved
        assert cleaned[0]["content"]["stimuli"][0]["content"] == "A sunset"
        assert cleaned[0]["content"]["stimuli"][1]["content"] == "Hello"
        assert cleaned[1]["content"]["action"]["content"] == "Look at this"


# ========================== Stimulus dict contents ==========================

class TestStimulusDictContents:
    """Tests verifying that the stimulus dict carries image_description and image_refs."""

    @pytest.mark.core
    def test_stimulus_contains_image_description(self, setup):
        """see() with an image should embed image_description in the stimulus."""
        agent = create_oscar_the_architect()
        agent.see(images=GAZPACHO_JPG, description="A product photo")
        last_episode = agent.episodic_memory.retrieve_all()[-1]
        stimulus = last_episode["content"]["stimuli"][0]

        assert "image_description" in stimulus, \
            "Stimulus should contain image_description."
        assert isinstance(stimulus["image_description"], str)
        assert len(stimulus["image_description"]) > 0, \
            "image_description should be non-empty."

    @pytest.mark.core
    def test_stimulus_contains_image_refs(self, setup):
        """see() with images should embed image_refs mapping IDs to file paths."""
        agent = create_oscar_the_architect()
        agent.see(images=[GAZPACHO_JPG, GAZPACHO_PNG_1], description="Two photos")
        last_episode = agent.episodic_memory.retrieve_all()[-1]
        stimulus = last_episode["content"]["stimuli"][0]

        assert "image_refs" in stimulus, "Stimulus should contain image_refs."
        refs = stimulus["image_refs"]
        assert isinstance(refs, dict)
        assert "img_1" in refs
        assert "img_2" in refs
        assert refs["img_1"] == GAZPACHO_JPG
        assert refs["img_2"] == GAZPACHO_PNG_1

    def test_text_only_see_has_no_image_refs(self, setup):
        """Text-only see() should NOT add image_description or image_refs."""
        agent = create_oscar_the_architect()
        agent.see(description="A beautiful sunset over the ocean.")
        last_episode = agent.episodic_memory.retrieve_all()[-1]
        stimulus = last_episode["content"]["stimuli"][0]

        assert "image_refs" not in stimulus
        assert "image_description" not in stimulus


# ========================== Image description extraction ====================

class TestImageDescriptionExtraction:
    """Tests for _extract_and_store_image_descriptions_from_episode."""

    @pytest.mark.core
    def test_no_eager_semantic_store(self, setup):
        """see() should NOT eagerly store image_description in semantic memory.

        Image descriptions are now extracted during consolidation, not at
        perception time.
        """
        agent = create_oscar_the_architect()
        # Record how many semantic memories exist before see()
        before_count = len(agent.semantic_memory.retrieve_all())
        agent.see(images=GAZPACHO_JPG, description="A product photo")
        after_count = len(agent.semantic_memory.retrieve_all())

        assert after_count == before_count, \
            "see() should not eagerly add to semantic memory."

    def test_extract_image_descriptions_basic(self, setup):
        """_extract_and_store_image_descriptions_from_episode should harvest descriptions."""
        agent = create_oscar_the_architect()

        # Simulate an episode with a visual stimulus carrying an image_description
        fake_episode = [
            {
                "role": "user",
                "content": {
                    "stimuli": [
                        {
                            "type": "VISUAL",
                            "content": "A product photo",
                            "images": ["img_1"],
                            "image_description": "A bottle of gazpacho soup on a white background.",
                            "image_refs": {"img_1": "/path/to/gazpacho.jpg"},
                        }
                    ]
                },
                "simulation_timestamp": "2026-01-15 10:00:00",
            }
        ]

        before_count = len(agent.semantic_memory.retrieve_all())
        agent._extract_and_store_image_descriptions_from_episode(fake_episode)
        after_count = len(agent.semantic_memory.retrieve_all())

        assert after_count == before_count + 1, \
            "Should have stored exactly one image_description engram."

    def test_extract_skips_empty_descriptions(self, setup):
        """Stimuli with empty image_description should be skipped."""
        agent = create_oscar_the_architect()

        fake_episode = [
            {
                "role": "user",
                "content": {
                    "stimuli": [
                        {
                            "type": "VISUAL",
                            "content": "Some text",
                            "images": ["img_1"],
                            "image_description": "",
                            "image_refs": {"img_1": "/path/to/img.jpg"},
                        }
                    ]
                },
                "simulation_timestamp": "2026-01-15 10:00:00",
            }
        ]

        before_count = len(agent.semantic_memory.retrieve_all())
        agent._extract_and_store_image_descriptions_from_episode(fake_episode)
        after_count = len(agent.semantic_memory.retrieve_all())

        assert after_count == before_count, \
            "Empty image_description should not be stored."
