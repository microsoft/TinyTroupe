import logging
logger = logging.getLogger("tinytroupe")

from tinytroupe import utils, config_manager

# We'll use various configuration elements below
config = utils.read_config_file()


###########################################################################
# Exposed API
###########################################################################
from .tiny_person_factory import TinyPersonFactory

__all__ = ["TinyPersonFactory"]