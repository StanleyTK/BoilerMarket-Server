from django.db import models
from user.models import User
from listing.models import Listing

from django.core.validators import FileExtensionValidator


class Report(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_filed')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_recieved')
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    dateReported = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'reported_user'], name='unique_report_per_user_pair')
        ]

