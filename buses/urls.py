from django.urls import path
from .views import *

urlpatterns = [
    path('create-bus/', create_bus, name='bus'),
    path('create-schedule/', create_schedule, name='schedule'),
    path('buses/', buses, name='buses'),
    path('bus-detail/<id>', bus_detail_view, name='bus_detail'),
]
