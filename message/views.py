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
def get_room(request, room_id):
    try:
        room = Room.objects.get(rid=room_id)
        if request.user.username != room.seller.uid and request.user.username != room.buyer.uid:
            return Response({"error": "You are not part of this room"}, status=status.HTTP_400_BAD_REQUEST)
        response = {
            "rid": room.rid,
            "seller": room.seller.displayName,
            "buyer": room.buyer.displayName,
            "listingName": room.listing.title,
            "listingId": room.listing.id,
        }
        return Response(response, status=status.HTTP_200_OK)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def get_rooms(request):
    user = User.objects.get(uid=request.user.username)
    rooms = Room.objects.filter(seller=user) | Room.objects.filter(buyer=user)
    response = []
    for room in rooms:
        recent_message = Message.objects.filter(room=room).order_by('-timeSent').first()
        if recent_message:
            response.append({
                "rid": room.rid,
                "seller": room.seller.displayName,
                "buyer": room.buyer.displayName,
                "listingName": room.listing.title,
                "listingId": room.listing.id,
                "recentMessage": recent_message.content if recent_message else None,
                "timeSent": recent_message.timeSent if recent_message else None,
            })

    response.sort(key=lambda x: x["timeSent"], reverse=True)
    return Response({"rooms": response}, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def get_or_create_room(request):
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
    room = Room.objects.filter(seller=seller, buyer=buyer, listing=listing).first()
    if room:
        return Response({"rid": room.rid}, status=status.HTTP_200_OK)
    # Create the room
    room = Room.objects.create(seller=seller, buyer=buyer, listing=listing)
    room.save()
    return Response({"rid": room.rid}, status=status.HTTP_201_CREATED)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def get_messages(request, room_id):
    room = Room.objects.get(rid=room_id)
    if request.user.username != room.seller.uid and request.user.username != room.buyer.uid:
        return Response({"error": "You are not part of this room"}, status=status.HTTP_400_BAD_REQUEST)
    messages = Message.objects.filter(room=room).order_by('timeSent')
    response = []
    for message in messages:
        response.append({
            "sender": message.sender.displayName,
            "content": message.content,
            "timeSent": message.timeSent,
        })
    return Response({"messages": response}, status=status.HTTP_200_OK)