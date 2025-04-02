from django.db import models
from user.models import User
from storages.backends.s3boto3 import S3Boto3Storage
from django.core.validators import FileExtensionValidator

def listing_media_upload_path(instance, filename):
    return f"users/{instance.listing.user.uid}/{instance.listing.id}/{filename}"

class Listing(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.FloatField()
    original_price = models.FloatField()
    category = models.CharField(max_length=255)
    location = models.CharField(max_length=255, default="other")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hidden = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    dateListed = models.DateTimeField(auto_now_add=True)
    sold = models.BooleanField(default=False)

class ListingMedia(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(
        upload_to=listing_media_upload_path,
        storage=S3Boto3Storage(),
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'mp4', 'mov'])]
    )
