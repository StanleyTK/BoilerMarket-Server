from rest_framework import serializers
from user.models import User

class DeleteUserSerializer(serializers.Serializer):
    uid = serializers.CharField()

class CreateUserSerializer(serializers.Serializer):
    uid = serializers.CharField()
    email = serializers.EmailField()
    displayName = serializers.CharField()
    bio = serializers.CharField(allow_blank=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "uid", "email", "purdueEmail", "displayName",
            "rating", "bio", "admin", "banned"
        ]
        # Mark certain fields as read-only so they can’t be updated by the user.
        read_only_fields = ["uid", "email", "rating", "admin", "banned"]
