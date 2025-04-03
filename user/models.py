from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage


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
    profilePicture = models.ImageField(
        storage=S3Boto3Storage(),
        upload_to=user_profile_picture_path,
        null=True,
        blank=True
    )
