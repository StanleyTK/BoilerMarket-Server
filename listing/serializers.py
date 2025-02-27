from rest_framework import serializers
from listing.models import Listing
from user.models import User

class CreateListingSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = serializers.CharField()
    user = serializers.CharField()
    hidden = serializers.BooleanField()

class DeleteListingSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user = serializers.CharField()
    
class UpdateListingSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    class Meta:
        model = Listing
        fields = ["title", "description", "price"]
    

class SpecificListingSerializer(serializers.ModelSerializer):
    displayName = serializers.ReadOnlyField(source='user.displayName')
    uid = serializers.ReadOnlyField(source='user.uid')

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'price', 'displayName',
            'original_price', 'category', 'hidden', 'views',
            'saves', 'dateListed', 'sold', 'uid'
        ]


class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "description",
            "price",
            "original_price",
            "category",
            "user",
            "hidden",
            "views",
            "saves",
            "dateListed",
            "sold"
        ]
        read_only_fields = ["id", "orignal_price",  "userId", "dateListed"]