import django
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from server.authentication import FirebaseAuthentication, FirebaseEmailVerifiedAuthentication
from server.firebase_auth import firebase_required
from listing.models import Listing
from listing.serializers import CreateListingSerializer, ListingSerializer, TopListingSerializer, DeleteListingSerializer
from user.models import User


@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def get_all_listings(request):
    """
    Fetch all listings
    """
    listings = Listing.objects.all()
    serializer = ListingSerializer(listings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def get_listings_by_keyword(request, keyword):
    """
    Fetch all listings that have a keyword in the title
    """
    listings = Listing.objects.filter(title__icontains=keyword)
    serializer = ListingSerializer(listings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([AllowAny])
def get_top_listings(request):
    listings = Listing.objects.order_by("-dateListed")[:12]
    serializer = TopListingSerializer(listings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def get_listings_by_user(request, uid):
    """
    Fetch all listings that a user owns
    """
    listings = Listing.objects.filter(user=uid)
    serializer = ListingSerializer(listings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(["POST"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def create_listing(request):
    """
    Create a listing
    """
    serializer = CreateListingSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    user = User.objects.get(uid=validated_data['user'])

    listing = Listing.objects.create(
        title=validated_data['title'],
        description=validated_data['description'],
        price=validated_data['price'],
        original_price=validated_data['price'],
        category=validated_data['category'],
        user=user,
        hidden=validated_data['hidden'] # Support for creating a listing as hidden, can be removed if not used
    )

    return Response({"message": "Listing created"}, status=status.HTTP_201_CREATED)

@api_view(["DELETE"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def delete_listing(request):
    """
    Delete a listing
    """
    serializer = DeleteListingSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    user = User.objects.get(uid=validated_data['user'])

    listing = Listing.objects.get(
        id=validated_data['id']
    )

    if listing.user != user:
        return Response({"message": "User does not own this listing"}, status=status.HTTP_403_FORBIDDEN)

    listing.delete()

    return Response({"message": "Listing deleted"}, status=status.HTTP_200_OK)