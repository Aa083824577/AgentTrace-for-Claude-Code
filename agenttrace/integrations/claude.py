import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from agenttrace.core.paths import project_root


CLAUDE_DIR_NAME = ".claude"
CLAUDE_SETTINGS_FILE_NAME = "settings.local.json"


AGENTTRACE_HOOK_COMMANDS = {
    "pre_tool": "agenttrace hook pre-tool",
    "post_tool": "agenttrace hook post-tool",
    "stop": "agenttrace hook stop",
}


def claude_dir() -> Path:
    return project_root() / CLAUDE_DIR_NAME


def claude_settings_file() -> Path:
    return claude_dir() / CLAUDE_SETTINGS_FILE_NAME


def backup_settings_file(settings_path: Path) -> Path | None:
    if not settings_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = settings_path.with_name(
        f"{settings_path.name}.agenttrace.{timestamp}.bak"
    )

    shutil.copy2(settings_path, backup_path)

    return backup_path


def read_settings(settings_path: Path) -> dict[str, Any]:
    if not settings_path.exists():
        return {}

    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid JSON in Claude settings file: {settings_path}") from error


def write_settings(settings_path: Path, settings: dict[str, Any]) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(settings, indent=2),
        encoding="utf-8",
    )


def agenttrace_hook_entry(command: str) -> dict[str, str]:
    return {
        "type": "command",
        "command": command,
    }


def agenttrace_matcher_group(matcher: str, command: str) -> dict[str, Any]:
    return {
        "matcher": matcher,
        "hooks": [
            agenttrace_hook_entry(command),
        ],
    }


def desired_agenttrace_hooks() -> dict[str, list[dict[str, Any]]]:
    return {
        "PreToolUse": [
            agenttrace_matcher_group("Bash", AGENTTRACE_HOOK_COMMANDS["pre_tool"]),
            agenttrace_matcher_group(
                "Read|Edit|Write|MultiEdit",
                AGENTTRACE_HOOK_COMMANDS["pre_tool"],
            ),
        ],
        "PostToolUse": [
            agenttrace_matcher_group("Bash", AGENTTRACE_HOOK_COMMANDS["post_tool"]),
            agenttrace_matcher_group(
                "Read|Edit|Write|MultiEdit",
                AGENTTRACE_HOOK_COMMANDS["post_tool"],
            ),
        ],
        "Stop": [
            {
                "hooks": [
                    agenttrace_hook_entry(AGENTTRACE_HOOK_COMMANDS["stop"]),
                ],
            }
        ],
    }


def is_agenttrace_hook_entry(hook: dict[str, Any]) -> bool:
    return (
        hook.get("type") == "command"
        and isinstance(hook.get("command"), str)
        and hook["command"].startswith("agenttrace hook ")
    )


def remove_agenttrace_hooks_from_group(group: dict[str, Any]) -> dict[str, Any] | None:
    hooks = group.get("hooks", [])

    if not isinstance(hooks, list):
        return group

    remaining_hooks = [
        hook
        for hook in hooks
        if not (isinstance(hook, dict) and is_agenttrace_hook_entry(hook))
    ]

    if not remaining_hooks:
        return None

    updated_group = dict(group)
    updated_group["hooks"] = remaining_hooks

    return updated_group


def remove_agenttrace_hooks(settings: dict[str, Any]) -> dict[str, Any]:
    updated_settings = dict(settings)
    hooks_config = updated_settings.get("hooks", {})

    if not isinstance(hooks_config, dict):
        return updated_settings

    updated_hooks_config: dict[str, Any] = {}

    for event_name, groups in hooks_config.items():
        if not isinstance(groups, list):
            updated_hooks_config[event_name] = groups
            continue

        remaining_groups = []

        for group in groups:
            if not isinstance(group, dict):
                remaining_groups.append(group)
                continue

            cleaned_group = remove_agenttrace_hooks_from_group(group)

            if cleaned_group is not None:
                remaining_groups.append(cleaned_group)

        if remaining_groups:
            updated_hooks_config[event_name] = remaining_groups

    if updated_hooks_config:
        updated_settings["hooks"] = updated_hooks_config
    else:
        updated_settings.pop("hooks", None)

    return updated_settings


def merge_agenttrace_hooks(settings: dict[str, Any]) -> dict[str, Any]:
    cleaned_settings = remove_agenttrace_hooks(settings)

    hooks_config = cleaned_settings.setdefault("hooks", {})

    if not isinstance(hooks_config, dict):
        hooks_config = {}
        cleaned_settings["hooks"] = hooks_config

    desired_hooks = desired_agenttrace_hooks()

    for event_name, groups in desired_hooks.items():
        existing_groups = hooks_config.setdefault(event_name, [])

        if not isinstance(existing_groups, list):
            existing_groups = []
            hooks_config[event_name] = existing_groups

        existing_groups.extend(groups)

    return cleaned_settings


def setup_claude_hooks() -> tuple[Path, Path | None]:
    settings_path = claude_settings_file()
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    backup_path = backup_settings_file(settings_path)
    settings = read_settings(settings_path)

    updated_settings = merge_agenttrace_hooks(settings)
    write_settings(settings_path, updated_settings)

    return settings_path, backup_path


def uninstall_claude_hooks() -> tuple[Path, Path | None]:
    settings_path = claude_settings_file()

    if not settings_path.exists():
        return settings_path, None

    backup_path = backup_settings_file(settings_path)
    settings = read_settings(settings_path)

    updated_settings = remove_agenttrace_hooks(settings)
    write_settings(settings_path, updated_settings)

    return settings_path, backup_path


def has_agenttrace_hooks(settings: dict[str, Any]) -> bool:
    hooks_config = settings.get("hooks", {})

    if not isinstance(hooks_config, dict):
        return False

    for groups in hooks_config.values():
        if not isinstance(groups, list):
            continue

        for group in groups:
            if not isinstance(group, dict):
                continue

            hooks = group.get("hooks", [])

            if not isinstance(hooks, list):
                continue

            for hook in hooks:
                if isinstance(hook, dict) and is_agenttrace_hook_entry(hook):
                    return True

    return False


def claude_hooks_status() -> tuple[Path, bool]:
    settings_path = claude_settings_file()
    settings = read_settings(settings_path)

    return settings_path, has_agenttrace_hooks(settings)