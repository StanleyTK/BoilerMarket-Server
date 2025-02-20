from django.db import models
from user.models import User

class Listing(models.Model):
    id = models.AutoField(primary_key=True)
    price = models.FloatField()
    orginal_price = models.FloatField()
    category = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    hidden = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    userId = models.ForeignKey(User, on_delete=models.CASCADE)
    dateListed = models.DateTimeField(auto_now_add=True)
    sold = models.BooleanField(default=False)