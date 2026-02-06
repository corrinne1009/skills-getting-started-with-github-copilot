"""
Tests for the Mergington High School Activities API.
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the activities endpoint."""
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
    
    def test_get_activities_has_required_fields(self, client):
        """Test that activities have required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for name, details in activities.items():
            assert isinstance(name, str)
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)
    
    def test_get_activities_contains_chess_club(self, client):
        """Test that Chess Club is in the activities"""
        response = client.get("/activities")
        activities = response.json()
        assert "Chess Club" in activities


class TestSignupEndpoint:
    """Tests for the signup endpoint."""
    
    def test_signup_successful(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "test@mergington.edu" in result["message"]
        assert "Chess Club" in result["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant"""
        # Sign up
        client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu",
            follow_redirects=True
        )
        
        # Check activities list
        response = client.get("/activities")
        activities = response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_already_registered(self, client, reset_activities):
        """Test that signing up twice fails"""
        email = "test@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}",
            follow_redirects=True
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Chess%20Club/signup?email={email}",
            follow_redirects=True
        )
        assert response2.status_code == 400
        result = response2.json()
        assert "already signed up" in result["detail"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Fake%20Activity/signup?email=test@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]
    
    def test_signup_activity_full(self, client, reset_activities):
        """Test signup when activity is at capacity (currently allowed in API)"""
        from app import activities
        
        activity_name = "Tennis Club"
        activity = activities[activity_name]
        max_participants = activity["max_participants"]
        
        # Fill the activity
        for i in range(max_participants - len(activity["participants"])):
            activity["participants"].append(f"participant{i}@mergington.edu")
        
        # Try to add one more (API currently allows this)
        response = client.post(
            f"/activities/{activity_name}/signup?email=overcapacity@mergington.edu",
            follow_redirects=True
        )
        # API currently allows signup even when full
        assert response.status_code == 200


class TestUnregisterEndpoint:
    """Tests for the unregister endpoint."""
    
    def test_unregister_successful(self, client, reset_activities):
        """Test successful unregister from an activity"""
        from app import activities
        
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify participant is there
        assert email in activities[activity_name]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}",
            follow_redirects=True
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "Unregistered" in result["message"]
        
        # Verify participant is removed
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_not_registered(self, client, reset_activities):
        """Test unregister for participant not signed up"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 400
        result = response.json()
        assert "not signed up" in result["detail"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from non-existent activity"""
        response = client.post(
            "/activities/Fake%20Activity/unregister?email=test@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]


class TestIntegration:
    """Integration tests combining multiple operations."""
    
    def test_signup_and_unregister_flow(self, client, reset_activities):
        """Test complete flow of signing up and unregistering"""
        activity_name = "Programming%20Class"
        email = "integration@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=True
        )
        assert signup_response.status_code == 200
        
        # Verify in activities list
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Programming Class"]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister?email={email}",
            follow_redirects=True
        )
        assert unregister_response.status_code == 200
        
        # Verify removed from activities list
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Programming Class"]["participants"]
