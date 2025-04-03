from message.views import get_messages, get_or_create_room, get_rooms, get_room
from django.urls import path

urlpatterns = [
    path('get_rooms/', get_rooms, name="get_rooms"),
    path('get_room/<int:room_id>/', get_room, name="get_room"),
    path('get_or_create_room/', get_or_create_room, name="get_or_create_room"),
    path('get_messages/<int:room_id>/', get_messages, name="get_messages"),
]