from message.views import get_rooms
from django.urls import path

urlpatterns = [
    path('get_rooms/', get_rooms, name="get_rooms"),
]