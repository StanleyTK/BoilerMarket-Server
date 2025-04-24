import django
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.db.models import F

from datetime import timedelta
from django.db import IntegrityError

from firebase_admin import auth as firebase_admin_auth

from server.authentication import FirebaseAuthentication, FirebaseEmailVerifiedAuthentication
from report.serializers import ReportSerializer, CreateReportSerializer
from report.models import Report
from listing.models import Listing
from user.models import User

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([AllowAny])
def get_all_reports(request):
    """
    Fetch all reports
    """
    reports = Report.objects
    serializer = ReportSerializer(reports, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([AllowAny])
def get_reports_about_user(request, uid):
    """
    Fetch all reports
    """
    reports = Report.objects.filter(reported_user=uid)
    serializer = ReportSerializer(reports, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([AllowAny])
def get_reports_by_user(request, uid):
    """
    Fetch all reports
    """
    reports = Report.objects.filter(user=uid)
    serializer = ReportSerializer(reports, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def create_report(request):
    serializer = CreateReportSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    reported_user = User.objects.get(uid=validated_data['reported_user'])
    user = User.objects.get(uid=validated_data['user'])

    listing = None
    if 'listing' in validated_data:
        listing = Listing.objects.get(id=validated_data['listing'])

    try:
        Report.objects.create(
            title=validated_data['title'],
            description=validated_data['description'],
            user=user,
            reported_user=reported_user,
            listing=listing
        )
    except IntegrityError:
        return Response({"error": "User has already reported this user."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Report created"}, status=status.HTTP_201_CREATED)

@api_view(["DELETE"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def delete_report(request, report_id):
    report = Report.objects.get(id=report_id)
    if not report:
        return Response({"error": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

    report.delete()
    return Response({"message": "Report deleted successfully."}, status=status.HTTP_200_OK)