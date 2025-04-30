from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.db.models import F
from django.db import IntegrityError

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
    reports = Report.objects.all()
    serializer = ReportSerializer(reports, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([AllowAny])
def get_reports_about_user(request, uid):
    """
    Fetch all reports against a specific user
    """
    reports = Report.objects.filter(reported_user__uid=uid)
    serializer = ReportSerializer(reports, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([AllowAny])
def get_reports_by_user(request, uid):
    """
    Fetch all reports filed by a specific user
    """
    reports = Report.objects.filter(user__uid=uid)
    serializer = ReportSerializer(reports, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def create_report(request):
    serializer = CreateReportSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    reported_user = User.objects.get(uid=data['reported_user'])
    user = User.objects.get(uid=data['user'])
    listing = None
    if data.get('listing'):
        listing = Listing.objects.get(id=data['listing'])

    try:
        Report.objects.create(
            title=data['title'],
            description=data['description'],
            user=user,
            reported_user=reported_user,
            listing=listing
        )
    except IntegrityError:
        return Response(
            {"error": f"{user.displayName} has already reported {reported_user.displayName}."},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({"message": "Report created"}, status=status.HTTP_201_CREATED)

@api_view(["DELETE"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def delete_report(request, report_id):
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return Response({"error": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

    report.delete()
    return Response({"message": "Report deleted successfully."}, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def ban_user(request, uid):
    """
    Ban a user by setting their 'banned' flag to True. Admin-only.
    """
    # fetch requester as User model, check admin flag
    try:
        requester = User.objects.get(uid=request.user.username)
    except User.DoesNotExist:
        return Response({"error": "Invalid requester."}, status=status.HTTP_403_FORBIDDEN)

    if not requester.admin:
        return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    try:
        user_to_ban = User.objects.get(uid=uid)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    user_to_ban.banned = True
    user_to_ban.save()
    return Response(
        {"message": f"User '{user_to_ban.displayName}' has been banned."},
        status=status.HTTP_200_OK
    )
