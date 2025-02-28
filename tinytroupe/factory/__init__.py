import logging
logger = logging.getLogger("tinytroupe")

from tinytroupe import utils

# We'll use various configuration elements below
config = utils.read_config_file()

###########################################################################
# Default parameter values
###########################################################################
default = {}
default["parallel_agent_generation"] = config["Simulation"].getboolean("PARALLEL_AGENT_GENERATION", True)

###########################################################################
# Exposed API
###########################################################################
from .tiny_person_factory import TinyPersonFactory

__all__ = ["TinyPersonFactory"]