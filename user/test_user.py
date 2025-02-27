import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from user.models import User
from unittest.mock import patch

# Dummy token verifier for testing purposes.
def dummy_verify_id_token(token):
    # For testing, always return a dummy uid.
    return {
        "uid": "dummy_uid",
        "email_verified": True
    }

def dummy_verify_id_token_unverified(token):
    # For testing, always return a dummy uid.
    return {
        "uid": "unverified_uid",
        "email_verified": True
    }

def dummy_verify_id_token_verified_purdue_unverified_email(token):
    # For testing, always return a dummy uid.
    return {
        "uid": "dummy_uid",
        "email_verified": False
    }

class UserEndpointTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a dummy user for testing.
        self.user = User.objects.create(
            uid="dummy_uid",
            email="dummy@example.com",
            displayName="Dummy",
            bio="Dummy bio",
            purdueEmail="fake@purdue.edu",
            purdueEmailVerified=True
        )
        self.unverified_user = User.objects.create(
            uid="unverified_uid",
            email="unverified@example.com",
            displayName="Unverified",
            bio="Dummy bio",
            purdueEmail="fake@purdue.edu",
            purdueEmailVerified=False
        )
        # We'll use a dummy token value.
        self.dummy_token = "dummy_token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.dummy_token}")

    # ---------------------------
    # Create User Tests (User Story #1)
    # ---------------------------
    # User Story #1: "As a user, I would like to create an account"
    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_us1_create_user_success(self, mock_verify):
        """US#1: Successful creation of a new user account."""
        url = reverse("create_user")
        payload = {
            "uid": "new_uid",
            "email": "new@example.com",
            "displayName": "New User",
            "bio": "New bio"
        }
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that the new user was created.
        self.assertTrue(User.objects.filter(uid="new_uid").exists())

    # User Story #1: Failure due to duplicate uid
    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_us1_create_user_duplicate_uid(self, mock_verify):
        """US#1: Attempt to create a user with a duplicate UID should fail."""
        url = reverse("create_user")
        payload = {
            "uid": "dummy_uid",
            "email": "another@example.com",
            "displayName": "Another User",
            "bio": "Another bio"
        }
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.json())

    # User Story #1: Failure due to missing required field
    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_us1_create_user_missing_field(self, mock_verify):
        """US#1: Missing required field (email) should return a 400 error."""
        url = reverse("create_user")
        payload = {
            "uid": "missing_email_uid",
            "displayName": "Missing Email",
            "bio": "No email provided"
        }
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.json())

    # ---------------------------
    # Email Verification Tests (User Story #2 and #3)
    # ---------------------------
    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token_verified_purdue_unverified_email)
    def test_us2_verify_email_failure(self, mock_verify):
        """US#2: Failure to verify email even though purdue email is verified"""
        url = reverse("check_email_auth")
        response = self.client.get(url, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_us3_verify_purdue_email_successful(self, mock_verify):
        """US#2: Successful verification of Purdue email."""
        url = reverse("check_email_auth")
        response = self.client.get(url, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token_unverified)
    def test_us3_verify_purdue_email_failure(self, mock_verify):
        """US#2: Attempt to verify Purdue email without authentication should fail."""
        url = reverse("check_email_auth")
        response = self.client.get(url, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------------------------
    # Delete User Tests (User Story #5)
    # ---------------------------
    # User Story #5: "As a user, I would like to delete my account"
    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_us5_delete_user_success(self, mock_verify):
        """US#4: Successful deletion of an existing user account."""
        url = reverse("delete_user")
        payload = {"uid": self.user.uid}
        response = self.client.delete(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(uid=self.user.uid)

    # User Story 5: Deletion failure (user not found)
    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_us5_delete_user_not_found(self, mock_verify):
        """US#4: Deleting a non-existent user should return a 404 error."""
        url = reverse("delete_user")
        payload = {"uid": "nonexistent_uid"}
        response = self.client.delete(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ---------------------------
    # Get User Info Tests (User Stories #5 & #6)
    # ---------------------------
    # User Story #6: "As a user, I would like to view my own profile"
    # User Story #7: "As a user, I would like to view another user’s profile"
    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_us6_view_user_info_success(self, mock_verify):
        """US#5/6: Retrieve user information successfully by UID."""
        url = reverse("get_user_by_uid", kwargs={"uid": self.user.uid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["uid"], self.user.uid)
        self.assertEqual(data["displayName"], self.user.displayName)

    # User Story #6: Viewing non-existent user profile
    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_us6_view_user_info_not_found(self, mock_verify):
        """US#6: Requesting profile for a non-existent UID should return 404."""
        url = reverse("get_user_by_uid", kwargs={"uid": "nonexistent_uid"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ---------------------------
    # Update User Info Tests (User Story #8)
    # ---------------------------
    # User Story #8: "As a user, I would like to edit account profile"
    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_us8_update_user_info_success(self, mock_verify):
        """US#8: Successful update of user profile fields."""
        url = reverse("update_user_info")
        payload = {
            "displayName": "Updated Dummy",
            "purdueEmail": "updated@example.com",
            "bio": "Updated bio"
        }
        response = self.client.put(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_user = User.objects.get(uid=self.user.uid)
        self.assertEqual(updated_user.displayName, "Updated Dummy")
        self.assertEqual(updated_user.purdueEmail, "updated@example.com")
        self.assertEqual(updated_user.bio, "Updated bio")

    # User Story #8: Update failure due to invalid data type for displayName
    @patch("user.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_us8_update_user_info_invalid(self, mock_verify):
        """US#8: Providing an invalid data type for displayName should return 400."""
        url = reverse("update_user_info")
        payload = {
            "displayName": 12345 
        }
        response = self.client.put(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("displayName", data)
