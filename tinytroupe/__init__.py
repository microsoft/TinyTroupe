import os
import logging
import configparser
import rich # for rich console output
import rich.jupyter

# add current path to sys.path
import sys
sys.path.append('.')
from tinytroupe import utils # now we can import our utils

# AI disclaimers
print(\
"""
!!!!
DISCLAIMER: TinyTroupe relies on Artificial Intelligence (AI) models to generate content. 
The AI models are not perfect and may produce inappropriate or inacurate results. 
For any serious or consequential use, please review the generated content before using it.
!!!!
""")


###########################################################################
# Default parameter values
###########################################################################
# We'll use various configuration elements below
config = utils.read_config_file()
utils.pretty_print_config(config)
utils.start_logger(config)


default = {}
default["model"] = config["OpenAI"].get("MODEL", "gpt-4o")
default["embedding_model"] = config["OpenAI"].get("EMBEDDING_MODEL", "text-embedding-3-small")
if config["OpenAI"].get("API_TYPE") == "azure":
    default["azure_embedding_model_api_version"] = config["OpenAI"].get("AZURE_EMBEDDING_MODEL_API_VERSION", "2023-05-15")
default["reasoning_model"] = config["OpenAI"].get("REASONING_MODEL", "o3-mini")

default["max_tokens"] = int(config["OpenAI"].get("MAX_TOKENS", "1024"))
default["temperature"] = float(config["OpenAI"].get("TEMPERATURE", "1.0"))
default["top_p"] = int(config["OpenAI"].get("TOP_P", "0"))
default["frequency_penalty"] = float(config["OpenAI"].get("FREQ_PENALTY", "0.0"))
default["presence_penalty"] = float(
    config["OpenAI"].get("PRESENCE_PENALTY", "0.0"))
default["reasoning_effort"] = config["OpenAI"].get("REASONING_EFFORT", "high")

default["timeout"] = float(config["OpenAI"].get("TIMEOUT", "30.0"))
default["max_attempts"] = float(config["OpenAI"].get("MAX_ATTEMPTS", "0.0"))
default["waiting_time"] = float(config["OpenAI"].get("WAITING_TIME", "1"))
default["exponential_backoff_factor"] = float(config["OpenAI"].get("EXPONENTIAL_BACKOFF_FACTOR", "5"))

default["cache_api_calls"] = config["OpenAI"].getboolean("CACHE_API_CALLS", False)
default["cache_file_name"] = config["OpenAI"].get("CACHE_FILE_NAME", "openai_api_cache.pickle")

default["max_content_display_length"] = config["OpenAI"].getint("MAX_CONTENT_DISPLAY_LENGTH", 1024)

default["parallel_agent_actions"] = config["Simulation"].getboolean("PARALLEL_AGENT_ACTIONS", True)

default["action_generator_max_attempts"] = config["ActionGenerator"].getint("MAX_ATTEMPTS", 2)
default["action_generator_enable_quality_checks"] = config["ActionGenerator"].getboolean("ENABLE_QUALITY_CHECKS", False)
default["action_generator_enable_regeneration"] = config["ActionGenerator"].getboolean("ENABLE_REGENERATION", False)
default["action_generator_enable_direct_correction"] = config["ActionGenerator"].getboolean("ENABLE_DIRECT_CORRECTION", False)
default["action_generator_continue_on_failure"] = config["ActionGenerator"].getboolean("CONTINUE_ON_FAILURE", True)
default["action_generator_quality_threshold"] = config["ActionGenerator"].getint("QUALITY_THRESHOLD", 2)


## LLaMa-Index configs ########################################################
#from llama_index.embeddings.huggingface import HuggingFaceEmbedding

if config["OpenAI"].get("API_TYPE") == "azure":
    from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
else:
    from llama_index.embeddings.openai import OpenAIEmbedding

from llama_index.core import Settings, Document, VectorStoreIndex, SimpleDirectoryReader
from llama_index.readers.web import SimpleWebPageReader


# this will be cached locally by llama-index, in a OS-dependend location

##Settings.embed_model = HuggingFaceEmbedding(
##    model_name="BAAI/bge-small-en-v1.5"
##)

if config["OpenAI"].get("API_TYPE") == "azure":
    llamaindex_openai_embed_model = AzureOpenAIEmbedding(model=default["embedding_model"],
                                                        deployment_name=default["embedding_model"],
                                                        api_version=default["azure_embedding_model_api_version"],
                                                        embed_batch_size=10)
else:
    llamaindex_openai_embed_model = OpenAIEmbedding(model=default["embedding_model"], embed_batch_size=10)
Settings.embed_model = llamaindex_openai_embed_model


###########################################################################
# Fixes and tweaks
###########################################################################

# fix an issue in the rich library: we don't want margins in Jupyter!
rich.jupyter.JUPYTER_HTML_FORMAT = \
    utils.inject_html_css_style_prefix(rich.jupyter.JUPYTER_HTML_FORMAT, "margin:0px;")


