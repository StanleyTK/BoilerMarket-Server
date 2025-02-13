from rest_framework import serializers

class CreateUserSerializer(serializers.Serializer):
    uid = serializers.CharField()
    email = serializers.EmailField()
    displayName = serializers.CharField()
    bio = serializers.CharField(allow_blank=True)
