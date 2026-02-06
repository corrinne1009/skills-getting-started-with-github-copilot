"""
Pytest configuration and fixtures for testing the Mergington High School API.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Provides a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test."""
    from app import activities
    
    # Store original state
    original_activities = {
        k: {**v, "participants": v["participants"].copy()}
        for k, v in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for k in list(activities.keys()):
        if k in original_activities:
            activities[k]["participants"] = original_activities[k]["participants"].copy()
        else:
            del activities[k]
    for k, v in original_activities.items():
        if k not in activities:
            activities[k] = v
