from django.db import models

class Message(models.Model):
    mid = models.AutoField(primary_key=True)
    sender = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timeSent = models.DateTimeField(auto_now_add=True)
    room = models.ForeignKey('Room', on_delete=models.CASCADE)

class Room(models.Model):
    rid = models.AutoField(primary_key=True)
    seller = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='seller_room')
    buyer = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='buyer_room')
    listing = models.ForeignKey('listing.Listing', on_delete=models.CASCADE)
    class Meta:
        unique_together = ('seller', 'buyer', 'listing')