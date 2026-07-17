import logging
import time

from tinytroupe import config_manager, utils
from tinytroupe.clients.openai_client import LLMCacheBase

logger = logging.getLogger("tinytroupe")


def _import_litellm():
    try:
        import litellm
        return litellm
    except ImportError:
        raise ImportError(
            "litellm is required for the LiteLLM client. "
            "Install it with: pip install 'tinytroupe[litellm]'"
        )


class LiteLLMClient(LLMCacheBase):
    """
    A client for interacting with LLM providers through LiteLLM,
    providing unified access to 100+ LLM providers (OpenAI, Anthropic,
    Google, Azure, Bedrock, Ollama, and more) via a single interface.
    """

    @config_manager.config_defaults(
        cache_api_calls="cache_api_calls", cache_file_name="cache_file_name"
    )
    def __init__(self, cache_api_calls=None, cache_file_name=None) -> None:
        logger.debug("Initializing LiteLLMClient")
        self.set_api_cache(cache_api_calls, cache_file_name)

    @config_manager.config_defaults(
        model="model",
        temperature="temperature",
        max_completion_tokens="max_completion_tokens",
        frequency_penalty="frequency_penalty",
        presence_penalty="presence_penalty",
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
        max_completion_tokens=None,
        top_p=None,
        frequency_penalty=None,
        presence_penalty=None,
        stop=None,
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
        Sends a message via LiteLLM and returns the response.
        Follows the same interface as OpenAIClient.send_message.
        """
        litellm = _import_litellm()

        from tinytroupe.clients import InvalidRequestError, NonTerminalError

        def aux_exponential_backoff():
            nonlocal waiting_time
            if waiting_time is None or waiting_time <= 0:
                waiting_time = 2
            logger.info(
                f"Request failed. Waiting {waiting_time} seconds between requests..."
            )
            time.sleep(waiting_time)
            waiting_time = waiting_time * (exponential_backoff_factor or 5)

        if max_attempts is None:
            max_attempts = 2

        if dedent_messages:
            for message in current_messages:
                if "content" in message and isinstance(message["content"], str):
                    message["content"] = utils.dedent(message["content"])

        chat_api_params = {
            "model": model,
            "messages": current_messages,
            "temperature": temperature,
            "max_completion_tokens": max_completion_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stop": stop,
            "timeout": timeout,
            "stream": False,
            "n": n,
            "drop_params": True,
        }

        if response_format is not None:
            chat_api_params["response_format"] = response_format

        chat_api_params = {k: v for k, v in chat_api_params.items() if v is not None}

        i = 0
        while i < max_attempts:
            try:
                i += 1

                start_time = time.monotonic()
                logger.debug(f"Sending request via LiteLLM. Attempt {i}")

                cache_key = str((model, chat_api_params))
                if self.cache_api_calls and hasattr(self, 'api_cache') and (cache_key in self.api_cache):
                    response = self.api_cache[cache_key]
                    raw_message = self._extract_response(response)
                else:
                    if waiting_time is not None and waiting_time > 0:
                        logger.info(
                            f"Waiting {waiting_time} seconds before next API request..."
                        )
                        time.sleep(waiting_time)

                    response = litellm.completion(**chat_api_params)
                    response_dict = response.model_dump()

                    if self.cache_api_calls:
                        if not hasattr(self, 'api_cache'):
                            self.api_cache = {}
                        self.api_cache[cache_key] = response_dict
                        self._save_cache()

                    raw_message = self._extract_response(response_dict)

                end_time = time.monotonic()
                logger.debug(
                    f"Got response in {end_time - start_time:.2f} seconds after {i} attempts."
                )

                if raw_message is None or raw_message.get("content") is None:
                    logger.warning("LiteLLM returned empty response content")
                    aux_exponential_backoff()
                    continue

                return utils.sanitize_dict(raw_message)

            except InvalidRequestError as e:
                logger.error(f"[{i}] Invalid request error, won't retry: {e}")
                return None

            except litellm.BadRequestError as e:
                logger.error(f"[{i}] Bad request error, won't retry: {e}")
                return None

            except litellm.AuthenticationError as e:
                logger.error(f"[{i}] Authentication error, won't retry: {e}")
                return None

            except litellm.NotFoundError as e:
                logger.error(f"[{i}] Model not found, won't retry: {e}")
                return None

            except litellm.RateLimitError:
                logger.warning(
                    f"[{i}] Rate limit error, waiting a bit and trying again."
                )
                aux_exponential_backoff()

            except litellm.Timeout as e:
                logger.error(f"[{i}] Timeout error: {e}")
                aux_exponential_backoff()

            except litellm.APIConnectionError as e:
                logger.error(f"[{i}] API connection error: {e}")
                aux_exponential_backoff()

            except litellm.InternalServerError as e:
                logger.error(f"[{i}] Provider internal server error: {e}")
                aux_exponential_backoff()

            except litellm.ServiceUnavailableError as e:
                logger.error(f"[{i}] Service unavailable: {e}")
                aux_exponential_backoff()

            except NonTerminalError as e:
                logger.error(f"[{i}] Non-terminal error: {e}")
                aux_exponential_backoff()

            except Exception as e:
                logger.error(f"[{i}] Unexpected {type(e).__name__}: {e}")
                aux_exponential_backoff()

        logger.error(f"Failed to get response after {max_attempts} attempts.")
        return None

    def _extract_response(self, response):
        """
        Extracts the relevant information from the API response dict.
        """
        try:
            choice = response["choices"][0]
            message = choice.get("message", {})
            return {
                "role": message.get("role", "assistant"),
                "content": message.get("content"),
            }
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error extracting response: {e}")
            logger.error(f"Response structure: {response}")
            return None

    def _count_tokens(self, messages: list, model: str):
        """
        Count tokens using LiteLLM's token counter.
        """
        try:
            litellm = _import_litellm()
            return litellm.token_counter(model=model, messages=messages)
        except ImportError:
            logger.debug("litellm not installed, skipping token count")
            return None
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return None
