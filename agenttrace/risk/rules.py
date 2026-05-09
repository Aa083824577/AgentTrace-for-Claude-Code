from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from agenttrace.core.paths import rules_file


DEFAULT_RULES = {
    "high_risk_commands": [
        "rm -rf",
        "curl * | sh",
        "wget * | sh",
        "sudo",
        "chmod 777",
        "git push --force",
        "git reset --hard",
    ],
    "low_risk_commands": [
        "npm test",
        "npm run test",
        "pytest",
        "python -m pytest",
        "npm run lint",
        "git status",
        "git diff",
    ],
    "high_risk_files": [
        ".env",
        ".env.*",
        "secrets/**",
        "id_rsa",
        "id_ed25519",
        ".github/workflows/**",
        "config/production.*",
    ],
    "medium_risk_paths": [
        "auth/**",
        "src/auth/**",
        "payments/**",
        "src/payments/**",
        "database/migrations/**",
        "migrations/**",
        "config/**",
    ],
    "low_risk_paths": [
        "README.md",
        "docs/**",
        "tests/**",
        "test/**",
        "__tests__/**",
    ],
}


class RiskRules(BaseModel):
    high_risk_commands: list[str] = Field(default_factory=list)
    low_risk_commands: list[str] = Field(default_factory=list)
    high_risk_files: list[str] = Field(default_factory=list)
    medium_risk_paths: list[str] = Field(default_factory=list)
    low_risk_paths: list[str] = Field(default_factory=list)


def default_rules() -> RiskRules:
    return RiskRules(**DEFAULT_RULES)


def default_rules_yaml() -> str:
    return yaml.safe_dump(DEFAULT_RULES, sort_keys=False)


def ensure_rules_file(path: Path | None = None) -> Path:
    target = path or rules_file()

    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(default_rules_yaml(), encoding="utf-8")

    return target


def load_rules(path: Path | None = None) -> RiskRules:
    target = path or rules_file()

    if not target.exists():
        return default_rules()

    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}

    merged = DEFAULT_RULES.copy()
    merged.update(raw)

    return RiskRules(**merged)