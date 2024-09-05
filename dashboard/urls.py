from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    # path('notifications/send/', views.admin_notification, name='admin_notification'),
    path('create-notification/', views.notification_view, name='create_notification'),
]
