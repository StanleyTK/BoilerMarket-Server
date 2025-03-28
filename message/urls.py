from message.views import create_room, get_rooms
from django.urls import path

urlpatterns = [
    path('get_rooms/', get_rooms, name="get_rooms"),
    path('create_room/', create_room, name="create_room"),
]