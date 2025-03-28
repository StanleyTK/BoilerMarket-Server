from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from listing.models import Listing
from message.serializers import CreateRoomSerializer
from server.authentication import FirebaseEmailVerifiedAuthentication
from user.models import User
from message.models import Room, Message

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def get_rooms(request):
    user = User.objects.get(uid=request.user.username)
    rooms = Room.objects.filter(seller=user) | Room.objects.filter(buyer=user)
    response = []
    for room in rooms:
        recent_message = Message.objects.filter(room=room).order_by('-timestamp').first()
        response.append({
            "rid": room.rid,
            "seller": room.seller.username,
            "buyer": room.buyer.username,
            "listingName": room.listing.title,
            "listingId": room.listing.id,
            "recentMessage": recent_message.content if recent_message else None,
        })
    return Response({"rooms": response}, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def create_room(request):
    print(request.data)
    serializer = CreateRoomSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    lid = serializer.validated_data.get("lid")
    buyer_uid = serializer.validated_data.get("uid")
    listing = Listing.objects.get(id=lid)
    buyer = User.objects.get(uid=buyer_uid)
    seller = listing.user
    # Check if the room already exists
    if Room.objects.filter(seller=seller, buyer=buyer, listing=listing).exists():
        return Response({"error": "Room already exists"}, status=status.HTTP_400_BAD_REQUEST)
    # Create the room
    room = Room.objects.create(seller=seller, buyer=buyer, listing=listing)
    room.save()
    return Response({"rid": room.rid}, status=status.HTTP_201_CREATED)