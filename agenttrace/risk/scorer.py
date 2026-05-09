from fnmatch import fnmatch
from typing import Literal

from pydantic import BaseModel, Field

from agenttrace.core.events import Event
from agenttrace.git.tracker import GitSummary
from agenttrace.risk.rules import RiskRules, load_rules


RiskLevel = Literal["unknown", "low", "medium", "high"]

RISK_ORDER = {
    "unknown": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
}


class RiskResult(BaseModel):
    level: RiskLevel = "unknown"
    reasons: list[str] = Field(default_factory=list)
    matched_rules: list[str] = Field(default_factory=list)


def normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def matches_pattern(value: str, pattern: str) -> bool:
    value = normalize_path(value)
    pattern = normalize_path(pattern)

    if fnmatch(value, pattern):
        return True

    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return value == prefix or value.startswith(prefix + "/")

    return False


def higher_risk(left: RiskLevel, right: RiskLevel) -> RiskLevel:
    if RISK_ORDER[right] > RISK_ORDER[left]:
        return right

    return left


def score_command(command: str, rules: RiskRules | None = None) -> RiskResult:
    rules = rules or load_rules()

    for pattern in rules.high_risk_commands:
        if matches_pattern(command, pattern) or pattern in command:
            return RiskResult(
                level="high",
                reasons=[f"High-risk command detected: {command}"],
                matched_rules=[f"high_risk_commands: {pattern}"],
            )

    for pattern in rules.low_risk_commands:
        if matches_pattern(command, pattern) or command.startswith(pattern):
            return RiskResult(
                level="low",
                reasons=[f"Low-risk command recorded: {command}"],
                matched_rules=[f"low_risk_commands: {pattern}"],
            )

    return RiskResult(
        level="unknown",
        reasons=[f"Command recorded with unknown risk: {command}"],
        matched_rules=[],
    )


def score_file_path(path: str, rules: RiskRules | None = None) -> RiskResult:
    rules = rules or load_rules()
    normalized = normalize_path(path)

    for pattern in rules.high_risk_files:
        if matches_pattern(normalized, pattern):
            return RiskResult(
                level="high",
                reasons=[f"High-risk file touched: {path}"],
                matched_rules=[f"high_risk_files: {pattern}"],
            )

    for pattern in rules.medium_risk_paths:
        if matches_pattern(normalized, pattern):
            return RiskResult(
                level="medium",
                reasons=[f"Medium-risk file touched: {path}"],
                matched_rules=[f"medium_risk_paths: {pattern}"],
            )

    for pattern in rules.low_risk_paths:
        if matches_pattern(normalized, pattern):
            return RiskResult(
                level="low",
                reasons=[f"Low-risk file touched: {path}"],
                matched_rules=[f"low_risk_paths: {pattern}"],
            )

    return RiskResult(
        level="unknown",
        reasons=[f"File touched with unknown risk: {path}"],
        matched_rules=[],
    )


def combine_results(results: list[RiskResult]) -> RiskResult:
    if not results:
        return RiskResult(
            level="unknown",
            reasons=["No events or Git changes found to score."],
            matched_rules=[],
        )

    final_level: RiskLevel = "unknown"
    reasons: list[str] = []
    matched_rules: list[str] = []

    for result in results:
        final_level = higher_risk(final_level, result.level)
        reasons.extend(result.reasons)
        matched_rules.extend(result.matched_rules)

    return RiskResult(
        level=final_level,
        reasons=reasons,
        matched_rules=matched_rules,
    )


def score_events(events: list[Event], rules: RiskRules | None = None) -> RiskResult:
    rules = rules or load_rules()
    results: list[RiskResult] = []

    for event in events:
        if event.type == "command":
            command = event.payload.get("command", event.message)
            results.append(score_command(command, rules))

        elif event.type == "file":
            file_path = event.payload.get("path", event.message)
            results.append(score_file_path(file_path, rules))

    return combine_results(results)


def score_git_summary(summary: GitSummary, rules: RiskRules | None = None) -> RiskResult:
    rules = rules or load_rules()

    results = [
        score_file_path(file_path, rules)
        for file_path in summary.changed_files
    ]

    return combine_results(results)


def score_session(
    events: list[Event],
    git_summary: GitSummary | None = None,
    rules: RiskRules | None = None,
) -> RiskResult:
    rules = rules or load_rules()

    results: list[RiskResult] = []

    event_result = score_events(events, rules)
    results.append(event_result)

    if git_summary:
        git_result = score_git_summary(git_summary, rules)
        results.append(git_result)

    final_result = combine_results(results)

    if final_result.level == "unknown":
        final_result.reasons.append("No known risky activity detected.")

    return final_result