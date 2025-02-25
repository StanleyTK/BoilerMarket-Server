import django
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from firebase_admin import auth as firebase_admin_auth

from server.authentication import FirebaseAuthentication, FirebaseEmailVerifiedAuthentication
from server.firebase_auth import firebase_required
from user.models import User
from user.serializers import AddPurdueVerificationTokenSerializer, CreateUserSerializer, DeleteUserSerializer, EditUserSerializer, UserSerializer, VerifyPurdueEmailSerializer
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
    """
    if uid is None and request.user.is_authenticated:
        user = request.user
    else:
        try:
            user = User.objects.get(uid=uid)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)



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
    except Exception as e:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        user = User.objects.get(uid=token_uid)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = EditUserSerializer(user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    serializer.save()
    full_serializer = UserSerializer(user)
    return Response(full_serializer.data, status=status.HTTP_200_OK)