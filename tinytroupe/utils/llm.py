import re
import json
import os
import chevron
from typing import Collection
import copy
import functools
import inspect
from tinytroupe.openai_utils import LLMRequest

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


def llm(**model_overrides):
    """
    Decorator that turns the decorated function into an LLM-based function.
    The decorated function must either return a string (the instruction to the LLM),
    or the parameters of the function will be used instead as the instruction to the LLM.
    The LLM response is coerced to the function's annotated return type, if present.

    Usage example:
    @llm(model="gpt-4-0613", temperature=0.5, max_tokens=100)
    def joke():
        return "Tell me a joke."
    
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            sig = inspect.signature(func)
            return_type = sig.return_annotation if sig.return_annotation != inspect.Signature.empty else str
            system_prompt = func.__doc__.strip() if func.__doc__ else "You are an AI system that executes a computation as requested."
            
            if isinstance(result, str):
                user_prompt = "EXECUTE THE INSTRUCTIONS BELOW:\n\n " + result
            else:
                user_prompt = f"Execute your function as best as you can using the following parameters: {kwargs}"
            
            llm_req = LLMRequest(system_prompt=system_prompt,
                                 user_prompt=user_prompt,
                                 output_type=return_type,
                                 **model_overrides)
            return llm_req.call()
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
        # remove any text before the first opening curly or square braces, using regex. Leave the braces.
        text = re.sub(r'^.*?({|\[)', r'\1', text, flags=re.DOTALL)

        # remove any trailing text after the LAST closing curly or square braces, using regex. Leave the braces.
        text  =  re.sub(r'(}|\])(?!.*(\]|\})).*$', r'\1', text, flags=re.DOTALL)
        
        # remove invalid escape sequences, which show up sometimes
        text = re.sub("\\'", "'", text) # replace \' with just '
        text = re.sub("\\,", ",", text)

        # use strict=False to correctly parse new lines, tabs, etc.
        parsed = json.loads(text, strict=False)
        
        # return the parsed JSON object
        return parsed
    
    except Exception as e:
        logger.error(f"Error occurred while extracting JSON: {e}")
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
        if "content" in element:
            msg_content = element["content"] 

            # now the actual action or stimulus content

            # has action, stimuli or stimulus as key?
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
    
    return cloned_list