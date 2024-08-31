from django.db import models
from users.models import *
from buses.models import *

# Create your models here.
class Notifications(models.Model):
    NOTICATION_TYPES = (
        ('SYSTEM', 'system'),
        ('BOOKING', 'booking'), 
        ('REMINDER', 'reminder')
    )
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTICATION_TYPES)
    message = models.CharField(max_length=2560)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.message} for {self.recipient}"
    
    