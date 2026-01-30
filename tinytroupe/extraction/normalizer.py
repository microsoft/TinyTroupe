import textwrap
from typing import List, Optional, Union

import pandas as pd

import tinytroupe.utils as utils
from tinytroupe.clients import client
from tinytroupe.extraction import logger
from tinytroupe.utils.llm import LLMChat


class Normalizer:
    """
    A mechanism to normalize passages, concepts and other textual elements.
    """

    def __init__(
        self,
        elements: List[str],
        n: int,
        verbose: bool = False,
        max_length: Optional[int] = None,
    ):
        """
        Normalizes the specified elements.

        Args:
            elements (list): The elements to normalize.
            n (int): The number of normalized elements to output.
            verbose (bool, optional): Whether to print debug messages. Defaults to False.
        Args:
            elements (list): The elements to normalize.
            n (int): The number of normalized elements to output.
            verbose (bool, optional): Whether to print debug messages. Defaults to False.
            max_length (int, optional): If provided, each normalized output element MUST NOT
                exceed this many characters. The LLM will be instructed to produce concise
                abstractions; as a safety net we also truncate/merge locally if still too long.
        """
        # ensure elements are unique
        self.elements = list(set(elements))

        self.n = n
        self.verbose = verbose
        self.max_length = max_length

        # a JSON-based structure, where each output element is a key to a list of input elements that were merged into it
        self.normalized_elements = None
        # a dict that maps each input element to its normalized output. This will be used as cache later.
        self.normalizing_map = {}

        rendering_configs = {"n": n, "elements": self.elements}
        if max_length is not None:
            rendering_configs["max_length"] = max_length

        logger.info(
            f"Computing up to {n} normalized elements from {len(self.elements)} originals (may return fewer if clusters merge)."
        )

        # Use LLMChat for robust structured JSON output
        chat = LLMChat(
            system_template_name="normalizer.system.mustache",
            user_template_name="normalizer.user.mustache",
            base_module_folder="extraction",
            output_type=dict,  # Request structured dict output
            enable_json_output_format=True,
            enable_justification_step=False,
            enable_reasoning_step=False
        )
        
        result = chat.call(**rendering_configs)

        debug_msg = f"Normalization result from LLMChat: {result}"
        logger.debug(debug_msg)
        if self.verbose:
            print(debug_msg)

        logger.debug(f"Raw LLM result: {result}")
        logger.debug(f"Result type: {type(result)}")
        if self.verbose:
            print(f"Raw LLM result: {result}")
            print(f"Result type: {type(result)}")

    # Normalize result structure to a dict[str, list[str]] mapping
    # Expected format: {"canonical_label": [list, of, originals], ...}
        mapping = {}
        if isinstance(result, dict):
            for k, v in result.items():
                if isinstance(v, (list, set, tuple)):
                    originals = [str(x) for x in v if x]
                else:
                    originals = [str(v)] if v else []
                mapping[str(k)] = originals
        else:
            # Unknown structure: fall back to identity over provided elements
            logger.warning(f"Normalizer received unexpected result format {type(result)}; falling back to identity mapping.")
            mapping = {e: [e] for e in self.elements}
        # Remove empties
        mapping = {k: v for k, v in mapping.items() if k and v}

        # Enforce HARD upper bound: never expose more than self.n categories
        if len(mapping) > self.n:
            logger.warning(
                f"Normalizer produced {len(mapping)} categories exceeding the cap {self.n}; merging overflow into 'Other'."
            )
            # Sort keys by descending size of originals so we retain the largest/most meaningful clusters
            sorted_keys = sorted(mapping.keys(), key=lambda k: len(mapping[k]), reverse=True)
            keep = sorted_keys[: self.n - 1] if self.n > 1 else []
            overflow = sorted_keys[len(keep):]
            other_bucket: List[str] = []
            for k in overflow:
                other_bucket.extend(mapping[k])
                del mapping[k]
            if self.n == 1:
                # Single bucket scenario: collapse everything into one abstraction
                merged_label = keep[0] if keep else "Other"
                if not keep:
                    mapping = {merged_label: other_bucket}
                else:
                    # Add overflow items into the sole kept cluster
                    mapping[merged_label].extend(other_bucket)
            else:
                mapping["Other"] = other_bucket

        # Safety: if still somehow > n (edge race), truncate deterministically
        if len(mapping) > self.n:
            logger.warning(
                f"Post-merge category count still {len(mapping)} > {self.n}; truncating extras."  # pragma: no cover
            )
            truncated = {}
            for i, (k, v) in enumerate(sorted(mapping.items(), key=lambda kv: len(kv[1]), reverse=True)):
                if i < self.n:
                    truncated[k] = v
            mapping = truncated

        # Enforce maximum length locally (merge clusters whose canonical label is shortened)
        def _shorten(label: str, max_len: int) -> str:
            if len(label) <= max_len:
                return label
            # Prefer first sentence if it fits
            first_sentence = label.split(".")[0].strip()
            if 0 < len(first_sentence) <= max_len:
                return first_sentence
            # Use textwrap.shorten to keep whole words
            return textwrap.shorten(label, width=max_len, placeholder="…")

        if self.max_length is not None and self.max_length > 10:  # basic sanity
            shortened: dict = {}
            for k, originals in mapping.items():
                new_k = _shorten(k, self.max_length)
                # Merge if collision
                if new_k not in shortened:
                    shortened[new_k] = list(originals)
                else:
                    shortened[new_k].extend(originals)
            mapping = shortened

        self.normalized_elements = mapping
        logger.debug(f"Final normalized mapping: {mapping}")
        if self.verbose:
            print(f"Final normalized mapping: {mapping}")

    def normalize(
        self, element_or_elements: Union[str, List[str]]
    ) -> Union[str, List[str]]:
        """
        Normalizes the specified element or elements.

        This method uses a caching mechanism to improve performance. If an element has been normalized before,
        its normalized form is stored in a cache (self.normalizing_map). When the same element needs to be
        normalized again, the method will first check the cache and use the stored normalized form if available,
        instead of normalizing the element again.

        The order of elements in the output will be the same as in the input. This is ensured by processing
        the elements in the order they appear in the input and appending the normalized elements to the output
        list in the same order.

        Args:
            element_or_elements (Union[str, List[str]]): The element or elements to normalize.

        Returns:
            str: The normalized element if the input was a string.
            list: The normalized elements if the input was a list, preserving the order of elements in the input.
        """
        if isinstance(element_or_elements, str):
            denormalized_elements = [element_or_elements]
        elif isinstance(element_or_elements, list):
            denormalized_elements = element_or_elements
        else:
            raise ValueError(
                "The element_or_elements must be either a string or a list."
            )

        normalized_elements = []
        elements_to_normalize = []
        for element in denormalized_elements:
            if element not in self.normalizing_map:
                elements_to_normalize.append(element)

        if elements_to_normalize:
            # Convert the mapping to a list of categories for the applier template
            categories_list = list(self.normalized_elements.keys())
            rendering_configs = {
                "categories": categories_list,
                "elements": elements_to_normalize,
            }
            
            logger.debug(f"Applier rendering configs: {rendering_configs}")
            if self.verbose:
                print(f"Applier rendering configs: {rendering_configs}")

            # For now, use the manual template method for the applier due to LLMChat issues
            # TODO: Debug and fix LLMChat template rendering for applier templates
            logger.debug("Using manual template method for applier (LLMChat has template rendering issues)")
            
            messages = utils.compose_initial_LLM_messages_with_templates(
                "normalizer.applier.system.mustache",
                "normalizer.applier.user.mustache", 
                base_module_folder="extraction",
                rendering_configs=rendering_configs,
            )

            next_message = client().send_message(messages)
            normalized_elements_from_llm = utils.extract_json(next_message["content"])
            
            debug_msg = f"Normalization applier result (manual): {normalized_elements_from_llm}"
            logger.debug(debug_msg)
            if self.verbose:
                print(debug_msg)
            assert isinstance(
                normalized_elements_from_llm, list
            ), "The normalized element must be a list."
            assert len(normalized_elements_from_llm) == len(
                elements_to_normalize
            ), "The number of normalized elements must be equal to the number of elements to normalize."

            for i, element in enumerate(elements_to_normalize):
                normalized_element = normalized_elements_from_llm[i]
                self.normalizing_map[element] = normalized_element

        for element in denormalized_elements:
            normalized_elements.append(self.normalizing_map[element])

        # Return appropriate type based on input
        if isinstance(element_or_elements, str):
            return normalized_elements[0]  # Return single string for string input
        else:
            return normalized_elements  # Return list for list input

    # --- Convenience API -------------------------------------------------
    def normalized_mapping(self) -> dict:
        """Return the normalized elements mapping (canonical -> list(originals)).

        Always returns a dict; if normalization somehow failed earlier and the
        internal data isn't a dict, it coerces it into identity mapping.
        """
        if isinstance(self.normalized_elements, dict):
            return self.normalized_elements
        if isinstance(self.normalized_elements, list):
            return {str(x): [str(x)] for x in self.normalized_elements if x}
        # fallback identity
        return {e: [e] for e in self.elements}
