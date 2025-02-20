from django.urls import path
from listing.views import get_all_listings, get_listings_by_keyword

urlpatterns = [
    path('listings/', get_all_listings, name="get_all_listings"),
    path('listings/<str:keyword>/', get_listings_by_keyword, name="get_listings_by_keyword"),
]
