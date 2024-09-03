from .views import *
from django.urls import path

urlpatterns = [
     path('list-notifications/', list_notifications, name='list-notifications'),
     path('unread-notifications/', unread_notifications, name='unread-notifications'),
     path('mark-as-read/', mark_as_read, name='mark-as-read'),
     path('delete-notification/', delete_notifications, name='delete-notification'),
     path('promo-notification/', promo_notifications, name='delete-notification'),
]
