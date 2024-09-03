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
from buses.tasks import initiate_payment_task
from .tasks import booking_notification
from django.shortcuts import get_object_or_404
from campay.sdk import Client as CamPayClient
from dotenv import load_dotenv
import time
import os
from .serializers import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.
user = get_user_model()

@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the response'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                    'data': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Notification ID'),
                                'recipient': openapi.Schema(type=openapi.TYPE_INTEGER, description='Recipient ID'),
                                'message': openapi.Schema(type=openapi.TYPE_STRING, description='Notification message'),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Creation timestamp'),
                                'updated_at': openapi.Schema(type=openapi.TYPE_STRING, description='Last update timestamp'),
                            }
                        ),
                        description='List of notifications'
                    )
                }
            )
        ),
        500: openapi.Response(
            'Internal Server Error',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )
        )
    },
    operation_description="Retrieve a list of notifications for the logged-in user."
)
@api_view(['GET'])
def list_notifications(request):
    user = request.user
    try:
        notifications = Notifications.objects.filter(recipient=user)
        serializer = NotificationSerializer(notifications, many=True)
        response_data = {
            "status": "success",
            "message": "Notifications retrieved successfully",
            "data": serializer.data,
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
    
@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the response'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                    'data': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Notification ID'),
                                'recipient': openapi.Schema(type=openapi.TYPE_INTEGER, description='Recipient ID'),
                                'message': openapi.Schema(type=openapi.TYPE_STRING, description='Notification message'),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Creation timestamp'),
                                'updated_at': openapi.Schema(type=openapi.TYPE_STRING, description='Last update timestamp'),
                                'is_read': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Read status of the notification'),
                            }
                        ),
                        description='List of unread notifications'
                    )
                }
            )
        ),
        404: openapi.Response(
            'Not Found',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the response'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )
        ),
        500: openapi.Response(
            'Internal Server Error',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )
        )
    },
    operation_description="Retrieve a list of unread notifications for the logged-in user."
)
@api_view(['GET'])
def unread_notifications(request):
    user = request.user
    try:
        notifications = Notifications.objects.filter(recipient=user, is_read=False)
        serializer = NotificationSerializer(notifications, many=True)
        response_data = {
            "status": "success",
            "message": "Unread notifications retrieved successfully",
            "data": serializer.data,
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'notification_id',
            openapi.IN_PATH,
            description="ID of the notification to mark as read",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the response'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                }
            )
        ),
        404: openapi.Response(
            'Not Found',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message indicating notification was not found'),
                }
            )
        ),
        500: openapi.Response(
            'Internal Server Error',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message indicating internal server issue'),
                }
            )
        )
    },
    operation_description="Mark a specific notification as read based on the notification ID."
)
@api_view(['POST'])
def mark_as_read(request, notification_id):
    user = request.user
    try:
        notification = Notifications.objects.get(id=notification_id, recipient=user)
        notification.is_read = True
        notification.save()
        response_data = {
            "status": "success",
            "message": "Notification successfully marked as read"
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except Notifications.DoesNotExist:
        return Response({"error": "Notification not found or not accessible by the user"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
    
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'notification_id',
            openapi.IN_PATH,
            description="ID of the notification to delete",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the response'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                }
            )
        ),
        404: openapi.Response(
            'Not Found',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message indicating notification was not found'),
                }
            )
        ),
        500: openapi.Response(
            'Internal Server Error',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message indicating internal server issue'),
                }
            )
        )
    },
    operation_description="Delete a specific notification based on the notification ID."
)
@api_view(['POST'])
def delete_notifications(request, notification_id):
    try:
        notification = Notifications.objects.get(id=notification_id)
        notification.delete()
        response_data = {
            "status": "success",
            "message": "Notification successfully deleted"
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except Notifications.DoesNotExist:
        return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING, description='Title of the notification'),
            'message': openapi.Schema(type=openapi.TYPE_STRING, description='Message content of the notification'),
        },
        required=['title', 'message']
    ),
    responses={
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Status message of the notification process'),
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Overall status of the operation'),
                    'notifications_sent': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of notifications successfully sent'),
                    'notifications_failed': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of notifications that failed'),
                    'errors': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT), description='List of errors for failed notifications')
                }
            )
        ),
        403: openapi.Response(
            'Forbidden',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message indicating the user is not authorized')
                }
            )
        ),
        500: openapi.Response(
            'Internal Server Error',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message indicating an internal server issue')
                }
            )
        )
    },
    operation_description="Send promotional notifications to all customers. Only available to users with the OPERATOR role."
)
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