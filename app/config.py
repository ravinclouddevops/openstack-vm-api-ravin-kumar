"""
Application configuration via environment variables.
Uses plain pydantic v2 BaseModel + os.environ to avoid the pydantic-settings
optional dependency.
"""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, Field


class Settings(BaseModel):
    # ── App ────────────────────────────────────────────────────────────────────
    app_name: str = "OpenStack VM API"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # ── OpenStack credentials (clouds.yaml OR env vars) ───────────────────────
    os_auth_url: str = ""
    os_username: str = ""
    os_password: str = ""
    os_project_name: str = ""
    os_user_domain_name: str = "Default"
    os_project_domain_name: str = "Default"
    os_region_name: str = "RegionOne"

    # ── Optional: use a named cloud from clouds.yaml ──────────────────────────
    os_cloud: str = ""

    # ── Service limits ────────────────────────────────────────────────────────
    default_page_size: int = 50
    max_page_size: int = 200


@lru_cache
def get_settings() -> Settings:
    """Build Settings from environment variables.  Cached as a singleton."""
    env = os.environ
    return Settings(
        app_name=env.get("APP_NAME", "OpenStack VM API"),
        app_version=env.get("APP_VERSION", "1.0.0"),
        debug=env.get("DEBUG", "false").lower() == "true",
        log_level=env.get("LOG_LEVEL", "INFO"),
        os_auth_url=env.get("OS_AUTH_URL", ""),
        os_username=env.get("OS_USERNAME", ""),
        os_password=env.get("OS_PASSWORD", ""),
        os_project_name=env.get("OS_PROJECT_NAME", ""),
        os_user_domain_name=env.get("OS_USER_DOMAIN_NAME", "Default"),
        os_project_domain_name=env.get("OS_PROJECT_DOMAIN_NAME", "Default"),
        os_region_name=env.get("OS_REGION_NAME", "RegionOne"),
        os_cloud=env.get("OS_CLOUD", ""),
        default_page_size=int(env.get("DEFAULT_PAGE_SIZE", "50")),
        max_page_size=int(env.get("MAX_PAGE_SIZE", "200")),
    )
