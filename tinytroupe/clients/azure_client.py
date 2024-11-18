import os
import openai

from openai import OpenAI, AzureOpenAI
import time
import json
import pickle
import logging
import configparser
import tiktoken
from tinytroupe import utils
from .config import default_params, config
from .openai_client import OpenAIClient
import logging

logger = logging.getLogger("tinytroupe")

class AzureClient(OpenAIClient):

    def __init__(self, cache_api_calls=default_params["cache_api_calls"], cache_file_name=default_params["cache_file_name"]) -> None:
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
    
    def _raw_model_call(self, model, chat_api_params):
        """
        Calls the Azue OpenAI Service API with the given parameters.
        """
        chat_api_params["model"] = model 

        return self.client.chat.completions.create(
                    **chat_api_params
                )