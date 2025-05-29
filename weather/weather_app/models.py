from django.db import models
from django.contrib.auth.models import User

class SearchHistory(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, blank=True)
    city = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    count = models.PositiveIntegerField(default=1)

    class Meta:
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['user']),
        ]