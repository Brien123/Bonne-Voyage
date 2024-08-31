from rest_framework import serializers
from .models import Notifications
from users.models import *
from buses.models import *

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = '__all__'