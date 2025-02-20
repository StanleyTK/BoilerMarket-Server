from rest_framework import serializers
from listing.models import Listing



class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = [
            "id", "title", "description", "price", "category",
            "condition", "location", "seller"
        ]
        read_only_fields = ["id", "seller"]