from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

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