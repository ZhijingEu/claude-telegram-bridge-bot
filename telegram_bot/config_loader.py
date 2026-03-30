"""Loads config.yaml and exposes typed constants for the Telegram bot."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

_PROJECT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def _load() -> dict[str, Any]:
    if not _CONFIG_PATH.exists():
        sys.exit(
            f"ERROR: config.yaml not found at {_CONFIG_PATH}.\n"
            "Copy config.yaml.example to config.yaml and fill in your details."
        )
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        sys.exit("ERROR: config.yaml is empty or malformed.")
    return data


_cfg = _load()

# ---------------------------------------------------------------------------
# Timezone and location
# ---------------------------------------------------------------------------
TIMEZONE: str = _cfg.get("timezone", "Asia/Singapore")
LOCATION_HINT: str = _cfg.get("location_hint", "")

# ---------------------------------------------------------------------------
# Calendar IDs  {"primary": "...", "family": "..."}
# ---------------------------------------------------------------------------
CALENDAR_IDS: dict[str, str] = _cfg.get("calendars", {})

# ---------------------------------------------------------------------------
# Users
# PRIMARY_USER  — single dict for the primary (admin) user
# FAMILY_USERS  — list of dicts for family users (limited access)
# FAMILY_USER_IDS — maps resolved Telegram ID (int) → user dict, populated at bot startup
# ---------------------------------------------------------------------------
_users: dict[str, Any] = _cfg.get("users", {})
PRIMARY_USER: dict[str, Any] = _users.get("primary", {})
FAMILY_USERS: list[dict[str, Any]] = _users.get("family", [])

# ---------------------------------------------------------------------------
# Family members  [{"name": ..., "calendar_prefix": ..., "aliases": [...]}, ...]
# ---------------------------------------------------------------------------
FAMILY_MEMBERS: list[dict[str, Any]] = _cfg.get("family_members", [])
CHILDREN_KEYWORDS: list[str] = _cfg.get("children_keywords", [])
CHILDREN_NAMES: list[str] = _cfg.get("children_names", [])

# ---------------------------------------------------------------------------
# Staging file path (relative to project root)
# ---------------------------------------------------------------------------
STAGING_FILE: str = _cfg.get("staging_file", "memory/suggestions.md")
