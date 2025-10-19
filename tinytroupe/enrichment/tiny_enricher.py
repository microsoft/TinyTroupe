from tinytroupe.enrichment import logger
from tinytroupe.utils import JsonSerializableRegistry


from tinytroupe import openai_utils
import tinytroupe.utils as utils
from pydantic import BaseModel, TypeAdapter

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
        
        # Define strict structured output for enrichment
        class EnrichmentOutput(BaseModel):
            content: str
            
            class Config:
                extra = 'forbid'  # Pydantic v2: reject extra fields

        # Prefer Responses JSON Schema with strict mode when available; fall back to Pydantic class
        response_format = EnrichmentOutput
        try:
            schema = TypeAdapter(EnrichmentOutput).json_schema()
            
            # Ensure additionalProperties: false for strict mode compatibility
            def _enforce_no_additional(node):
                if isinstance(node, dict):
                    if node.get("type") == "object":
                        node["additionalProperties"] = False
                    for v in node.get("properties", {}).values():
                        _enforce_no_additional(v)
                    if "items" in node:
                        _enforce_no_additional(node["items"])
            
            _enforce_no_additional(schema)
            
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": "EnrichmentOutput", "schema": schema, "strict": True},
            }
        except Exception:
            pass

        next_message = openai_utils.client().send_message(
            messages,
            temperature=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            response_format=response_format,
        )
        
        debug_msg = f"Enrichment result message: {next_message}"
        logger.debug(debug_msg)
        if verbose:
            print(debug_msg)

        if next_message is None:
            return None

        # Refusal handling
        refusal = next_message.get("refusal")
        if refusal:
            logger.warning(f"Model refusal received in enrichment: {refusal}")
            raise EnrichmentRefusedException(refusal)

        # Prefer typed parsed payload; fallback to JSON decode or code-block extraction
        parsed = next_message.get("parsed")
        if parsed is not None:
            return parsed

        # When using JSON Schema (text.format), the content is JSON-encoded; decode it
        content = next_message.get("content")
        if content:
            try:
                import json
                return json.loads(content)
            except (json.JSONDecodeError, TypeError):
                # Fall back to code-block extraction for legacy
                return utils.extract_code_block(content)
        
        return None


class EnrichmentRefusedException(Exception):
    pass
    

