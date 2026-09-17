"""Finding model and the ``interpret`` entry point."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from roomscope.models.result import AnalysisResult


class Severity(StrEnum):
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    topic: str
    severity: Severity
    message: str
    #: The measured values the message is based on (units in the keys).
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "severity": str(self.severity),
            "message": self.message,
            "evidence": self.evidence,
        }


def interpret(result: AnalysisResult, profile_name: str = "generic") -> list[Finding]:
    """Produce findings for ``result`` using the named recording profile."""
    from roomscope.interpretation.profiles import get_profile

    return get_profile(profile_name).interpret(result)
