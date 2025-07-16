"""
Simulations produce a lot of data, and it is often useful to extract these data in a structured way. For instance, you might wish to:
  - Extract the main points from an agent's interactions history, so that you can consult them later in a concise form.
  - Generate synthetic data from a simulation, so that you can use it for training machine learning models or testing software.
  - Simply turn some of the data into a more machine-readable format, such as JSON or CSV, so that you can analyze it more easily.

This module provides various utilities to help you extract data from TinyTroupe elements, such as agents and worlds. It also provides a 
mechanism to reduce the extracted data to a more concise form, and to export artifacts from TinyTroupe elements. Incidentaly, it showcases 
one of the many ways in which agent simulations differ from AI assistants, as the latter are not designed to be introspected in this way.
"""

import logging
logger = logging.getLogger("tinytroupe")

###########################################################################
# Exposed API
###########################################################################
from tinytroupe.extraction.artifact_exporter import ArtifactExporter
from tinytroupe.extraction.normalizer import Normalizer
from tinytroupe.extraction.results_extractor import ResultsExtractor
from tinytroupe.extraction.results_reducer import ResultsReducer
from tinytroupe.extraction.results_reporter import ResultsReporter

__all__ = ["ArtifactExporter", "Normalizer", "ResultsExtractor", "ResultsReducer", "ResultsReporter"]