from tinytroupe.enrichment import logger
from tinytroupe.utils import JsonSerializableRegistry
from tinytroupe.utils.llm import LLMChat
import tinytroupe.utils as utils


class TinyStyler(JsonSerializableRegistry):
    """
    A class for applying a specified writing or speaking style to content while preserving
    the original information.
    """

    def __init__(self, use_past_results_in_context=False) -> None:
        """
        Initialize the TinyStyler.

        Args:
            use_past_results_in_context (bool): Whether to use past styling results in the context.
        """
        self.use_past_results_in_context = use_past_results_in_context
        self.context_cache = []
    
    def apply_style(self, content: str, style: str, content_type: str = None, 
                   context_info: str = "", context_cache: list = None, verbose: bool = False, 
                   temperature: float = 0.7):
        """
        Apply a specified style to the content while preserving all the original information.

        Args:
            content (str): The content to style.
            style (str): The style to apply (e.g., "professional", "casual", "technical", etc.).
            content_type (str, optional): The type of content (e.g., "email", "report", "conversation").
            context_info (str, optional): Additional context information.
            context_cache (list, optional): Previous styling results to use as context.
            verbose (bool, optional): Whether to print debug information.
            temperature (float, optional): The temperature to use for the LLM generation.

        Returns:
            str: The styled content.
        """
        if context_cache is None and self.use_past_results_in_context:
            context_cache = self.context_cache

        rendering_configs = {
            "content": content,
            "style": style,
            "content_type": content_type,
            "context_info": context_info,
            "context_cache": context_cache
        }

        # Initialize the LLMChat with appropriate templates
        chat = LLMChat(
            system_template_name="styler.system.mustache",
            user_template_name="styler.user.mustache",
            base_module_folder="enrichment",
            temperature=temperature
        )
        
        # Call the model and get the response
        result = chat.call(**rendering_configs)
        
        debug_msg = f"Styling result: {result}"
        logger.debug(debug_msg)
        if verbose:
            print(debug_msg)
            
        # Extract the styled content from code blocks if present
        if result is not None:
            styled_content = utils.extract_code_block(result)
            # If no code block was found, use the raw result
            if not styled_content:
                styled_content = result
            
            # Add to context cache if enabled
            if self.use_past_results_in_context:
                self.context_cache.append({
                    "original": content,
                    "style": style,
                    "styled": styled_content
                })
                
            return styled_content
        else:
            return None
