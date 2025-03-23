from django.db import models

class Message(models.Model):
    mid = models.AutoField(primary_key=True)
    sender = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timeSent = models.DateTimeField(auto_now_add=True)