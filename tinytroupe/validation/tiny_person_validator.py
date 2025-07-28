import os
import json
import chevron
import logging
from pydantic import BaseModel
from typing import Optional, List

from tinytroupe import openai_utils
from tinytroupe.agent import TinyPerson
from tinytroupe import config
import tinytroupe.utils as utils


default_max_content_display_length = config["OpenAI"].getint("MAX_CONTENT_DISPLAY_LENGTH", 1024)


class ValidationResponse(BaseModel):
    """Response structure for the validation process"""
    questions: Optional[List[str]] = None
    next_phase_description: Optional[str] = None
    score: Optional[float] = None
    justification: Optional[str] = None
    is_complete: bool = False


class TinyPersonValidator:

    @staticmethod
    def validate_person(person, expectations=None, include_agent_spec=True, max_content_length=default_max_content_display_length) -> tuple[float, str]:
        """
        Validate a TinyPerson instance using OpenAI's LLM.

        This method sends a series of questions to the TinyPerson instance to validate its responses using OpenAI's LLM.
        The method returns a float value representing the confidence score of the validation process.
        If the validation process fails, the method returns None.

        Args:
            person (TinyPerson): The TinyPerson instance to be validated.
            expectations (str, optional): The expectations to be used in the validation process. Defaults to None.
            include_agent_spec (bool, optional): Whether to include the agent specification in the prompt. Defaults to False.
            max_content_length (int, optional): The maximum length of the content to be displayed when rendering the conversation.

        Returns:
            float: The confidence score of the validation process (0.0 to 1.0), or None if the validation process fails.
            str: The justification for the validation score, or None if the validation process fails.
        """
        # Initiating the current messages
        current_messages = []
        
        # Generating the prompt to check the person
        check_person_prompt_template_path = os.path.join(os.path.dirname(__file__), 'prompts/check_person.mustache')
        with open(check_person_prompt_template_path, 'r', encoding='utf-8', errors='replace') as f:
            check_agent_prompt_template = f.read()
        
        system_prompt = chevron.render(check_agent_prompt_template, {"expectations": expectations})

        # use dedent
        import textwrap
        user_prompt = textwrap.dedent(\
        """
        Now, based on the following characteristics of the person being interviewed, and following the rules given previously, 
        create your questions and interview the person. Good luck!

        """)

        if include_agent_spec:
            user_prompt += f"\n\n{json.dumps(person._persona, indent=4)}"
        
        # TODO this was confusing the expectations
        #else:
        #    user_prompt += f"\n\nMini-biography of the person being interviewed: {person.minibio()}"


        logger = logging.getLogger("tinytroupe")

        logger.info(f"Starting validation of the person: {person.name}")

        # Sending the initial messages to the LLM
        current_messages.append({"role": "system", "content": system_prompt})
        current_messages.append({"role": "user", "content": user_prompt})

        message = openai_utils.client().send_message(current_messages, response_format=ValidationResponse, enable_pydantic_model_return=True)

        max_iterations = 10  # Limit the number of iterations to prevent infinite loops
        cur_iteration = 0
        while cur_iteration < max_iterations and message is not None and not message.is_complete:
            cur_iteration += 1
            
            # Check if we have questions to ask
            if message.questions:
                # Format questions as a text block
                if message.next_phase_description:
                    questions_text = f"{message.next_phase_description}\n\n"
                else:
                    questions_text = ""
                
                questions_text += "\n".join([f"{i+1}. {q}" for i, q in enumerate(message.questions)])
                
                current_messages.append({"role": "assistant", "content": questions_text})
                logger.info(f"Question validation:\n{questions_text}")

                # Asking the questions to the persona
                person.listen_and_act(questions_text, max_content_length=max_content_length)
                responses = person.pop_actions_and_get_contents_for("TALK", False)
                logger.info(f"Person reply:\n{responses}")

                # Appending the responses to the current conversation and checking the next message
                current_messages.append({"role": "user", "content": responses})
                message = openai_utils.client().send_message(current_messages, response_format=ValidationResponse, enable_pydantic_model_return=True)
            else:
                # If no questions but not complete, something went wrong
                logger.warning("LLM did not provide questions but validation is not complete")
                break

        if message is not None and message.is_complete and message.score is not None:
            logger.info(f"Validation score: {message.score:.2f}; Justification: {message.justification}")
            return message.score, message.justification
        else:
            logger.error("Validation process failed to complete properly")
            return None, None