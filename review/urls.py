from django.urls import path
from review.views import (get_all_reviews,
  create_review,
  delete_review,
  get_reviews_about_user,
  get_reviews_by_user
)

urlpatterns = [
  path('get/', get_all_reviews, name="get_all_reviews"),
  path('about/<str:uid>/', get_reviews_about_user, name="get_reviews_about_user"),
  path('by/<str:uid>/', get_reviews_by_user, name="get_reviews_by_user"),
  path('create/', create_review, name="create_review"),
  path('delete/<str:review_id>/', delete_review, name='delete_review'),
]