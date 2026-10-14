import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activity_data():
    return {
        "Chess Club": {
            "description": "Practice chess",
            "schedule": "Fridays",
            "max_participants": 4,
            "participants": ["existing@example.edu"],
        },
        "Art Club": {
            "description": "Make art",
            "schedule": "Wednesdays",
            "max_participants": 8,
            "participants": [],
        },
    }


@pytest.fixture
def client(monkeypatch, activity_data):
    monkeypatch.setattr(app_module, "activities", activity_data)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_catalog(client, activity_data):
    # Arrange
    expected_activities = activity_data

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_student_to_selected_activity(client, activity_data):
    # Arrange
    email = "new-student@example.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert activity_data["Chess Club"]["participants"] == ["existing@example.edu", email]
    assert activity_data["Art Club"]["participants"] == []


def test_signup_for_unknown_activity_returns_404(client):
    # Arrange
    email = "new-student@example.edu"

    # Act
    response = client.post("/activities/Unknown Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_duplicate_signup_returns_409_without_adding_student(client, activity_data):
    # Arrange
    email = "existing@example.edu"
    original_participants = activity_data["Chess Club"]["participants"].copy()

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 409
    assert response.json() == {"detail": "Student is already signed up for this activity"}
    assert activity_data["Chess Club"]["participants"] == original_participants


def test_unregister_removes_student_from_activity(client, activity_data):
    # Arrange
    email = "existing@example.edu"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    assert activity_data["Chess Club"]["participants"] == []


def test_unregister_from_unknown_activity_returns_404(client):
    # Arrange
    email = "existing@example.edu"

    # Act
    response = client.delete("/activities/Unknown Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_student_not_signed_up_returns_404(client, activity_data):
    # Arrange
    email = "not-signed-up@example.edu"
    original_participants = activity_data["Chess Club"]["participants"].copy()

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert activity_data["Chess Club"]["participants"] == original_participants