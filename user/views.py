import django
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from user.authentication import FirebaseAuthentication
from user.models import User
from user.serializers import CreateUserSerializer

@api_view(["POST"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def create_user(request):
    serializer = CreateUserSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    uid, email, displayName, bio = (lambda uid, email, displayName, bio: (uid, email, displayName, bio))(**serializer.validated_data)

    try:
        User.objects.create(uid=uid, email=email, displayName=displayName, bio=bio)
    except (django.db.utils.IntegrityError, django.core.exceptions.ValidationError) as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"message": "User created"}, status=status.HTTP_201_CREATED)