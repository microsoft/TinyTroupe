import logging

from tinytroupe import config_manager, utils

from .azure_client import AzureClient
from .ollama_client import OllamaClient
from .openai_client import OpenAIClient

logger = logging.getLogger("tinytroupe")

###########################################################################
# Exceptions
###########################################################################


class InvalidRequestError(Exception):
    """
    Exception raised when the request to the OpenAI API is invalid.
    """

    pass


class NonTerminalError(Exception):
    """
    Exception raised when an unspecified error occurs but we know we can retry.
    """

    pass


###########################################################################
# Clients registry
#
# We can have potentially different clients, so we need a place to
# register them and retrieve them when needed.
#
# We support both OpenAI and Azure OpenAI Service API by default.
# Thus, we need to set the API parameters based on the choice of the user.
# This is done within specialized classes.
#
# It is also possible to register custom clients, to access internal or
# otherwise non-conventional API endpoints.
###########################################################################
_api_type_to_client = {}
_api_type_override = None


def register_client(api_type, client):
    """
    Registers a client for the given API type.

    Args:
    api_type (str): The API type for which we want to register the client.
    client: The client to register.
    """
    _api_type_to_client[api_type] = client


def _get_client_for_api_type(api_type):
    """
    Returns the client for the given API type.

    Args:
    api_type (str): The API type for which we want to get the client.
    """
    try:
        return _api_type_to_client[api_type]
    except KeyError:
        raise ValueError(
            f"API type {api_type} is not supported. Please check the 'config.ini' file."
        )


def client():
    """
    Returns the client for the configured API type.
    """
    api_type = (
        config_manager.get("api_type")
        if _api_type_override is None
        else _api_type_override
    )

    logger.debug(f"Using  API type {api_type}.")
    return _get_client_for_api_type(api_type)


# TODO simplify the custom configuration methods below


def force_api_type(api_type):
    """
    Forces the use of the given API type, thus overriding any other configuration.

    Args:
    api_type (str): The API type to use.
    """
    global _api_type_override
    _api_type_override = api_type


@config_manager.config_defaults(cache_file_name="cache_file_name")
def force_api_cache(cache_api_calls, cache_file_name=None):
    """
    Forces the use of the given API cache configuration, thus overriding any other configuration.

    Args:
    cache_api_calls (bool): Whether to cache API calls.
    cache_file_name (str): The name of the file to use for caching API calls.
    """
    # set the cache parameters on all clients
    for client in _api_type_to_client.values():
        client.set_api_cache(cache_api_calls, cache_file_name)


# default client
register_client("openai", OpenAIClient())
register_client("azure", AzureClient())
register_client("ollama", OllamaClient())
