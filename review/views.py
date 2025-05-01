import django
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.db.models import F

from datetime import timedelta
from django.db import IntegrityError, transaction

from firebase_admin import auth as firebase_admin_auth

from server.authentication import FirebaseAuthentication, FirebaseEmailVerifiedAuthentication
from review.serializers import ReviewSerializer, CreateReviewSerializer
from review.models import Review
from listing.models import Listing
from user.models import User

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([AllowAny])
def get_all_reviews(request):
    """
    Fetch all reviews
    """
    reviews = Review.objects
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([AllowAny])
def get_reviews_about_user(request, uid):
    """
    Fetch all reviews about a user
    """
    reviews = Review.objects.filter(reviewed_user=uid)
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([AllowAny])
def get_reviews_by_user(request, uid):
    """
    Fetch all reviews by a user
    """
    reviews = Review.objects.filter(user=uid)
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def create_review(request):
    serializer = CreateReviewSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    reviewed_user = User.objects.get(uid=validated_data['reviewed_user'])
    user = User.objects.get(uid=validated_data['user'])

    if user.uid == reviewed_user.uid: 
        return Response({"error": "You cannot review yourself."}, status=status.HTTP_400_BAD_REQUEST)

    listing = None
    if 'listing' in validated_data:
        listing = Listing.objects.get(id=validated_data['listing'])

    try:
        with transaction.atomic():
            Review.objects.create(
                comment=validated_data['comment'],
                rating=validated_data['rating'],
                user=user,
                reviewed_user=reviewed_user,
                listing=listing
            )

            # Update average rating and number of reviews
            all_reviews = Review.objects.filter(reviewed_user=reviewed_user.uid)
            total_rating = sum(review.rating for review in all_reviews)
            reviewed_user.rating = total_rating / all_reviews.count()
            print("Saving new rating info...")
            print("Average Rating:", reviewed_user.rating)
            reviewed_user.save()

    except IntegrityError:
        return Response(
            {"error": f"{user.displayName} has already reviewed {reviewed_user.displayName}."},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({"message": "Review created"}, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@authentication_classes([FirebaseEmailVerifiedAuthentication])
@permission_classes([IsAuthenticated])
def delete_review(request, review_id):
    review = Review.objects.get(id=review_id)
    if not review:
        return Response({"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND)


    review.delete()
    
    return Response({"message": "Review deleted successfully."}, status=status.HTTP_200_OK)