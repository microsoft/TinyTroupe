"""Lightweight persona and world preflight validators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from tinytroupe.agent.tiny_person import TinyPerson
from tinytroupe.environment.tiny_world import TinyWorld


@dataclass
class ValidationIssue:
    scope: str
    message: str

    def __str__(self) -> str:  # pragma: no cover - convenience
        return f"[{self.scope}] {self.message}"


def validate_personas(personas: Sequence[TinyPerson]) -> List[ValidationIssue]:
    """Validate persona completeness before running simulations."""
    issues: List[ValidationIssue] = []
    for persona in personas:
        spec = getattr(persona, "_persona", {}) or {}
        name = getattr(persona, "name", spec.get("name"))

        if not name:
            issues.append(ValidationIssue("persona", "Missing persona name"))

        required_fields = [
            "backstory",
            "beliefs",
            "goals",
            "personality",
            "knowledge",
        ]

        for field in required_fields:
            value = spec.get(field)
            if value in (None, "", [], {}):
                issues.append(
                    ValidationIssue(
                        "persona",
                        f"Persona '{name or 'UNKNOWN'}' is missing '{field}'",
                    )
                )

    return issues


def validate_world(world: TinyWorld) -> List[ValidationIssue]:
    """Validate TinyWorld readiness before execution."""
    issues: List[ValidationIssue] = []

    if not getattr(world, "agents", []):
        issues.append(ValidationIssue("world", "World has no agents attached"))

    if getattr(world, "broadcast_if_no_target", None) is False and not getattr(
        world, "name_to_agent", {}
    ):
        issues.append(
            ValidationIssue(
                "world",
                "Broadcasting disabled but world has no routable agents",
            )
        )

    return issues


def assert_simulation_ready(personas: Iterable[TinyPerson], world: TinyWorld) -> None:
    """Raise ValueError if validation issues are found."""
    persona_issues = validate_personas(list(personas))
    world_issues = validate_world(world)
    all_issues = persona_issues + world_issues

    if all_issues:
        joined = "\n".join(str(issue) for issue in all_issues)
        raise ValueError(f"Simulation preflight failed:\n{joined}")
