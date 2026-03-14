"""
Root conftest.py — shared fixtures for all tests.

Unit tests: use mocks, no external services.
Integration tests: use real Docker containers via docker-compose.test.yml.
"""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: fast tests with no external dependencies")
    config.addinivalue_line("markers", "integration: tests that require running Docker services")
