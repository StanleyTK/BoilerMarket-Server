from message.views import get_or_create_room, get_rooms
from django.urls import path

urlpatterns = [
    path('get_rooms/', get_rooms, name="get_rooms"),
    path('get_or_create_room/', get_or_create_room, name="get_or_create_room"),
]