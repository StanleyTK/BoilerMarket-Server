from rest_framework import serializers
from user.models import User

class VerifyPurdueEmailSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

class AddPurdueVerificationTokenSerializer(serializers.Serializer):
    uid = serializers.CharField()
    purdueEmail = serializers.EmailField()

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
            "uid", "email", "purdueEmail", "purdueEmailVerified", "displayName",
            "rating", "bio", "admin", "banned"
        ]
        # Mark certain fields as read-only so they can’t be updated by the user.
        read_only_fields = ["uid", "email", "rating", "admin", "banned"]

class EditUserSerializer(serializers.ModelSerializer):
    displayName = serializers.CharField()

    class Meta:
        model = User
        fields = ["purdueEmail", "displayName", "bio"]

    def validate_displayName(self, value):
        raw_value = self.initial_data.get("displayName")
        if not isinstance(raw_value, str):
            raise serializers.ValidationError("displayName must be a string")
        return value