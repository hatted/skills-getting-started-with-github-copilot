"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the app"""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_has_expected_fields(self, client):
        """Test that activities have required fields"""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_details in activities.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_contains_basketball(self, client):
        """Test that Basketball activity exists"""
        response = client.get("/activities")
        activities = response.json()
        assert "Basketball" in activities


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_with_valid_activity_and_email(self, client):
        """Test signing up with valid activity and email"""
        response = client.post(
            "/activities/Tennis/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        response = client.post(
            f"/activities/Basketball/signup?email={email}"
        )
        assert response.status_code == 200

        # Verify the participant was added
        activities = client.get("/activities").json()
        assert email in activities["Basketball"]["participants"]

    def test_signup_to_nonexistent_activity(self, client):
        """Test signup to an activity that doesn't exist"""
        response = client.post(
            "/activities/NonexistentActivity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_duplicate_email(self, client):
        """Test signing up the same email twice"""
        email = "duplicate@mergington.edu"

        # First signup should succeed
        response1 = client.post(
            f"/activities/Tennis/signup?email={email}"
        )
        assert response1.status_code == 200

        # Second signup should fail
        response2 = client.post(
            f"/activities/Tennis/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_response_message_format(self, client):
        """Test that signup response has proper message format"""
        response = client.post(
            "/activities/Art Studio/signup?email=artist@mergington.edu"
        )
        data = response.json()
        assert "Signed up" in data["message"]
        assert "artist@mergington.edu" in data["message"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_removes_participant(self, client):
        """Test that unregister removes a participant"""
        email = "unregister@mergington.edu"

        # First, sign up
        client.post(f"/activities/Chess Club/signup?email={email}")

        # Verify participant is registered
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]

        # Now unregister
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200

        # Verify participant is removed
        activities = client.get("/activities").json()
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregistering from activity that doesn't exist"""
        response = client.delete(
            "/activities/NonexistentActivity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering someone not registered"""
        response = client.delete(
            "/activities/Debate Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_unregister_response_message_format(self, client):
        """Test that unregister response has proper message format"""
        email = "removetest@mergington.edu"

        # Sign up first
        client.post(f"/activities/Drama Club/signup?email={email}")

        # Unregister
        response = client.delete(
            f"/activities/Drama Club/unregister?email={email}"
        )
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_html(self, client):
        """Test that root endpoint redirects to static HTML"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegrationScenarios:
    """Integration tests for common user scenarios"""

    def test_full_signup_and_unregister_flow(self, client):
        """Test complete flow: signup, verify, unregister"""
        email = "integration@mergington.edu"
        activity = "Robotics Club"

        # 1. Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200

        # 2. Verify signup
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        initial_count = len(activities[activity]["participants"])

        # 3. Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200

        # 4. Verify unregister
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count - 1

    def test_multiple_signups_to_different_activities(self, client):
        """Test signing up to multiple activities"""
        email = "multiactivity@mergington.edu"
        activities_to_join = ["Basketball", "Tennis", "Chess Club"]

        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200

        # Verify in all activities
        activities = client.get("/activities").json()
        for activity in activities_to_join:
            assert email in activities[activity]["participants"]
