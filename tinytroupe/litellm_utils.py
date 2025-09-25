import configparser
import hashlib
import inspect
import json
import logging
import os
import pickle
import textwrap  # to dedent strings
import time
from typing import Any, Dict, List, Optional, Type, Union

import litellm
from pydantic import BaseModel

from tinytroupe import utils
from tinytroupe.control import transactional

logger = logging.getLogger("tinytroupe")


def _json_default_serializer(o):
    """
    A default JSON serializer for objects that are not serializable by default.
    This handles various cases including:
    - Pydantic model classes (not instances)
    - Pydantic model instances
    - Type objects
    - Other custom classes
    """
    # Handle Pydantic model classes
    if inspect.isclass(o) and issubclass(o, BaseModel):
        return f"PydanticClass:{o.__name__}"

    # Handle Pydantic model instances
    if isinstance(o, BaseModel):
        return f"PydanticInstance:{o.__class__.__name__}"

    # Handle Type objects
    if isinstance(o, type):
        return f"Type:{o.__name__}"

    # Handle any other class objects
    if inspect.isclass(o):
        return f"Class:{o.__name__}"

    # For any other objects, convert to string
    try:
        return str(o)
    except:
        return f"Unserializable:{type(o).__name__}"


# We'll use various configuration elements below
config = utils.read_config_file()

###########################################################################
# Default parameter values
###########################################################################
default = {}
default["provider"] = config["LLM"].get("PROVIDER", "openai")
default["model"] = config["LLM"].get("MODEL", "gpt-4o-mini")
default["max_tokens"] = int(config["LLM"].get("MAX_TOKENS", "4000"))
default["temperature"] = float(config["LLM"].get("TEMPERATURE", "1.2"))
default["top_p"] = float(config["LLM"].get("TOP_P", "1.0"))
default["frequency_penalty"] = float(config["LLM"].get("FREQUENCY_PENALTY", "0.0"))
default["presence_penalty"] = float(config["LLM"].get("PRESENCE_PENALTY", "0.0"))
default["timeout"] = float(config["LLM"].get("TIMEOUT", "60.0"))
default["max_attempts"] = int(config["LLM"].get("MAX_ATTEMPTS", "5"))
default["waiting_time"] = float(config["LLM"].get("WAITING_TIME", "1"))
default["exponential_backoff_factor"] = float(
    config["LLM"].get("EXPONENTIAL_BACKOFF_FACTOR", "5")
)

default["embedding_model"] = config["LLM"].get(
    "EMBEDDING_MODEL", "text-embedding-3-small"
)

default["cache_api_calls"] = config["LLM"].getboolean("CACHE_API_CALLS", False)
default["cache_file_name"] = config["LLM"].get(
    "CACHE_FILE_NAME", "litellm_api_cache.pickle"
)

# LiteLLM specific settings
default["enable_fallbacks"] = config["LLM"].getboolean("ENABLE_FALLBACKS", False)
default["fallback_models"] = (
    config["LLM"].get("FALLBACK_MODELS", "").split(",")
    if config["LLM"].get("FALLBACK_MODELS", "")
    else []
)

###########################################################################
# Model calling helpers
###########################################################################


class LLMRequest:
    """
    A class that represents an LLM model call. It contains the input messages, the model configuration, and the model output.
    """

    def __init__(
        self,
        system_template_name: str = None,
        system_prompt: str = None,
        user_template_name: str = None,
        user_prompt: str = None,
        output_type=None,
        **model_params,
    ):
        """
        Initializes an LLMCall instance with the specified system and user templates, or the system and user prompts.
        If a template is specified, the corresponding prompt must be None, and vice versa.
        """
        if (
            (system_template_name is not None and system_prompt is not None)
            or (user_template_name is not None and user_prompt is not None)
            or (system_template_name is None and system_prompt is None)
            or (user_template_name is None and user_prompt is None)
        ):
            raise ValueError(
                "Either the template or the prompt must be specified, but not both."
            )

        self.system_template_name = system_template_name
        self.user_template_name = user_template_name

        self.system_prompt = textwrap.dedent(system_prompt)  # remove identation
        self.user_prompt = textwrap.dedent(user_prompt)  # remove identation

        self.output_type = output_type

        self.model_params = model_params
        self.model_output = None

        self.messages = []

        #  will be set after the call
        self.response_raw = None
        self.response_json = None
        self.response_value = None
        self.response_justification = None
        self.response_confidence = None

    def __call__(self, *args, **kwds):
        return self.call(*args, **kwds)

    def call(self, **rendering_configs):
        """
        Calls the LLM model with the specified rendering configurations.

        Args:
            rendering_configs: The rendering configurations (template variables) to use when composing the initial messages.

        Returns:
            The content of the model response.
        """
        if (
            self.system_template_name is not None
            and self.user_template_name is not None
        ):
            self.messages = utils.compose_initial_LLM_messages_with_templates(
                self.system_template_name, self.user_template_name, rendering_configs
            )
        else:
            self.messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt},
            ]

        #
        # Setup typing for the output
        #
        if self.output_type is not None:
            # specify the structured output
            self.model_params["response_format"] = LLMScalarWithJustificationResponse
            self.messages.append(
                {
                    "role": "user",
                    "content": "In your response, you **MUST** provide a value, along with a justification and your confidence level that the value and justification are correct (0.0 means no confidence, 1.0 means complete confidence)."
                    + 'Furtheremore, your response **MUST** be a JSON object with the following structure: {"value": value, "justification": justification, "confidence": confidence}.',
                }
            )

            # specify the value type
            if self.output_type == bool:
                self.messages.append(self._request_bool_llm_message())
            elif self.output_type == int:
                self.messages.append(self._request_integer_llm_message())
            elif self.output_type == float:
                self.messages.append(self._request_float_llm_message())
            elif self.output_type == list and all(
                isinstance(option, str) for option in self.output_type
            ):
                self.messages.append(
                    self._request_enumerable_llm_message(self.output_type)
                )
            elif self.output_type == str:
                pass
            else:
                raise ValueError(f"Unsupported output type: {self.output_type}")

        #
        # call the LLM model
        #
        self.model_output = client().send_message(self.messages, **self.model_params)

        if "content" in self.model_output:
            self.response_raw = self.response_value = self.model_output["content"]

            # further, if an output type is specified, we need to coerce the result to that type
            if self.output_type is not None:
                self.response_json = utils.extract_json(self.response_raw)

                self.response_value = self.response_json["value"]
                self.response_justification = self.response_json["justification"]
                self.response_confidence = self.response_json["confidence"]

                if self.output_type == bool:
                    self.response_value = self._coerce_to_bool(self.response_value)
                elif self.output_type == int:
                    self.response_value = self._coerce_to_integer(self.response_value)
                elif self.output_type == float:
                    self.response_value = self._coerce_to_float(self.response_value)
                elif self.output_type == list and all(
                    isinstance(option, str) for option in self.output_type
                ):
                    self.response_value = self._coerce_to_enumerable(
                        self.response_value, self.output_type
                    )
                elif self.output_type == str:
                    pass
                else:
                    raise ValueError(f"Unsupported output type: {self.output_type}")

            return self.response_value

        else:
            logger.error(
                f"Model output does not contain 'content' key: {self.model_output}"
            )
            return None

    def _coerce_to_bool(self, llm_output):
        """
        Coerces the LLM output to a boolean value.

        This method looks for the string "True", "False", "Yes", "No", "Positive", "Negative" in the LLM output, such that
          - case is neutralized;
          - the first occurrence of the string is considered, the rest is ignored. For example,  " Yes, that is true" will be considered "Yes";
          - if no such string is found, the method raises an error. So it is important that the prompts actually requests a boolean value.

        Args:
            llm_output (str, bool): The LLM output to coerce.

        Returns:
            The boolean value of the LLM output.
        """

        # if the LLM output is already a boolean, we return it
        if isinstance(llm_output, bool):
            return llm_output

        # let's extract the first occurrence of the string "True", "False", "Yes", "No", "Positive", "Negative" in the LLM output.
        # using a regular expression
        import re

        match = re.search(
            r"\b(?:True|False|Yes|No|Positive|Negative)\b", llm_output, re.IGNORECASE
        )
        if match:
            first_match = match.group(0).lower()
            if first_match in ["true", "yes", "positive"]:
                return True
            elif first_match in ["false", "no", "negative"]:
                return False

        raise ValueError(
            "The LLM output does not contain a recognizable boolean value."
        )

    def _request_bool_llm_message(self):
        return {
            "role": "user",
            "content": "The `value` field you generate **must** be either 'True' or 'False'. This is critical for later processing. If you don't know the correct answer, just output 'False'.",
        }

    def _coerce_to_integer(self, llm_output: str):
        """
        Coerces the LLM output to an integer value.

        This method looks for the first integer in the LLM output, such that
          - the first occurrence of the integer is considered, the rest is ignored. For example,  " 42, that is true" will be considered 42;
          - if no integer is found, the method raises an error. So it is important that the prompts actually requests an integer value.

        Args:
            llm_output (str): The LLM output to coerce.

        Returns:
            The integer value of the LLM output.
        """
        import re

        match = re.search(r"\b\d+\b", llm_output)
        if match:
            return int(match.group(0))
        raise ValueError(
            "The LLM output does not contain a recognizable integer value."
        )

    def _request_integer_llm_message(self):
        return {
            "role": "user",
            "content": "The `value` field you generate **must** be an integer. This is critical for later processing.",
        }

    def _coerce_to_float(self, llm_output: str):
        """
        Coerces the LLM output to a float value.

        This method looks for the first float in the LLM output, such that
          - the first occurrence of the float is considered, the rest is ignored. For example,  " 42.5, that is true" will be considered 42.5;
          - if no float is found, the method raises an error. So it is important that the prompts actually requests a float value.

        Args:
            llm_output (str): The LLM output to coerce.

        Returns:
            The float value of the LLM output.
        """
        import re

        match = re.search(r"\b\d+\.\d+\b", llm_output)
        if match:
            return float(match.group(0))
        # also try to match integers
        match = re.search(r"\b\d+\b", llm_output)
        if match:
            return float(match.group(0))
        raise ValueError("The LLM output does not contain a recognizable float value.")

    def _request_float_llm_message(self):
        return {
            "role": "user",
            "content": "The `value` field you generate **must** be a float. This is critical for later processing.",
        }

    def _coerce_to_enumerable(self, llm_output: str, options: list):
        """
        Coerces the LLM output to one of the specified options.

        This method looks for the first occurrence of any of the specified options in the LLM output, such that
          - case is neutralized;
          - the first occurrence of any option is considered, the rest is ignored;
          - if no option is found, the method raises an error. So it is important that the prompts actually requests one of the specified options.

        Args:
            llm_output (str): The LLM output to coerce.
            options (list): The list of valid options.

        Returns:
            The option value from the LLM output.
        """
        llm_output_lower = llm_output.lower()
        for option in options:
            if option.lower() in llm_output_lower:
                return option
        raise ValueError(
            f"The LLM output does not contain any of the recognizable options: {options}"
        )

    def _request_enumerable_llm_message(self, options: list):
        return {
            "role": "user",
            "content": f"The `value` field you generate **must** be one of the following options: {options}. This is critical for later processing.",
        }

    def __repr__(self):
        return f"LLMRequest(system_template_name={self.system_template_name}, user_template_name={self.user_template_name}, output_type={self.output_type})"


class LLMScalarWithJustificationResponse(BaseModel):
    """
    LLMTypedResponse represents a typed response from an LLM (Language Learning Model).
    Attributes:
        value (str, int, float, list): The value of the response.
        justification (str): The justification or explanation for the response.
    """

    value: Union[str, int, float, bool]
    justification: str
    confidence: float


###########################################################################
# LiteLLM Client
###########################################################################


class LiteLLMClient:
    """
    A client for interacting with various LLM providers through LiteLLM.
    Supports multiple providers, caching, fallbacks, and usage tracking.
    """

    def __init__(
        self,
        cache_api_calls=default["cache_api_calls"],
        cache_file_name=default["cache_file_name"],
    ) -> None:
        """
        Initialize the LiteLLM client.

        Args:
            cache_api_calls: Whether to cache API calls
            cache_file_name: Name of the cache file
        """
        self.cache_api_calls = cache_api_calls
        self.cache_file_name = cache_file_name
        self.api_cache = self._load_cache() if cache_api_calls else {}
        self.usage_tracker = {}

        # Setup LiteLLM configuration
        self._setup_from_config()

        # Register the client
        register_client("litellm", self)

    def set_api_cache(
        self, cache_api_calls, cache_file_name=default["cache_file_name"]
    ):
        """
        Set the API cache configuration.

        Args:
            cache_api_calls: Whether to cache API calls
            cache_file_name: Name of the cache file
        """
        self.cache_api_calls = cache_api_calls
        self.cache_file_name = cache_file_name

        if cache_api_calls:
            self.api_cache = self._load_cache()
        else:
            self.api_cache = {}

    def _setup_from_config(self):
        """Setup LiteLLM configuration from config file."""
        # Set API keys from environment or config
        if "LITELLM_URL" in os.environ and "LITELLM_KEY" in os.environ:
            # Use custom LiteLLM endpoint
            litellm.api_base = os.environ["LITELLM_URL"]
            litellm.api_key = os.environ["LITELLM_KEY"]
        else:
            # Use provider-specific API keys
            for provider in ["openai", "anthropic", "cohere", "replicate"]:
                api_key = config["LLM"].get(f"{provider.upper()}_API_KEY", "")
                if api_key:
                    os.environ[f"{provider.upper()}_API_KEY"] = api_key

        # Set default model
        litellm.set_verbose = False

    def send_message(
        self,
        current_messages,
        model=None,
        temperature=default["temperature"],
        max_tokens=default["max_tokens"],
        top_p=default["top_p"],
        frequency_penalty=default["frequency_penalty"],
        presence_penalty=default["presence_penalty"],
        stop=[],
        timeout=default["timeout"],
        max_attempts=default["max_attempts"],
        waiting_time=default["waiting_time"],
        exponential_backoff_factor=default["exponential_backoff_factor"],
        n=1,
        response_format=None,
        **kwargs,
    ):
        """
        Send a message to the LLM model.

        Args:
            current_messages: List of message dictionaries
            model: Model to use (if None, uses default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop: Stop sequences
            timeout: Request timeout
            max_attempts: Maximum retry attempts
            waiting_time: Base waiting time between retries
            exponential_backoff_factor: Exponential backoff factor
            n: Number of completions
            response_format: Response format specification
            **kwargs: Additional parameters

        Returns:
            Dictionary containing the model response
        """
        if model is None:
            model = default["model"]

        # Re-enable caching based on config setting
        self.cache_api_calls = default["cache_api_calls"]

        cache_key = None
        # Only try to use cache if caching is enabled
        if self.cache_api_calls:
            try:
                # Create cache key
                cache_key = self._create_cache_key(
                    current_messages,
                    model,
                    temperature,
                    max_tokens,
                    top_p,
                    frequency_penalty,
                    presence_penalty,
                    stop,
                    response_format,
                    **kwargs,
                )

                # Check cache first
                if cache_key in self.api_cache:
                    logger.debug(f"Cache hit for key: {cache_key[:50]}...")
                    return self.api_cache[cache_key]
            except Exception as e:
                # If we can't create a cache key due to non-serializable objects, log and continue without caching
                logger.warning(f"Could not use cache due to error: {e}")
                self.cache_api_calls = (
                    False  # Temporarily disable caching for this request
                )

        # Prepare parameters for LiteLLM
        litellm_params = {
            "model": model,
            "messages": current_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stop": stop,
            "n": n,
            **kwargs,
        }

        # Remove model-specific unsupported parameters
        if model.startswith("groq/") and "echo" in litellm_params:
            logger.debug("Removing 'echo' parameter for Groq models")
            litellm_params.pop("echo")

        # Handle Gemini models - ensure correct provider and remove unsupported parameters
        if "gemini" in model.lower():
            # Ensure correct provider for Gemini
            if not model.startswith("vertex_ai/"):
                new_model = f"vertex_ai/gemini-2.0-flash"
                logger.warning(
                    f"Converting model {model} to use vertex_ai provider: {new_model}"
                )
                litellm_params["model"] = new_model

            # Remove unsupported parameters
            unsupported_params = ["presence_penalty"]
            for param in unsupported_params:
                if param in litellm_params:
                    logger.debug(f"Removing '{param}' parameter for Gemini models")
                    litellm_params.pop(param)

        # Add response format if specified
        if response_format:
            litellm_params["response_format"] = response_format

        # Remove None values
        litellm_params = {k: v for k, v in litellm_params.items() if v is not None}

        # Retry logic with exponential backoff
        def aux_exponential_backoff():
            for attempt in range(max_attempts + 1):
                try:
                    logger.debug(
                        f"Attempting LLM call to {model} (attempt {attempt + 1}/{max_attempts + 1})"
                    )

                    # Use LiteLLM completion
                    response = litellm.completion(**litellm_params)

                    # Extract the response
                    result = self._raw_model_response_extractor(response)

                    # Cache the result if caching is enabled and we have a valid cache key
                    if self.cache_api_calls and cache_key:
                        try:
                            self.api_cache[cache_key] = result
                            self._save_cache()
                        except Exception as e:
                            logger.warning(f"Could not cache result: {e}")

                    # Track usage
                    self._track_usage(response, model)

                    return result

                except litellm.RateLimitError as e:
                    logger.warning(f"Rate limit error (attempt {attempt + 1}): {e}")
                    if attempt < max_attempts:
                        wait_time = waiting_time * (exponential_backoff_factor**attempt)
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        raise

                except litellm.AuthenticationError as e:
                    logger.error(f"Authentication error: {e}")
                    raise

                except litellm.BadRequestError as e:
                    logger.error(f"Bad request error with model {model}: {e}")
                    # Extract specific parameter errors from the exception
                    error_msg = str(e)

                    # Check for specific provider issues
                    if "groq" in model.lower() and "echo" in error_msg.lower():
                        logger.warning(
                            "Groq does not support the 'echo' parameter. Removing it and retrying..."
                        )
                        if "echo" in litellm_params:
                            litellm_params.pop("echo")
                            return (
                                aux_exponential_backoff()
                            )  # Retry with fixed parameters

                    # Check for unsupported parameters in Gemini
                    if (
                        "gemini" in model.lower()
                        and "UnsupportedParamsError" in error_msg
                    ):
                        if "presence_penalty" in error_msg:
                            logger.warning(
                                "Gemini does not support the 'presence_penalty' parameter. Removing it and retrying..."
                            )
                            if "presence_penalty" in litellm_params:
                                litellm_params.pop("presence_penalty")
                                return (
                                    aux_exponential_backoff()
                                )  # Retry with fixed parameters

                    raise

                except litellm.NotFoundError as e:
                    logger.error(f"Not Found error with model {model}: {e}")
                    error_msg = str(e)

                    # Check for Vertex AI provider issues
                    if "gemini" in model.lower() and "VertexAIException" in error_msg:
                        if not model.startswith("vertex_ai/"):
                            new_model = f"vertex_ai/gemini-2.0-flash"
                            logger.warning(
                                f"Possible provider mismatch. Converting model {model} to {new_model}"
                            )
                            litellm_params["model"] = new_model
                            return (
                                aux_exponential_backoff()
                            )  # Retry with fixed model name

                    if attempt < max_attempts:
                        wait_time = waiting_time * (exponential_backoff_factor**attempt)
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        raise

                except Exception as e:
                    logger.error(
                        f"Unexpected error (attempt {attempt + 1}) with model {model}: {e}"
                    )
                    if attempt < max_attempts:
                        wait_time = waiting_time * (exponential_backoff_factor**attempt)
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        raise

        return aux_exponential_backoff()

    def _raw_model_response_extractor(self, response):
        """
        Extract the response from the LiteLLM response object.

        Args:
            response: LiteLLM response object

        Returns:
            Dictionary containing the response
        """
        try:
            return {
                "role": response.choices[0].message.role,
                "content": response.choices[0].message.content,
            }
        except Exception as e:
            logger.error(f"Error extracting response: {e}")
            return None

    def _create_cache_key(
        self,
        messages,
        model,
        temperature,
        max_tokens,
        top_p,
        frequency_penalty,
        presence_penalty,
        stop,
        response_format,
        **kwargs,
    ):
        """
        Create a cache key for the request.

        Args:
            messages: List of message dictionaries
            model: Model name
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            top_p: Top-p parameter
            frequency_penalty: Frequency penalty parameter
            presence_penalty: Presence penalty parameter
            stop: Stop sequences
            response_format: Response format
            **kwargs: Additional parameters

        Returns:
            Cache key string
        """
        try:
            # Create a hash of the request parameters
            request_data = {
                "messages": messages,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "stop": stop,
                "response_format": response_format,
                **kwargs,
            }

            # Use our improved serializer to handle non-serializable objects
            request_str = json.dumps(
                request_data, sort_keys=True, default=_json_default_serializer
            )
            return hashlib.md5(request_str.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Error creating cache key: {e}")
            # Create a fallback key based on a subset of parameters that are likely to be serializable
            fallback_data = {
                "model": str(model),
                "temperature": temperature,
                "max_tokens": max_tokens,
                # Include a hash of the messages content
                "messages_hash": hashlib.md5(
                    str([m.get("content", "") for m in messages]).encode()
                ).hexdigest(),
            }
            request_str = json.dumps(fallback_data, sort_keys=True)
            return hashlib.md5(f"fallback:{request_str}".encode()).hexdigest()

    def _track_usage(self, response, model):
        """
        Track usage statistics.

        Args:
            response: LiteLLM response object
            model: Model name
        """
        if hasattr(response, "usage") and response.usage:
            if model not in self.usage_tracker:
                self.usage_tracker[model] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "calls": 0,
                }

            self.usage_tracker[model]["prompt_tokens"] += (
                response.usage.prompt_tokens or 0
            )
            self.usage_tracker[model]["completion_tokens"] += (
                response.usage.completion_tokens or 0
            )
            self.usage_tracker[model]["total_tokens"] += (
                response.usage.total_tokens or 0
            )
            self.usage_tracker[model]["calls"] += 1

    def get_usage_report(self):
        """
        Get usage statistics.

        Returns:
            Dictionary containing usage statistics
        """
        return self.usage_tracker

    def _save_cache(self):
        """Save the API cache to disk."""
        try:
            with open(self.cache_file_name, "wb") as f:
                pickle.dump(self.api_cache, f)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def _load_cache(self):
        """Load the API cache from disk."""
        try:
            if os.path.exists(self.cache_file_name):
                with open(self.cache_file_name, "rb") as f:
                    return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
        return {}

    def get_embedding(self, text, model=default["embedding_model"]):
        """
        Get embeddings for the given text.

        Args:
            text: Text to embed
            model: Embedding model to use

        Returns:
            List of embeddings
        """
        try:
            response = litellm.embedding(model=model, input=text)
            return self._raw_embedding_model_response_extractor(response)
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None

    def _raw_embedding_model_response_extractor(self, response):
        """
        Extract embeddings from the LiteLLM embedding response.

        Args:
            response: LiteLLM embedding response object

        Returns:
            List of embeddings
        """
        try:
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error extracting embedding: {e}")
            return None


###########################################################################
# Client Registry and Management
###########################################################################

# Global client registry
_clients = {}
_current_api_type = "litellm"


def register_client(api_type, client):
    """
    Register a client for a specific API type.

    Args:
        api_type: API type identifier
        client: Client instance
    """
    global _clients
    _clients[api_type] = client
    logger.info(f"Registered client for API type: {api_type}")


def _get_client_for_api_type(api_type):
    """
    Get the client for a specific API type.

    Args:
        api_type: API type identifier

    Returns:
        Client instance
    """
    if api_type not in _clients:
        if api_type == "litellm":
            _clients[api_type] = LiteLLMClient()
        else:
            raise ValueError(f"No client registered for API type: {api_type}")

    return _clients[api_type]


def client():
    """
    Get the current client instance.

    Returns:
        Current client instance
    """
    return _get_client_for_api_type(_current_api_type)


def force_api_type(api_type):
    """
    Force the use of a specific API type.

    Args:
        api_type: API type to use
    """
    global _current_api_type
    _current_api_type = api_type
    logger.info(f"Forced API type to: {api_type}")


def force_api_cache(cache_api_calls, cache_file_name=default["cache_file_name"]):
    """
    Force API cache configuration.

    Args:
        cache_api_calls: Whether to cache API calls
        cache_file_name: Name of the cache file
    """
    client().set_api_cache(cache_api_calls, cache_file_name)


# Initialize the default client
