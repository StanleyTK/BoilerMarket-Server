from django.urls import path
from listing.views import get_all_listings, get_listings_by_keyword, create_listing, get_top_listings, get_listings_by_user, delete_listing

urlpatterns = [
    path('get/', get_all_listings, name="get_all_listings"),
    path('get/<str:keyword>/', get_listings_by_keyword, name="get_listings_by_keyword"),
    path('getUserListing/<str:uid>/', get_listings_by_user, name="get_listings_by_user"),
    path('create/', create_listing, name="create_listing"),
    path('homepage/', get_top_listings, name='get_top_listings'),
    path('delete/', delete_listing, name='delete_listing')
]
