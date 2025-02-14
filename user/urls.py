from django.urls import path
from user.views import create_user, get_user_info, update_user_info

urlpatterns = [
    path('create_user/', create_user, name="create_user"),
    path('info/', get_user_info, name="get_user_info"), 
    path('info/<str:uid>/', get_user_info, name="get_user_by_uid"), 
    path('update/', update_user_info, name="update_user_info"),
]
