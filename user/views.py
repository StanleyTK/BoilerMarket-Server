import os
import django
from django.conf import settings
from django.db.models import Q, Sum
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from firebase_admin import auth as firebase_admin_auth

from listing.serializers import ListingSerializer
from listing.models import Listing
from message.models import Message, Room
from user.models import History
from server.authentication import FirebaseAuthentication, FirebaseEmailVerifiedAuthentication
from server.firebase_auth import firebase_required
from user.models import User
from user.serializers import AddPurdueVerificationTokenSerializer, CreateUserSerializer, DeleteUserSerializer, EditUserSerializer, UploadProfilePictureSerializer, UserSerializer, VerifyPurdueEmailSerializer
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from decouple import config
import uuid



SENDGRID_API_KEY = config('SENDGRID_API_KEY')
APP_URL = config("APP_URL")

@api_view(["POST"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def verify_purdue_email(request):
    serializer = VerifyPurdueEmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    uid = serializer.validated_data["uid"]
    token = serializer.validated_data["token"]
    try:
        user = User.objects.get(uid=uid)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if user.purdueVerificationToken != token:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
    
    user.purdueEmailVerified = True
    user.save()
    return Response({"message": "Purdue email verified"}, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def send_purdue_verification(request):
    serializer = AddPurdueVerificationTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    uid = serializer.validated_data["uid"]
    purdueEmail = serializer.validated_data["purdueEmail"]
    try:
        user = User.objects.get(uid=uid)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if User.objects.filter(purdueEmail=purdueEmail).exists() and User.objects.get(purdueEmail=purdueEmail).uid != uid:
        return Response({"error": "This email has already been used"}, status=status.HTTP_400_BAD_REQUEST)
    
    if user.purdueVerificationLastSent is not None and (django.utils.timezone.now() - user.purdueVerificationLastSent).seconds < 60:
        return Response({"error": "Verification email already sent within the last minute"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    token = str(uuid.uuid4())

    user.purdueVerificationToken = token
    user.purdueEmail = purdueEmail
    user.purdueEmailVerified = False
    user.save()

    message = Mail(
        from_email="boilermarket21@gmail.com",
        to_emails=user.purdueEmail,
    )

    message.template_id = "d-fa79c8ecdc4a401f92d8136d357ed4d7"
    message.dynamic_template_data = {
        "firstName": user.displayName,
        "link": f"{APP_URL}verify/{token}"
    }

    try:
        print("attempting to send email")
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        user.purdueVerificationLastSent = django.utils.timezone.now()
        user.save()
    except Exception as e:
        print("error")
        print(e.with_traceback())
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Purdue verification token added and sent"}, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def create_user(request):
    serializer = CreateUserSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    uid, email, displayName, bio = (
        lambda uid, email, displayName, bio: (uid, email, displayName, bio)
    )(**serializer.validated_data)

    try:
        User.objects.create(uid=uid, email=email, displayName=displayName, bio=bio)
    except (django.db.utils.IntegrityError, django.core.exceptions.ValidationError) as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"message": "User created"}, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def delete_user(request):
    serializer = DeleteUserSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    uid = serializer.validated_data["uid"]
    try:
        user = User.objects.get(uid=uid)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    user.delete()
    return Response({"message": "User deleted"}, status=status.HTTP_200_OK)



@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_info(request, uid=None):
    """
    Fetch a user's profile by UID.
    - If no UID is provided, return the authenticated user's profile.
    - If a UID is provided, return that user's profile.
    This also returns the total views across all of that user's listings.
    """
    if uid is None and request.user.is_authenticated:
        user = request.user
    else:
        try:
            user = User.objects.get(uid=uid)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    # serialize the user
    serializer = UserSerializer(user)

    # sum up all the views on this user's listings
    agg = Listing.objects.filter(user=user).aggregate(views=Sum("views"))
    total = agg.get("views") or 0
    # print(total)

    # merge serializer data with the new field
    response_data = serializer.data
    response_data["views"] = total

    return Response(response_data, status=status.HTTP_200_OK)

@api_view(["PUT", "PATCH"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def update_user_info(request):
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

    remove = request.data.get("removeProfilePicture") == "true"
    new_profile_picture = request.FILES.get("profilePicture")

    if user.profilePicture and (remove or new_profile_picture):
        user.profilePicture.delete(save=False)

    if remove:
        user.profilePicture = None

    serializer = EditUserSerializer(user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    full_serializer = UserSerializer(user)
    return Response(full_serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def check_email_auth(request):
    return Response({"message": "User is Verified"}, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def upload_profile_picture(request):
    print("DJANGO_SETTINGS_MODULE:", os.environ.get("DJANGO_SETTINGS_MODULE"))
    print("DEFAULT_FILE_STORAGE from settings:", settings.DEFAULT_FILE_STORAGE)
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


    serializer = UploadProfilePictureSerializer(user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        serializer.save()

    except Exception as e:
        return Response({"error": "File save failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        "message": "Profile picture uploaded successfully",
        "profilePicture": serializer.data['profilePicture']
    }, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def block_user(request, uid):
    try:
        blocked_user = User.objects.get(uid=uid)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    user = User.objects.get(uid=request.user.username)
    if blocked_user in user.blockedUsers.all():
        return Response({"error": "User already blocked"}, status=status.HTTP_400_BAD_REQUEST)
    user.blockedUsers.add(blocked_user)
    user.save()
    rooms = Room.objects.filter(
        (Q(seller=user, buyer=blocked_user) | Q(seller=blocked_user, buyer=user))
    )

    room_ids = rooms.values_list('rid', flat=True)
    Message.objects.filter(room_id__in=room_ids).delete()
    rooms.delete()
    return Response({"message": "User blocked"}, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def get_blocked_users(request):
    user = User.objects.get(uid=request.user.username)
    blocked_users = user.blockedUsers.all()

    display_names = [
        {
            "displayName": blocked_user.displayName, 
            "uid": blocked_user.uid
        }
        for blocked_user in blocked_users
    ]

    return Response(display_names, status=200)

@api_view(["POST"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def unblock_user(request, uid):
    try:
        blocked_user = User.objects.get(uid=uid)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    user = User.objects.get(uid=request.user.username)
    if blocked_user not in user.blockedUsers.all():
        return Response({"error": "User is not blocked"}, status=status.HTTP_400_BAD_REQUEST)
    user.blockedUsers.remove(blocked_user)
    user.save()
    return Response({"message": "User unblocked"}, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def get_history(request, uid):
    user = User.objects.get(uid=request.user.username)
    
    viewed_listings = user.get_history()

    listings = [entry.listing for entry in viewed_listings]

    serializer = ListingSerializer(listings, many=True)

    return Response(serializer.data, status=200)

@api_view(["POST"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def addToHistory(request):
    print("addToHistory function is running")
    
    user_id = request.data.get("userId")
    listing_id = request.data.get("lid")

    if not user_id or not listing_id:
        return Response({"error": "userId and listingId are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(uid=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        listing = Listing.objects.get(id=listing_id)
    except Listing.DoesNotExist:
        return Response({"error": "Listing not found"}, status=status.HTTP_404_NOT_FOUND)

    History.objects.update_or_create(
        user=user,
        listing=listing,
        defaults={"viewed_at": django.utils.timezone.now()}
    )

# Way to delete old history if we care
#    history_entries = History.objects.filter(user=user).order_by('-viewed_at')
#    if history_entries.count() > 5:
#        history_entries[5:].delete()

    return Response({"message": "Listing added to history"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def getRecommendedListings(request, uid):
    user = User.objects.get(uid=request.user.username)
    
    viewed_listings = user.get_history()
    if not viewed_listings:
        return Response({"error": "No history found for the user"}, status=status.HTTP_404_NOT_FOUND)

    category_counts = {}
    for entry in viewed_listings:
        category = entry.listing.category
        if category in category_counts:
            category_counts[category] += 1
        else:
            category_counts[category] = 1

    most_common_category = max(category_counts, key=category_counts.get)

    viewed_listing_ids = [entry.listing.id for entry in viewed_listings]
    recommended_listings = Listing.objects.filter(
        category=most_common_category
    ).exclude(id__in=viewed_listing_ids).order_by('-dateListed')[:6]

    serializer = ListingSerializer(recommended_listings, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)