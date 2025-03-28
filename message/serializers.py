from rest_framework import serializers

class CreateRoomSerializer(serializers.Serializer):
    lid = serializers.IntegerField()
    uid = serializers.CharField(max_length=255)