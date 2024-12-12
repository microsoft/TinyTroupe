"""
Environments provide a structured way to define the world in which the
agents interact with each other as well as external entities (e.g., search engines).
"""

import logging
logger = logging.getLogger("tinytroupe")

from tinytroupe import default

###########################################################################
# Exposed API
###########################################################################
from tinytroupe.environment.tiny_world import TinyWorld
from tinytroupe.environment.tiny_social_network import TinySocialNetwork

__all__ = ["TinyWorld", "TinySocialNetwork"]