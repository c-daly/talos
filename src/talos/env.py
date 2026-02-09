"""Environment helpers for Talos repository configuration.

This module provides utilities for resolving repository paths and loading
environment configuration in a consistent way across tests and scripts.

The primary use case is the ``TALOS_REPO_ROOT`` environment variable which
allows tests to run correctly when the repository is relocated or when
running in CI environments.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import cast

from logos_config.env import get_env_value as resolve_env_value
from logos_config.env import get_repo_root as resolve_repo_root
from logos_config.ports import get_repo_ports


def _default_env_path() -> Path:
    """Get the default path to the stack environment file."""
    override = os.getenv("TALOS_STACK_ENV")
    if override:
        return Path(override)
    repo_root = get_repo_root()
    # Standard location for generated stack env file
    candidate = repo_root / "tests" / "e2e" / "stack" / "talos" / ".env.test"
    if candidate.exists():
        return candidate
    # Fallback to root .env.test (legacy location)
    return repo_root / ".env.test"


@cache
def load_stack_env(env_path: str | Path | None = None) -> dict[str, str]:
    """Load the canonical stack environment (key/value pairs).

    Values are parsed from the ``.env.test`` file. Callers can override the
    location via ``env_path`` or the ``TALOS_STACK_ENV`` environment variable.
    Missing files simply yield an empty mapping so tests can still fall back
    to hard-coded defaults.

    Args:
        env_path: Optional path to the environment file.

    Returns:
        Dictionary of environment variable name to value.
    """
    path = Path(env_path) if env_path else _default_env_path()
    env: dict[str, str] = {}
    if not path.exists():
        return env

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        env[key.strip()] = value
    return env


def get_env_value(
    key: str,
    env: Mapping[str, str] | None = None,
    default: str | None = None,
) -> str | None:
    """Resolve an env var by checking OS env, stack env, then default.

    Priority order:
    1. OS environment variable
    2. Provided env mapping (e.g., from load_stack_env)
    3. Default value

    Args:
        key: Environment variable name.
        env: Optional mapping to check (typically from load_stack_env).
        default: Default value if not found elsewhere.

    Returns:
        The resolved value or None if not found and no default.
    """
    return cast(str | None, resolve_env_value(key, env=env, default=default))


@cache
def get_repo_root(env: Mapping[str, str] | None = None) -> Path:
    """Resolve the Talos repo root, honoring TALOS_REPO_ROOT if set.

    Priority:
    1. TALOS_REPO_ROOT from OS env or provided mapping (if path exists).
    2. GITHUB_WORKSPACE (set by GitHub Actions in CI).
    3. Fallback to parent of this package (works when running from source).

    Args:
        env: Optional mapping to check for TALOS_REPO_ROOT.

    Returns:
        Path to the repository root directory.
    """
    return cast(Path, resolve_repo_root("talos", env=env))


def get_neo4j_config(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Get Neo4j connection configuration.

    Loads from environment variables with sensible defaults for testing.

    Args:
        env: Optional mapping from load_stack_env().

    Returns:
        Dictionary with 'uri', 'user', and 'password' keys.
    """
    if env is None:
        env = load_stack_env()
    ports = get_repo_ports("talos", env)
    default_uri = f"bolt://localhost:{ports.neo4j_bolt}"
    return {
        "uri": get_env_value("NEO4J_URI", env, default_uri) or default_uri,
        "user": get_env_value("NEO4J_USER", env, "neo4j") or "neo4j",
        "password": get_env_value("NEO4J_PASSWORD", env, "logosdev") or "logosdev",
    }


def get_milvus_config(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Get Milvus connection configuration.

    Loads from environment variables with sensible defaults for testing.

    Args:
        env: Optional mapping from load_stack_env().

    Returns:
        Dictionary with 'host', 'port', and 'healthcheck' keys.
    """
    if env is None:
        env = load_stack_env()
    ports = get_repo_ports("talos", env)
    default_health = f"http://localhost:{ports.milvus_metrics}/healthz"
    return {
        "host": get_env_value("MILVUS_HOST", env, "localhost") or "localhost",
        "port": get_env_value("MILVUS_PORT", env, str(ports.milvus_grpc))
        or str(ports.milvus_grpc),
        "healthcheck": get_env_value("MILVUS_HEALTHCHECK", env, default_health)
        or default_health,
    }
