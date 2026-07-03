"""
Tools allow agents to accomplish specialized tasks.
"""

import logging
logger = logging.getLogger("tinytroupe")

###########################################################################
# Exposed API
###########################################################################
from tinytroupe.tools.tiny_tool import TinyTool
from tinytroupe.tools.services import TinyService
from tinytroupe.tools.tiny_word_processor import TinyWordProcessor
from tinytroupe.tools.tiny_contacts_directory import TinyContactsDirectory
from tinytroupe.tools.tiny_calendar import TinyCalendar, CalendarService
from tinytroupe.tools.tiny_email import TinyEmailClient, EmailService

__all__ = [
    "TinyTool",
    "TinyService",
    "TinyWordProcessor",
    "TinyContactsDirectory",
    "TinyCalendar",
    "CalendarService",
    "TinyEmailClient",
    "EmailService",
]