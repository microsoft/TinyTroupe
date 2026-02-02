import logging
import os

import httpx
import openai
from openai import AzureOpenAI, OpenAI

from tinytroupe import config_manager

from .openai_client import OpenAIClient

logger = logging.getLogger("tinytroupe")


class AzureClient(OpenAIClient):

    @config_manager.config_defaults(
        cache_api_calls="cache_api_calls", cache_file_name="cache_file_name"
    )
    def __init__(self, cache_api_calls=None, cache_file_name=None) -> None:
        logger.debug("Initializing AzureClient")
        super().__init__(cache_api_calls, cache_file_name)

    @config_manager.config_defaults(timeout="timeout")
    def _setup_from_config(self, timeout=None):
        """
        Sets up the Azure OpenAI Service API configurations for this client,
        including the API endpoint and key.
        """
        # Create httpx client with proper timeouts to prevent hanging
        # This ensures timeouts work at ALL levels: connection, read, write, pool
        httpx_client = httpx.Client(
            timeout=httpx.Timeout(
                timeout=timeout,      # Overall timeout
                connect=10.0,         # Connection timeout (fixed at 10s)
                read=timeout,         # Read timeout (from config)
                write=10.0,           # Write timeout (fixed at 10s)
                pool=5.0              # Pool timeout (fixed at 5s)
            )
        )
        
        if os.getenv("AZURE_OPENAI_KEY"):
            logger.info("Using Azure OpenAI Service API with key...")
            self.client = AzureOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=config_manager.get("AZURE_API_VERSION"),
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                max_retries=0,  # we do our own retrying with customized exponential backoff
                http_client=httpx_client
            )
        else:  # Use Entra ID Auth
            logger.info("Using Azure OpenAI Service API with Entra ID Auth.")
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider

            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            self.client = AzureOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=config_manager.get("AZURE_API_VERSION"),
                azure_ad_token_provider=token_provider,
                max_retries=0,  # we do our own retrying with customized exponential backoff
                http_client=httpx_client
            )
