from django.urls import path
from listing.views import get_all_listings, get_listings_by_keyword, create_listing, get_top_listings, get_listings_by_user, delete_listing, update_listing
from listing.views import get_listing_by_lid, save_listing, unsave_listing, get_saved_listings

urlpatterns = [
    path('get/', get_all_listings, name="get_all_listings"),
    path('get/<str:keyword>/', get_listings_by_keyword, name="get_listings_by_keyword"),
    path('getUserListing/<str:uid>/', get_listings_by_user, name="get_listings_by_user"),
    path('create/', create_listing, name="create_listing"),
    path('homepage/', get_top_listings, name='get_top_listings'),
    path('delete/<str:listing_id>/', delete_listing, name='delete_listing'),
    path('update/<str:listing_id>/', update_listing, name='update_listing'),
    path('save/<int:listing_id>/', save_listing, name='save-listing'),
    path('unsave/<int:listing_id>/', unsave_listing, name='unsave-listing'),
    path('getSaved/', get_saved_listings, name='get-saved-listings'),
    path('getListing/<str:lid>/', get_listing_by_lid, name=" get_listing_by_lid"),
    
]
