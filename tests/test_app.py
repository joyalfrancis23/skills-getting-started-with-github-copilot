"""Tests for the FastAPI application"""
import pytest


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that getting activities returns all activities with correct structure"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        
        assert isinstance(activities, dict)
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert len(activities) == 9
    
    def test_activity_has_required_fields(self, client, reset_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)
            assert isinstance(details["max_participants"], int)


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_email_fails(self, client, reset_activities):
        """Test that signing up with an email already registered fails"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()
    
    def test_signup_activity_full_fails(self, client, reset_activities):
        """Test signup fails when activity is at max capacity"""
        # First, fill up Swimming (max_participants=25, currently has 1)
        for i in range(24):
            client.post(
                "/activities/Swimming/signup",
                params={"email": f"student{i}@mergington.edu"}
            )
        
        # Try to sign up one more - should fail
        response = client.post(
            "/activities/Swimming/signup",
            params={"email": "extraStudent@mergington.edu"}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "full" in result["detail"].lower()


class TestRemoveParticipant:
    """Test the DELETE /activities/{activity_name}/participant endpoint"""
    
    def test_remove_participant_success(self, client, reset_activities):
        """Test successfully removing a participant from an activity"""
        # First add a participant
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Then remove them
        response = client.delete(
            "/activities/Chess Club/participant",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "Removed" in result["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" not in activities["Chess Club"]["participants"]
    
    def test_remove_participant_not_found(self, client, reset_activities):
        """Test removing a participant that doesn't exist fails"""
        response = client.delete(
            "/activities/Chess Club/participant",
            params={"email": "nonexistent@mergington.edu"}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()
    
    def test_remove_from_nonexistent_activity_fails(self, client, reset_activities):
        """Test removing participant from non-existent activity fails"""
        response = client.delete(
            "/activities/Nonexistent Activity/participant",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()
    
    def test_remove_existing_participant_success(self, client, reset_activities):
        """Test removing an existing participant"""
        response = client.delete(
            "/activities/Chess Club/participant",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == 1


class TestEdgeCases:
    """Test edge cases and integration scenarios"""
    
    def test_signup_then_remove_then_signup_again(self, client, reset_activities):
        """Test signing up, removing, then signing up again"""
        email = "testuser@mergington.edu"
        activity = "Art Studio"
        
        # Sign up
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Remove
        response2 = client.delete(
            f"/activities/{activity}/participant",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Sign up again - should work
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        
        # Verify participant is there
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
    
    def test_multiple_signups_then_verify_list(self, client, reset_activities):
        """Test multiple signups and verify the participant list"""
        activity = "Debate Team"
        new_emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in new_emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all are in the list
        activities_response = client.get("/activities")
        activities = activities_response.json()
        participants = activities[activity]["participants"]
        
        for email in new_emails:
            assert email in participants
        
        # Verify original participants are still there
        assert "isabella@mergington.edu" in participants
        assert "ethan@mergington.edu" in participants
