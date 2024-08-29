from django.contrib import admin
from .models import *

# Register your models here.
class BusAdmin(admin.ModelAdmin):
    list_display = ['operator', 'name', 'bus_number', 'capacity']
    search_fields = ['operator', 'name', 'bus_number', 'capacity']
    list_filter = ['operator', 'name', 'bus_number', 'capacity']
    
class RouteAdmin(admin.ModelAdmin):
    list_display = ['origin', 'destination', 'distance']
    search_fields = ['origin', 'destination', 'distance']
    list_filter = ['origin', 'distance']
    
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['bus', 'route', 'departure_time', 'arrival_time', 'price']
    search_fields = ['bus', 'route', 'price']
    list_filter = ['price', 'departure_time', 'arrival_time']
    
class BookingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'schedule', 'seats_booked', 'total_price', 'booking_date', 'status']
    search_fields = ['user', 'schedule']
    list_filter = ['total_price', 'booking_date', 'seats_booked']
    
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'amount', 'status']
    list_filter = ['status']
    
admin.site.register(Bus, BusAdmin)
admin.site.register(Route, RouteAdmin)
admin.site.register(BusImage)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Booking, BookingsAdmin)
admin.site.register(Payment, PaymentAdmin)