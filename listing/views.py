import django
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from datetime import timedelta

from firebase_admin import auth as firebase_admin_auth

from server.authentication import FirebaseAuthentication, FirebaseEmailVerifiedAuthentication
from listing.models import Listing, ListingMedia
from listing.serializers import CreateListingSerializer, ListingSerializer, DeleteListingSerializer, UpdateListingSerializer
from user.models import User


@api_view(["POST"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def get_all_listings(request):
    """
    Fetch all listings
    """

    sort = request.data.get("sort", "dateListed")
    direction = request.data.get("dir", "desc")
    category = request.data.get("categoryFilter", None)
    date_range = request.data.get("dateFilter", None) # Current values: '', week, month
    price_range = request.data.get("priceFilter", None)
    location = request.data.get("locationFilter", None)
    keyword = request.data.get("keyword", None)

    if direction == "desc":
        sort = f"-{sort}"

    listings = Listing.objects.filter(hidden=False)

    if category:
        listings = listings.filter(category__iexact=category)

    if location:
        listings = listings.filter(location__iexact=location)

    if date_range:
        if date_range == "week":
            listings = listings.filter(dateListed__gte=django.utils.timezone.now() - timedelta(days=7))
        elif date_range == "month":
            listings = listings.filter(dateListed__gte=django.utils.timezone.now() - timedelta(days=30))

    if price_range:
        try:
            min_price, max_price = map(float, price_range.split("-"))
            listings = listings.filter(price__gte=min_price, price__lte=max_price)
        except ValueError:
            return Response({"error": "Invalid price range format. Use 'min-max' format."}, status=status.HTTP_400_BAD_REQUEST)

    if keyword:
        listings = listings.filter(title__icontains=keyword)

    listings = listings.order_by(sort)
    serializer = ListingSerializer(listings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([AllowAny])
def get_top_listings(request):
    user = User.objects.get(uid=request.user) if request.user.is_authenticated else None
    print(user)
    blocked_users = user.blockedUsers.all() if user else []
    print(blocked_users)
    listings = Listing.objects.exclude(user__in=blocked_users).order_by("-dateListed")[:12]
    serializer = ListingSerializer(listings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([AllowAny])
def get_top_listings_verified(request):
    user = User.objects.get(uid=request.user) if request.user.is_authenticated else None
    blocked_users = user.blockedUsers.all() if user else []
    listings = Listing.objects.exclude(user__in=blocked_users).order_by("-dateListed")[:12]
    serializer = ListingSerializer(listings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([AllowAny])
def get_listings_by_user(request, uid):
    """
    Fetch all listings that a user owns
    """
    listings = Listing.objects.filter(user=uid)
    serializer = ListingSerializer(listings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([AllowAny]) 
def get_listing_by_lid(request, lid=None):
    """
    Fetch a lising by LID.
    - If a LID is provided, return that listing.
    """
    try:
        listing = Listing.objects.get(id=lid)
    except Listing.DoesNotExist:
        return Response({"error": "Listing not found"}, status=status.HTTP_404_NOT_FOUND)
    # request_user = User.objects.get(uid=request.user)
    # listing_user = listing.user
    # print(f"Request user: {request_user.displayName}, Listing user: {listing_user.displayName}")
    # print(f"Request user blocked users: {[user.displayName for user in request_user.blocked_users.all()]}")
    # print(f"Listing user blocked users: {[user.displayName for user in listing_user.blocked_users.all()]}")
    # if request_user in listing_user.blocked_users.all():
    #     return Response({"error": "You are blocked by this user"}, status=status.HTTP_403_FORBIDDEN)
    # if listing_user in request_user.blocked_users.all():
    #     return Response({"error": "You have blocked this user"}, status=status.HTTP_403_FORBIDDEN)

    serializer = ListingSerializer(listing)
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(["POST"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def create_listing(request):
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
        location=validated_data['location'],
        user=user,
        hidden=validated_data['hidden']
    )

    # Save each media file
    media_files = request.FILES.getlist('media')
    for f in media_files:
        ListingMedia.objects.create(listing=listing, file=f)

    return Response({"message": "Listing created"}, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def delete_listing(request, listing_id):
    """
    Delete a listing and its associated media from S3
    """
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1]
    
    try:
        decoded_token = firebase_admin_auth.verify_id_token(token)
        token_uid = decoded_token.get("uid")
    except Exception:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        user = User.objects.get(uid=token_uid)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        listing = Listing.objects.get(id=listing_id)
    except Listing.DoesNotExist:
        return Response({"error": "Listing not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if listing.user != user:
        return Response({"error": "User does not own this listing"}, status=status.HTTP_401_UNAUTHORIZED)

    if hasattr(listing, 'media'):
        for media in listing.media.all():
            media.file.delete(save=False)
            media.delete()


    listing.delete()

    return Response({"message": "Listing deleted"}, status=status.HTTP_200_OK)

@api_view(["PUT", "PATCH"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def update_listing(request, listing_id):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1]
    
    try:
        decoded_token = firebase_admin_auth.verify_id_token(token)
        token_uid = decoded_token.get("uid")
    except Exception as e:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        user = User.objects.get(uid=token_uid)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        listing = Listing.objects.get(id=listing_id)
    except Listing.DoesNotExist:
        return Response({"error": "Listing not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if listing.user != user:
        return Response({"error": "User does not own this listing"}, status=status.HTTP_401_UNAUTHORIZED)
    
    serializer = UpdateListingSerializer(listing, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    serializer.save()
    full_serializer = ListingSerializer(listing)
    return Response(full_serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def save_listing(request, listing_id):
    """
    Have a user save a listing
    """
    try:
        user = User.objects.get(uid=request.user)
        listing = Listing.objects.get(id=listing_id)
    except (User.DoesNotExist, Listing.DoesNotExist):
        return Response({"error": "User or Listing not found"}, status=status.HTTP_404_NOT_FOUND)

    listing.saved_by.add(user)
    return Response({"message": "Listing saved"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def unsave_listing(request, listing_id):
    """
    Have a user un save a listing
    """
    try:
        user = User.objects.get(uid=request.user)
        listing = Listing.objects.get(id=listing_id)
    except (User.DoesNotExist, Listing.DoesNotExist):
        return Response({"error": "User or Listing not found"}, status=status.HTTP_404_NOT_FOUND)

    listing.saved_by.remove(user)
    return Response({"message": "Listing unsaved"}, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def get_saved_listings(request):
    """
    Get all saved listings for a user
    """
    user = User.objects.get(uid=request.user)
    blocked_users = user.blockedUsers.all() if user else []

    listings = Listing.objects.filter(saved_by=user).exclude(user__in=blocked_users)
    serializer = ListingSerializer(listings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# @api_view(["GET"])
# @permission_classes([AllowAny]) 
# def get_listing_by_lid(request, lid=None):
#     """
#     Fetch a lising by LID.
#     - If a LID is provided, return that listing.
#     """
#     try:
#         listing = Listing.objects.get(id=lid)
#     except Listing.DoesNotExist:
#         return Response({"error": "Listing not found"}, status=status.HTTP_404_NOT_FOUND)

#     serializer = SpecificListingSerializer(listing)
#     return Response(serializer.data, status=status.HTTP_200_OK)
