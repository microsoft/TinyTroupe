"""
Tools allow agents to accomplish specialized tasks.
"""

import logging

logger = logging.getLogger("tinytroupe")

from tinytroupe.tools.tiny_calendar import TinyCalendar
###########################################################################
# Exposed API
###########################################################################
from tinytroupe.tools.tiny_tool import TinyTool
from tinytroupe.tools.tiny_word_processor import TinyWordProcessor

__all__ = ["TinyTool", "TinyWordProcessor", "TinyCalendar"]
