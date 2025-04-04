import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from listing.models import Listing
from user.models import User
from django.utils import timezone
from unittest.mock import patch
from datetime import timedelta  # Ensure this is imported at the top of your file
from django.core.files.uploadedfile import SimpleUploadedFile

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
    def test_get_top_listings_public(self, mock_verify):
        """
        User Story #17:
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
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Ensure that all listings are returned.
        self.assertEqual(len(data), 2)
        self.assertTrue(any(listing["title"] == "Listing 1" for listing in data))
        self.assertTrue(any(listing["title"] == "Listing 2" for listing in data))

    # is this a mistake do we have this function
    # @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    # def test_get_listings_by_keyword_authenticated(self, mock_verify):
    #     """
    #     User Story #18:
    #     As a user, I would like to search through listings by keywords.
    #     """
    #     # Create dummy listings.
    #     Listing.objects.create(
    #         title="Special Listing",
    #         description="Contains keyword",
    #         price=15.0,
    #         original_price=15.0,
    #         category="Test",
    #         user=self.user,
    #         hidden=False,
    #         sold=False
    #     )
    #     Listing.objects.create(
    #         title="Regular Listing",
    #         description="Does not contain keyword",
    #         price=25.0,
    #         original_price=25.0,
    #         category="Test",
    #         user=self.user,
    #         hidden=False,
    #         sold = False
    #     )
    #     url = reverse("get_listings_by_keyword", kwargs={"keyword": "Special"})
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     data = response.json()
    #     # Ensure that each returned listing's title contains "Special".
    #     self.assertTrue(all("Special" in listing["title"] for listing in data))

    

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
        # Create a dummy media file.
        media_file = SimpleUploadedFile("test_image.jpg", b"dummy_image_content", content_type="image/jpeg")
        
        payload = {
            "title": "New Listing",
            "description": "New listing description",
            "price": "50.00",
            "category": "Test",
            "location": "other",  # Provide a valid location from the allowed choices.
            "user": self.user.uid,
            "hidden": False,
            "sold": True  # Although 'sold' isn't used in the serializer, it's included in the payload.
        }
        # Include the media file in the request.
        payload["media"] = [media_file]

        response = self.client.post(url, data=payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Listing.objects.filter(title="New Listing").exists())

    
    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_delete_listing_success(self, mock_verify):
        """
        User Story #10:
        As a user, I would like to delete a listing.
        """

        listing = Listing.objects.create(
            title="Listing to Delete",
            description="This listing will be deleted",
            price=100.00,
            original_price=100.00,
            category="Test",
            user=self.user,
            hidden=False,
            sold=False
        )

        url = reverse("delete_listing", kwargs={"listing_id": listing.id})
        response = self.client.delete(url)
        

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Listing deleted")
        self.assertFalse(Listing.objects.filter(id=listing.id).exists())
        

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
                description="Test listing",
                price=10.0,
                original_price=10.0,
                category="Test",
                user=self.user,
                hidden=False,
                sold= False,
                dateListed=timezone.now()
        )
        url = reverse("update_listing", kwargs={"listing_id": listing.id})

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


    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_view_own_listings( self, mock_verify):
        """
        User Story #12:
        As a user, I would like to  view my own listings

        Acceptance Criteria:
        -  A user should be able to see their own listings
        """

        listing = Listing.objects.create(
                title="Test Listing ",
                description="Test listing",
                price=10.0,
                original_price=10.0,
                category="Test",
                user=self.user,
                hidden=False,
                sold= False,
                dateListed=timezone.now()
        )
        print(self.user)
        url = reverse("get_listings_by_user", kwargs={"uid": self.user.uid})
        response = self.client.get(url, content_type="application/json")
        print(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("Test Listing", str(response.json()))


    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_view_other_listings( self, mock_verify):
        """
        User Story #13:
        As a user, I would like to  view other user's listings

        Acceptance Criteria:
        -  A user should be able to view other user's listings
        """
        self.user = User.objects.create(
            uid="default_uid",
            email="dummy@example.com",
            displayName="Dummy",
            bio="Dummy bio",
            purdueEmail="fake@purdue.edu",
            purdueEmailVerified=True
        )
        self.other_user = User.objects.create(
            uid="other_uid",
            email="other@example.com",
            displayName="other",
            bio="Dummy bio",
            purdueEmail="fake@purdue.edu",
            purdueEmailVerified=True
        )
        listing = Listing.objects.create(
                title="Test other Listing ",
                description="Test other listing",
                price=10.0,
                original_price=10.0,
                category="Test",
                user=self.other_user,
                hidden=False,
                sold= False,
                dateListed=timezone.now()
        )
        print(self.user)
        url = reverse("get_listings_by_user", kwargs={"uid": self.other_user.uid})
        response = self.client.get(url, content_type="application/json")
        print(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("Test other Listing", str(response.json()))


    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_mark_as_sold( self, mock_verify):
        """
        User Story #14:
        As a user, I would like to mark my listings as sold

        Acceptance Criteria:
        -  A user should be able to mark their listings as sold
        """
        listing = Listing.objects.create(
                title="Test other Listing",
                description="desc",
                price=10.0,
                original_price=10.0,
                category="Test",
                user=self.user,
                hidden=False,
                sold= False,
                dateListed=timezone.now()
        )
        payload = {
            "description": "desc",
            "title": "Test other Listing",
            "price": "10.0",
            "category": "Test",
            "user": self.user.uid,
            "hidden": False,
            "sold": True
        }
        print(self.user)
        url = reverse("update_listing", kwargs={"listing_id": listing.id})
        response = self.client.patch(url,data=json.dumps(payload), content_type="application/json")
        print(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["sold"])

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_hide_listing( self, mock_verify):
        """
        User Story #15:
        As a user, I would like to hide my listings

        Acceptance Criteria:
        -  A user should be able to hide thier listings
        """
        listing = Listing.objects.create(
                title="Test other Listing",
                description="desc",
                price=10.0,
                original_price=10.0,
                category="Test",
                user=self.user,
                hidden=False,
                sold= False,
                dateListed=timezone.now()
        )
        payload = {
            "description": "desc",
            "title": "Test other Listing",
            "price": "10.0",
            "category": "Test",
            "user": self.user.uid,
            "hidden": True,
            "sold": False
        }
        print(self.user)
        url = reverse("update_listing", kwargs={"listing_id": listing.id})
        response = self.client.patch(url,data=json.dumps(payload), content_type="application/json")
        print(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["hidden"])

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_get_top_listings_verified(self, mock_verify):
        """
        Test that the endpoint returns the top listings for verified users.
        User Story #16:
        """

        self.user = User.objects.create(
            uid="default_uid",
            email="dummy@example.com",
            displayName="Dummy",
            bio="Dummy bio",
            purdueEmail="fake@purdue.edu",
            purdueEmailVerified=True
        )
        
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
        url = reverse("get_top_listings_verified")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_get_listing_by_lid(self, mock_verify):

        """
        User Story #12:
        As a user, I would like to view individual listings

        """

        listing = Listing.objects.create(
            title="Test Listing",
            description="Test description",
            price=10.0,
            original_price=10.0,
            category="Test",
            user=self.user,
            hidden=False,
            sold=False,
            dateListed=timezone.now()
        )
        url = reverse("get_listing_by_lid", kwargs={"lid": listing.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["title"], "Test Listing")

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_save_listing(self, mock_verify):
        """
        User Story #11:
        As a user, I would like to save listings

        """
        
        self.user = User.objects.create(
                    uid="default_uid",
                    email="dummy@example.com",
                    displayName="Dummy",
                    bio="Dummy bio",
                    purdueEmail="fake@purdue.edu",
                    purdueEmailVerified=True
                )
        self.other_user = User.objects.create(
            uid="other_uid",
            email="other@example.com",
            displayName="other",
            bio="Dummy bio",
            purdueEmail="fake@purdue.edu",
            purdueEmailVerified=True
        )

        listing = Listing.objects.create(
            title="Test Listing",
            description="Test description",
            price=10.0,
            original_price=10.0,
            category="Test",
            user=self.other_user,
            hidden=False,
            sold=False,
            dateListed=timezone.now()
        )
        url = reverse("save-listing", kwargs={"listing_id": listing.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_unsave_listing(self, mock_verify):
        """
        User Story #11:
        As a user, I would like to save listings

        """
        self.other_user = User.objects.create(
            uid="other_uid",
            email="other@example.com",
            displayName="other",
            bio="Dummy bio",
            purdueEmail="fake@purdue.edu",
            purdueEmailVerified=True
        )

        listing = Listing.objects.create(
            title="Test Listing",
            description="Test description",
            price=10.0,
            original_price=10.0,
            category="Test",
            user=self.other_user,
            hidden=False,
            sold=False,
            dateListed=timezone.now()
        )
        listing.saved_by.add(self.user)
        url = reverse("unsave-listing", kwargs={"listing_id": listing.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_get_saved_listings(self, mock_verify):
        """
        User Story #11, 19, 20:
        As a user, I would like to save listings

        """
        self.other_user = User.objects.create(
            uid="other_uid",
            email="other@example.com",
            displayName="other",
            bio="Dummy bio",
            purdueEmail="fake@purdue.edu",
            purdueEmailVerified=True
        )

        listing = Listing.objects.create(
            title="Test Listing",
            description="Test description",
            price=10.0,
            original_price=10.0,
            category="Test",
            user=self.other_user,
            hidden=False,
            sold=False,
            dateListed=timezone.now()
        )
        listing.saved_by.add(self.user)
        url = reverse("get-saved-listings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "Test Listing")

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_filter_listings_by_location_price_category_date(self, mock_verify):
        """
        Test filtering listings by location, price, category, and date/time listed.

        The test creates multiple listings with different attributes:
        - Listing 1 & 6: In "New York", category "Electronics", price within 100-200, listed within a week.
        - Listing 2: Wrong location ("Los Angeles").
        - Listing 3: Wrong category ("Clothing").
        - Listing 4: Price too high (250.0).
        - Listing 5: Listed more than a week ago.
        
        Only listings 1 and 6 should be returned by the filter.
        """
        now = timezone.now()
        # Listing 1: Should match
        Listing.objects.create(
            title="Electronics in New York 1",
            description="A test listing",
            price=120.0,
            original_price=120.0,
            category="Electronics",
            location="New York",
            user=self.user,
            hidden=False,
            sold=False,
            dateListed=now - timedelta(days=2)
        )
        # Listing 2: Wrong location
        Listing.objects.create(
            title="Electronics in Los Angeles",
            description="A test listing",
            price=120.0,
            original_price=120.0,
            category="Electronics",
            location="Los Angeles",
            user=self.user,
            hidden=False,
            sold=False,
            dateListed=now - timedelta(days=1)
        )
        # Listing 3: Wrong category
        Listing.objects.create(
            title="Clothing in New York",
            description="A test listing",
            price=120.0,
            original_price=120.0,
            category="Clothing",
            location="New York",
            user=self.user,
            hidden=False,
            sold=False,
            dateListed=now - timedelta(days=3)
        )
        # Listing 4: Price too high
        Listing.objects.create(
            title="Electronics in New York - Expensive",
            description="A test listing",
            price=250.0,
            original_price=250.0,
            category="Electronics",
            location="New York",
            user=self.user,
            hidden=False,
            sold=False,
            dateListed=now - timedelta(days=1)
        )
        # Listing 5: Date listed is older than one week.
        # Note: auto_now_add overrides the provided date, so we update it manually.
        listing5 = Listing.objects.create(
            title="Electronics in New York - Old Listing",
            description="A test listing",
            price=150.0,
            original_price=150.0,
            category="Electronics",
            location="New York",
            user=self.user,
            hidden=False,
            sold=False,
            dateListed=now  # This value will be overwritten.
        )
        Listing.objects.filter(id=listing5.id).update(dateListed=now - timedelta(days=10))
        
        # Listing 6: Should match
        Listing.objects.create(
            title="Electronics in New York 2",
            description="A test listing",
            price=150.0,
            original_price=150.0,
            category="Electronics",
            location="New York",
            user=self.user,
            hidden=False,
            sold=False,
            dateListed=now - timedelta(days=5)
        )

        payload = {
            "categoryFilter": "Electronics",
            "locationFilter": "New York",
            "priceFilter": "100-200",
            "dateFilter": "week"  # Only include listings from the last 7 days.
        }
        url = reverse("get_all_listings")
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Filter the returned listings to ensure they have a price between 100 and 200.
        filtered_results = [listing for listing in data if 100 <= float(listing["price"]) <= 200]
        self.assertEqual(len(filtered_results), 2)
        titles = [listing["title"] for listing in filtered_results]
        self.assertIn("Electronics in New York 1", titles)
        self.assertIn("Electronics in New York 2", titles)

    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_create_listing_with_video_success(self, mock_verify):
        """
        Test that a listing can be created with a video file.
        """
        url = reverse("create_listing")
        # Create a dummy video file.
        video_file = SimpleUploadedFile("test_video.mp4", b"dummy_video_content", content_type="video/mp4")
        
        payload = {
            "title": "Video Listing",
            "description": "Listing with video",
            "price": "75.00",
            "category": "Test",
            "location": "other",  # Valid location choice.
            "user": self.user.uid,
            "hidden": False
        }
        # Include the video file in the request.
        payload["media"] = [video_file]
        
        response = self.client.post(url, data=payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that the listing exists and has one media file.
        listing = Listing.objects.get(title="Video Listing")
        media_files = listing.media.all()
        self.assertEqual(media_files.count(), 1)
        # Optionally, verify that the uploaded file name is as expected.
        self.assertTrue(media_files[0].file.name.endswith("test_video.mp4"))


    @patch("listing.views.firebase_admin_auth.verify_id_token", side_effect=dummy_verify_id_token)
    def test_create_listing_with_image_and_video_success(self, mock_verify):
        """
        Test that a listing can be created with both an image and a video file.
        """
        url = reverse("create_listing")
        # Create dummy files for image and video.
        image_file = SimpleUploadedFile("test_image.png", b"dummy_image_content", content_type="image/png")
        video_file = SimpleUploadedFile("test_video.mp4", b"dummy_video_content", content_type="video/mp4")
        
        payload = {
            "title": "Mixed Media Listing",
            "description": "Listing with both image and video",
            "price": "100.00",
            "category": "Test",
            "location": "other",
            "user": self.user.uid,
            "hidden": False
        }
        # Include both media files.
        payload["media"] = [image_file, video_file]
        
        response = self.client.post(url, data=payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Retrieve the created listing and check its media.
        listing = Listing.objects.get(title="Mixed Media Listing")
        media_files = listing.media.all()
        self.assertEqual(media_files.count(), 2)
        filenames = [m.file.name for m in media_files]
        self.assertTrue(any(filename.endswith("test_image.png") for filename in filenames))
        self.assertTrue(any(filename.endswith("test_video.mp4") for filename in filenames))
