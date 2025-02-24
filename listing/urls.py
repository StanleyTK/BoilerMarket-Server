from django.urls import path
from listing.views import get_all_listings, get_listings_by_keyword, create_listing

urlpatterns = [
    path('get/', get_all_listings, name="get_all_listings"),
    path('get/<str:keyword>/', get_listings_by_keyword, name="get_listings_by_keyword"),
    path('create/', create_listing, name="create_listing")
]
