from rest_framework import serializers
from listing.models import Listing


class CreateListingSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = serializers.CharField()
    userId = serializers.CharField()
    hidden = serializer.BooleanField()
    
    


class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = [
            "id", "title", "description", "price", "category",
            "condition", "location", "seller"
        ]
        read_only_fields = ["id", "seller"]