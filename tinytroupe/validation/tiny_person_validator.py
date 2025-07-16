import os
import json
import chevron
import logging

from tinytroupe import openai_utils
from tinytroupe.agent import TinyPerson
from tinytroupe import config
import tinytroupe.utils as utils


default_max_content_display_length = config["OpenAI"].getint("MAX_CONTENT_DISPLAY_LENGTH", 1024)


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
        with open(check_person_prompt_template_path, 'r') as f:
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
        else:
            user_prompt += f"\n\nMini-biography of the person being interviewed: {person.minibio()}"


        logger = logging.getLogger("tinytroupe")

        logger.info(f"Starting validation of the person: {person.name}")

        # Sending the initial messages to the LLM
        current_messages.append({"role": "system", "content": system_prompt})
        current_messages.append({"role": "user", "content": user_prompt})

        message = openai_utils.client().send_message(current_messages)

        # What string to look for to terminate the conversation
        termination_mark = "```json"
        max_iterations = 10  # Limit the number of iterations to prevent infinite loops
        cur_iteration = 0
        while cur_iteration < max_iterations and message is not None and not (termination_mark in message["content"]):
            cur_iteration += 1
            
            # Appending the questions to the current messages
            questions = message["content"]
            current_messages.append({"role": message["role"], "content": questions})
            logger.info(f"Question validation:\n{questions}")

            # Asking the questions to the person
            person.listen_and_act(questions, max_content_length=max_content_length)
            responses = person.pop_actions_and_get_contents_for("TALK", False)
            logger.info(f"Person reply:\n{responses}")

            # Appending the responses to the current conversation and checking the next message
            current_messages.append({"role": "user", "content": responses})
            message = openai_utils.client().send_message(current_messages)

        if message is not None:
            json_content = utils.extract_json(message['content'])
            # read score and justification
            score = float(json_content["score"])
            justification = json_content["justification"]
            logger.info(f"Validation score: {score:.2f}; Justification: {justification}")
            
            return score, justification
        
        else:
            return None, None