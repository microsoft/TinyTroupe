import logging
import os
import threading
import time

import requests

from tinytroupe import config_manager, utils
from tinytroupe.clients.openai_client import LLMCacheBase

logger = logging.getLogger("tinytroupe")


class OllamaClient(LLMCacheBase):
    """
    A client for interacting with the Ollama API using direct HTTP requests.
    Supports a pool of base URLs (OLLAMA_BASE_URLS) for round-robin when
    multiple Ollama instances run on different ports.
    """

    @config_manager.config_defaults(
        cache_api_calls="cache_api_calls", cache_file_name="cache_file_name"
    )
    def __init__(self, cache_api_calls=None, cache_file_name=None) -> None:
        logger.debug("Initializing OllamaClient")
        urls = config_manager.get("ollama_base_urls", ["http://localhost:11434/v1"])
        if isinstance(urls, str):
            urls = [u.strip() for u in urls.split(",") if u.strip()] or [
                "http://localhost:11434/v1"
            ]
        self._base_urls = urls if urls else ["http://localhost:11434/v1"]
        self._round_robin_index = 0
        self._round_robin_lock = threading.Lock()
        # Backward compat: single URL for code that reads base_url
        self.base_url = self._base_urls[0]
        logger.debug(
            f"Ollama base URLs: {len(self._base_urls)} host(s) "
            f"{'[pool]' if len(self._base_urls) > 1 else '[single]'}"
        )

        # Set up caching via the base class method
        self.set_api_cache(cache_api_calls, cache_file_name)

    @config_manager.config_defaults(
        model="model",
        temperature="temperature",
        top_p="top_p",
        frequency_penalty="frequency_penalty",
        presence_penalty="presence_penalty",
        num_ctx="num_ctx",
        timeout="timeout",
        max_attempts="max_attempts",
        waiting_time="waiting_time",
        exponential_backoff_factor="exponential_backoff_factor",
        response_format=None,
        echo=None,
    )
    def send_message(
        self,
        current_messages,
        dedent_messages=True,
        model=None,
        temperature=None,
        max_completion_tokens=None,  # Ollama doesn't use max_completion_tokens
        top_p=None,
        frequency_penalty=None,
        presence_penalty=None,
        stop=None,
        num_ctx=None,
        timeout=None,
        max_attempts=None,
        waiting_time=None,
        exponential_backoff_factor=None,
        n=1,
        response_format=None,
        enable_pydantic_model_return=False,
        echo=False,
    ):
        """
        Sends a message to the Ollama API and returns the response.
        """

        from tinytroupe.clients import (  # avoid circular import
            InvalidRequestError,
            NonTerminalError,
        )

        def aux_exponential_backoff():
            nonlocal waiting_time
            logger.info(
                f"Request failed. Waiting {waiting_time} seconds between requests..."
            )
            time.sleep(waiting_time)
            waiting_time = waiting_time * exponential_backoff_factor

        # Prepare the API parameters
        chat_api_params = {
            "model": model,
            "messages": current_messages,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "stop": stop,
                "num_ctx": num_ctx,  # special Ollama parameter for the input size
            },
            "stream": False,
            "n": n,
        }

        # Ollama v1/chat/completions supports response_format (JSON mode) - same as OpenAI
        # Constrains output to valid JSON, fixing models that return XML/markdown/plain text
        if response_format is not None:
            chat_api_params["response_format"] = (
                {"type": "json_object"}
                if not isinstance(response_format, dict)
                else response_format
            )

        # remove any parameter that is None, so we use the API defaults
        chat_api_params = {k: v for k, v in chat_api_params.items() if v is not None}
        # ... within options too
        chat_api_params["options"] = {
            k: v for k, v in chat_api_params["options"].items() if v is not None
        }

        i = 0
        while i < max_attempts:
            try:
                i += 1

                start_time = time.monotonic()
                logger.debug(f"Sending request to Ollama API. Attempt {i}")

                # Check cache first
                cache_key = str((model, chat_api_params))
                if self.cache_api_calls and (cache_key in self.api_cache):
                    response = self.api_cache[cache_key]
                else:
                    logger.info(
                        f"Waiting {waiting_time} seconds before next API request..."
                    )
                    time.sleep(waiting_time)

                    # Make the API call
                    response = self._make_request(
                        "chat/completions",
                        method="POST",
                        json=chat_api_params,
                        timeout=timeout,
                    )

                    # Cache the response if caching is enabled
                    if self.cache_api_calls:
                        self.api_cache[cache_key] = response
                        self._save_cache()

                end_time = time.monotonic()
                logger.debug(
                    f"Got response in {end_time - start_time:.2f} seconds after {i} attempts"
                )

                # Extract and return the relevant part of the response
                return utils.sanitize_dict(self._extract_response(response))

            except requests.exceptions.RequestException as e:
                logger.error(f"[{i}] Request error: {e}")
                if "Invalid request" in str(e):
                    raise InvalidRequestError(str(e))
                aux_exponential_backoff()

            except Exception as e:
                logger.error(f"[{i}] Error: {e}")
                aux_exponential_backoff()

        logger.error(f"Failed to get response after {max_attempts} attempts")
        return None

    def _get_base_url(self) -> str:
        """Return next base URL (round-robin) when pool has multiple hosts."""
        if len(self._base_urls) <= 1:
            return self._base_urls[0]
        with self._round_robin_lock:
            url = self._base_urls[self._round_robin_index % len(self._base_urls)]
            self._round_robin_index += 1
        return url

    def _make_request(self, endpoint, method="POST", **kwargs):
        """
        Makes a request to the Ollama API. On connection failure, tries each
        URL in the pool so the client works whether Ollama is on 11434, 11444, etc.
        """
        last_error = None
        for base in self._base_urls:
            url = f"{base}/{endpoint}"
            logger.debug(f"Making {method} request to {url}")
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
                last_error = e
                logger.debug(f"Connection to {url} failed: {e}, trying next URL")
                continue
        if last_error:
            raise last_error

    def _extract_response(self, response):
        """
        Extracts the relevant information from the API response.
        """
        logger.debug(f"Extracting from response: {response}")
        try:
            return {
                "role": response["choices"][0]["message"]["role"],
                "content": response["choices"][0]["message"]["content"],
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error extracting response: {e}")
            logger.error(f"Response structure: {response}")
            raise ValueError("Invalid response format from Ollama")

    def get_models(self):
        """
        Gets the list of available models from Ollama.
        """
        try:
            response = self._make_request("models", method="GET")
            return response.get("models", [])
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            return []

    def _count_tokens(self, messages: list, model: str):
        """
        Count the number of tokens in a list of messages using Ollama's API.

        Args:
            messages (list): A list of dictionaries representing the conversation history.
            model (str): The name of the model to use for encoding the string.

        Returns:
            int or None: The number of tokens in the messages, or None if an error occurs.
        """
        try:
            # Combine all message content into a single string
            combined_text = ""
            for message in messages:
                # Add role/name if present
                if "name" in message:
                    combined_text += f"{message['name']}: "
                if "role" in message:
                    combined_text += f"{message['role']}: "
                # Add message content
                if "content" in message:
                    combined_text += f"{message['content']}\n"

            # Prepare the request payload
            payload = {
                "model": model,
                "input": combined_text,
                "options": {
                    "temperature": 0  # Set to 0 since we only care about token count
                },
            }

            # Make the request to Ollama's API
            temp_url = self._get_base_url().replace(
                "/v1", ""
            )  # Not sure what happened in their API, complete hack
            response = requests.post(f"{temp_url}/api/embed", json=payload)
            response.raise_for_status()

            # Extract token count from response
            data = response.json()
            token_count = data.get("prompt_eval_count", 0)

            return token_count

        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Ollama API: {e}")
            return None
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return None
