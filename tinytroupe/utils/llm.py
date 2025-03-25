import re
import json
import os
import chevron
from typing import Collection, Dict, List, Union
from pydantic import BaseModel
import copy
import functools
import inspect
import pprint
import textwrap

from tinytroupe import utils
from tinytroupe.utils import logger
from tinytroupe.utils.rendering import break_text_at_length

################################################################################
# Model input utilities
################################################################################

def compose_initial_LLM_messages_with_templates(system_template_name:str, user_template_name:str=None, 
                                                base_module_folder:str=None,
                                                rendering_configs:dict={}) -> list:
    """
    Composes the initial messages for the LLM model call, under the assumption that it always involves 
    a system (overall task description) and an optional user message (specific task description). 
    These messages are composed using the specified templates and rendering configurations.
    """

    # ../ to go to the base library folder, because that's the most natural reference point for the user
    if base_module_folder is None:
        sub_folder =  "../prompts/" 
    else:
        sub_folder = f"../{base_module_folder}/prompts/"

    base_template_folder = os.path.join(os.path.dirname(__file__), sub_folder)    

    system_prompt_template_path = os.path.join(base_template_folder, f'{system_template_name}')
    user_prompt_template_path = os.path.join(base_template_folder, f'{user_template_name}')

    messages = []

    messages.append({"role": "system", 
                         "content": chevron.render(
                             open(system_prompt_template_path).read(), 
                             rendering_configs)})
    
    # optionally add a user message
    if user_template_name is not None:
        messages.append({"role": "user", 
                            "content": chevron.render(
                                    open(user_prompt_template_path).read(), 
                                    rendering_configs)})
    return messages


#
# Data structures to enforce output format during LLM API call.
#

class LLMScalarWithJustificationResponse(BaseModel):
    """
    Represents a typed response from an LLM (Language Learning Model) including justification.
    Attributes:
        value (str, int, float, bool): The value of the response.
        justification (str): The justification or explanation for the response.
    """
    value: Union[str, int, float, bool]
    justification: str
    confidence: float

class LLMScalarWithJustificationAndReasoningResponse(BaseModel):
    """
    Represents a typed response from an LLM (Language Learning Model) including justification and reasoning.
    Attributes:
        reasoning (str): The reasoning behind the response.
        value (str, int, float, bool): The value of the response.
        justification (str): The justification or explanation for the response.
        confidence (float): The confidence level of the response.
    """
    reasoning: str

    # we need to repeat these fields here, instead of inheriting from LLMScalarWithJustificationResponse,
    # because we need to ensure `reasoning` is always the first field in the JSON object.
    value: Union[str, int, float, bool]
    justification: str
    confidence: float



###########################################################################
# Model calling helpers
###########################################################################

class LLMChat:
    """
    A class that represents an ongoing LLM conversation. It maintains the conversation history,
    allows adding new messages, and handles model output type coercion.
    """

    def __init__(self, system_template_name:str=None, system_prompt:str=None,
                 user_template_name:str=None, user_prompt:str=None,
                 output_type=None,
                 enable_reasoning_step:bool=False,
                 **model_params):
        """
        Initializes an LLMChat instance with the specified system and user templates, or the system and user prompts.
        If a template is specified, the corresponding prompt must be None, and vice versa.

        Args:
            system_template_name (str): Name of the system template file.
            system_prompt (str): System prompt content.
            user_template_name (str): Name of the user template file.
            user_prompt (str): User prompt content.
            output_type (type): Expected type of the model output.
            enable_reasoning_step (bool): Flag to enable reasoning step in the conversation. This IS NOT the use of "reasoning models" (e.g., o1, o3),
              but rather the use of an additional reasoning step in the regular text completion.
            **model_params: Additional parameters for the LLM model call.

        """
        if (system_template_name is not None and system_prompt is not None) or \
        (user_template_name is not None and user_prompt is not None) or\
        (system_template_name is None and system_prompt is None) or \
        (user_template_name is None and user_prompt is None):
            raise ValueError("Either the template or the prompt must be specified, but not both.")

        self.system_template_name = system_template_name
        self.user_template_name = user_template_name

        self.system_prompt = textwrap.dedent(system_prompt) if system_prompt is not None else None
        self.user_prompt = textwrap.dedent(user_prompt) if user_prompt is not None else None

        self.output_type = output_type

        self.enable_reasoning_step = enable_reasoning_step

        self.model_params = model_params
        
        # Conversation history
        self.messages = []
        self.conversation_history = []
        
        # Response tracking
        self.response_raw = None
        self.response_json = None
        self.response_reasoning = None
        self.response_value = None
        self.response_justification = None
        self.response_confidence = None
        
    def __call__(self, *args, **kwds):
        return self.call(*args, **kwds)
        
    def _render_template(self, template_name, base_module_folder=None, rendering_configs={}):
        """
        Helper method to render templates for messages.
        
        Args:
            template_name: Name of the template file
            base_module_folder: Optional subfolder path within the library
            rendering_configs: Configuration variables for template rendering
            
        Returns:
            Rendered template content
        """
        if base_module_folder is None:
            sub_folder =  "../prompts/" 
        else:
            sub_folder = f"../{base_module_folder}/prompts/"
            
        base_template_folder = os.path.join(os.path.dirname(__file__), sub_folder)
        template_path = os.path.join(base_template_folder, template_name)
        
        return chevron.render(open(template_path).read(), rendering_configs)

    def add_user_message(self, message=None, template_name=None, base_module_folder=None, rendering_configs={}):
        """
        Add a user message to the conversation.
        
        Args:
            message: The direct message content from the user (mutually exclusive with template_name)
            template_name: Optional template file name to use for the message
            base_module_folder: Optional subfolder for template location
            rendering_configs: Configuration variables for template rendering
            
        Returns:
            self for method chaining
        """
        if message is not None and template_name is not None:
            raise ValueError("Either message or template_name must be specified, but not both.")
        
        if template_name is not None:
            content = self._render_template(template_name, base_module_folder, rendering_configs)
        else:
            content = textwrap.dedent(message)
            
        self.messages.append({"role": "user", "content": content})
        return self
        
    def add_system_message(self, message=None, template_name=None, base_module_folder=None, rendering_configs={}):
        """
        Add a system message to the conversation.
        
        Args:
            message: The direct message content from the system (mutually exclusive with template_name)
            template_name: Optional template file name to use for the message
            base_module_folder: Optional subfolder for template location
            rendering_configs: Configuration variables for template rendering
            
        Returns:
            self for method chaining
        """
        if message is not None and template_name is not None:
            raise ValueError("Either message or template_name must be specified, but not both.")
        
        if template_name is not None:
            content = self._render_template(template_name, base_module_folder, rendering_configs)
        else:
            content = textwrap.dedent(message)
            
        self.messages.append({"role": "system", "content": content})
        return self
    
    def add_assistant_message(self, message=None, template_name=None, base_module_folder=None, rendering_configs={}):
        """
        Add an assistant message to the conversation.
        
        Args:
            message: The direct message content from the assistant (mutually exclusive with template_name)
            template_name: Optional template file name to use for the message
            base_module_folder: Optional subfolder for template location
            rendering_configs: Configuration variables for template rendering
            
        Returns:
            self for method chaining
        """
        if message is not None and template_name is not None:
            raise ValueError("Either message or template_name must be specified, but not both.")
        
        if template_name is not None:
            content = self._render_template(template_name, base_module_folder, rendering_configs)
        else:
            content = textwrap.dedent(message)
            
        self.messages.append({"role": "assistant", "content": content})
        return self

    def call(self, output_type=None, **rendering_configs):
        """
        Initiates or continues the conversation with the LLM model using the current message history.

        Args:
            output_type: Optional parameter to override the output type for this specific call
            rendering_configs: The rendering configurations (template variables) to use when composing the initial messages.

        Returns:
            The content of the model response.
        """
        from tinytroupe.openai_utils import client # import here to avoid circular import

        # Initialize the conversation if this is the first call
        if not self.messages:
            if self.system_template_name is not None and self.user_template_name is not None:
                self.messages = utils.compose_initial_LLM_messages_with_templates(
                    self.system_template_name, 
                    self.user_template_name, 
                    rendering_configs=rendering_configs
                )
            else:
                if self.system_prompt:
                    self.messages.append({"role": "system", "content": self.system_prompt})
                if self.user_prompt:
                    self.messages.append({"role": "user", "content": self.user_prompt})

        # Use the provided output_type if specified, otherwise fall back to the instance's output_type
        current_output_type = output_type if output_type is not None else self.output_type

        # Set up typing for the output
        if current_output_type is not None:
            # Add type coercion instructions if not already added
            if not any(msg.get("content", "").startswith("In your response, you **MUST** provide a value") 
                      for msg in self.messages if msg.get("role") == "system"):
                
                if not self.enable_reasoning_step:
                    # Default structured output
                    self.model_params["response_format"] = LLMScalarWithJustificationResponse
                    
                    typing_instruction = {"role": "system",
                        "content": "In your response, you **MUST** provide a value, along with a justification and your confidence level that the value and justification are correct (0.0 means no confidence, 1.0 means complete confidence)."+
                        "Furtheremore, your response **MUST** be a JSON object with the following structure: {\"value\": value, \"justification\": justification, \"confidence\": confidence}."}
                
                else: 
                    # Override the response format to also use a reasoning step
                    self.model_params["response_format"] = LLMScalarWithJustificationAndReasoningResponse
                    
                    typing_instruction = {"role": "system",
                        "content": \
                            "In your response, you **FIRST** think step-by-step on how you are going to compute the value, and you put this reasoning in the \"reasoning\" field (which must come before all others). "+
                            "This allows you to think carefully as much as you need to deduce the best and most correct value. "+
                            "After that, you **MUST** provide the resulting value, along with a justification (which can tap into the previous reasoning), and your confidence level that the value and justification are correct (0.0 means no confidence, 1.0 means complete confidence)."+
                            "Furtheremore, your response **MUST** be a JSON object with the following structure: {\"reasoning\": reasoning, \"value\": value, \"justification\": justification, \"confidence\": confidence}."}
                    
                
                # Specify the value type
                if current_output_type == bool:
                    typing_instruction["content"] += " " + self._request_bool_llm_message()["content"]
                elif current_output_type == int:
                    typing_instruction["content"] += " " + self._request_integer_llm_message()["content"]
                elif current_output_type == float:
                    typing_instruction["content"] += " " + self._request_float_llm_message()["content"]
                elif isinstance(current_output_type, list) and all(isinstance(option, str) for option in current_output_type):
                    typing_instruction["content"] += " " + self._request_enumerable_llm_message(current_output_type)["content"]
                elif current_output_type == List[Dict[str, any]]:
                    # Override the response format
                    self.model_params["response_format"] = {"type": "json_object"}
                    typing_instruction["content"] += " " + self._request_list_of_dict_llm_message()["content"]
                elif current_output_type == dict or current_output_type == "json":
                    # Override the response format
                    self.model_params["response_format"] = {"type": "json_object"}
                    typing_instruction["content"] += " " + self._request_dict_llm_message()["content"]
                elif current_output_type == list:
                    # Override the response format
                    self.model_params["response_format"] = {"type": "json_object"}
                    typing_instruction["content"] += " " + self._request_list_llm_message()["content"]
                # Check if it is actually a pydantic model
                elif issubclass(current_output_type, BaseModel):
                    # Completely override the response format
                    self.model_params["response_format"] = current_output_type
                    typing_instruction = {"role": "system", "content": "Your response **MUST** be a JSON object."}
                elif current_output_type == str:
                    pass # no coercion needed, it is already a string
                else:
                    raise ValueError(f"Unsupported output type: {current_output_type}")
                
                self.messages.append(typing_instruction)

        # Call the LLM model with all messages in the conversation
        model_output = client().send_message(self.messages, **self.model_params)

        if 'content' in model_output:
            self.response_raw = self.response_value = model_output['content']
            
            # Add the assistant's response to the conversation history
            self.add_assistant_message(self.response_raw)
            self.conversation_history.append({"messages": copy.deepcopy(self.messages)})

            # Type coercion if output type is specified
            if current_output_type is not None:
                self.response_json = utils.extract_json(self.response_raw)

                self.response_reasoning = self.response_json.get("reasoning", None)
                self.response_value = self.response_json.get("value", None)
                self.response_justification = self.response_json.get("justification", None)
                self.response_confidence = self.response_json.get("confidence", None)

                if current_output_type == bool:
                    self.response_value = self._coerce_to_bool(self.response_value)
                elif current_output_type == int:
                    self.response_value = self._coerce_to_integer(self.response_value)
                elif current_output_type == float:
                    self.response_value = self._coerce_to_float(self.response_value)
                elif isinstance(current_output_type, list) and all(isinstance(option, str) for option in current_output_type):
                    self.response_value = self._coerce_to_enumerable(self.response_value, current_output_type)
                elif current_output_type == List[Dict[str, any]]:
                    self.response_value = self._coerce_to_dict_or_list(self.response_value)
                elif current_output_type == dict or current_output_type == "json":
                    self.response_value = self._coerce_to_dict_or_list(self.response_value)
                elif current_output_type == list:
                    self.response_value = self._coerce_to_list(self.response_value)
                elif issubclass(current_output_type, BaseModel):
                    self.response_value = current_output_type.parse_obj(self.response_json)
                elif current_output_type == str:
                    pass # no coercion needed, it is already a string
                else:
                    raise ValueError(f"Unsupported output type: {current_output_type}")

            return self.response_value
        else:
            logger.error(f"Model output does not contain 'content' key: {model_output}")
            return None
    
    def continue_conversation(self, user_message=None, **rendering_configs):
        """
        Continue the conversation with a new user message and get a response.
        
        Args:
            user_message: The new message from the user
            rendering_configs: Additional rendering configurations
            
        Returns:
            The content of the model response
        """
        if user_message:
            self.add_user_message(user_message)
        return self.call(**rendering_configs)
    
    def reset_conversation(self):
        """
        Reset the conversation state but keep the initial configuration.
        
        Returns:
            self for method chaining
        """
        self.messages = []
        self.response_raw = None
        self.response_json = None
        self.response_value = None
        self.response_justification = None
        self.response_confidence = None
        return self
    
    def get_conversation_history(self):
        """
        Get the full conversation history.
        
        Returns:
            List of all messages in the conversation
        """
        return self.messages
    
    # Keep all the existing coercion methods
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
        return f"LLMChat(messages={self.messages}, model_params={self.model_params})"


def llm(**model_overrides):
    """
    Decorator that turns the decorated function into an LLM-based function.
    The decorated function must either return a string (the instruction to the LLM)
    or a one-argument function that will be used to post-process the LLM response.

    If the function returns a string, the function's docstring will be used as the system prompt,
    and the returned string will be used as the user prompt. If the function returns a function,
    the parameters of the function will be used instead as the system instructions to the LLM,
    and the returned function will be used to post-process the LLM response.


    The LLM response is coerced to the function's annotated return type, if present.

    Usage example:
        @llm(model="gpt-4-0613", temperature=0.5, max_tokens=100)
        def joke():
            return "Tell me a joke."
    
    Usage example with post-processing:
        @llm()
        def unique_joke_list():
            \"\"\"Creates a list of unique jokes.\"\"\"
            return lambda x: list(set(x.split("\n")))
    
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            sig = inspect.signature(func)
            return_type = sig.return_annotation if sig.return_annotation != inspect.Signature.empty else str
            postprocessing_func = lambda x: x # by default, no post-processing
            
            system_prompt = "You are an AI system that executes a computation as defined below.\n\n"
            if func.__doc__ is not None:
                system_prompt += func.__doc__.strip() 
            
            #
            # Setup user prompt
            #
            if isinstance(result, str):
                user_prompt = "EXECUTE THE INSTRUCTIONS BELOW:\n\n " + result
            
            else:
                # if there's a parameter named "self" in the function signature, remove it from args
                if "self" in sig.parameters:
                    args = args[1:]
                
                # TODO obsolete?
                #
                # if we are relying on parameters, they must be named
                #if len(args) > 0:
                #    raise ValueError("Positional arguments are not allowed in LLM-based functions whose body does not return a string.")               

                user_prompt  = f"Execute your computation as best as you can using the following input parameter values: \n"
                user_prompt += f"  - Unnamed parameters: {json.dumps(args, indent=4)}" 
                user_prompt += f"  - Named parameters: {json.dumps(kwargs, indent=4)}" 
            
            #
            # Set the post-processing function if the function returns a function
            #
            if inspect.isfunction(result):
                # uses the returned function as a post-processing function
                postprocessing_func = result
            
            
            llm_req = LLMChat(system_prompt=system_prompt,
                                 user_prompt=user_prompt,
                                 output_type=return_type,
                                 **model_overrides)
            
            llm_result = postprocessing_func(llm_req.call())
            
            return llm_result
        return wrapper
    return decorator

################################################################################	
# Model output utilities
################################################################################
def extract_json(text: str) -> dict:
    """
    Extracts a JSON object from a string, ignoring: any text before the first 
    opening curly brace; and any Markdown opening (```json) or closing(```) tags.
    """
    try:
        logger.debug(f"Extracting JSON from text: {text}")

        # if it already is a dictionary or list, return it
        if isinstance(text, dict) or isinstance(text, list):

            # validate that all the internal contents are indeed JSON-like
            try:
                json.dumps(text)
            except Exception as e:
                logger.error(f"Error occurred while validating JSON: {e}. Input text: {text}.")
                return {}

            logger.debug(f"Text is already a dictionary. Returning it.")
            return text

        filtered_text = ""

        # remove any text before the first opening curly or square braces, using regex. Leave the braces.
        filtered_text = re.sub(r'^.*?({|\[)', r'\1', text, flags=re.DOTALL)

        # remove any trailing text after the LAST closing curly or square braces, using regex. Leave the braces.
        filtered_text  =  re.sub(r'(}|\])(?!.*(\]|\})).*$', r'\1', filtered_text, flags=re.DOTALL)
        
        # remove invalid escape sequences, which show up sometimes
        filtered_text = re.sub("\\'", "'", filtered_text) # replace \' with just '
        filtered_text = re.sub("\\,", ",", filtered_text)

        # use strict=False to correctly parse new lines, tabs, etc.
        parsed = json.loads(filtered_text, strict=False)
        
        # return the parsed JSON object
        return parsed
    
    except Exception as e:
        logger.error(f"Error occurred while extracting JSON: {e}. Input text: {text}. Filtered text: {filtered_text}")
        return {}

def extract_code_block(text: str) -> str:
    """
    Extracts a code block from a string, ignoring any text before the first 
    opening triple backticks and any text after the closing triple backticks.
    """
    try:
        # remove any text before the first opening triple backticks, using regex. Leave the backticks.
        text = re.sub(r'^.*?(```)', r'\1', text, flags=re.DOTALL)

        # remove any trailing text after the LAST closing triple backticks, using regex. Leave the backticks.
        text  =  re.sub(r'(```)(?!.*```).*$', r'\1', text, flags=re.DOTALL)
        
        return text
    
    except Exception:
        return ""

################################################################################
# Model control utilities
################################################################################    

def repeat_on_error(retries:int, exceptions:list):
    """
    Decorator that repeats the specified function call if an exception among those specified occurs, 
    up to the specified number of retries. If that number of retries is exceeded, the
    exception is raised. If no exception occurs, the function returns normally.

    Args:
        retries (int): The number of retries to attempt.
        exceptions (list): The list of exception classes to catch.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    logger.debug(f"Exception occurred: {e}")
                    if i == retries - 1:
                        raise e
                    else:
                        logger.debug(f"Retrying ({i+1}/{retries})...")
                        continue
        return wrapper
    return decorator

 
def try_function(func, postcond_func=None, retries=5, exceptions=[Exception]):

    @repeat_on_error(retries=retries, exceptions=exceptions)
    def aux_apply_func():
        logger.debug(f"Trying function {func.__name__}...")
        result = func()
        logger.debug(f"Result of function {func.__name__}: {result}")
        
        if postcond_func is not None:
            if not postcond_func(result):
                # must raise an exception if the postcondition is not met.
                raise ValueError(f"Postcondition not met for function {func.__name__}!")

        return result
    
    return aux_apply_func()
   
################################################################################
# Prompt engineering
################################################################################
def add_rai_template_variables_if_enabled(template_variables: dict) -> dict:
    """
    Adds the RAI template variables to the specified dictionary, if the RAI disclaimers are enabled.
    These can be configured in the config.ini file. If enabled, the variables will then load the RAI disclaimers from the 
    appropriate files in the prompts directory. Otherwise, the variables will be set to None.

    Args:
        template_variables (dict): The dictionary of template variables to add the RAI variables to.

    Returns:
        dict: The updated dictionary of template variables.
    """

    from tinytroupe import config # avoids circular import
    rai_harmful_content_prevention = config["Simulation"].getboolean(
        "RAI_HARMFUL_CONTENT_PREVENTION", True 
    )
    rai_copyright_infringement_prevention = config["Simulation"].getboolean(
        "RAI_COPYRIGHT_INFRINGEMENT_PREVENTION", True
    )

    # Harmful content
    with open(os.path.join(os.path.dirname(__file__), "prompts/rai_harmful_content_prevention.md"), "r") as f:
        rai_harmful_content_prevention_content = f.read()

    template_variables['rai_harmful_content_prevention'] = rai_harmful_content_prevention_content if rai_harmful_content_prevention else None

    # Copyright infringement
    with open(os.path.join(os.path.dirname(__file__), "prompts/rai_copyright_infringement_prevention.md"), "r") as f:
        rai_copyright_infringement_prevention_content = f.read()

    template_variables['rai_copyright_infringement_prevention'] = rai_copyright_infringement_prevention_content if rai_copyright_infringement_prevention else None

    return template_variables


################################################################################
# Truncation
################################################################################

def truncate_actions_or_stimuli(list_of_actions_or_stimuli: Collection[dict], max_content_length: int) -> Collection[str]:
    """
    Truncates the content of actions or stimuli at the specified maximum length. Does not modify the original list.

    Args:
        list_of_actions_or_stimuli (Collection[dict]): The list of actions or stimuli to truncate.
        max_content_length (int): The maximum length of the content.

    Returns:
        Collection[str]: The truncated list of actions or stimuli. It is a new list, not a reference to the original list, 
        to avoid unexpected side effects.
    """
    cloned_list = copy.deepcopy(list_of_actions_or_stimuli)
    
    for element in cloned_list:
        # the external wrapper of the LLM message: {'role': ..., 'content': ...}
        if "content" in element and "role" in element and element["role"] != "system":
            msg_content = element["content"] 

            # now the actual action or stimulus content

            # has action, stimuli or stimulus as key?
            if isinstance(msg_content, dict):
                if "action" in msg_content:
                    # is content there?
                    if "content" in msg_content["action"]:
                        msg_content["action"]["content"] = break_text_at_length(msg_content["action"]["content"], max_content_length)
                elif "stimulus" in msg_content:
                    # is content there?
                    if "content" in msg_content["stimulus"]:
                        msg_content["stimulus"]["content"] = break_text_at_length(msg_content["stimulus"]["content"], max_content_length)
                elif "stimuli" in msg_content:
                    # for each element in the list
                    for stimulus in msg_content["stimuli"]:
                        # is content there?
                        if "content" in stimulus:
                            stimulus["content"] = break_text_at_length(stimulus["content"], max_content_length)

        # if no condition was met, we just ignore it. It is not an action or a stimulus.
    
    return cloned_list