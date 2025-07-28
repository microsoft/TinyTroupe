import json 
import os

def load_example_agent_specification(name:str):
    """
    Load an example agent specification.

    Args:
        name (str): The name of the agent.

    Returns:
        dict: The agent specification.
    """
    return json.load(open(os.path.join(os.path.dirname(__file__), f'./agents/{name}.agent.json'), 'r', encoding='utf-8', errors='replace'))

def load_example_fragment_specification(name:str):
    """
    Load an example fragment specification.

    Args:
        name (str): The name of the fragment.

    Returns:
        dict: The fragment specification.
    """
    return json.load(open(os.path.join(os.path.dirname(__file__), f'./fragments/{name}.fragment.json'), 'r', encoding='utf-8', errors='replace'))

def list_example_agents():
    """
    List the available example agents.

    Returns:
        list: A list of the available example agents.
    """
    return [f.replace('.agent.json', '') for f in os.listdir(os.path.join(os.path.dirname(__file__), './agents'))]

def list_example_fragments():
    """
    List the available example fragments.

    Returns:
        list: A list of the available example fragments.
    """
    return [f.replace('.fragment.json', '') for f in os.listdir(os.path.join(os.path.dirname(__file__), './fragments'))]