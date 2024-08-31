from django.shortcuts import render
from .models import Notifications
from users.models import *
from .models import *
from django.utils import timezone
from .serializers import *
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .tasks import initiate_payment_task
from django.shortcuts import get_object_or_404
from campay.sdk import Client as CamPayClient
from dotenv import load_dotenv
import time
import os
from .serializers import *

# Create your views here.
user = get_user_model()

@api_view(['GET'])
def list_notifications(request):
    user = request.user
    try:
        notifications = Notifications.objects.get(recipient=user)
        serializer = NotificationSerializer(notifications, many=True)
        response_data = {
            "status": "success",
            "message": "notification created successfully",
            "data": serializer.data,
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def unread_notifications(request):
    user = request.user
    try:
        notifications = Notifications.objects.get(recipient=user, is_read=False)
        serializer = NotificationSerializer(notifications, many=True)
        response_data = {
            "status": "success",
            "message": "notification created successfully",
            "data": serializer.data,
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def mark_as_read(request, notification_id):
    user = request.user
    try:
        notification = Notifications.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()
        response_data = {
            "status": "success",
            "message": "message successfully read"
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def delete_notifications(request, notification_id):
    try:
        notification = Notifications.objects.get(id=notification_id)
        # notification.is_read = True
        notification.delete()
        response_data = {
            "status": "success",
            "message": "message successfully deleted"
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def promo_notifications(request):
    user = request.user
    if user.role != User.OPERATOR:
        return Response({"error": "User not authorized to create a notification."}, status=status.HTTP_403_FORBIDDEN)
    
    success_count = 0
    failure_count = 0
    errors = []
    
    try:
        with transaction.atomic():
            customers = User.objects.filter(role=CUSTOMER)
            for customer in customers:
                serializer = NotificationSerializer(data={**request.data, 'user': customer.id}, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append(serializer.errors)
                    
        response_data = {
            "message": "Notification process completed",
            "status": "success" if success_count > 0 else "failure",
            "notifications_sent": success_count,
            "notifications_failed": failure_count,
            "errors": errors
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)