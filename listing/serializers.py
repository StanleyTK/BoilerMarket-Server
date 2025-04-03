from rest_framework import serializers
from listing.models import Listing, ListingMedia
from user.models import User

class CreateListingSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = serializers.CharField()
    location = serializers.ChoiceField(choices=["chauncy", "west campus", "ross ade", "lafayette", "other"])
    user = serializers.CharField()
    hidden = serializers.BooleanField()
    saves = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source='saved_by')
    media = serializers.ListField(
        child=serializers.FileField(),
        required=True
    ),
    saves = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source='saved_by')

    

class DeleteListingSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user = serializers.CharField()

class UpdateListingSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    class Meta:
        model = Listing
        fields = ["title", "description", "price", "hidden", "sold"]

class ListingMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingMedia
        fields = ['file']

class SpecificListingSerializer(serializers.ModelSerializer):
    displayName = serializers.ReadOnlyField(source='user.displayName')
    uid = serializers.ReadOnlyField(source='user.uid')
    profilePicture = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'price', 'displayName',
            'original_price', 'category', 'hidden', 'views',
            'saved_by', 'dateListed', 'sold', 'uid', 'profilePicture', 'media'
        ]

    def get_profilePicture(self, obj):
        profile_pic = getattr(obj.user, 'profilePicture', None)
        if profile_pic and hasattr(profile_pic, 'url'):
            return profile_pic.url
        return None

    def get_media(self, obj):
        return [media.file.url for media in obj.media.all()]

class ListingSerializer(serializers.ModelSerializer):
    media = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            "id", "title", "description", "price", "original_price",
            "category", "user", "hidden", "views", "saved_by",
            "dateListed", "sold", "media"
        ]
        read_only_fields = ["id", "original_price", "user", "dateListed"]

    def get_media(self, obj):
        return [media.file.url for media in obj.media.all()]
