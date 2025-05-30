from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage
from django.utils.timezone import now


def user_profile_picture_path(instance, filename):
    # Save to: users/<uid>/profile_picture.<ext>
    ext = filename.split('.')[-1]
    return f'users/{instance.uid}/profile_picture.{ext}'



class User(models.Model):
    uid = models.CharField(max_length=255, primary_key=True)
    email = models.EmailField()
    purdueEmail = models.EmailField(null=True, blank=True)
    purdueEmailVerified = models.BooleanField(default=False)
    purdueVerificationToken = models.CharField(max_length=255, null=True, blank=True)
    purdueVerificationLastSent = models.DateTimeField(null=True, blank=True)
    displayName = models.CharField(max_length=255)
    rating = models.FloatField(default=0)
    bio = models.TextField(null=True, blank=True)
    admin = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)
    appeal = models.TextField(null=True, blank=True)
    blockedUsers = models.ManyToManyField('self', symmetrical=False, related_name='blocked_by', blank=True)

    profilePicture = models.ImageField(
        storage=S3Boto3Storage(),
        upload_to=user_profile_picture_path,
        null=True,
        blank=True
    )

    def get_history(self):
        return self.viewed_listings.all()[:6]


class History(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='viewed_listings')
    listing = models.ForeignKey('listing.Listing', on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(default=now)

    class Meta:
        ordering = ['-viewed_at']
        unique_together = ('user', 'listing')