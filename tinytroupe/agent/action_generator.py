import json
import statistics  # Add this import

import tinytroupe.utils as utils
from tinytroupe.clients import client
from tinytroupe.control import current_simulation, transactional
from tinytroupe.experimentation import Proposition
from tinytroupe.utils import JsonSerializableRegistry
from tinytroupe.validation import propositions


class ActionGenerator(JsonSerializableRegistry):

    def __init__(
        self,
        max_attempts=2,
        enable_quality_checks=True,
        enable_regeneration=True,
        enable_direct_correction=False,  # TODO enable_direct_correction not working very well yet
        enable_quality_check_for_persona_adherence=True,
        enable_quality_check_for_selfconsistency=True,
        enable_quality_check_for_fluency=True,
        enable_quality_check_for_suitability=False,
        enable_quality_check_for_similarity=False,
        continue_on_failure=True,
        quality_threshold=7,
        max_action_similarity=0.6,
        enable_reasoning_step=False,
        enable_multi_action_output=True,
    ):
        """
        Initializes the ActionGenerator.

        Args:
            max_attempts (int): The maximum number of attempts to generate an action.
            enable_quality_checks (bool): Whether to perform quality checks on the generated action. If False, the first action generated
              is returned without any checks.
            enable_regeneration (bool): Whether to try to make the agent regenerate the action if the first attempt fails.
            enable_direct_correction (bool): Whether to directly correct the action if the first attempt fails, without asking the agent to regenerate it.
            enable_quality_check_for_persona_adherence (bool): Whether to check the action for persona adherence.
            enable_quality_check_for_selfconsistency (bool): Whether to check the action for self-consistency.
            enable_quality_check_for_fluency (bool): Whether to check the action for fluency.
            enable_quality_check_for_suitability (bool): Whether to check the action for suitability.
            continue_on_failure (bool): Whether to return the last tentative action, even if it fails to pass quality checks.
               Presumably, the last tentative action is the one that is most likely to be correct, since it has gone through the most iterations of regeneration and correction.
            quality_threshold (int): The minimum score for each quality check for the action to be considered good quality.
            enable_reasoning_step (bool): Whether to enable reasoning step in the action generation process. This IS NOT the use of "reasoning models" (e.g., o1, o3),
              but rather the use of an additional reasoning step in the regular text completion.
            enable_multi_action_output (bool): If True, the LLM is expected to output the full sequence of actions for the turn (ending with DONE).
        """

        self.max_attempts = max_attempts
        self.regeneration_attempts = 0
        self.direct_correction_attempts = 0

        self.enable_quality_checks = enable_quality_checks
        self.enable_regeneration = enable_regeneration
        self.enable_direct_correction = enable_direct_correction
        self.enable_multi_action_output = enable_multi_action_output

        self.enable_quality_check_for_persona_adherence = (
            enable_quality_check_for_persona_adherence
        )
        self.enable_quality_check_for_selfconsistency = (
            enable_quality_check_for_selfconsistency
        )
        self.enable_quality_check_for_fluency = enable_quality_check_for_fluency
        self.enable_quality_check_for_suitability = enable_quality_check_for_suitability
        self.enable_quality_check_for_similarity = enable_quality_check_for_similarity

        self.continue_on_failure = continue_on_failure
        self.quality_threshold = quality_threshold
        self.max_action_similarity = max_action_similarity

        self.enable_reasoning_step = enable_reasoning_step

        # This generator has its own copies of the propositions, in order to be able to isolate them
        # from other agents, particularly when running the simulation in parallel.
        self.action_persona_adherence = (
            propositions.hard_action_persona_adherence.copy()
        )
        self.action_self_consistency = propositions.action_self_consistency.copy()
        self.action_fluency = propositions.action_fluency.copy()
        self.action_suitability = propositions.action_suitability.copy()

        # initialize statistics
        self.regeneration_failures = 0
        self.direct_correction_failures = 0
        self.regeneration_scores = []
        self.direct_correction_scores = []
        self.total_actions_produced = 0
        self.total_original_actions_succeeded = 0

    # New public API returning the full sequence of actions for the turn
    def generate_next_actions(self, agent, current_messages: list):
        action_or_actions, role, content, all_negative_feedbacks = (
            self.generate_next_action(agent, current_messages)
        )

        # Normalize to sequence
        if isinstance(action_or_actions, list):
            actions = action_or_actions
        else:
            actions = [action_or_actions]

        # If multi-action is enabled but no DONE present, append DONE defensively
        if self.enable_multi_action_output:
            if not any(a.get("type") == "DONE" for a in actions):
                actions = actions + [{"type": "DONE", "content": "", "target": ""}]
                if isinstance(content, dict):
                    content = content.copy()
                    content["actions"] = actions
                    content.pop("action", None)

        return actions, role, content, all_negative_feedbacks

    def generate_next_action(self, agent, current_messages: list):

        from tinytroupe.agent import (
            logger,
        )  # import here to avoid circular import issues

        # clean up (remove unnecessary elements) and copy the list of current messages to avoid modifying the original ones
        current_messages = [
            {"role": msg["role"], "content": json.dumps(msg["content"])}
            for msg in current_messages
        ]

        # starts with no feedback
        cur_feedback = None
        all_negative_feedbacks = []

        best_action = None
        best_role = None
        best_content = None
        best_score = float("-inf")
        original_score = None

        def update_best(tentative_action, role, content, total_score):
            nonlocal best_action, best_role, best_content, best_score
            if total_score > best_score:
                best_action = tentative_action
                best_role = role
                best_content = content
                best_score = total_score

        def finish_return(tentative_action, role, content, final_score):
            if original_score is not None and final_score > original_score:
                logger.warning(
                    f"[{agent.name}] improved total quality from {original_score} to {final_score}"
                )

            # ensure that tentative_action and content are dicts or lists where applicable
            if isinstance(tentative_action, str):
                tentative_action = json.loads(tentative_action)
            if isinstance(content, str):
                content = json.loads(content)

            return tentative_action, role, content, all_negative_feedbacks

        # First attempt to generate an action or actions
        tentative, role, content = self._generate_tentative_action(
            agent,
            current_messages,
            feedback_from_previous_attempt=cur_feedback,
            previous_tentative_action=None,
            previous_llm_role=None,
            previous_llm_content=None,
        )

        # TODO obsolete?
        #
        # If model returned multi-action payload, we will score based on the first action
        # def pick_reference_action_for_scoring(tentative_action_or_actions):
        #    if (
        #        isinstance(tentative_action_or_actions, list)
        #        and tentative_action_or_actions
        #    ):
        #        # Prefer first action
        #        return tentative_action_or_actions[0]
        #    return tentative_action_or_actions

        def remove_done_actions(tentative_action_or_actions):
            if isinstance(tentative_action_or_actions, list):
                return [
                    action
                    for action in tentative_action_or_actions
                    if action is not None and isinstance(action, dict) and action.get("type") != "DONE"
                ]
            return tentative_action_or_actions

        tentative_action_for_quality = remove_done_actions(
            tentative  # TODO remove pick_reference_action_for_scoring(tentative)
        )

        if self.enable_quality_checks:
            # First quality check (single-action proxy)
            good_quality, total_score, cur_feedback = self._check_action_quality(
                "Original Action", agent, tentative_action=tentative_action_for_quality
            )

            update_best(tentative, role, content, total_score)
            if original_score is None:
                original_score = total_score
            if good_quality:
                self.total_original_actions_succeeded += 1
                # Found a good action(s), let's return it now
                return finish_return(tentative, role, content, total_score)
            else:
                logger.warning(
                    f"[{agent.name}] Original action did not pass quality checks: {cur_feedback}"
                )
                all_negative_feedbacks.append(cur_feedback)

            # GENERATE AND REGENERATE the action by the agent
            if self.enable_regeneration:
                for attempt in range(self.max_attempts):

                    # Generate tentative action
                    tentative, role, content = self._generate_tentative_action(
                        agent,
                        current_messages,
                        feedback_from_previous_attempt=cur_feedback,
                        previous_tentative_action=tentative,
                        previous_llm_role=role,
                        previous_llm_content=content,
                    )
                    logger.debug(f"[{agent.name}] Tentative action: {tentative}")
                    self.regeneration_attempts += 1

                    tentative_action_for_quality = remove_done_actions(
                        tentative
                    )  # TODO remove pick_reference_action_for_scoring(tentative)

                    good_quality, total_score, cur_feedback_single = (
                        self._check_action_quality(
                            f"Action Regeneration ({attempt})",
                            agent,
                            tentative_action=tentative_action_for_quality,
                        )
                    )

                    update_best(tentative, role, content, total_score)
                    if good_quality:
                        # Found a good action(s), let's return it now
                        return finish_return(tentative, role, content, total_score)
                    else:
                        self.regeneration_failures += 1
                        self.regeneration_scores.append(total_score)
                        all_negative_feedbacks.append(cur_feedback_single)
                        cur_feedback = cur_feedback_single

            # CORRECT OR REPHRASE the action directly
            if self.enable_direct_correction:
                for attempt in range(self.max_attempts):
                    # Only meaningful for single action, so pick the last action for correction
                    last_action = remove_done_actions(
                        tentative
                    )  # TODO remove pick_reference_action_for_scoring(tentative)
                    corrected_action, role, content = self._correct_action(
                        last_action,
                        feedback=cur_feedback,
                        llm_role=role,
                        llm_content=content,
                    )
                    logger.warning(
                        f"[{agent.name}] Rephrased the action directly as: {corrected_action}"
                    )
                    self.direct_correction_attempts += 1

                    good_quality, total_score, cur_feedback = (
                        self._check_action_quality(
                            f"Direct Action Correction or Rephrasing ({attempt})",
                            agent,
                            tentative_action=corrected_action,
                        )
                    )
                    update_best(corrected_action, role, content, total_score)
                    if good_quality:
                        # Return corrected single action
                        return finish_return(
                            corrected_action, role, content, total_score
                        )
                    else:
                        self.direct_correction_failures += 1
                        self.direct_correction_scores.append(total_score)
                        all_negative_feedbacks.append(cur_feedback)

            # If we got here, all attempts to generate a good action failed
            if self.continue_on_failure:
                logger.warning(
                    f"[{agent.name}] All attempts to generate a good action failed. Returning the best one."
                )
                return finish_return(best_action, best_role, best_content, best_score)

            else:
                raise PoorQualityActionException()

        else:
            # If we got here, it means that the action(s) was generated without quality checks
            return tentative, role, content, []

    def _generate_tentative_action(
        self,
        agent,
        current_messages,
        feedback_from_previous_attempt=None,
        previous_tentative_action=None,
        previous_llm_role=None,
        previous_llm_content=None,
    ):

        from tinytroupe.agent import (  # import here to avoid circular import issues
            CognitiveActionModel,
            CognitiveActionModelWithReasoning,
            CognitiveActionsModel,
            CognitiveActionsModelWithReasoning,
            logger,
        )

        self.total_actions_produced += 1

        # shallow clone current_messages
        current_messages_context = current_messages.copy()

        logger.debug(f"[{agent.name}] Sending messages to OpenAI API")
        logger.debug(f"[{agent.name}] Last interaction: {current_messages[-1]}")

        if feedback_from_previous_attempt:
            current_messages_context.append(
                {
                    "role": "user",
                    "content": f"""
                                WARNING! TENTATIVE ACTION GENERATION FAILED IN QUALITY CHECKS!

                                You were about to produce the following action(s), as a sequence for the previous actions or feedbacks (if any):
                                      ```
                                      {previous_tentative_action}
                                      ```
                                   
                                However, it failed to pass the quality checks (as described in the quality feedback below), and therefore it was aborted and not added
                                to the simulation trajectory.

                                Now you **must** try again to generate a **BETTER** action or sequence of actions, such that the quality issues mentioned in the feedback are addressed,
                                or instead issue a DONE action and stop for this turn if it is unclear how to improve quality. 
                                Your objective is to **PASS** the quality checks this time if possible.

                                You can choose either to FIX somehow the action(s) you were about to produce, or to generate something COMPLETELY NEW and DIFFERENT.  
                                Each time your tentative action fail a quality check, you should be MORE RADICAL in your changes, and try to produce 
                                something that is **very** different from the previous attempts.

                                If it is unclear how to produce a better action, you can choose to issue a DONE action instead. 
                                **It is better to stop acting than to act poorly.**
                                
                                In general, desireable properties of the action are:
                                  - The action is consistent with the agent's persona, it is what one would expect from the agent given its persona.
                                  - The action is self-consistent, it does contradict the agent's previous actions.
                                  - The action is fluent and natural, and does not repeat itself or use overly formulaic language.
                                
                                {feedback_from_previous_attempt}
                                """,
                }
            )

            current_messages_context.append(
                {
                    "role": "system",
                    "content": "Now generate a better action or sequence of actions based on the above feedback, and finish with a DONE action if you are done.",
                }
            )

        # Choose response schema based on configuration
        if not self.enable_reasoning_step:
            if self.enable_multi_action_output:
                response_format = CognitiveActionsModel
            else:
                response_format = CognitiveActionModel
            next_message = client().send_message(
                current_messages_context, response_format=response_format
            )

        else:
            current_messages_context.append(
                {
                    "role": "system",
                    "content": 'Use the "reasoning" field to add any reasoning process you might wish to use before generating the next action(s) and cognitive state. ',
                }
            )
            if self.enable_multi_action_output:
                response_format = CognitiveActionsModelWithReasoning
            else:
                response_format = CognitiveActionModelWithReasoning
            next_message = client().send_message(
                current_messages_context,
                response_format=response_format,
            )

        logger.debug(f"[{agent.name}] Received message: {next_message}")

        role, content = next_message["role"], utils.extract_json(
            next_message["content"]
        )

        # Support both single-action and multi-action payloads
        if "actions" in content and isinstance(content.get("actions"), list):
            actions = content["actions"]
            # Ensure the sequence ends with DONE
            if not actions or actions[-1].get("type") != "DONE":
                actions.append({"type": "DONE", "content": "", "target": ""})
            return actions, role, content
        else:
            action = content["action"]
            return action, role, content

    ###############################################################################################
    # Quality evaluation methods
    ###############################################################################################

    def _check_action_quality(self, stage, agent, tentative_action):

        from tinytroupe.agent import (
            logger,
        )  # import here to avoid circular import issues

        #
        # Compute various propositions about the action
        #
        (
            persona_adherence_passed,
            persona_adherence_score,
            persona_adherence_feedback,
        ) = self._check_proposition(
            agent,
            self.action_persona_adherence,
            tentative_action,
            enable_proposition_check=self.enable_quality_check_for_persona_adherence,
        )

        selfconsistency_passed, selfconsistency_score, selfconsistency_feedback = (
            self._check_proposition(
                agent,
                self.action_self_consistency,
                tentative_action,
                minimum_required_qty_of_actions=1,
                enable_proposition_check=self.enable_quality_check_for_selfconsistency,
            )
        )

        fluency_passed, fluency_passed_score, fluency_feedback = (
            self._check_proposition(
                agent,
                self.action_fluency,
                tentative_action,
                enable_proposition_check=self.enable_quality_check_for_fluency,
            )
        )

        suitability_passed, suitability_score, suitability_feedback = (
            self._check_proposition(
                agent,
                self.action_suitability,
                tentative_action,
                enable_proposition_check=self.enable_quality_check_for_suitability,
            )
        )

        similarity_passed, similarity_score, similarity_feedback = (
            self._check_next_action_similarity(
                agent,
                tentative_action,
                threshold=self.max_action_similarity,
                enable_similarity_check=self.enable_quality_check_for_similarity,
            )
        )

        # put the results together
        good_quality = (
            persona_adherence_passed
            and selfconsistency_passed
            and fluency_passed
            and suitability_passed
            and similarity_passed
        )
        total_score = (
            persona_adherence_score
            + selfconsistency_score
            + fluency_passed_score
            + suitability_score
            + (similarity_score * Proposition.MAX_SCORE)
        )

        combined_feedback = utils.combine_texts(
            persona_adherence_feedback,
            selfconsistency_feedback,
            fluency_feedback,
            suitability_feedback,
            similarity_feedback,
        )

        # give verdict
        if good_quality:
            return True, total_score, combined_feedback

        else:

            failure_feedback = f"""
                # Quality feedback

                This is the action that was about to be generated by the agent:
                    {tentative_action}

                Unfortunately, the action failed to pass the quality checks, and therefore was aborted and not added to the similation trajectory. 
                The following problems were detected.
                """

            if not persona_adherence_passed:
                failure_feedback += f"""
                ## Problem: The action does not adhere to the persona specification.
                {persona_adherence_feedback}

                ### RECOMMENDATIONS FOR IMPROVEMENT
                Please follow the recommendations below when trying to generate this action again.

                Use the feedback above to generate a better action.
                {self.action_persona_adherence.recommendations_for_improvement()}

                """

            if not selfconsistency_passed:
                failure_feedback += f"""
                ## Problem: The action is not self-consistent.
                {selfconsistency_feedback}

                ### RECOMMENDATIONS FOR IMPROVEMENT
                Please follow the recommendations below when trying to generate this action again.

                Use the feedback above to generate a better action.
                {self.action_self_consistency.recommendations_for_improvement()}

                """

            if not fluency_passed:
                failure_feedback += f"""
                ## Problem: The action is not fluent.
                {fluency_feedback}

                ### RECOMMENDATIONS FOR IMPROVEMENT
                Please follow the recommendations below when trying to generate this action again.

                Use the feedback above to generate a better action.
                {self.action_fluency.recommendations_for_improvement()}
                
                """

            if not suitability_passed:
                failure_feedback += f"""
                ## Problem: The action is not suitable to the situation or task.
                {suitability_feedback}

                ### RECOMMENDATIONS FOR IMPROVEMENT
                Please follow the recommendations below when trying to generate this action again.

                Use the feedback above to generate a better action.
                {self.action_suitability.recommendations_for_improvement()}

                """

            if not similarity_passed:
                failure_feedback += f"""
                ## Problem: The action is too similar to the previous one.
                {similarity_feedback}

                """

            logger.warning(
                f"[{agent.name}][{stage}] failed to pass quality checks: {failure_feedback}"
            )
            return False, total_score, failure_feedback

    def _check_proposition(
        self,
        agent,
        proposition,
        tentative_action,
        minimum_required_qty_of_actions=0,
        enable_proposition_check=True,
    ):

        from tinytroupe.agent import (
            logger,
        )  # import here to avoid circular import issues

        if enable_proposition_check:
            if agent.actions_count >= minimum_required_qty_of_actions:
                result = proposition.score(
                    target=agent,
                    claim_variables={"action": tentative_action},
                    return_full_response=True,
                )

                value_with_justification = f"Score = {result['value']} (out of {Proposition.MAX_SCORE}). Justification = {result['justification']}"

                logger.debug(
                    f"[{agent.name}] Proposition '{proposition.__class__.__name__}' evaluation result: {value_with_justification}"
                )

                if result["value"] >= self.quality_threshold:
                    return True, result["value"], value_with_justification
                else:
                    return False, result["value"], value_with_justification

            else:
                return (
                    True,
                    Proposition.MAX_SCORE,
                    f"The proposition is trivially true due to the lack of enough actions for comparison.",
                )
        else:
            # If the proposition check is disabled, we assume it passed
            return (
                True,
                Proposition.MAX_SCORE,
                f"The proposition check is disabled, so it is assumed to have passed.",
            )

    def _check_next_action_similarity(
        self, agent, proposed_next_action, threshold, enable_similarity_check=True
    ):
        """
        Checks the similarity between the agent's current action and a proposed next action.
        High similarity indicates that the proposed action is too similar to the current one, and this
        check fails.
        """
        from tinytroupe.agent import (
            logger,
        )  # import here to avoid circular import issues

        if enable_similarity_check:
            similarity = utils.next_action_jaccard_similarity(
                agent, proposed_next_action
            )
            logger.debug(f"[{agent.name}] Next-action Jaccard similarity: {similarity}")

            if similarity >= threshold:
                logger.warning(
                    f"[{agent.name}] Next-action Jaccard similarity is above the threshold ({threshold})."
                )
                return (
                    False,
                    similarity,
                    f"Similarity = {similarity} (range: 0.0 to 1.0). The action is too similar to the previous one.",
                )
            else:
                logger.debug(
                    f"[{agent.name}] Next-action Jaccard similarity is below the threshold ({threshold})."
                )
                return (
                    True,
                    similarity,
                    f"Similarity = {similarity} (range: 0.0 to 1.0). The action is sufficiently different from the previous one.",
                )

        else:
            # If the similarity check is disabled, we assume it passed
            return (
                True,
                0.0,
                f"The similarity check is disabled, so it is assumed to have passed.",
            )

    ################################################################################################
    # Action correction methods
    ################################################################################################

    def _correct_action(self, action: dict, feedback, llm_role, llm_content):
        situation = f"""
            The following action by an agent was observed:
                
                {action}

            However, it does not conform to expectations about this agent behavior, 
            due to the following reasons.
            {feedback}
            """
        # restructured_situation =\
        #    utils.restructure_as_observed_vs_expected(\

        #        """)
        # rule = utils.formulate_corrective_rule(restructured_situation)
        rules = utils.extract_observed_vs_expected_rules(situation)
        rephrased_action_content = utils.correct_according_to_rule(
            action["content"], rules
        )

        # copy action
        rephrased_action = action.copy()

        # update content
        rephrased_action["content"] = rephrased_action_content

        # replace in the 'action' key in the original llm content message
        llm_content["action"] = rephrased_action

        return rephrased_action, llm_role, llm_content

    def get_statistics(self):
        regeneration_failure_rate = (
            self.regeneration_failures / self.regeneration_attempts
            if self.regeneration_attempts
            else 0
        )
        direct_correction_failure_rate = (
            self.direct_correction_failures / self.direct_correction_attempts
            if self.direct_correction_attempts
            else 0
        )

        regeneration_mean_score = (
            statistics.mean(self.regeneration_scores) if self.regeneration_scores else 0
        )
        regeneration_sd_score = (
            statistics.stdev(self.regeneration_scores)
            if len(self.regeneration_scores) > 1
            else 0
        )

        direct_correction_mean_score = (
            statistics.mean(self.direct_correction_scores)
            if self.direct_correction_scores
            else 0
        )
        direct_correction_sd_score = (
            statistics.stdev(self.direct_correction_scores)
            if len(self.direct_correction_scores) > 1
            else 0
        )

        original_success_rate = (
            self.total_original_actions_succeeded / self.total_actions_produced
            if self.total_actions_produced
            else 0
        )

        return {
            "regeneration_failure_rate": regeneration_failure_rate,
            "direct_correction_failure_rate": direct_correction_failure_rate,
            "regeneration_mean_score": regeneration_mean_score,
            "regeneration_sd_score": regeneration_sd_score,
            "direct_correction_mean_score": direct_correction_mean_score,
            "direct_correction_sd_score": direct_correction_sd_score,
            "total_actions_produced": self.total_actions_produced,
            "total_original_actions_succeeded": self.total_original_actions_succeeded,
            "original_success_rate": original_success_rate,
            "regeneration_success_rate": 1 - regeneration_failure_rate,
            "direct_correction_success_rate": 1 - direct_correction_failure_rate,
        }


class PoorQualityActionException(Exception):
    def __init__(self, message="The generated action is of poor quality"):
        self.message = message
        super().__init__(self.message)
