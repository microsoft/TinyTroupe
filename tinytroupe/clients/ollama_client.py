import logging
import requests
import time
import pickle
import os
from tinytroupe import utils
from .config import default_params, config, InvalidRequestError, NonTerminalError

logger = logging.getLogger("tinytroupe")

class OllamaClient:
    """
    A client for interacting with the Ollama API using direct HTTP requests.
    """
    def __init__(self, cache_api_calls=default_params["cache_api_calls"], cache_file_name=default_params["cache_file_name"]) -> None:
        logger.debug("Initializing OllamaClient")
        self.base_url = config["OpenAI"].get("BASE_URL", "http://localhost:11434/v1")
        logger.debug(f"base_url set to {self.base_url}")
        
        # Set up caching
        self.cache_api_calls = cache_api_calls
        self.cache_file_name = cache_file_name
        if self.cache_api_calls:
            self.api_cache = self._load_cache()

    def send_message(self,
                    current_messages,
                    model=default_params["model"],
                    temperature=default_params["temperature"],
                    max_tokens=None,  # Ollama doesn't use max_tokens
                    top_p=default_params["top_p"],
                    frequency_penalty=default_params["frequency_penalty"],
                    presence_penalty=default_params["presence_penalty"],
                    stop=[],
                    timeout=default_params["timeout"],
                    max_attempts=default_params["max_attempts"],
                    waiting_time=default_params["waiting_time"],
                    exponential_backoff_factor=default_params["exponential_backoff_factor"],
                    n=1,
                    echo=False):
        """
        Sends a message to the Ollama API and returns the response.
        """
        def aux_exponential_backoff():
            nonlocal waiting_time
            logger.info(f"Request failed. Waiting {waiting_time} seconds between requests...")
            time.sleep(waiting_time)
            waiting_time = waiting_time * exponential_backoff_factor

        # Prepare the API parameters
        chat_api_params = {
            "model": model,
            "messages": current_messages,
            "options":{
                "temperature": temperature,
                "top_p": top_p,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "stop": stop,
            },
           
            "stream": False,
            "n": n
            
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
                    logger.info(f"Waiting {waiting_time} seconds before next API request...")
                    time.sleep(waiting_time)
                    
                    # Make the API call
                    response = self._make_request(
                        "chat/completions",
                        method="POST",
                        json=chat_api_params,
                        timeout=timeout
                    )
                    
                    # Cache the response if caching is enabled
                    if self.cache_api_calls:
                        self.api_cache[cache_key] = response
                        self._save_cache()

                end_time = time.monotonic()
                logger.debug(f"Got response in {end_time - start_time:.2f} seconds after {i} attempts")
                
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

    def _make_request(self, endpoint, method="POST", **kwargs):
        """
        Makes a request to the Ollama API.
        """
        url = f"{self.base_url}/{endpoint}"
        logger.debug(f"Making {method} request to {url}")
        logger.debug(f"Request parameters: {kwargs}")
        
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        
        return response.json()

    def _extract_response(self, response):
        """
        Extracts the relevant information from the API response.
        """
        logger.debug(f"Extracting from response: {response}")
        try:
            return {
                'role': response['choices'][0]['message']['role'],
                'content': response['choices'][0]['message']['content']
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error extracting response: {e}")
            logger.error(f"Response structure: {response}")
            raise ValueError("Invalid response format from Ollama")

    def _save_cache(self):
        """
        Saves the API cache to disk using pickle.
        """
        with open(self.cache_file_name, "wb") as f:
            pickle.dump(self.api_cache, f)

    def _load_cache(self):
        """
        Loads the API cache from disk.
        """
        if os.path.exists(self.cache_file_name):
            with open(self.cache_file_name, "rb") as f:
                return pickle.load(f)
        return {}

    def get_models(self):
        """
        Gets the list of available models from Ollama.
        """
        try:
            response = self._make_request("models", method="GET")
            return response.get('models', [])
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
                if 'name' in message:
                    combined_text += f"{message['name']}: "
                if 'role' in message:
                    combined_text += f"{message['role']}: "
                # Add message content
                if 'content' in message:
                    combined_text += f"{message['content']}\n"
            
            # Prepare the request payload
            payload = {
                "model": model,
                "input": combined_text,
                "options": {
                    "temperature": 0  # Set to 0 since we only care about token count
                }
            }
            
            # Make the request to Ollama's API
            temp_url = self.base_url.replace("/v1", "") # Not sure what happened in their API, complete hack
            response = requests.post(
                f"{temp_url}/api/embed",
                json=payload
            )
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