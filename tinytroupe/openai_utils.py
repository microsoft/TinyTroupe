import os
import openai
from openai import OpenAI, AzureOpenAI
import time
import pickle
import logging
import configparser
from typing import Union


import tiktoken
from pydantic import BaseModel
from tinytroupe import utils
from tinytroupe.control import transactional
from tinytroupe import default
from tinytroupe import config_manager

logger = logging.getLogger("tinytroupe")

# We'll use various configuration elements below
config = utils.read_config_file()

###########################################################################
# Client class
###########################################################################

class OpenAIClient:
    """
    A utility class for interacting with the OpenAI API.
    """

    def __init__(self, cache_api_calls=default["cache_api_calls"], cache_file_name=default["cache_file_name"]) -> None:
        logger.debug("Initializing OpenAIClient")

        # should we cache api calls and reuse them?
        self.set_api_cache(cache_api_calls, cache_file_name)
    
    def set_api_cache(self, cache_api_calls, cache_file_name=default["cache_file_name"]):
        """
        Enables or disables the caching of API calls.

        Args:
        cache_file_name (str): The name of the file to use for caching API calls.
        """
        self.cache_api_calls = cache_api_calls
        self.cache_file_name = cache_file_name
        if self.cache_api_calls:
            # load the cache, if any
            self.api_cache = self._load_cache()
    
    
    def _setup_from_config(self):
        """
        Sets up the OpenAI API configurations for this client.
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # API mode: 'responses' or 'legacy' (default to legacy to preserve behavior unless configured)
        try:
            self.api_mode = config["OpenAI"].get("API_MODE", "legacy").strip().lower()
        except Exception:
            self.api_mode = "legacy"

    @config_manager.config_defaults(
        model="model",
        temperature="temperature",
        max_tokens="max_tokens",
        top_p="top_p",
        frequency_penalty="frequency_penalty",
        presence_penalty="presence_penalty",
        timeout="timeout",
        max_attempts="max_attempts",
        waiting_time="waiting_time",
        exponential_backoff_factor="exponential_backoff_factor",
        response_format=None,
        echo=None
    )
    def send_message(self,
                    current_messages,
                    dedent_messages=True,
                    model=None,
                    temperature=None,
                    max_tokens=None,
                    top_p=None,
                    frequency_penalty=None,
                    presence_penalty=None,
                    stop=[],
                    timeout=None,
                    max_attempts=None,
                    waiting_time=None,
                    exponential_backoff_factor=None,
                    n = 1,
                    response_format=None,
                    enable_pydantic_model_return=False,
                    echo=False):
        """
        Sends a message to the OpenAI API and returns the response.

        Args:
        current_messages (list): A list of dictionaries representing the conversation history.
        dedent_messages (bool): Whether to dedent the messages before sending them to the API.
        model (str): The ID of the model to use for generating the response.
        temperature (float): Controls the "creativity" of the response. Higher values result in more diverse responses.
        max_tokens (int): The maximum number of tokens (words or punctuation marks) to generate in the response.
        top_p (float): Controls the "quality" of the response. Higher values result in more coherent responses.
        frequency_penalty (float): Controls the "repetition" of the response. Higher values result in less repetition.
        presence_penalty (float): Controls the "diversity" of the response. Higher values result in more diverse responses.
        stop (str): A string that, if encountered in the generated response, will cause the generation to stop.
        max_attempts (int): The maximum number of attempts to make before giving up on generating a response.
        timeout (int): The maximum number of seconds to wait for a response from the API.
        waiting_time (int): The number of seconds to wait between requests.
        exponential_backoff_factor (int): The factor by which to increase the waiting time between requests.
        n (int): The number of completions to generate.
        response_format: The format of the response, if any.
        echo (bool): Whether to echo the input message in the response.
        enable_pydantic_model_return (bool): Whether to enable Pydantic model return instead of dict when possible.

        Returns:
        A dictionary representing the generated response.
        """

        def aux_exponential_backoff():
            nonlocal waiting_time

            # in case waiting time was initially set to 0
            if waiting_time <= 0:
                waiting_time = 2

            logger.info(f"Request failed. Waiting {waiting_time} seconds between requests...")
            time.sleep(waiting_time)

            # exponential backoff
            waiting_time = waiting_time * exponential_backoff_factor

        # setup the OpenAI configurations for this client.
        self._setup_from_config()

        # dedent the messages (field 'content' only) if needed (using textwrap)
        if dedent_messages:
            for message in current_messages:
                if "content" in message:
                    message["content"] = utils.dedent(message["content"])
            
        
        # We need to adapt the parameters to the API type, so we create a dictionary with them first
        chat_api_params = {
            "model": model,
            "messages": current_messages,
            "temperature": temperature,
            "max_tokens":max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stop": stop,
            "timeout": timeout,
            "stream": False,
            "n": n,
        }

        if response_format is not None:
            chat_api_params["response_format"] = response_format

        i = 0
        while i < max_attempts:
            try:
                i += 1

                try:
                    logger.debug(f"Sending messages to OpenAI API. Token count={self._count_tokens(current_messages, model)}.")
                except NotImplementedError:
                    logger.debug(f"Token count not implemented for model {model}.")
                    
                start_time = time.monotonic()
                logger.debug(f"Calling model with client class {self.__class__.__name__}.")

                ###############################################################
                # call the model, either from the cache or from the API
                ###############################################################
                cache_key = str((model, chat_api_params)) # need string to be hashable
                if self.cache_api_calls and (cache_key in self.api_cache):
                    response = self.api_cache[cache_key]
                else:
                    if waiting_time > 0:
                        logger.info(f"Waiting {waiting_time} seconds before next API request (to avoid throttling)...")
                        time.sleep(waiting_time)
                    
                    response = self._raw_model_call(model, chat_api_params)
                    if self.cache_api_calls:
                        self.api_cache[cache_key] = response
                        self._save_cache()
                
                
                logger.debug(f"Got response from API: {response}")
                end_time = time.monotonic()
                logger.debug(
                    f"Got response in {end_time - start_time:.2f} seconds after {i} attempts.")

                if enable_pydantic_model_return:
                    return utils.to_pydantic_or_sanitized_dict(self._raw_model_response_extractor(response), model=response_format)
                else:
                    return utils.sanitize_dict(self._raw_model_response_extractor(response))

            except InvalidRequestError as e:
                logger.error(f"[{i}] Invalid request error, won't retry: {e}")

                # there's no point in retrying if the request is invalid
                # so we return None right away
                return None
            
            except openai.BadRequestError as e:
                logger.error(f"[{i}] Invalid request error, won't retry: {e}")
                
                # there's no point in retrying if the request is invalid
                # so we return None right away
                return None
            
            except openai.RateLimitError:
                logger.warning(
                    f"[{i}] Rate limit error, waiting a bit and trying again.")
                aux_exponential_backoff()
            
            except NonTerminalError as e:
                logger.error(f"[{i}] Non-terminal error: {e}")
                aux_exponential_backoff()
                
            except Exception as e:
                logger.error(f"[{i}] {type(e).__name__} Error: {e}")
                aux_exponential_backoff()

        logger.error(f"Failed to get response after {max_attempts} attempts.")
        return None
    
    def _raw_model_call(self, model, chat_api_params):
        """
        Calls the OpenAI API with the given parameters. Subclasses should
        override this method to implement their own API calls.
        """

        # Choose API mode (legacy chat vs responses)
        api_mode = config["OpenAI"].get("API_MODE", "legacy").lower()

        # adjust parameters depending on the model (legacy path expectations)
        if self._is_reasoning_model(model):
            # Reasoning models have slightly different parameters
            if api_mode == "legacy":
                if "stream" in chat_api_params: del chat_api_params["stream"]
                if "temperature" in chat_api_params: del chat_api_params["temperature"]
                if "top_p" in chat_api_params: del chat_api_params["top_p"]
                if "frequency_penalty" in chat_api_params: del chat_api_params["frequency_penalty"]
                if "presence_penalty" in chat_api_params: del chat_api_params["presence_penalty"]

                chat_api_params["max_completion_tokens"] = chat_api_params["max_tokens"]
                del chat_api_params["max_tokens"]

                chat_api_params["reasoning_effort"] = default["reasoning_effort"]

        # To make the log cleaner, we remove the messages from the logged parameters
        logged_params = {k: v for k, v in chat_api_params.items() if k != "messages"}

        if api_mode == "responses":
            # Build Responses API params
            responses_params = self._build_responses_params(model, chat_api_params)

            # Log sanitized params and full messages separately
            rp_logged = {k: v for k, v in responses_params.items() if k != "input" and k != "messages"}
            logger.debug(f"Calling LLM model (Responses API) with these parameters: {rp_logged}. Not showing 'messages'/'input' parameter.")
            logger.debug(f"   --> Complete messages sent to LLM: {responses_params.get('messages') or responses_params.get('input')}")

            # If using Pydantic model, prefer parse helper when available
            if isinstance(chat_api_params.get("response_format"), type):
                # Responses parse path with Pydantic model
                return self.client.responses.parse(**responses_params)
            else:
                return self.client.responses.create(**responses_params)

        # Legacy Chat Completions path
        if "response_format" in chat_api_params:
            if "stream" in chat_api_params:
                del chat_api_params["stream"]

            logger.debug(f"Calling LLM model (using .parse too) with these parameters: {logged_params}. Not showing 'messages' parameter.")
            logger.debug(f"   --> Complete messages sent to LLM: {chat_api_params['messages']}")
            return self.client.beta.chat.completions.parse(**chat_api_params)
        else:
            logger.debug(f"Calling LLM model with these parameters: {logged_params}. Not showing 'messages' parameter.")
            return self.client.chat.completions.create(**chat_api_params)

    def _build_responses_params(self, model, chat_api_params):
        """
        Map legacy chat-style params to Responses API params.
        - Prefer 'messages' as input if present; else use 'input'.
        - Map max_tokens -> max_output_tokens
        - For reasoning models add reasoning: { effort: ... } and drop sampling params.
        - If response_format is a Pydantic model class, pass it directly (Responses parse supports Pydantic);
          if it's a dict (JSON Schema), pass as-is with strict mode expected to be set by caller.
        """
        params = {
            "model": model,
            # Latest SDKs accept either 'input' or 'messages'. We pass both for compatibility; the SDK ignores the unused one.
            "messages": chat_api_params.get("messages"),
            "input": chat_api_params.get("messages"),
            "max_output_tokens": chat_api_params.get("max_tokens"),
            "timeout": chat_api_params.get("timeout"),
        }

        # Include response_format (Pydantic class or JSON Schema dict)
        if chat_api_params.get("response_format") is not None:
            rf = chat_api_params["response_format"]
            params["response_format"] = rf

        # Reasoning models: remove sampling controls and set reasoning effort
        if self._is_reasoning_model(model):
            params["reasoning"] = {"effort": default["reasoning_effort"]}
        else:
            # Non-reasoning: sampling controls are valid
            for key in ("temperature", "top_p", "frequency_penalty", "presence_penalty"):
                if chat_api_params.get(key) is not None:
                    params[key] = chat_api_params[key]

        return params

    def _is_reasoning_model(self, model):
        return ("o1" in model) or ("o3" in model) or ("gpt-5" in model)

    def _raw_model_response_extractor(self, response):
        """
        Extract the response into a unified dict shape used by callers.
        Supports both Chat Completions and Responses API return shapes.
        """
        # Legacy chat path
        if hasattr(response, "choices"):
            return response.choices[0].message.to_dict()

        # Responses API path
        try:
            # Try to obtain a dict-like representation
            resp_dict = None
            if hasattr(response, "to_dict"):
                resp_dict = response.to_dict()
            elif hasattr(response, "model_dump"):
                resp_dict = response.model_dump()

            # Fall back to attribute traversal if needed
            output_items = None
            if resp_dict is not None:
                output_items = resp_dict.get("output") or resp_dict.get("outputs")
            else:
                output_items = getattr(response, "output", None) or getattr(response, "outputs", None)

            role = "assistant"
            content_text = None
            parsed = None
            refusal = None

            if output_items:
                # Expect the first item to be a message with content parts
                first = output_items[0]
                contents = first.get("content") if isinstance(first, dict) else getattr(first, "content", [])
                for part in contents or []:
                    ptype = part.get("type") if isinstance(part, dict) else getattr(part, "type", None)
                    # Text output
                    if ptype in ("output_text", "text"):
                        content_text = part.get("text") if isinstance(part, dict) else getattr(part, "text", None)
                    # Structured parse
                    if (isinstance(part, dict) and "parsed" in part):
                        parsed = part.get("parsed")
                    elif hasattr(part, "parsed"):
                        parsed = getattr(part, "parsed")
                    # Refusal
                    if (isinstance(part, dict) and "refusal" in part):
                        refusal = part.get("refusal")
                    elif hasattr(part, "refusal"):
                        refusal = getattr(part, "refusal")

            # As a final fallback, try convenience property 'output_text'
            if content_text is None and hasattr(response, "output_text"):
                try:
                    content_text = response.output_text
                except Exception:
                    pass

            return {"role": role, "content": content_text, "parsed": parsed, "refusal": refusal}
        except Exception as e:
            logger.error(f"Failed to extract Responses API payload: {e}")
            # best-effort fallback
            return {"role": "assistant", "content": None, "parsed": None, "refusal": None}

    def _count_tokens(self, messages: list, model: str):
        """
        Count the number of OpenAI tokens in a list of messages using tiktoken.

        Adapted from https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb

        Args:
        messages (list): A list of dictionaries representing the conversation history.
        model (str): The name of the model to use for encoding the string.
        """
        try:
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                logger.debug("Token count: model not found. Using cl100k_base encoding.")
                encoding = tiktoken.get_encoding("cl100k_base")
            
            if model in {
                "gpt-3.5-turbo-0613",
                "gpt-3.5-turbo-16k-0613",
                "gpt-4-0314",
                "gpt-4-32k-0314",
                "gpt-4-0613",
                "gpt-4-32k-0613",
                } or "o1" in model or "o3" in model: # assuming o1/3 models work the same way
                tokens_per_message = 3
                tokens_per_name = 1
            elif model == "gpt-3.5-turbo-0301":
                tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
                tokens_per_name = -1  # if there's a name, the role is omitted
            elif "gpt-3.5-turbo" in model:
                logger.debug("Token count: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
                return self._count_tokens(messages, model="gpt-3.5-turbo-0613")
            elif ("gpt-4" in model) or ("ppo" in model) :
                logger.debug("Token count: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
                return self._count_tokens(messages, model="gpt-4-0613")
            else:
                raise NotImplementedError(
                    f"""_count_tokens() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
                )
            
            num_tokens = 0
            for message in messages:
                num_tokens += tokens_per_message
                for key, value in message.items():
                    num_tokens += len(encoding.encode(value))
                    if key == "name":
                        num_tokens += tokens_per_name
            num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
            return num_tokens
        
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return None

    def _save_cache(self):
        """
        Saves the API cache to disk. We use pickle to do that because some obj
        are not JSON serializable.
        """
        # use pickle to save the cache
        pickle.dump(self.api_cache, open(self.cache_file_name, "wb", encoding="utf-8", errors="replace"))

    
    def _load_cache(self):

        """
        Loads the API cache from disk.
        """
        # unpickle
        return pickle.load(open(self.cache_file_name, "rb", encoding="utf-8", errors="replace")) if os.path.exists(self.cache_file_name) else {}

    def get_embedding(self, text, model=default["embedding_model"]):
        """
        Gets the embedding of the given text using the specified model.

        Args:
        text (str): The text to embed.
        model (str): The name of the model to use for embedding the text.

        Returns:
        The embedding of the text.
        """
        response = self._raw_embedding_model_call(text, model)
        return self._raw_embedding_model_response_extractor(response)
    
    def _raw_embedding_model_call(self, text, model):
        """
        Calls the OpenAI API to get the embedding of the given text. Subclasses should
        override this method to implement their own API calls.
        """
        return self.client.embeddings.create(
            input=[text],
            model=model
        )
    
    def _raw_embedding_model_response_extractor(self, response):
        """
        Extracts the embedding from the API response. Subclasses should
        override this method to implement their own response extraction.
        """
        return response.data[0].embedding

class AzureClient(OpenAIClient):

    def __init__(self, cache_api_calls=default["cache_api_calls"], cache_file_name=default["cache_file_name"]) -> None:
        logger.debug("Initializing AzureClient")

        super().__init__(cache_api_calls, cache_file_name)
    
    def _setup_from_config(self):
        """
        Sets up the Azure OpenAI Service API configurations for this client,
        including the API endpoint and key.
        """
        if os.getenv("AZURE_OPENAI_KEY"):
            logger.info("Using Azure OpenAI Service API with key.")
            self.client = AzureOpenAI(azure_endpoint= os.getenv("AZURE_OPENAI_ENDPOINT"),
                                    api_version = config["OpenAI"]["AZURE_API_VERSION"],
                                    api_key = os.getenv("AZURE_OPENAI_KEY"))
        else:  # Use Entra ID Auth
            logger.info("Using Azure OpenAI Service API with Entra ID Auth.")
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider

            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
            self.client = AzureOpenAI(
                azure_endpoint= os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version = config["OpenAI"]["AZURE_API_VERSION"],
                azure_ad_token_provider=token_provider
            )
    

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
        raise ValueError(f"API type {api_type} is not supported. Please check the 'config.ini' file.")

def client():
    """
    Returns the client for the configured API type.
    """
    api_type = config["OpenAI"]["API_TYPE"] if _api_type_override is None else _api_type_override
    
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

def force_api_cache(cache_api_calls, cache_file_name=default["cache_file_name"]):
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



