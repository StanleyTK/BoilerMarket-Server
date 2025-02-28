import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from listing.models import Listing
from user.models import User
from django.utils import timezone
from unittest.mock import patch

# Dummy token verifier for testing purposes.
def dummy_verify_id_token(token):
    return {
        "uid": "dummy_uid",
        "email_verified": True
    }

class ListingEndpointTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a dummy user for testing.
        self.user = User.objects.create(
            uid="dummy_uid",
            email="dummy@example.com",
            displayName="Dummy User",
            bio="Dummy bio",
            purdueEmail="fake@purdue.edu",
            purdueEmailVerified=True
        )
        # Set a dummy token in the request headers.
        self.dummy_token = "dummy_token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.dummy_token}")

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_get_all_listings_authenticated(self, mock_verify):
        """
        User Story #18:
        As a user, I would like to see all listings.
        """
        # Create dummy listings.
        Listing.objects.create(
            title="Listing 1",
            description="First listing",
            price=10.0,
            original_price=10.0,
            category="Test",
            user=self.user,
            hidden=False
        )
        Listing.objects.create(
            title="Listing 2",
            description="Second listing",
            price=20.0,
            original_price=20.0,
            category="Test",
            user=self.user,
            hidden=False
        )
        url = reverse("get_all_listings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Ensure that all listings are returned.
        self.assertEqual(len(data), 2)
        self.assertTrue(any(listing["title"] == "Listing 1" for listing in data))
        self.assertTrue(any(listing["title"] == "Listing 2" for listing in data))

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_get_listings_by_keyword_authenticated(self, mock_verify):
        """
        User Story #18:
        As a user, I would like to search through listings by keywords.
        """
        # Create dummy listings.
        Listing.objects.create(
            title="Special Listing",
            description="Contains keyword",
            price=15.0,
            original_price=15.0,
            category="Test",
            user=self.user,
            hidden=False,
            sold=False
        )
        Listing.objects.create(
            title="Regular Listing",
            description="Does not contain keyword",
            price=25.0,
            original_price=25.0,
            category="Test",
            user=self.user,
            hidden=False,
            sold = False
        )
        url = reverse("get_listings_by_keyword", kwargs={"keyword": "Special"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Ensure that each returned listing's title contains "Special".
        self.assertTrue(all("Special" in listing["title"] for listing in data))

    def test_get_top_listings_public(self):
        """
        User Story #16:
        As a user, I would like to see top listings when I log in.
        """
        # Create more than 12 listings.
        for i in range(15):
            Listing.objects.create(
                title=f"Listing {i}",
                description="Test top listing",
                price=10.0 + i,
                original_price=10.0 + i,
                category="Test",
                user=self.user,
                hidden=False,
                sold= False,
                dateListed=timezone.now()
            )
        url = reverse("get_top_listings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertLessEqual(len(data), 12)

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_create_listing_success(self, mock_verify):
        """
        User Story #9:
        As a user, I would like to create a listing to sell an item.

        Acceptance Criteria:
          - When a user provides all required fields, the listing is created successfully.
        This test posts valid data and confirms that the listing is created.
        """
        url = reverse("create_listing")
        payload = {
            "title": "New Listing",
            "description": "New listing description",
            "price": "50.00",
            "category": "Test",
            "user": self.user.uid,
            "hidden": False,
            "sold": True
        }
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Listing.objects.filter(title="New Listing").exists())

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_create_listing_missing_field(self, mock_verify):
        """
        User Story #9:
        As a user, I would like to create a listing to sell an item.

        Acceptance Criteria:
          - If a required field (e.g., title) is missing, the creation fails with a 400 error.
        This test omits the 'title' field and verifies that a 400 error is returned.
        """
        url = reverse("create_listing")
        payload = {
            "description": "Listing without title",
            "price": "30.00",
            "category": "Test",
            "user": self.user.uid,
            "hidden": False,
            "sold": True
        }
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("title", data)




    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_update_listing( self, mock_verify):
        """
        User Story #11:
        As a user, I would like to edit a listing

        Acceptance Criteria:
          -  When a user inputs a changed field, the listing is updated successfully.
        This test updaes valid data and confirms that the listing is successfully updated.
        """

        listing = Listing.objects.create(
                title="Test Listing ",
                description="Test top listing",
                price=10.0,
                original_price=10.0,
                category="Test",
                user=self.user,
                hidden=False,
                sold= False,
                dateListed=timezone.now()
        )
        url = reverse("update_listing", kwargs={"listing_id": "1"})

        payload = {
            "description": "desc",
            "title": "New Title",
            "price": "30.00",
            "category": "Test",
            "user": self.user.uid,
            "hidden": False,
            "sold": True
        }
        response = self.client.patch(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(Listing.objects.filter(title="New Title").exists())


    # @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    # def test_view_own_listings( self, mock_verify):
    #     """
    #     User Story #12:
    #     As a user, I would like to  view my own listings

    #     Acceptance Criteria:
    #     -  A user should be able to see their own listings
    #     """

    #     listing = Listing.objects.create(
    #             title="Test Listing ",
    #             description="Test top listing",
    #             price=10.0,
    #             original_price=10.0,
    #             category="Test",
    #             user=self.user,
    #             hidden=False,
    #             sold= False,
    #             dateListed=timezone.now()
    #     )
    #     url = reverse("update_listing", kwargs={"listing_id": "1"})

    #     payload = {
    #         "description": "desc",
    #         "title": "New Title",
    #         "price": "30.00",
    #         "category": "Test",
    #         "user": self.user.uid,
    #         "hidden": False,
    #         "sold": True
    #     }
    #     response = self.client.patch(url, data=json.dumps(payload), content_type="application/json")
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     data = response.json()
    #     self.assertTrue(Listing.objects.filter(title="New Title").exists())
