import os
import openai
from openai import OpenAI, AzureOpenAI
import time
import json
import pickle
import logging
import configparser
from pydantic import BaseModel
from typing import Union
import textwrap  # to dedent strings
from typing import List, Dict


import tiktoken
from tinytroupe import utils
from tinytroupe.control import transactional

logger = logging.getLogger("tinytroupe")

# We'll use various configuration elements below
config = utils.read_config_file()

###########################################################################
# Default parameter values
###########################################################################
default = {}
default["model"] = config["OpenAI"].get("MODEL", "gpt-4o")
default["max_tokens"] = int(config["OpenAI"].get("MAX_TOKENS", "1024"))
default["temperature"] = float(config["OpenAI"].get("TEMPERATURE", "1.0"))
default["top_p"] = int(config["OpenAI"].get("TOP_P", "0"))
default["frequency_penalty"] = float(config["OpenAI"].get("FREQ_PENALTY", "0.0"))
default["presence_penalty"] = float(
    config["OpenAI"].get("PRESENCE_PENALTY", "0.0"))
default["timeout"] = float(config["OpenAI"].get("TIMEOUT", "30.0"))
default["max_attempts"] = float(config["OpenAI"].get("MAX_ATTEMPTS", "0.0"))
default["waiting_time"] = float(config["OpenAI"].get("WAITING_TIME", "1"))
default["exponential_backoff_factor"] = float(config["OpenAI"].get("EXPONENTIAL_BACKOFF_FACTOR", "5"))

default["embedding_model"] = config["OpenAI"].get("EMBEDDING_MODEL", "text-embedding-3-small")

default["cache_api_calls"] = config["OpenAI"].getboolean("CACHE_API_CALLS", False)
default["cache_file_name"] = config["OpenAI"].get("CACHE_FILE_NAME", "openai_api_cache.pickle")

###########################################################################
# Model calling helpers
###########################################################################

class LLMRequest:
    """
    A class that represents an LLM model call. It contains the input messages, the model configuration, and the model output.
    """
    def __init__(self, system_template_name:str=None, system_prompt:str=None, 
                 user_template_name:str=None, user_prompt:str=None, 
                 output_type=None,
                 **model_params):
        """
        Initializes an LLMCall instance with the specified system and user templates, or the system and user prompts.
        If a template is specified, the corresponding prompt must be None, and vice versa.
        """
        if (system_template_name is not None and system_prompt is not None) or \
        (user_template_name is not None and user_prompt is not None) or\
        (system_template_name is None and system_prompt is None) or \
        (user_template_name is None and user_prompt is None):
            raise ValueError("Either the template or the prompt must be specified, but not both.") 
        
        self.system_template_name = system_template_name
        self.user_template_name = user_template_name
        
        self.system_prompt = textwrap.dedent(system_prompt) # remove identation
        self.user_prompt = textwrap.dedent(user_prompt) # remove identation

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
        if self.system_template_name is not None and self.user_template_name is not None:
            self.messages = utils.compose_initial_LLM_messages_with_templates(self.system_template_name, self.user_template_name, rendering_configs)
        else:
            self.messages = [{"role": "system", "content": self.system_prompt}, 
                             {"role": "user", "content": self.user_prompt}]
        
        
        #
        # Setup typing for the output
        #
        if self.output_type is not None:
            # specify the default structured output. We can change it below if needed.
            self.model_params["response_format"] = LLMScalarWithJustificationResponse
            extra_messages = [{"role": "system", 
                               "content": "In your response, you **MUST** provide a value, along with a justification and your confidence level that the value and justification are correct (0.0 means no confidence, 1.0 means complete confidence)."+
                                             "Furtheremore, your response **MUST** be a JSON object with the following structure: {\"justification\": justification, \"value\": value,  \"confidence\": confidence}." +
                                             "Note that \"justification\" comes first, this is to allow you to think through before providing the value."}]
            

            # specify the value type
            if self.output_type == bool:
                self.messages.append(self._request_bool_llm_message())
            elif self.output_type == int:
                self.messages.append(self._request_integer_llm_message())
            elif self.output_type == float:
                self.messages.append(self._request_float_llm_message())
            elif isinstance(self.output_type, list) and all(isinstance(option, str) for option in self.output_type):
                self.messages.append(self._request_enumerable_llm_message(self.output_type))
            elif self.output_type == str:
                pass
            elif self.output_type == List[Dict[str, any]]:
                # override the response format, because the pydantic model is not compatible with the arbitrary list of dict type
                self.model_params["response_format"] = {"type": "json_object"}
                self.messages.append(self._request_list_of_dict_llm_message())
            elif self.output_type == dict or self.output_type == "json":
                # override the response format, because the pydantic model is not compatible with the arbitrary dict type
                self.model_params["response_format"] = {"type": "json_object"}
                self.messages.append(self._request_dict_llm_message())
            
            elif self.output_type == list:
                # override the response format, because the pydantic model is not compatible with the arbitrary list type
                self.model_params["response_format"] = {"type": "json_object"}
                self.messages.append(self._request_list_llm_message())  
            
            # check if it is actually a pydantic model
            elif issubclass(self.output_type, BaseModel):
                # completely override the response format
                self.model_params["response_format"] = self.output_type

                # replace formatting instruction
                extra_messages = [{"role": "system",
                                      "content": "Your response **MUST** be a JSON object."}]
            else:
                raise ValueError(f"Unsupported output type: {self.output_type}")

            self.messages += extra_messages
        
        #
        # call the LLM model
        #
        self.model_output = client().send_message(self.messages, **self.model_params)

        if 'content' in self.model_output:
            self.response_raw = self.response_value = self.model_output['content']            

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
                elif isinstance(self.output_type, list) and all(isinstance(option, str) for option in self.output_type):
                    self.response_value = self._coerce_to_enumerable(self.response_value, self.output_type)
                elif self.output_type == List[Dict[str, any]]:
                    self.response_value = self._coerce_to_dict_or_list(self.response_value)
                elif self.output_type == str:
                    pass
                elif self.output_type == dict or self.output_type == "json":
                    self.response_value = self._coerce_to_dict_or_list(self.response_value)
                elif self.output_type == list:
                    self.response_value = self._coerce_to_list(self.response_value)
                # check if it is actually a pydantic model
                elif issubclass(self.output_type, BaseModel):
                    self.response_value = self.output_type.parse_obj(self.response_json)
                else:
                    raise ValueError(f"Unsupported output type: {self.output_type}")
            
            return self.response_value
        
        else:
            logger.error(f"Model output does not contain 'content' key: {self.model_output}")
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
        match = re.search(r'\b(?:True|False|Yes|No|Positive|Negative)\b', llm_output, re.IGNORECASE)
        if match:
            first_match = match.group(0).lower()
            if first_match in ["true", "yes", "positive"]:
                return True
            elif first_match in ["false", "no", "negative"]:
                return False
            
        raise ValueError("The LLM output does not contain a recognizable boolean value.")

    def _request_bool_llm_message(self):
        return {"role": "user", 
                "content": "The `value` field you generate **must** be either 'True' or 'False'. This is critical for later processing. If you don't know the correct answer, just output 'False'."}


    def _coerce_to_integer(self, llm_output:str):
        """
        Coerces the LLM output to an integer value.

        This method looks for the first occurrence of an integer in the LLM output, such that
          - the first occurrence of the integer is considered, the rest is ignored. For example,  "There are 3 cats" will be considered 3;
          - if no integer is found, the method raises an error. So it is important that the prompts actually requests an integer value. 

        Args:
            llm_output (str, int): The LLM output to coerce.
        
        Returns:
            The integer value of the LLM output.
        """

        # if the LLM output is already an integer, we return it
        if isinstance(llm_output, int):
            return llm_output

        # let's extract the first occurrence of an integer in the LLM output.
        # using a regular expression
        import re
        match = re.search(r'\b\d+\b', llm_output)
        if match:
            return int(match.group(0))
            
        raise ValueError("The LLM output does not contain a recognizable integer value.")

    def _request_integer_llm_message(self):
        return {"role": "user", 
                "content": "The `value` field you generate **must** be an integer number (e.g., '1'). This is critical for later processing.."}
    
    def _coerce_to_float(self, llm_output:str):
        """
        Coerces the LLM output to a float value.

        This method looks for the first occurrence of a float in the LLM output, such that
          - the first occurrence of the float is considered, the rest is ignored. For example,  "The price is $3.50" will be considered 3.50;
          - if no float is found, the method raises an error. So it is important that the prompts actually requests a float value. 

        Args:
            llm_output (str, float): The LLM output to coerce.
        
        Returns:
            The float value of the LLM output.
        """

        # if the LLM output is already a float, we return it
        if isinstance(llm_output, float):
            return llm_output
        

        # let's extract the first occurrence of a float in the LLM output.
        # using a regular expression
        import re
        match = re.search(r'\b\d+\.\d+\b', llm_output)
        if match:
            return float(match.group(0))
            
        raise ValueError("The LLM output does not contain a recognizable float value.")

    def _request_float_llm_message(self):
        return {"role": "user", 
                "content": "The `value` field you generate **must** be a float number (e.g., '980.16'). This is critical for later processing."}
    
    def _coerce_to_enumerable(self, llm_output:str, options:list):
        """
        Coerces the LLM output to one of the specified options.

        This method looks for the first occurrence of one of the specified options in the LLM output, such that
          - the first occurrence of the option is considered, the rest is ignored. For example,  "I prefer cats" will be considered "cats";
          - if no option is found, the method raises an error. So it is important that the prompts actually requests one of the specified options. 

        Args:
            llm_output (str): The LLM output to coerce.
            options (list): The list of options to consider.
        
        Returns:
            The option value of the LLM output.
        """

        # let's extract the first occurrence of one of the specified options in the LLM output.
        # using a regular expression
        import re
        match = re.search(r'\b(?:' + '|'.join(options) + r')\b', llm_output, re.IGNORECASE)
        if match:
            return match.group(0)
            
        raise ValueError("The LLM output does not contain a recognizable option value.")

    def _request_enumerable_llm_message(self, options:list):
        options_list_as_string = ', '.join([f"'{o}'" for o in options])
        return {"role": "user", 
                "content": f"The `value` field you generate **must** be exactly one of the following strings: {options_list_as_string}. This is critical for later processing."}

    def _coerce_to_dict_or_list(self, llm_output:str):
        """
        Coerces the LLM output to a list or dictionary, i.e., a JSON structure.

        This method looks for a JSON object in the LLM output, such that
          - the JSON object is considered;
          - if no JSON object is found, the method raises an error. So it is important that the prompts actually requests a JSON object. 

        Args:
            llm_output (str): The LLM output to coerce.
        
        Returns:
            The dictionary value of the LLM output.
        """

        # if the LLM output is already a dictionary, we return it
        if isinstance(llm_output, dict):
            return llm_output

        return utils.extract_json(llm_output)   

    def _request_dict_llm_message(self):
            return {"role": "user", 
                    "content": "The `value` field you generate **must** be a JSON structure embedded in a string. This is critical for later processing."}    
    
    def _request_list_of_dict_llm_message(self):
            return {"role": "user", 
                    "content": "The `value` field you generate **must** be a list of dictionaries, specified as a JSON structure embedded in a string. For example, `[\{...\}, \{...\}, ...]`. This is critical for later processing."}    

    def _coerce_to_list(self, llm_output:str):
        """
        Coerces the LLM output to a list.

        This method looks for a list in the LLM output, such that
          - the list is considered;
          - if no list is found, the method raises an error. So it is important that the prompts actually requests a list. 

        Args:
            llm_output (str): The LLM output to coerce.
        
        Returns:
            The list value of the LLM output.
        """

        # if the LLM output is already a list, we return it
        if isinstance(llm_output, list):
            return llm_output

        # must make sure there's actually a list. Let's start with regex
        import re
        match = re.search(r'\[.*\]', llm_output)
        if match:
            return json.loads(match.group(0))
        
        raise ValueError("The LLM output does not contain a recognizable list value.")

    def _request_list_llm_message(self):
        return {"role": "user", 
                "content": "The `value` field you generate **must** be a JSON **list** (e.g., [\"apple\", 1, 0.9]), NOT a dictionary, always embedded in a string. This is critical for later processing."}    
    
    def __repr__(self):
        return f"LLMRequest(messages={self.messages}, model_params={self.model_params}, model_output={self.model_output})"

#
# Data structures to enforce output format during LLM API call.
#
class LLMScalarWithJustificationResponse(BaseModel):
    """
    LLMTypedResponse represents a typed response from an LLM (Language Learning Model).
    Attributes:
        value (str, int, float, bool): The value of the response.
        justification (str): The justification or explanation for the response.
    """
    justification: str # comes first to allow thinking before providing the value
    value: Union[str, int, float, bool]
    confidence: float


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

    def send_message(self,
                    current_messages,
                     model=default["model"],
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
                     n = 1,
                     response_format=None,
                     echo=False):
        """
        Sends a message to the OpenAI API and returns the response.

        Args:
        current_messages (list): A list of dictionaries representing the conversation history.
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
                logger.error(f"[{i}] Error: {e}")

        logger.error(f"Failed to get response after {max_attempts} attempts.")
        return None
    
    def _raw_model_call(self, model, chat_api_params):
        """
        Calls the OpenAI API with the given parameters. Subclasses should
        override this method to implement their own API calls.
        """   

        if "response_format" in chat_api_params:
            # to enforce the response format via pydantic, we need to use a different method

            del chat_api_params["stream"]

            return self.client.beta.chat.completions.parse(
                    **chat_api_params
                )
        
        else:
            return self.client.chat.completions.create(
                        **chat_api_params
                    )

    def _raw_model_response_extractor(self, response):
        """
        Extracts the response from the API response. Subclasses should
        override this method to implement their own response extraction.
        """
        return response.choices[0].message.to_dict()

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
                }:
                tokens_per_message = 3
                tokens_per_name = 1
            elif model == "gpt-3.5-turbo-0301":
                tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
                tokens_per_name = -1  # if there's a name, the role is omitted
            elif "gpt-3.5-turbo" in model:
                logger.debug("Token count: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
                return self._count_tokens(messages, model="gpt-3.5-turbo-0613")
            elif ("gpt-4" in model) or ("ppo" in model):
                logger.debug("Token count: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
                return self._count_tokens(messages, model="gpt-4-0613")
            else:
                raise NotImplementedError(
                    f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
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
        pickle.dump(self.api_cache, open(self.cache_file_name, "wb"))

    
    def _load_cache(self):

        """
        Loads the API cache from disk.
        """
        # unpickle
        return pickle.load(open(self.cache_file_name, "rb")) if os.path.exists(self.cache_file_name) else {}

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
        self.client = AzureOpenAI(azure_endpoint= os.getenv("AZURE_OPENAI_ENDPOINT"),
                                  api_version = config["OpenAI"]["AZURE_API_VERSION"],
                                  api_key = os.getenv("AZURE_OPENAI_KEY"))
    

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



