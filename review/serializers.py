from rest_framework import serializers
from review.models import Review


class CreateReviewSerializer(serializers.Serializer):
    user = serializers.CharField()
    reviewed_user = serializers.CharField()
    listing = serializers.CharField(required=False, allow_null=True)
    comment = serializers.CharField()
    rating = serializers.IntegerField()

class ReviewSerializer(serializers.ModelSerializer):

    reviewed_uid = serializers.ReadOnlyField(source='reviewed_user.uid')
    uid = serializers.ReadOnlyField(source='user.uid')
    listing_id = serializers.ReadOnlyField(source='listing.id')
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewed_uid', 'uid', 'listing_id',
            'comment', 'rating', 'dateReviewed'
        ]

