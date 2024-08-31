from celery import shared_task
from django.conf import settings
from .models import *
from django.utils import timezone
import time
import os

@shared_task
def booking_notification(booking_id, user_id):
    user = User.objects.get(id=user_id)
    booking = Booking.objects.get(id=booking_id)
    try:
        notification = Notifications.objects.create(
            recipient=user,
            notification_type='BOOKING',
            message=f"Your booking {booking_id} was successful"
        )
        print(f"Notification created for user {user.id} regarding booking {booking_id}")
    except Exception as e:
        print(f"Failed to create notification for booking {booking_id}: {e}")  