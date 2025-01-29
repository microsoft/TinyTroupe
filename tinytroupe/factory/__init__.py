import logging
logger = logging.getLogger("tinytroupe")

###########################################################################
# Exposed API
###########################################################################
from .tiny_person_factory import TinyPersonFactory

__all__ = ["TinyPersonFactory"]