from rest_framework import serializers
from report.models import Report


class CreateReportSerializer(serializers.Serializer):
    user = serializers.CharField()
    reported_user = serializers.CharField()
    listing = serializers.CharField(required=False, allow_null=True)
    title = serializers.CharField()
    description = serializers.CharField()

class ReportSerializer(serializers.ModelSerializer):

    reported_uid = serializers.ReadOnlyField(source='reported_user.uid')
    uid = serializers.ReadOnlyField(source='user.uid')
    listing_id = serializers.ReadOnlyField(source='listing.id')
    
    class Meta:
        model = Report
        fields = [
            'id', 'reported_uid', 'uid', 'listing_id',
            'title', 'description', 'dateReported'
        ]

