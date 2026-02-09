"""Tests for MathPilot."""

import pytest


@pytest.fixture
def sample_task():
    """Sample user task."""
    return "implement a Kalman filter"


def test_placeholder(sample_task):
    """Placeholder test."""
    assert sample_task is not None
