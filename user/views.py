import django
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from server.authentication import FirebaseAuthentication
from server.firebase_auth import firebase_required
from user.models import User
from user.serializers import CreateUserSerializer, UserSerializer

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

@api_view(["PUT"])
@firebase_required
def update_user_info(request):
    serializer = UserSerializer(request.user, data=request.data)
    if serializer.is_valid():
        try:
            serializer.save()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
