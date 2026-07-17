import logging
import time

from tinytroupe import config_manager, utils
from tinytroupe.clients.openai_client import LLMCacheBase

logger = logging.getLogger("tinytroupe")


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
        import litellm

        from tinytroupe.clients import InvalidRequestError, NonTerminalError

        def aux_exponential_backoff():
            nonlocal waiting_time
            if waiting_time <= 0:
                waiting_time = 2
            logger.info(
                f"Request failed. Waiting {waiting_time} seconds between requests..."
            )
            time.sleep(waiting_time)
            waiting_time = waiting_time * exponential_backoff_factor

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
                if self.cache_api_calls and (cache_key in self.api_cache):
                    response = self.api_cache[cache_key]
                    raw_message = self._extract_response(response)
                else:
                    if waiting_time > 0:
                        logger.info(
                            f"Waiting {waiting_time} seconds before next API request..."
                        )
                        time.sleep(waiting_time)

                    response = litellm.completion(**chat_api_params)
                    response_dict = response.model_dump()

                    if self.cache_api_calls:
                        self.api_cache[cache_key] = response_dict
                        self._save_cache()

                    raw_message = self._extract_response(response_dict)

                end_time = time.monotonic()
                logger.debug(
                    f"Got response in {end_time - start_time:.2f} seconds after {i} attempts."
                )

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

            except litellm.RateLimitError:
                logger.warning(
                    f"[{i}] Rate limit error, waiting a bit and trying again."
                )
                aux_exponential_backoff()

            except litellm.Timeout as e:
                logger.error(f"[{i}] Timeout error: {e}")

            except NonTerminalError as e:
                logger.error(f"[{i}] Non-terminal error: {e}")
                aux_exponential_backoff()

            except Exception as e:
                logger.error(f"[{i}] {type(e).__name__} Error: {e}")
                aux_exponential_backoff()

        logger.error(f"Failed to get response after {max_attempts} attempts.")
        return None

    def _extract_response(self, response):
        """
        Extracts the relevant information from the API response dict.
        """
        try:
            return {
                "role": response["choices"][0]["message"]["role"],
                "content": response["choices"][0]["message"]["content"],
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error extracting response: {e}")
            raise ValueError("Invalid response format from LiteLLM")

    def _count_tokens(self, messages: list, model: str):
        """
        Count tokens using LiteLLM's token counter.
        """
        try:
            import litellm
            return litellm.token_counter(model=model, messages=messages)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return None
