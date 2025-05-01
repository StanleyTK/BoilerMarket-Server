from django.db import models
from user.models import User
from listing.models import Listing

from django.core.validators import FileExtensionValidator


class Review(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_filed')
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_recieved')
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.TextField()
    rating = models.IntegerField(default=0)
    dateReviewed = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'reviewed_user'], name='unique_review_per_user_pair')
        ]

