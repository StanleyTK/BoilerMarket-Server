from django.db import models

class User(models.Model):
    uid = models.CharField(max_length=255, primary_key=True)
    email = models.EmailField()
    purdueEmail = models.EmailField(null=True, blank=True)
    purdueEmailVerified = models.BooleanField(default=False)
    displayName = models.CharField(max_length=255)
    rating = models.FloatField(default=0)
    bio = models.TextField(null=True, blank=True)
    admin = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)
