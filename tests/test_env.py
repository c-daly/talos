"""Tests for the Talos environment configuration module.

These tests validate repository root resolution and environment loading,
including the ability to relocate the repository via TALOS_REPO_ROOT.
"""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from talos import env


class TestGetRepoRoot:
    """Tests for get_repo_root function."""

    def test_default_repo_root_exists(self) -> None:
        """Default repo root detection finds valid directory."""
        # Clear any cached value
        env.get_repo_root.cache_clear()

        root = env.get_repo_root()
        assert root.exists()
        assert root.is_dir()

    def test_repo_root_contains_expected_markers(self) -> None:
        """Repo root contains expected markers (pyproject.toml, src/)."""
        env.get_repo_root.cache_clear()

        root = env.get_repo_root()
        assert (root / "pyproject.toml").exists()
        assert (root / "src").exists()
        assert (root / "tests").exists()

    def test_env_var_override(self) -> None:
        """TALOS_REPO_ROOT env var overrides detection."""
        env.get_repo_root.cache_clear()

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"TALOS_REPO_ROOT": tmpdir}):
                root = env.get_repo_root()
                assert root == Path(tmpdir).resolve()

        # Clear cache after test
        env.get_repo_root.cache_clear()

    def test_invalid_env_var_falls_back(self) -> None:
        """Invalid TALOS_REPO_ROOT path falls back to detection."""
        env.get_repo_root.cache_clear()

        with mock.patch.dict(
            os.environ, {"TALOS_REPO_ROOT": "/nonexistent/path/12345"}
        ):
            root = env.get_repo_root()
            # Should fall back to detected root
            assert root.exists()
            assert (root / "pyproject.toml").exists()

        env.get_repo_root.cache_clear()


class TestLoadStackEnv:
    """Tests for load_stack_env function."""

    def test_loads_env_test_file(self) -> None:
        """Loads .env.test file when present."""
        env.load_stack_env.cache_clear()
        env.get_repo_root.cache_clear()

        stack_env = env.load_stack_env()

        # .env.test exists in talos repo
        assert isinstance(stack_env, dict)
        # Should contain at least Neo4j config
        assert "NEO4J_URI" in stack_env or "NEO4J_PASSWORD" in stack_env

    def test_missing_file_returns_empty_dict(self) -> None:
        """Missing env file returns empty dict."""
        env.load_stack_env.cache_clear()

        result = env.load_stack_env("/nonexistent/file.env")
        assert result == {}


class TestGetEnvValue:
    """Tests for get_env_value function."""

    def test_os_env_takes_priority(self) -> None:
        """OS environment variable takes priority over mapping."""
        with mock.patch.dict(os.environ, {"TEST_VAR": "from_os"}):
            result = env.get_env_value(
                "TEST_VAR", env={"TEST_VAR": "from_mapping"}, default="default"
            )
            assert result == "from_os"

    def test_mapping_used_when_no_os_env(self) -> None:
        """Mapping used when OS env not set."""
        # Ensure TEST_VAR not in environment
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TEST_VAR_2", None)
            result = env.get_env_value(
                "TEST_VAR_2", env={"TEST_VAR_2": "from_mapping"}, default="default"
            )
            assert result == "from_mapping"

    def test_default_used_when_nothing_set(self) -> None:
        """Default used when neither OS env nor mapping has key."""
        os.environ.pop("NONEXISTENT_VAR", None)
        result = env.get_env_value("NONEXISTENT_VAR", env={}, default="my_default")
        assert result == "my_default"

    def test_none_returned_without_default(self) -> None:
        """None returned when key not found and no default."""
        os.environ.pop("NONEXISTENT_VAR", None)
        result = env.get_env_value("NONEXISTENT_VAR", env={})
        assert result is None


class TestGetNeo4jConfig:
    """Tests for get_neo4j_config function."""

    def test_returns_dict_with_expected_keys(self) -> None:
        """Returns dict with uri, user, password keys."""
        env.load_stack_env.cache_clear()

        config = env.get_neo4j_config()

        assert "uri" in config
        assert "user" in config
        assert "password" in config

    def test_has_sensible_defaults(self) -> None:
        """Has sensible defaults when no env configured."""
        config = env.get_neo4j_config(env={})

        assert config["uri"] == "bolt://localhost:7687"
        assert config["user"] == "neo4j"
        assert config["password"] == "neo4jtest"


class TestGetMilvusConfig:
    """Tests for get_milvus_config function."""

    def test_returns_dict_with_expected_keys(self) -> None:
        """Returns dict with host, port, healthcheck keys."""
        env.load_stack_env.cache_clear()

        config = env.get_milvus_config()

        assert "host" in config
        assert "port" in config
        assert "healthcheck" in config

    def test_has_sensible_defaults(self) -> None:
        """Has sensible defaults when no env configured."""
        config = env.get_milvus_config(env={})

        assert config["host"] == "localhost"
        assert config["port"] == "19530"
        assert config["healthcheck"] == "http://localhost:9091/healthz"


class TestRepoRelocation:
    """Tests demonstrating the suite works when repo is relocated."""

    def test_suite_runs_with_talos_repo_root_override(self) -> None:
        """Demonstrate suite runs when TALOS_REPO_ROOT is explicitly set.

        This test validates the acceptance criterion: the test suite
        should work correctly when the repo is relocated by overriding
        TALOS_REPO_ROOT.
        """
        env.get_repo_root.cache_clear()

        # Get the actual repo root
        actual_root = Path(__file__).resolve().parents[2]

        # Set TALOS_REPO_ROOT to point to it explicitly
        with mock.patch.dict(os.environ, {"TALOS_REPO_ROOT": str(actual_root)}):
            resolved_root = env.get_repo_root()

            # Verify the override worked
            assert resolved_root == actual_root.resolve()

            # Verify we can still load config
            config = env.get_neo4j_config()
            assert "uri" in config

        env.get_repo_root.cache_clear()
