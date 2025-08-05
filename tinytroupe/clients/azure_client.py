import openai
from openai import OpenAI, AzureOpenAI
from tinytroupe import config_manager
from .openai_client import OpenAIClient
import logging

logger = logging.getLogger("tinytroupe")

class AzureClient(OpenAIClient):

    @config_manager.config_defaults(
        cache_api_calls="cache_api_calls",
        cache_file_name="cache_file_name"
    )
    def __init__(self, cache_api_calls=None, cache_file_name=None) -> None:
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