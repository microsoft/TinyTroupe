"""
TinyTroupe UI Module

This module provides user interface components and widgets for TinyTroupe,
enabling interactive experiences with TinyTroupe agents and environments.

The module is organized into different sub-modules based on the UI framework:

- jupyter_widgets: Interactive widgets for Jupyter notebooks
- web: Web-based interfaces (future)
- cli: Command-line interfaces (future)

Example usage:
    from tinytroupe.ui.jupyter_widgets import AgentChatJupyterWidget
    
    # Create a chat interface with your agents
    chat = AgentChatJupyterWidget(agents)
    chat.display()
"""

from .jupyter_widgets import AgentChatJupyterWidget
from .api_dashboard import (
    TinyTroupeDashboard,
    create_dashboard_app,
    run_dashboard,
)

__all__ = [
    'AgentChatJupyterWidget',
    'TinyTroupeDashboard',
    'create_dashboard_app',
    'run_dashboard',
    'HermesTurn',
    'HermesChatRequest',
    'HermesChatResponse',
    'create_hermes_gui_app',
    'run_hermes_gui',
]


def __getattr__(name):
    if name in {'HermesTurn', 'HermesChatRequest', 'HermesChatResponse', 'create_hermes_gui_app', 'run_hermes_gui'}:
        from .hermes_gui import (
            HermesChatRequest,
            HermesChatResponse,
            HermesTurn,
            create_hermes_gui_app,
            run_hermes_gui,
        )
        return {
            'HermesTurn': HermesTurn,
            'HermesChatRequest': HermesChatRequest,
            'HermesChatResponse': HermesChatResponse,
            'create_hermes_gui_app': create_hermes_gui_app,
            'run_hermes_gui': run_hermes_gui,
        }[name]
    raise AttributeError(name)
