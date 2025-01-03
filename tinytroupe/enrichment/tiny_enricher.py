from tinytroupe.enrichment import logger
from tinytroupe.utils import JsonSerializableRegistry


from tinytroupe import openai_utils
import tinytroupe.utils as utils

class TinyEnricher(JsonSerializableRegistry):

    def __init__(self, use_past_results_in_context=False) -> None:
        self.use_past_results_in_context = use_past_results_in_context

        self.context_cache = []
    
    def enrich_content(self, requirements: str, content:str, content_type:str =None, context_info:str ="", context_cache:list=None, verbose:bool=False):

        rendering_configs = {"requirements": requirements,
                             "content": content,
                             "content_type": content_type, 
                             "context_info": context_info,
                             "context_cache": context_cache}

        messages = utils.compose_initial_LLM_messages_with_templates("enricher.system.mustache", "enricher.user.mustache", 
                                                                     base_module_folder = "enrichment",
                                                                     rendering_configs=rendering_configs)
        
        next_message = openai_utils.client().send_message(messages, temperature=1.0, frequency_penalty=0.0, presence_penalty=0.0)
        
        debug_msg = f"Enrichment result message: {next_message}"
        logger.debug(debug_msg)
        if verbose:
            print(debug_msg)

        if next_message is not None:
            result = utils.extract_code_block(next_message["content"])
        else:
            result = None

        return result
    

