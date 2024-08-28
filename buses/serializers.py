from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *

User = get_user_model()

class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = ['id', 'operator', 'name', 'bus_number', 'capacity', 'amenities', 'created_at']
        read_only_fields = ['created_at']

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'origin', 'destination', 'distance']
        
class ScheduleSerializer(serializers.ModelSerializer):
    bus = BusSerializer()
    route = RouteSerializer()

    class Meta:
        model = Schedule
        fields = ['id', 'bus', 'route', 'departure_time', 'arrival_time', 'price', 'currency']

class ScheduleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'bus', 'route', 'departure_time', 'arrival_time', 'price', 'currency']

class BookingSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    schedule = ScheduleSerializer()

    class Meta:
        model = Booking
        fields = ['id', 'user', 'schedule', 'seats_booked', 'total_price', 'booking_date', 'status']

class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'user', 'schedule', 'seats_booked', 'status']

    def create(self, validated_data):
        booking = Booking.objects.create(**validated_data)
        return booking