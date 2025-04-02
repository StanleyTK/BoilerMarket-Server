from django.urls import path

from listing.views import get_listing_by_lid, get_all_listings, create_listing, get_top_listings, get_listings_by_user, delete_listing, update_listing

urlpatterns = [
    path('get/', get_all_listings, name="get_all_listings"),
    path('getUserListing/<str:uid>/', get_listings_by_user, name="get_listings_by_user"),
    path('getListing/<str:lid>/', get_listing_by_lid, name=" get_listing_by_lid"),
    path('create/', create_listing, name="create_listing"),
    path('homepage/', get_top_listings, name='get_top_listings'),
    path('delete/<str:listing_id>/', delete_listing, name='delete_listing'),
    path('update/<str:listing_id>/', update_listing, name='update_listing')
]
