from django.db import models
from user.models import User

class Listing(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.FloatField()
    orginal_price = models.FloatField()
    category = models.CharField(max_length=255)
    userId = models.ForeignKey(User, on_delete=models.CASCADE)
    hidden = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    dateListed = models.DateTimeField(auto_now_add=True)
    sold = models.BooleanField(default=False)