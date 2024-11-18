import logging
from tinytroupe import utils
logger = logging.getLogger("tinytroupe")

# We'll use various configuration elements below
config = utils.read_config_file()

###########################################################################
# default_params parameter values
###########################################################################
default_params = {}
default_params["model"] = config["OpenAI"].get("MODEL", "gpt-4")
default_params["max_tokens"] = int(config["OpenAI"].get("MAX_TOKENS", "1024"))
default_params["temperature"] = float(config["OpenAI"].get("TEMPERATURE", "0.3"))
default_params["top_p"] = int(config["OpenAI"].get("TOP_P", "0"))
default_params["frequency_penalty"] = float(config["OpenAI"].get("FREQ_PENALTY", "0.0"))
default_params["presence_penalty"] = float(
    config["OpenAI"].get("PRESENCE_PENALTY", "0.0"))
default_params["timeout"] = float(config["OpenAI"].get("TIMEOUT", "30.0"))
default_params["max_attempts"] = float(config["OpenAI"].get("MAX_ATTEMPTS", "0.0"))
default_params["waiting_time"] = float(config["OpenAI"].get("WAITING_TIME", "0.5"))
default_params["exponential_backoff_factor"] = float(config["OpenAI"].get("EXPONENTIAL_BACKOFF_FACTOR", "5"))

default_params["embedding_model"] = config["OpenAI"].get("EMBEDDING_MODEL", "text-embedding-3-small")

default_params["cache_api_calls"] = config["OpenAI"].getboolean("CACHE_API_CALLS", False)
default_params["cache_file_name"] = config["OpenAI"].get("CACHE_FILE_NAME", "openai_api_cache.pickle")


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
