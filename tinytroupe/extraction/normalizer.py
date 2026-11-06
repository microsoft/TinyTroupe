import json
from typing import List, Optional, Union

import tinytroupe.utils as utils
from tinytroupe.clients import client
from tinytroupe.extraction import logger


class Normalizer:
    """Partition text semantically while reconstructing exact source occurrences."""

    def __init__(
        self,
        elements: List[str],
        n: int,
        verbose: bool = False,
        max_length: Optional[int] = None,
        chunk_size: int = 240,
    ):
        """Create up to n themes; large collections use frozen themes and bounded batches.

        Args:
            elements: Original strings, including duplicate occurrences.
            n: Positive upper bound on the number of semantic categories.
            verbose: Whether to print progress counts.
            max_length: Positive label-length ceiling, defaulting to 40 characters.
            chunk_size: Maximum items per assignment call, between 1 and 240.

        Invalid responses raise ValueError rather than rewriting, dropping or
        assigning unmatched source text to an arbitrary fallback category.
        """
        if not isinstance(elements, list) or any(not isinstance(s, str) or not s for s in elements):
            raise ValueError("elements must be a list of nonempty strings.")
        if type(n) is not int or n < 1:
            raise ValueError("n must be a positive integer.")
        if max_length is not None and (type(max_length) is not int or max_length < 1):
            raise ValueError("max_length must be a positive integer or None.")
        if type(chunk_size) is not int or not 1 <= chunk_size <= 240:
            raise ValueError("chunk_size must be an integer between 1 and 240.")
        self.elements = list(elements)
        self.n = n
        self.verbose = verbose
        self.max_length = max_length
        self.chunk_size = chunk_size
        self.normalizing_map = {}
        self.normalized_elements = {}
        self._groups = []
        unique = list(dict.fromkeys(elements))
        if not unique:
            return

        limit = min(n, len(unique))
        label_schema = {"type": "string", "minLength": 1, "maxLength": max_length or 40}
        logger.info(f"Partitioning {len(elements)} occurrences into up to {limit} themes.")
        if len(unique) <= chunk_size:
            schema = self._object_schema({
                "labels": {"type": "array", "items": label_schema, "minItems": 1, "maxItems": limit},
                "assignments": self._assignment_schema(len(unique), limit),
            })
            result = self._call("normalizer", {
                "maximum_groups": limit, "max_length": max_length or 40,
                "items": {str(i): s for i, s in enumerate(unique, 1)},
            }, schema)
            if not isinstance(result, dict) or set(result) != {"labels", "assignments"}:
                raise ValueError("Normalizer requires labels and assignments.")
            labels = result["labels"]
            self._validate_labels(labels, limit)
            self._groups = [{"label": label, "scope": label} for label in labels]
            assignments = self._validate_assignments(result["assignments"], len(unique), len(labels))
        else:
            group_schema = self._object_schema({
                "label": label_schema, "scope": {"type": "string", "minLength": 1},
            })
            result = self._call("normalizer.plan", {
                "maximum_groups": limit, "max_length": max_length or 40,
                "items": {str(i): s for i, s in enumerate(unique, 1)},
            }, self._object_schema({
                "groups": {"type": "array", "items": group_schema, "minItems": 1, "maxItems": limit},
            }))
            if not isinstance(result, dict) or set(result) != {"groups"} or not isinstance(result["groups"], list):
                raise ValueError("Normalizer requires global group definitions.")
            self._groups = result["groups"]
            if any(not isinstance(g, dict) or set(g) != {"label", "scope"}
                   or not isinstance(g["scope"], str) or not g["scope"].strip()
                   for g in self._groups):
                raise ValueError("Global themes require labels and nonempty scope boundaries.")
            labels = [g["label"] for g in self._groups]
            self._validate_labels(labels, limit)
            assignments = self._assign(unique)

        if set(assignments) != set(range(1, len(labels) + 1)):
            raise ValueError("Normalizer returned an empty global category.")
        self.normalizing_map = {s: labels[group - 1] for s, group in zip(unique, assignments)}
        self.normalized_elements = {label: [] for label in labels}
        for element in self.elements:
            self.normalized_elements[self.normalizing_map[element]].append(element)
        if self.verbose:
            print(f"Normalized {len(elements)} occurrences into {len(labels)} categories.")

    @staticmethod
    def _object_schema(properties):
        """Require exactly the supplied JSON object properties."""
        return {"type": "object", "additionalProperties": False,
                "properties": properties, "required": list(properties)}

    @classmethod
    def _assignment_schema(cls, count, groups):
        """Use bounded integers rather than repeated enums that exceed API limits."""
        return cls._object_schema({
            str(i): {"type": "integer", "minimum": 1, "maximum": groups}
            for i in range(1, count + 1)
        })

    def _call(self, template, payload, schema):
        """Call the configured client with a strict intermediate JSON contract."""
        messages = utils.compose_initial_LLM_messages_with_templates(
            template + ".system.mustache", "normalizer.user.mustache",
            base_module_folder="extraction",
            rendering_configs={"payload": json.dumps(payload, ensure_ascii=False)},
        )
        response = client().send_message(messages, response_format={
            "type": "json_schema", "json_schema": {
                "name": template.replace(".", "_"), "strict": True, "schema": schema,
            },
        })
        if not response or not response.get("content"):
            raise ValueError(f"{template} returned no content.")
        return json.loads(response["content"])

    def _validate_labels(self, labels, limit):
        """Reject ambiguous, empty or overlong categories without truncating them."""
        if (not isinstance(labels, list) or not 1 <= len(labels) <= limit
                or any(not isinstance(s, str) or not s.strip()
                       or len(s) > (self.max_length or 40) for s in labels)
                or len(set(labels)) != len(labels)):
            raise ValueError("Normalizer requires distinct nonempty labels within the requested bounds.")

    @staticmethod
    def _validate_assignments(assignments, count, groups):
        """Require every input ID exactly once and only existing integer group IDs."""
        if (not isinstance(assignments, dict)
                or set(assignments) != {str(i) for i in range(1, count + 1)}
                or any(type(v) is not int or not 1 <= v <= groups for v in assignments.values())):
            raise ValueError("Assignments must cover every item ID with a valid integer group.")
        return [assignments[str(i)] for i in range(1, count + 1)]

    def _assign(self, elements):
        """Assign bounded batches using the same immutable global theme definitions."""
        assignments = []
        for offset in range(0, len(elements), self.chunk_size):
            batch = elements[offset:offset + self.chunk_size]
            result = self._call("normalizer.assign", {
                "groups": {str(i): g for i, g in enumerate(self._groups, 1)},
                "items": {str(i): s for i, s in enumerate(batch, 1)},
            }, self._object_schema({
                "assignments": self._assignment_schema(len(batch), len(self._groups)),
            }))
            if not isinstance(result, dict) or set(result) != {"assignments"}:
                raise ValueError("Normalizer requires an assignments object.")
            assignments.extend(self._validate_assignments(
                result["assignments"], len(batch), len(self._groups)))
        return assignments

    def normalize(self, element_or_elements: Union[str, List[str]]) -> Union[str, List[str]]:
        """Map strings to themes, preserving order and caching validated assignments.

        Source strings reuse their original partition assignments without a new
        model call. New strings use bounded assignments to the frozen categories.
        """
        if isinstance(element_or_elements, str) and element_or_elements:
            elements = [element_or_elements]
        elif isinstance(element_or_elements, list) and all(isinstance(s, str) and s for s in element_or_elements):
            elements = element_or_elements
        else:
            raise ValueError("The element_or_elements must be either a string or a list of nonempty strings.")
        missing = list(dict.fromkeys(s for s in elements if s not in self.normalizing_map))
        if missing:
            if not self._groups:
                raise ValueError("Cannot normalize new elements without any source categories.")
            assignments = self._assign(missing)
            self.normalizing_map.update({
                s: self._groups[group - 1]["label"] for s, group in zip(missing, assignments)
            })
        result = [self.normalizing_map[s] for s in elements]
        return result[0] if isinstance(element_or_elements, str) else result

    def normalized_mapping(self) -> dict:
        """Return the validated canonical-to-original mapping, without fallback categories."""
        if not isinstance(self.normalized_elements, dict):
            raise ValueError("The normalized mapping has been corrupted.")
        return self.normalized_elements
