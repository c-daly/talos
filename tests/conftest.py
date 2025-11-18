"""Pytest configuration and shared fixtures.

This file imports all Talos fixtures to make them available to all tests
without requiring explicit imports in each test file.
"""

# Import all fixtures from talos.fixtures to make them available
pytest_plugins = ["talos.fixtures"]
