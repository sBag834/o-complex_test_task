from django.db import models


class SearchHistory(models.Model):
    city = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40, db_index=True)

    def __str__(self):
        return f"{self.city} ({self.timestamp})"