from django.contrib.auth.models import User
from django.db import models
class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # Default user ID
    coin = models.CharField(max_length=50)
    quantity = models.FloatField()
    purchased_price = models.FloatField()
    purchased_at = models.DateTimeField(auto_now_add=True)
