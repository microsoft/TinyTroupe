import pytest
import os
import json
import random

import logging
logger = logging.getLogger("tinytroupe")

import sys
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

from testing_utils import *
from tinytroupe.extraction import ArtifactExporter, Normalizer
from tinytroupe import utils

@pytest.fixture
def exporter():
    return ArtifactExporter(base_output_folder=EXPORT_BASE_FOLDER)

def test_export_json(exporter):
    # Define the artifact data
    artifact_data = {
        "name": "John Doe",
        "age": 30,
        "occupation": "Engineer",
        "content": "This is a sample JSON data."
    }
    
    # Export the artifact data as JSON
    exporter.export("test_artifact", artifact_data, content_type="record", target_format="json")
    
    #check if the JSON file was exported correctly
    assert os.path.exists(f"{EXPORT_BASE_FOLDER}/record/test_artifact.json"), "The JSON file should have been exported."

    # does it contain the data?
    with open(f"{EXPORT_BASE_FOLDER}/record/test_artifact.json", "r") as f:
        exported_data = json.load(f)
        assert exported_data == artifact_data, "The exported JSON data should match the original data."

def test_export_text(exporter):
    # Define the artifact data
    artifact_data = "This is a sample text."
    
    # Export the artifact data as text
    exporter.export("test_artifact", artifact_data, content_type="text", target_format="txt")
    
    # check if the text file was exported correctly
    assert os.path.exists(f"{EXPORT_BASE_FOLDER}/text/test_artifact.txt"), "The text file should have been exported."

    # does it contain the data?
    with open(f"{EXPORT_BASE_FOLDER}/text/test_artifact.txt", "r") as f:
        exported_data = f.read()
        assert exported_data == artifact_data, "The exported text data should match the original data."

def test_export_docx(exporter):
    # Define the artifact data. Include some fancy markdown formatting so we can test if it is preserved.
    artifact_data =\
    """
    # This is a sample markdown text
    This is a **bold** text.
    This is an *italic* text.
    This is a [link](https://www.example.com).
    """
    
    # Export the artifact data as a docx file
    exporter.export("test_artifact", artifact_data, content_type="Document", content_format="markdown", target_format="docx")
    
    # check if the docx file was exported correctly
    assert os.path.exists(f"{EXPORT_BASE_FOLDER}/Document/test_artifact.docx"), "The docx file should have been exported."

    # does it contain the data?
    from docx import Document
    doc = Document(f"{EXPORT_BASE_FOLDER}/Document/test_artifact.docx")
    exported_data = ""
    for para in doc.paragraphs:
        exported_data += para.text

    assert "This is a sample markdown text" in exported_data, "The exported docx data should contain some of the original content."
    assert "#" not in exported_data, "The exported docx data should not contain Markdown."

    
def test_normalizer():
    # Define the concepts to be normalized
    concepts = ['Antique Book Collection', 'Medical Research', 'Electrical safety', 'Reading', 'Technology', 'Entrepreneurship', 'Multimedia Teaching Tools', 'Photography', 
     'Smart home technology', 'Gardening', 'Travel', 'Outdoors', 'Hiking', 'Yoga', 'Finance', 'Health and wellness', 'Sustainable Living', 'Barista Skills', 'Oral health education',
     'Patient care', 'Professional Development', 'Project safety', 'Coffee', 'Literature', 'Continuous learning', 'Model trains', 'Education', 'Mental and Physical Balance', 'Kayaking',
     'Social Justice', 'National Park Exploration', 'Outdoor activities', 'Dental technology', 'Teaching electrical skills', 'Volunteering', 'Cooking', 'Industry trends', 
     'Energy-efficient systems', 'Mentoring', 'Empathetic communication', 'Medical Technology', 'Historical Research', 'Public Speaking', 'Museum Volunteering', 'Conflict Resolution']
    
    unique_concepts = list(set(concepts))

    normalizer = Normalizer(concepts, n=10, verbose=True)

    assert len(normalizer.normalized_elements) == 10, "The number of normalized elements should be equal to the specified value."

    # sample 5 random elements from concepts using standard python methods
    
    random_concepts_buckets = [random.sample(concepts, 15), random.sample(concepts, 15), random.sample(concepts, 15), random.sample(concepts, 15), random.sample(concepts, 15)]


    assert len(normalizer.normalizing_map.keys()) == 0, "The normalizing map should be empty at the beginning."
    for bucket in random_concepts_buckets:
        init_cache_size = len(normalizer.normalizing_map.keys())
        
        normalized_concept = normalizer.normalize(bucket)
        assert normalized_concept is not None, "The normalized concept should not be None."
        logger.debug(f"Normalized concept: {bucket} -> {normalized_concept}")
        print(f"Normalized concept: {bucket} -> {normalized_concept}")

        # Semantic verification: ensure normalized concepts are semantically related to original concepts
        original_concepts_str = ", ".join(bucket)
        normalized_concepts_str = ", ".join(normalized_concept)
        combined_text = f"Original concepts: {original_concepts_str}\nNormalized concepts: {normalized_concepts_str}"
        assert proposition_holds(combined_text + " - The normalized concepts are semantically related to or categorically similar to the original concepts")

        next_cache_size = len(normalizer.normalizing_map.keys())

        # check same length
        assert len(normalized_concept) == len(bucket), "The normalized concept should have the same length as the input concept."

        # assert that all elements from normalized concepts are in normalizing map keys
        for element in bucket:
            assert element in normalizer.normalizing_map.keys(), f"{element} should be in the normalizing map keys."

        assert next_cache_size > 0, "The cache size should be greater than 0 after normalizing a new concept."
        assert next_cache_size >= init_cache_size, "The cache size should not decrease after normalizing a new concept."
    
    
